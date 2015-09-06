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

from os import path

BASE_DIR = path.abspath(path.join(path.dirname(__file__), "../tests"))

from zope.interface import implements
from twisted.python import failure
from twisted.python import log
from twisted.cred import portal
from twisted.cred import checkers
from twisted.cred import error
from twisted.cred import credentials
from twisted.internet import defer
from twisted.python import log
from twisted.spread import pb

from django.test import Client, override_settings
from django.conf import settings


class DjangoAuthChecker():

    def _passwordMatch(self, matched, user):

        if matched:
            return user
        elif matched == False:
            return error.UnauthorizedLogin("Incorrect password.")

    def requestAvatarId(self, databaseCredentials, testCredentials):

        try:
            settings.configure(DEBUG=True, 
              DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3',
                  'NAME': path.join(BASE_DIR, 'test.db'),
                'TEST_NAME': path.join(BASE_DIR, 'test.db'),}},
                INSTALLED_APPS = ('django.contrib.auth',))


            from django.contrib.auth.models import User, check_password

            user = User.objects.create_user(databaseCredentials.username,\
            'test@satnet.org', databaseCredentials.password)

            log.msg(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Settings configured.")

        except RuntimeError:
            log.msg(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Settings already configured.")

        from django.contrib.auth.models import User, check_password
    	

        try:
            user = User.objects.get(username=testCredentials.username)

            return defer.maybeDeferred(user.check_password, testCredentials.password).\
            addCallback(self._passwordMatch, user)

        except User.DoesNotExist:
            raise error.UnauthorizedLogin("Incorrect username.")


"""
Reads the elements from the database and create a list of twisted creds.
"""
class DjangoAuthCheckers():
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
            user = User.objects.get(username=credentials.username)
            return defer.maybeDeferred(
                check_password,
                credentials.password,
                user.password).addCallback(self._passwordMatch, user)
        except User.DoesNotExist:
            return defer.fail(error.UnauthorizedLogin())


class Realm(object):
    implements(portal.IRealm)

    def requestAvatar(self, user, mind, *interfaces):
        assert pb.IPerspective in interfaces
        avatar = Avatar(user)
        avatar.attached(mind)
        return pb.IPerspective, avatar, lambda a=avatar:a.detached(mind)


class Avatar(pb.Avatar):
    def __init__(self, user):
        self.user = user

    def attached(self, mind):
        self.remote = mind
        print 'User %s connected' % (self.user,)

    def detached(self, mind):
        self.remote = None
        print 'User %s disconnected' % (self.user,)
