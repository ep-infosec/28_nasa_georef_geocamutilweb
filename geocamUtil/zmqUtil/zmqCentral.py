#!/usr/bin/env python
#__BEGIN_LICENSE__
# Copyright (c) 2017, United States Government, as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All rights reserved.
#
# The GeoRef platform is licensed under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0.
#
# Unless required by applicable law or agreed to in writing, software distributed
# under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
# CONDITIONS OF ANY KIND, either express or implied. See the License for the
# specific language governing permissions and limitations under the License.
#__END_LICENSE__

import sys
import os
import logging
import datetime
import time
import traceback
import atexit
import random

import zmq
from zmq.eventloop.zmqstream import ZMQStream
from zmq.devices import ThreadDevice
from zmq.eventloop import ioloop
ioloop.install()

from geocamUtil import anyjson as json
from geocamUtil.zmqUtil.util import (DEFAULT_CENTRAL_RPC_PORT,
                                     DEFAULT_CENTRAL_SUBSCRIBE_PORT,
                                     DEFAULT_CENTRAL_PUBLISH_PORT,
                                     getTimestamp,
                                     parseEndpoint,
                                     hasAttachments,
                                     parseMessage)

# pylint: disable=E1101

THIS_MODULE = 'zmqCentral'
DEFAULT_KEEPALIVE_US = 10000000
MONITOR_ENDPOINT = 'inproc://monitor'
INJECT_ENDPOINT = 'inproc://inject'


class ZmqCentral(object):
    def __init__(self, opts):
        self.opts = opts
        self.info = {}
        self.messageLogPath = None
        self.messageLog = None
        self.rpcStream = None
        self.disconnectTimer = None
        self.injectStream = None
        self.monStream = None
        self.forwarder = None
        self.logDir = None
        self.context = None
        self.consoleLogPath = None

    def announceConnect(self, moduleName, params):
        logging.info('module %s connected', moduleName)
        self.injectStream.send('central.connect.%s:%s'
                               % (moduleName, json.dumps(params)))

    def announceDisconnect(self, moduleName):
        logging.info('module %s disconnected', moduleName)
        self.injectStream.send('central.disconnect.%s:%s'
                               % (moduleName,
                                  json.dumps({'timestamp': str(getTimestamp())})))

    def logMessage(self, msg, posixTime=None, attachmentDir='-'):
        mlog = self.messageLog
        mlog.write('@@@ %d %d %s ' % (getTimestamp(posixTime), len(msg), attachmentDir))
        mlog.write(msg)
        mlog.write('\n')

    def logMessageWithAttachments0(self, msg):
        parsed = parseMessage(msg)
        posixTime = time.time()

        # construct attachment directory
        dt = datetime.datetime.utcfromtimestamp(posixTime)
        dateText = dt.strftime('%Y-%m-%d')
        timeText = dt.strftime('%H-%M-%S') + '.%06d' % dt.microsecond
        uniq = '%08x' % random.getrandbits(32)
        attachmentSuffix = os.path.join('attachments',
                                        dateText,
                                        timeText,
                                        parsed['topic'],
                                        uniq)
        attachmentPath = os.path.join(self.logDir, attachmentSuffix)
        os.makedirs(attachmentPath)

        # write attachments to attachment directory
        for attachment in parsed['attachments']:
            fullName = os.path.join(attachmentPath, attachment.get_filename())
            open(fullName, 'wb').write(attachment.get_payload())

        # log message with a pointer to the attachment directory
        self.logMessage(':'.join((parsed['topic'], parsed['json'])),
                        posixTime,
                        attachmentSuffix)

    def logMessageWithAttachments(self, msg):
        try:
            return self.logMessageWithAttachments0(msg)
        except:  # pylint: disable=W0702
            self.logException('logging message with attachments')

    def handleHeartbeat(self, params):
        moduleName = params['module'].encode('utf-8')
        now = getTimestamp()

        oldInfo = self.info.get(moduleName, None)
        if oldInfo:
            if oldInfo.get('pub', None) != params.get('pub', None):
                self.announceDisconnect(moduleName)
                self.announceConnect(moduleName, params)
        else:
            self.announceConnect(moduleName, params)

        self.info[moduleName] = params
        keepalive = params.get('keepalive', DEFAULT_KEEPALIVE_US)
        params['timeout'] = now + keepalive
        return 'ok'

    def handleInfo(self):
        return self.info

    def logException(self, whileClause):
        errClass, errObject, errTB = sys.exc_info()[:3]
        errText = '%s.%s: %s' % (errClass.__module__,
                                 errClass.__name__,
                                 str(errObject))
        logging.warning(''.join(traceback.format_tb(errTB)))
        logging.warning(errText)
        logging.warning('[error while %s at time %s]', whileClause, getTimestamp())

    def handleMessages(self, messages):
        for msg in messages:
            if self.messageLog:
                if hasAttachments(msg):
                    self.logMessageWithAttachments(msg)
                else:
                    self.logMessage(msg)
            if msg.startswith('central.heartbeat.'):
                try:
                    _topic, body = msg.split(':', 1)
                    self.handleHeartbeat(json.loads(body))
                except:  # pylint: disable=W0702
                    self.logException('handling heartbeat')

    def handleRpcCall(self, messages):
        for msg in messages:
            try:
                call = json.loads(msg)
                callId = call['id']
            except:  # pylint: disable=W0702
                self.rpcStream.send(json.dumps({'result': None,
                                                'error': 'malformed request'}))

            try:
                method = call['method']
                _params = call['params']
                if method == 'info':
                    result = self.handleInfo()
                else:
                    raise ValueError('unknown method %s' % method)
                self.rpcStream.send(json.dumps({'result': result,
                                                'error': None,
                                                'id': callId}))
            except:  # pylint: disable=W0702
                self.logException('handling rpc message')
                errClass, errObject = sys.exc_info()[:2]
                errText = '%s.%s: %s' % (errClass.__module__,
                                         errClass.__name__,
                                         str(errObject))
                self.rpcStream.send(json.dumps({'result': None,
                                                'error': errText,
                                                'id': callId}))

    def handleDisconnectTimer(self):
        now = getTimestamp()
        disconnectModules = []
        for moduleName, entry in self.info.iteritems():
            timeout = entry.get('timeout', None)
            if timeout is not None and now > timeout:
                disconnectModules.append(moduleName)
        for moduleName in disconnectModules:
            self.announceDisconnect(moduleName)
            del self.info[moduleName]

    def readyLog(self, pathTemplate, timestamp):
        if '%s' in pathTemplate:
            timeText = timestamp.strftime('%Y-%m-%d-%H-%M-%S')
            logFile = pathTemplate % timeText
        else:
            logFile = pathTemplate
        if not os.path.exists(self.logDir):
            os.makedirs(self.logDir)
        logPath = os.path.join(self.logDir, logFile)
        if '%s' in pathTemplate:
            latestPath = os.path.join(self.logDir, pathTemplate % 'latest')
            if os.path.islink(latestPath):
                os.unlink(latestPath)
        os.symlink(logFile, latestPath)
        return logPath

    def start(self):
        # respect --bindInterface argument
        self.opts.rpcEndpoint = self.opts.rpcEndpoint.format(bindInterface=self.opts.bindInterface)
        self.opts.publishEndpoint = self.opts.publishEndpoint.format(bindInterface=self.opts.bindInterface)
        self.opts.subscribeEndpoint = self.opts.subscribeEndpoint.format(bindInterface=self.opts.bindInterface)

        # open log files
        now = datetime.datetime.utcnow()
        self.logDir = os.path.abspath(self.opts.logDir)
        if self.opts.messageLog != 'none':
            self.messageLogPath = self.readyLog(self.opts.messageLog, now)
            self.messageLog = open(self.messageLogPath, 'a')
        if self.opts.consoleLog != 'none':
            self.consoleLogPath = self.readyLog(self.opts.consoleLog, now)

        rootLogger = logging.getLogger()
        rootLogger.setLevel(logging.DEBUG)
        fmt = logging.Formatter('%(asctime)s - %(levelname)-7s - %(message)s')
        fmt.converter = time.gmtime

        if self.opts.consoleLog != 'none':
            fh = logging.FileHandler(self.consoleLogPath)
            fh.setFormatter(fmt)
            fh.setLevel(logging.DEBUG)
            rootLogger.addHandler(fh)

        if self.opts.foreground:
            ch = logging.StreamHandler()
            ch.setLevel(logging.DEBUG)
            ch.setFormatter(fmt)
            rootLogger.addHandler(ch)

        # daemonize
        if self.opts.foreground:
            logging.info('staying in foreground')
        else:
            logging.info('daemonizing')
            pid = os.fork()
            if pid != 0:
                os._exit(0)
            os.setsid()
            pid = os.fork()
            if pid != 0:
                os._exit(0)
            os.chdir('/')
            os.close(1)
            os.close(2)
            nullFd = os.open('/dev/null', os.O_RDWR)
            os.dup2(nullFd, 1)
            os.dup2(nullFd, 2)

        try:
            # set up zmq
            self.context = zmq.Context.instance()
            self.rpcStream = ZMQStream(self.context.socket(zmq.REP))
            self.rpcStream.bind(self.opts.rpcEndpoint)
            logging.info('bound rpcEndpoint %s', self.opts.rpcEndpoint)
            self.rpcStream.on_recv(self.handleRpcCall)

            self.forwarder = ThreadDevice(zmq.FORWARDER, zmq.SUB, zmq.PUB)
            self.forwarder.setsockopt_in(zmq.IDENTITY, THIS_MODULE)
            self.forwarder.setsockopt_out(zmq.IDENTITY, THIS_MODULE)
            self.forwarder.setsockopt_in(zmq.SUBSCRIBE, '')
            # self.forwarder.setsockopt_out(zmq.HWM, self.opts.highWaterMark)
            self.forwarder.bind_in(self.opts.subscribeEndpoint)
            logging.info('bound subscribeEndpoint %s', self.opts.subscribeEndpoint)
            self.forwarder.bind_in(INJECT_ENDPOINT)
            self.forwarder.bind_out(self.opts.publishEndpoint)
            logging.info('bound publishEndpoint %s', self.opts.publishEndpoint)
            self.forwarder.bind_out(MONITOR_ENDPOINT)
            for entry in self.opts.subscribeTo:
                try:
                    moduleName, endpoint = entry.split('@')
                    endpoint = parseEndpoint(endpoint)
                except ValueError:
                    raise ValueError('--subscribeTo argument "%s" is not in the format "<moduleName>@<endpoint>"' % entry)
                self.forwarder.connect_in(endpoint)
                self.info[moduleName] = {'module': moduleName,
                                         'pub': endpoint}
            self.forwarder.start()
            time.sleep(0.1)  # wait for forwarder to bind sockets

            self.monStream = ZMQStream(self.context.socket(zmq.SUB))
            self.monStream.setsockopt(zmq.SUBSCRIBE, '')
            self.monStream.connect(MONITOR_ENDPOINT)
            self.monStream.on_recv(self.handleMessages)

            self.injectStream = ZMQStream(self.context.socket(zmq.PUB))
            self.injectStream.connect(INJECT_ENDPOINT)

            self.disconnectTimer = ioloop.PeriodicCallback(self.handleDisconnectTimer, 5000)
            self.disconnectTimer.start()

        except:  # pylint: disable=W0702
            errClass, errObject, errTB = sys.exc_info()[:3]
            errText = '%s.%s: %s' % (errClass.__module__,
                                     errClass.__name__,
                                     str(errObject))
            logging.error(''.join(traceback.format_tb(errTB)))
            logging.error(errText)
            logging.error('[error during startup -- exiting]')
            sys.exit(1)

    def shutdown(self):
        if self.messageLog:
            self.messageLog.close()
            self.messageLog = None


def main():
    import optparse
    parser = optparse.OptionParser('usage: %prog')
    parser.add_option('-b', '--bindInterface',
                      default='127.0.0.1',
                      help='Interface to bind endpoints to [%default]')
    parser.add_option('-r', '--rpcEndpoint',
                      default='tcp://{bindInterface}:%s' % DEFAULT_CENTRAL_RPC_PORT,
                      help='Endpoint to listen on for RPC requests [%default]')
    parser.add_option('-s', '--subscribeEndpoint',
                      default='tcp://{bindInterface}:%s' % DEFAULT_CENTRAL_SUBSCRIBE_PORT,
                      help='Endpoint to listen for messages on [%default]')
    parser.add_option('-p', '--publishEndpoint',
                      default='tcp://{bindInterface}:%s' % DEFAULT_CENTRAL_PUBLISH_PORT,
                      help='Endpoint to forward messages to [%default]')
    parser.add_option('--subscribeTo',
                      default=[],
                      action='append',
                      help='Non-central-aware publisher to subscribe to (format "<moduleName>@<endpoint>"; can specify multiple times)')
    parser.add_option('-d', '--logDir',
                      default='log',
                      help='Directory to place logs in [%default]')
    parser.add_option('-m', '--messageLog',
                      default='zmqCentral-messages-%s.txt',
                      help='Log file for message traffic, or "none" [%default]')
    parser.add_option('-c', '--consoleLog',
                      default='zmqCentral-console-%s.txt',
                      help='Log file for debugging zmqCentral [%default]')
    parser.add_option('-f', '--foreground',
                      action='store_true', default=False,
                      help='Do not daemonize zmqCentral on startup')
    #parser.add_option('--highWaterMark',
    #                  default=10000, type='int',
    #                  help='High-water mark for publish socket (see 0MQ docs) [%default]')
    opts, args = parser.parse_args()
    if args:
        parser.error('expected no args')
    zc = ZmqCentral(opts)
    zc.start()
    atexit.register(zc.shutdown)
    ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    main()
