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

from django.test import TestCase

from geocamUtil.models import JsonExample


class JsonFieldTest(TestCase):
    def setUp(self):
        self.obj = JsonExample()
        self.obj.intChar = [3, -4]
        self.obj.floatChar = [5.1, -6.2]
        self.obj.intText = [3, -4]
        self.obj.floatText = [5.1, -6.2]
        self.obj.save()

    def test_recoverContents(self):
        obj2 = JsonExample.objects.get(id=self.obj.id)
        self.assertEqual(obj2.intChar, self.obj.intChar)
        self.assertEqual(obj2.floatChar, self.obj.floatChar)
        self.assertEqual(obj2.intText, self.obj.intText)
        self.assertEqual(obj2.floatText, self.obj.floatText)
