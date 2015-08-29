# coding=utf-8
"""
   Copyright 2014 Xabier Crespo Álvarez

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
    Xabier Crespo Álvarez (xabicrespog@gmail.com)
"""
__author__ = 'xabicrespog@gmail.com'

import sys
from os import path
import unittest

import mock

sys.path.append(path.abspath(path.join(path.dirname(__file__), "..")))

from twisted.internet import defer, protocol
# from twisted.trial import unittest
from twisted.cred.portal import Portal
from twisted.internet import reactor, ssl

from client_amp import ClientProtocol
from ampauth.server import CredReceiver
# from ampauth.credentials import *
from ampauth.server import *
#from ampauth.client import login
from ampauth.commands import Login
from ampauth.testing import DjangoAuthCheckers, Realm

# from services.common.testing import helpers as db_tools

"""
Configuration settings.
"""
BASE_DIR = path.abspath(path.join(path.dirname(__file__), "."))
from django.conf import settings
settings.configure(DEBUG=True, 
  DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3',
      'NAME': path.join(BASE_DIR, 'test.db'),
    'TEST_NAME': path.join(BASE_DIR, 'test.db'),}},
    INSTALLED_APPS = ('django.contrib.auth',))

from django.contrib.auth.models import User

"""
To perform correct end to end tests:
1. The server must stop listening.
2. The client connection must disconnect.
3. The server connection must disconnect.

For more information about how to perform end to end
unit tests check http://blackjml.livejournal.com/23029.html
"""


class ServerProtocolTest(CredReceiver):

    def connectionLost(self, reason):
        super(ServerProtocolTest, self).connectionLost(reason)
        self.factory.onConnectionLost.callback(self)


class ClientProtocolTest(ClientProtocol):

    def connectionMade(self):
        self.factory.protoInstance = self
        self.factory.onConnectionMade.callback(self)

    def connectionLost(self, reason):
        self.factory.onConnectionLost.callback(self)


class TestSingleClient(unittest.TestCase):

    """
    Testing for one single client connection
    TODO. Test timeout
    """

    def _setUp_databases(self):
        """
        This method populates the database with some information to be used
        only for this test suite.
        """
        username_1 = 'xabi'
        password_1 = 'pwdxabi'
        email_1 = 'xabi@aguarda.es'

        username_2 = 'marti'
        password_2 = 'pwdmarti'
        email_2 = 'marti@montederramo.es'

        self.user_1 = mock.Mock()
        self.user_1.username = username_1 
        self.user_1.email = email_1
        self.user_1.password = password_1

        self.user_2 = mock.Mock()
        self.user_2.username = username_2
        self.user_2.email = email_2
        self.user_2.password = password_2
        

    def setUp(self):
        log.startLogging(sys.stdout)

        # log.msg(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Flushing database")
        # management.execute_from_command_line(['manage.py', 'flush', '--noinput'])
        
        log.msg(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Populating database")        
        # management.execute_from_command_line(['manage.py', 'createsuperuser', '--username', 'crespum', '--email', 'crespum@humsat.org', '--noinput'])
        self._setUp_databases()
        
        log.msg(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Running tests")

        self.serverDisconnected = defer.Deferred()
        self.serverPort = self._listenServer(self.serverDisconnected)
        self.connected = defer.Deferred()
        self.clientDisconnected = defer.Deferred()
        self.clientConnection = self._connectClient(self.connected,
                                                    self.clientDisconnected)
        return self.connected

    def _listenServer(self, d):
        """
        Class DjangoAuthCheckers.

        Should return a pair of creds.
        """
        checker = DjangoAuthCheckers()
        print checker
        """
        Realm?
        """
        realm = Realm()
        """
        Class Portal. A mediator between clients and a realm.

        A portal is associated with one Realm and zero or more credentials checkers.
        When a login is attempted, the portal finds the appropriate credentials
        checker for the credentials given, invokes it, and if the credentials are
        valid, retrieves the appropriate avatar from the Realm.
        """
        portal = Portal(realm, [checker])

        print portal

        # pf = CredAMPServerFactory(portal)
        pf = CredAMPServerFactory()

        pf.protocol = CredReceiver
        pf.onConnectionLost = d
        cert = ssl.PrivateCertificate.loadPEM(
            open('../key/server.pem').read())
        return reactor.listenSSL(1234, pf, cert.options())

    def _connectClient(self, d1, d2):
        self.factory = protocol.ClientFactory.forProtocol(ClientProtocolTest)
        self.factory.onConnectionMade = d1
        self.factory.onConnectionLost = d2

        cert = ssl.Certificate.loadPEM(open('../key/public.pem').read())
        options = ssl.optionsForClientTLS(u'example.humsat.org', cert)

        return reactor.connectSSL("localhost", 1234, self.factory, options)

    def tearDown(self):
        d = defer.maybeDeferred(self.serverPort.stopListening)
        self.clientConnection.disconnect()
        return defer.gatherResults([d,
                                    self.clientDisconnected])      
        try:
            self.connection.close()
            os.remove('test.db')
            log.msg(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Deleting database.")
        except:
            pass 

    """
    Log in with valid credentianls. The server should return True
    """

    def test_validLogin(self):
        d = Login(self.factory.protoInstance, UsernamePassword(
            'xabi', 'pwdxabi'))
        d.addCallback(lambda res : self.assertTrue(res['bAuthenticated']))
        return d

    # """
    # Log in with wrong username. The server should raise UnauthorizedLogin
    # with 'Incorrect username' message
    # """

    # def test_wrongUsername(self):
    #     d = login(self.factory.protoInstance, UsernamePassword(
    #         'wrongUser', 'pwdxabi'))

    #     def checkError(result):
    #         self.assertEqual(result.message, 'Incorrect username')
    #     return self.assertFailure(d, UnauthorizedLogin).addCallback(checkError)

    # """
    # Log in with wrong password. The server should raise UnauthorizedLogin
    # with 'Incorrect password' message
    # """

    # def test_wrongPassword(self):
    #     d = login(self.factory.protoInstance, UsernamePassword(
    #         'xabi', 'wrongPass'))

    #     def checkError(result):
    #         self.assertEqual(result.message, 'Incorrect password')
    #     return self.assertFailure(d, UnauthorizedLogin).addCallback(checkError)

if __name__ == '__main__':
    unittest.main()  