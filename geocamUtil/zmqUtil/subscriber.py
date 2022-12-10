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

# pylint: disable=E1101

import logging
import sys
import zmq
from zmq.eventloop.zmqstream import ZMQStream

from django.core import serializers

from geocamUtil import anyjson as json
from geocamUtil.zmqUtil.util import parseEndpoint, DEFAULT_CENTRAL_PUBLISH_PORT, LogParser
from geocamUtil.models.ExtrasDotField import convertToDotDictRecurse

SUBSCRIBER_OPT_DEFAULTS = {'centralHost': '127.0.0.1',
                           'moduleName': None,
                           'centralPublishEndpoint': 'tcp://{centralHost}:%d'
                           % DEFAULT_CENTRAL_PUBLISH_PORT,
                           'replay': None}


class ZmqSubscriber(object):
    def __init__(self,
                 moduleName,
                 centralHost=SUBSCRIBER_OPT_DEFAULTS['centralHost'],
                 context=None,
                 centralPublishEndpoint=SUBSCRIBER_OPT_DEFAULTS['centralPublishEndpoint'],
                 replay=None):
        self.moduleName = moduleName
        self.centralHost = centralHost

        if context is None:
            context = zmq.Context.instance()
        self.context = context

        self.centralPublishEndpoint = parseEndpoint(centralPublishEndpoint,
                                                    defaultPort=DEFAULT_CENTRAL_PUBLISH_PORT,
                                                    centralHost=self.centralHost)
        self.replayPaths = replay
        if self.replayPaths is None:
            self.replayPaths = []

        self.handlers = {}
        self.counter = 0
        self.deserializer = serializers.get_deserializer('json')
        self.stream = None

    @classmethod
    def addOptions(cls, parser, defaultModuleName):
        if not parser.has_option('--centralHost'):
            parser.add_option('--centralHost',
                              default=SUBSCRIBER_OPT_DEFAULTS['centralHost'],
                              help='Host where central runs [%default]')
        if not parser.has_option('--moduleName'):
            parser.add_option('--moduleName',
                              default=defaultModuleName,
                              help='Name to use for this module [%default]')
        if not parser.has_option('--centralPublishEndpoint'):
            parser.add_option('--centralPublishEndpoint',
                              default=SUBSCRIBER_OPT_DEFAULTS['centralPublishEndpoint'],
                              help='Endpoint where central publishes messages [%default]')
        if not parser.has_option('--replay'):
            parser.add_option('--replay',
                              action='append',
                              help='Replay specified message log (can specify multiple times), or use - to read from stdin')

    @classmethod
    def getOptionValues(cls, opts):
        result = {}
        for key in SUBSCRIBER_OPT_DEFAULTS.iterkeys():
            val = getattr(opts, key, None)
            if val is not None:
                result[key] = val
        return result

    def start(self):
        sock = self.context.socket(zmq.SUB)
        self.stream = ZMQStream(sock)
        # causes problems with multiple instances
        #self.stream.setsockopt(zmq.IDENTITY, self.moduleName)
        self.stream.connect(self.centralPublishEndpoint)
        logging.info('zmq.subscriber: connected to central at %s', self.centralPublishEndpoint)
        self.stream.on_recv(self.routeMessages)

    def routeMessages(self, messages):
        for msg in messages:
            self.routeMessage(msg)

    def routeMessage(self, msg):
        colonIndex = msg.find(':')
        topic = msg[:(colonIndex + 1)]
        body = msg[(colonIndex + 1):]

        handled = 0
        for topicPrefix, registry in self.handlers.iteritems():
            if topic.startswith(topicPrefix):
                for handler in registry.itervalues():
                    handler(topic[:-1], body)
                    handled = 1

        return handled

    def subscribeRaw(self, topicPrefix, handler):
        topicRegistry = self.handlers.setdefault(topicPrefix, {})
        if not topicRegistry:
            logging.info('zmq.subscriber: subscribe %s', topicPrefix)
            self.stream.setsockopt(zmq.SUBSCRIBE, topicPrefix)
        handlerId = (topicPrefix, self.counter)
        topicRegistry[self.counter] = handler
        self.counter += 1
        return handlerId

    def subscribeJson(self, topicPrefix, handler):
        def jsonHandler(topicPrefix, body):
            return handler(topicPrefix, convertToDotDictRecurse(json.loads(body)))
        return self.subscribeRaw(topicPrefix, jsonHandler)

    def subscribeDjango(self, topicPrefix, handler):
        def djangoHandler(topicPrefix, body):
            obj = json.loads(body)
            dataText = json.dumps([obj['data']])
            modelInstance = list(self.deserializer(dataText))[0]
            return handler(topicPrefix, modelInstance.object)
        return self.subscribeRaw(topicPrefix, djangoHandler)

    def unsubscribe(self, handlerId):
        topicPrefix, index = handlerId
        topicRegistry = self.handlers[topicPrefix]
        del topicRegistry[index]
        if not topicRegistry:
            logging.info('zmq.subscriber: unsubscribe %s', topicPrefix)
            self.stream.setsockopt(zmq.UNSUBSCRIBE, topicPrefix)

    def connect(self, endpoint):
        self.stream.connect(endpoint)

    def replay(self):
        numReplayed = 0
        numHandled = 0
        for replayPath in self.replayPaths:
            print '=== replaying messages from %s' % replayPath
            if replayPath == '-':
                replayFile = sys.stdin
            else:
                replayFile = open(replayPath, 'rb')
            stream = LogParser(replayFile)
            for rec in stream:
                numReplayed += 1
                numHandled += self.routeMessage(rec.msg)

                if numReplayed % 10000 == 0:
                    print 'replayed %d messages, %d handled' % (numReplayed, numHandled)
