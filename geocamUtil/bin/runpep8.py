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
import re

from geocamUtil.management.commandUtil import getSiteDir, lintignore, pipeToCommand

STRIP_COMMENT = re.compile(r'#.*$')
CONFIG_FILE = os.path.join(getSiteDir(), 'management', 'pep8Flags.txt')
DEFAULT_FLAGS = '--ignore=E501 --show-source --show-pep8 --repeat'


def dosys(cmd, verbosity):
    if verbosity > 1:
        print >> sys.stderr, 'running: %s' % cmd
    ret = os.system(cmd)
    if verbosity > 1:
        if ret != 0:
            print >> sys.stderr, 'warning: command exited with non-zero return value %d' % ret
    return ret


def readFlags(path):
    f = file(path, 'r')
    flags = []
    for line in f:
        line = re.sub(STRIP_COMMENT, '', line)
        line = line.strip()
        if line:
            flags.append(line)
    return ' '.join(flags)


def runpep8(paths, verbosity=1):
    if verbosity > 0:
        print >> sys.stderr, '### pep8'

    if not paths:
        paths = ['.']

    # give helpful error message if pep8 is not installed
    ret = os.system('pep8 --help > /dev/null')
    if ret != 0:
        print >> sys.stderr, "\nWARNING: can't run pep8 command -- try 'pip install pep8'\n"
        sys.exit(1)

    # extract flags from <site>/management/pep8Flags.txt if it exists
    if verbosity > 1:
        print >> sys.stderr, 'checking for pep8 flags in %s' % CONFIG_FILE
    if os.path.exists(CONFIG_FILE):
        flags = readFlags(CONFIG_FILE)
    else:
        flags = DEFAULT_FLAGS

    exitCode = 0
    for d in paths:
        d = os.path.relpath(d)
        cmd = 'pep8 %s' % flags
        if verbosity > 2:
            xargsFlags = '--verbose'
        else:
            xargsFlags = ''
        if os.path.isdir(d):
            pathsText = lintignore(os.popen('find %s -name "*.py"' % d).read())
            ret = pipeToCommand('xargs %s --no-run-if-empty -n50 -d"\n" %s' % (xargsFlags, cmd),
                                pathsText, verbosity)
            if ret != 0:
                exitCode = 1
        else:
            ret = dosys('%s %s' % (cmd, d), verbosity)
            if ret != 0:
                exitCode = 1

    return exitCode


def main():
    import optparse
    parser = optparse.OptionParser('usage: %prog [dir1] [file2.py] ...')
    parser.add_option('-v', '--verbosity',
                      type='int',
                      default=1,
                      help='Verbosity level; 0=minimal output, 1=normal output, 2=verbose output, 3=very verbose output')
    opts, args = parser.parse_args()
    exitCode = runpep8(args, verbosity=opts.verbosity)
    sys.exit(exitCode)


if __name__ == '__main__':
    main()
