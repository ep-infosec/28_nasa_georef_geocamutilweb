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


# stop pylint from warning that these variable docstrings are "useless"
# pylint: disable=W0105

GEOCAM_UTIL_DELETE_TMP_FILE_WAIT_SECONDS = 60 * 60
"""
The age at which a geocamUtil.tempfiles file becomes "stale".  When
tempfiles detects a stale file in its directory it will be deleted.
"""

GEOCAM_UTIL_INSTALLER_USE_SYMLINKS = False

######################################################################
# GEOCAM_UTIL_SECURITY_* -- settings for geocamUtil.middleware.SecurityMiddleware

"""
You can find copious documentation for these settings with::

  from geocamUtil.middleware import SecurityMiddleware
  help(SecurityMiddleware)
"""

GEOCAM_UTIL_SECURITY_ENABLED = True
"""
If False, turn off all SecurityMiddleware security checks and
redirects.
"""

GEOCAM_UTIL_SECURITY_DEFAULT_POLICY = None
"""
The default security policy to which other rules are added.
"""

GEOCAM_UTIL_SECURITY_RULES = ()
"""
A tuple of rules that change the default security policy depending on
the URL pattern the request matches.
"""

GEOCAM_UTIL_SECURITY_TURN_OFF_SSL_WHEN_NOT_REQUIRED = False
"""
Controls what happens when users use SSL to connect to a URL where it is
not required.  If True, they will be redirected to the non-SSL version.
"""

GEOCAM_UTIL_SECURITY_REQUIRE_ENCRYPTED_PASSWORDS = True
"""
If True, only accept encrypted or hashed passwords.
"""

GEOCAM_UTIL_SECURITY_SECRET_URL_REGEX = None
"""
If the request path matches this regex and the security policy
permits 'secretUrl' authentication, the request is authenticated.
"""

GEOCAM_UTIL_SECURITY_DEPRECATED_BEHAVIOR = 'warn'
"""
Changes how geocamUtil responds to use of deprecated features.
"""

GEOCAM_UTIL_SECURITY_SSL_REQUIRED_BY_DEFAULT = True
"""
DEPRECATED. Use GEOCAM_UTIL_SECURITY_DEFAULT_POLICY sslRequired instead.
"""

GEOCAM_UTIL_SECURITY_LOGIN_REQUIRED_BY_DEFAULT = True
"""
DEPRECATED. Use GEOCAM_UTIL_SECURITY_DEFAULT_POLICY loginRequired instead.
"""

GEOCAM_UTIL_SECURITY_DEFAULT_CHALLENGE = 'django'
"""
DEPRECATED. Use GEOCAM_UTIL_SECURITY_DEFAULT_POLICY challenge instead.
"""

GEOCAM_UTIL_SECURITY_ACCEPT_AUTH_TYPES = ('basic',)
"""
DEPRECATED. Use GEOCAM_UTIL_SECURITY_DEFAULT_POLICY acceptAuthTypes instead.
"""

DIGEST_REALM = 'undefinedrealm'
"""
Realm to display to user when using the 'basic' challenge.

(Note: The name of the setting was chosen when it was used primarily
with HTTP digest authentication, which is no longer supported. We
avoided changing the name to keep backward compatibility.)
"""

GEOCAM_UTIL_LIVE_MODE = False
"""
If live mode is true, various live feed data can send inputs to site and
 more parts of the site will be visible.  Suggest expansion to include a
 list of services.

 IMPORTANT YOU MUST INCLUDE THIS IN SITE SETTINGS
 TEMPLATE_CONTEXT_PROCESSORS = (global_settings.TEMPLATE_CONTEXT_PROCESSORS + (
     ...
     'geocamUtil.context_processors.SettingsContextProcessor.SettingsContextProcessor'
 """

GEOCAM_UTIL_ZMQ_PORTS_PATH = "/home/geocam/georef/apps/georefApp/ports.json"
