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

import unittest
import itertools

import gevent
from gevent.event import AsyncResult

from qrouter import QueueRouter


def firstNElementsOf(it, n):
    return list(itertools.islice(it, 0, n))


def subscriber1(router, resultSlot):
    q = router.subscribe('foo*')
    resultSlot.set(firstNElementsOf(q, 3))


def subscriber2(router, resultSlot):
    q = router.subscribe('f*')
    result = []
    with gevent.Timeout(0.05, False):
        for elt in q:
            result.append(elt)
            if len(result) >= 3:
                router.unsubscribe(q)
    resultSlot.set(result)


def publisher(router):
    for i in xrange(5):
        router.publish('foobar', i)
        router.publish('baz', i)
        gevent.sleep(0)


class TestQueueRouter(unittest.TestCase):
    def test_foo(self):
        router = QueueRouter()
        resultSlot1 = AsyncResult()
        resultSlot2 = AsyncResult()
        gevent.spawn(subscriber1, router, resultSlot1)
        gevent.spawn(subscriber2, router, resultSlot2)
        gevent.sleep(0)  # yield to subscribers for setup
        gevent.spawn(publisher, router)
        result1 = resultSlot1.wait()
        result2 = resultSlot2.wait()
        expected = [('foobar', 0),
                    ('foobar', 1),
                    ('foobar', 2)]
        self.assertEqual(result1, expected)
        self.assertEqual(result2, expected)


if __name__ == '__main__':
    unittest.main()
