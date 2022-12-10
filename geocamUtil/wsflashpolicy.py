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

import optparse
import sys
import signal
import SocketServer


class FlashPolicyServer(SocketServer.BaseRequestHandler):
    def __init__(self, *args, **kwargs):
        SocketServer.BaseRequestHandler.__init__(self, *args, **kwargs)
        self.data = None

    def handle(self):
        policyText = '<?xml version="1.0"?><cross-domain-policy><allow-access-from domain="%s" to-ports="%s" /></cross-domain-policy>' % (FlashPolicyServer.allowedDomain, FlashPolicyServer.allowedPort)

        self.data = self.request.recv(1024).strip()
        print "%s wrote:" % self.client_address[0]
        print self.data
        #self.allowedDomain = '*'
        #self.allowedPort = '*'
        if '<policy-file-request/>' in self.data:
            print 'received policy request'
            print 'sending policy: %s' % policyText
            self.request.send(policyText)


class Usage(Exception):
    def __init__(self, msg):
        super(Usage, self).__init__()
        self.msg = msg


def main():
    try:
        usage = 'wsflashpolicy.py -b bind-host [-p bind-port] -d allowed-domains -o allowed-ports'
        parser = optparse.OptionParser(usage=usage)
        parser.add_option('-b', '--bind-host', dest='bhost', help="Host to which server should bind")
        parser.add_option('-p', '--bind-port', dest='bport', help="Port to which server should bind")
        parser.add_option('-d', '--allowed-domains', dest='ahosts', help="List of domains to which flash is allowed to connect")
        parser.add_option('-o', '--allowed-ports', dest='aports', help="List of ports to which flash is allowed to connect")
        options, _ = parser.parse_args()
    except optparse.OptionError, msg:
        raise Usage(msg)

    if options.bhost:
        bhost = options.bhost
    else:
        bhost = ''

    if options.bport:
        bport = int(options.bport)
    else:
        bport = 843

    if options.ahosts:
        ahosts = options.ahosts
    else:
        ahosts = ''

    if options.aports:
        aports = options.aports
    else:
        aports = ''

    FlashPolicyServer.allowedDomain = ahosts
    FlashPolicyServer.allowedPort = aports

    server = SocketServer.TCPServer((bhost, bport), FlashPolicyServer)

    def signal_handler(sig, frame):
        print "Caught Ctrl+C, shutting down..."
        sys.exit()
    signal.signal(signal.SIGINT, signal_handler)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        sys.stdout.write('\r\n')
        sys.exit()

if __name__ == "__main__":
    sys.exit(main())
