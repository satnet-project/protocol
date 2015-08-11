# coding=utf-8
"""
   Copyright 2015 Samuel Góngora García

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.

:Author:
    Samuel Góngora García (s.gongoragarcia@gmail.com)
"""
__author__ = 's.gongoragarcia@gmail.com'

from zope.interface import implements
from twisted.python import failure, log
from twisted.cred import portal, checkers, error, credentials
from twisted.internet import defer

import os

from django.conf import settings
settings.configure()

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

from django.contrib.auth.models import User, check_password


class DjangoAuthChecker:
    implements(checkers.ICredentialsChecker)
    credentialInterfaces = (credentials.IUsernamePassword,
    credentials.IUsernameHashedPassword)

    def _passwordMatch(self, matched, user):
        if matched:
            return user
        else:
            return failure.Failure(error.UnauthorizedLogin())

    def requestAvatarId(self, credentials):
        try:
            user = User.objects.get(username='potato')
            return defer.maybeDeferred(
                check_password,
                credentials.password,
                user.password).addCallback(self._passwordMatch, user)
        except User.DoesNotExist:
            return defer.fail(error.UnauthorizedLogin())