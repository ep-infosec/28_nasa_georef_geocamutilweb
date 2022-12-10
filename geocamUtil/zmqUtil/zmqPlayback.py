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
import logging

from zmq.eventloop import ioloop
ioloop.install()

from geocamUtil.zmqUtil.util import zmqLoop, LogParser
from geocamUtil.zmqUtil.publisher import ZmqPublisher


class ZmqPlayback(object):
    def __init__(self, logPath, opts):
        self.logPath = logPath
        self.logFile = None
        self.log = None
        self.opts = opts
        self.publisher = ZmqPublisher(**ZmqPublisher.getOptionValues(opts))
        self.publishTimer = None
        print 'topics:', self.opts.topic

    def start(self):
        self.publisher.start()

        # the delay gives a chance to connect to central before publishing
        self.publishTimer = ioloop.DelayedCallback(self.playLog, 100)
        self.publishTimer.start()

    def playLog(self):
        self.logFile = open(self.logPath, 'rb')
        self.log = LogParser(self.logFile)
        i = 0
        for rec in self.log:
            topicMatch = False
            if self.opts.topic:
                for topic in self.opts.topic:
                    if rec.msg.startswith(topic):
                        topicMatch = True
                        break
            else:
                topicMatch = True

            if topicMatch:
                self.publisher.pubStream.send(rec.msg)
                if i % 100 == 0:
                    sys.stdout.write('.')
                    sys.stdout.flush()
                i += 1
        print
        print 'message count:', i


def main():
    import optparse
    parser = optparse.OptionParser('usage: %prog <zmqCentral-messages-xxx.txt>')
    parser.add_option('-t', '--topic',
                      action='append',
                      help='Only print specified topics, can specify multiple times')
    ZmqPublisher.addOptions(parser, 'zmqPlayback')
    opts, args = parser.parse_args()
    if len(args) != 1:
        parser.error('expected exactly 1 arg')
    logging.basicConfig(level=logging.DEBUG)

    pb = ZmqPlayback(args[0], opts)
    pb.start()

    zmqLoop()

if __name__ == '__main__':
    main()
