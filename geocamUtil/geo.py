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


import math
from math import sqrt, sin, cos

DATUMS = dict(WGS84=dict(a=6378137.0,
                         f=1.0 / 298.257223563))

RAD_TO_DEG_CONSTANT = (180.0 / math.pi)
DEG_TO_RAD_CONSTANT = (math.pi / 180.0)


def getEcefFromLonLatAlt(lla, datum='WGS84'):
    dat = DATUMS[datum]
    a = dat['a']
    f = dat['f']
    e2 = 2 * f - f ** 2
    lonDeg, latDeg, h = lla
    lon = lonDeg * DEG_TO_RAD_CONSTANT
    lat = latDeg * DEG_TO_RAD_CONSTANT
    chi = sqrt(1 - e2 * sin(lat) ** 2)
    q = (a / chi + h) * cos(lat)
    return (q * cos(lon), q * sin(lon), ((a * (1 - e2) / chi) + h) * sin(lat))


def dist(x, y):
    total = 0
    for i in xrange(0, len(x)):
        total += (x[i] - y[i]) ** 2
    return sqrt(total)


def distLla(lla1, lla2):
    return dist(getEcefFromLonLatAlt(lla1),
                getEcefFromLonLatAlt(lla2))
