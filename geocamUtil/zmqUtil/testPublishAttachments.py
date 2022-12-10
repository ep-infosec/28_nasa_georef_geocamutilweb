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

import os
import logging

from zmq.eventloop import ioloop
ioloop.install()

from geocamUtil.zmqUtil.publisher import ZmqPublisher
from geocamUtil.zmqUtil.util import zmqLoop

thisDir = os.path.dirname(__file__)
TEST_MESSAGE = open(os.path.join(thisDir, 'exampleMessageWithAttachment.txt'), 'rb').read()


def pubMessage(p):
    topic = 'dds.Resolve.RESOLVE_CAM_ProcessedImage'
    body = TEST_MESSAGE
    logging.debug('publishing: %s:%s', topic, body)
    p.sendRaw(topic, body)


def main():
    import optparse
    parser = optparse.OptionParser('usage: %prog')
    ZmqPublisher.addOptions(parser, 'testPublishAttachments')
    opts, args = parser.parse_args()
    if args:
        parser.error('expected no args')
    logging.basicConfig(level=logging.DEBUG)

    # set up networking
    p = ZmqPublisher(**ZmqPublisher.getOptionValues(opts))
    p.start()

    # start publishing an arbitrary message that central should forward
    pubTimer = ioloop.PeriodicCallback(lambda: pubMessage(p), 1000)
    pubTimer.start()

    zmqLoop()


if __name__ == '__main__':
    main()
