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
from twisted.python import failure, log
from twisted.cred import portal, checkers, error, credentials
from twisted.internet import defer
from twisted.python import log

from django.test import Client
from django.conf import settings

settings.configure(DEBUG=True, 
					DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3',
        			'NAME': path.join(BASE_DIR, 'test.db'),
    			 	'TEST_NAME': path.join(BASE_DIR, 'test.db'),}},
    			 	INSTALLED_APPS = ('django.contrib.auth',))

from django.contrib.auth.models import User, check_password


class DjangoAuthChecker():

    def _passwordMatch(self, matched, user):

        if matched:
            return user
        else:
            return failure.Failure(error.UnauthorizedLogin())

    def requestAvatarId(self, databaseCredentials, testCredentials):

    	user = User.objects.create_user(databaseCredentials.username,\
    	 'lennon@thebeatles.com', databaseCredentials.password)

        try:
            user = User.objects.get(username=testCredentials.username)

            return defer.maybeDeferred(user.check_password, databaseCredentials.password).\
            addCallback(self._passwordMatch, user)

        except User.DoesNotExist:
            raise error.UnauthorizedLogin("Incorrect username")