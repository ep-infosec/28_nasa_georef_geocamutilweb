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

CLASS_TEMPLATE = """
class %(decoratedName)s(%(parentName)s):
"""

FUNC_TEMPLATE = """
    def %(name)s(self, %(signature)s):
        %(docstring)s
        return self._client('%(name)s', %(argNames)s)
"""


def firstCaps(s):
    if s:
        return s[0].upper() + s[1:]
    else:
        return s


class MissingVal(object):
    pass
MISSING = MissingVal()


def nameFromArg(arg):
    name = arg['name']
    if isinstance(name, tuple):
        name = '(%s)' % ', '.join([n for n in name])
    return name


def declarationFromZerorpcInspectArg(arg):
    result = nameFromArg(arg)

    defaultVal = arg.get('default', MISSING)
    if defaultVal is not MISSING:
        result += '=' + repr(defaultVal)

    return result


class ClientProxy(object):
    def __init__(self, name, client):
        self._name = name
        self._client = client

    def __getattr__(self, name):
        # don't intercept requests for special attributes
        if name.startswith('__'):
            raise AttributeError(name)
        return getattr(self._client, name)

    @classmethod
    def makeDecoratedProxy(cls, name, client):
        try:
            meta = client._zerorpc_inspect()
        except:  # pylint: disable=W0702
            #print ('could not inspect methods for service %s, may not be running'
            #       % self._name)
            return None
        decoratedName = '%sClient' % firstCaps(name)
        src = (CLASS_TEMPLATE
               % {'decoratedName': decoratedName,
                  'parentName': cls.__name__})

        methods = meta['methods']
        for name, info in methods.iteritems():
            argSigs = [declarationFromZerorpcInspectArg(arg) for arg in info['args']]
            signature = ', '.join(argSigs[1:])
            argNames = ', '.join(nameFromArg(arg) for arg in info['args'][1:])
            docstring = repr(info.get('doc', '<unknown>'))
            src += (FUNC_TEMPLATE
                    % {'name': name,
                       'signature': signature,
                       'argNames': argNames,
                       'docstring': docstring})
        # print 'zerorpcClientProxy:', src
        code = compile(src, '<string>', 'single')
        evaldict = {'__name__': 'geocamUtil.zmqUtil.zerorpcClientProxy',
                    'ClientProxy': ClientProxy}
        exec code in evaldict  # pylint: disable=W0122
        return evaldict[decoratedName]
