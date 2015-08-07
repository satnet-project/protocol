# coding=utf-8
"""
   Copyright 2015 Xabier Crespo Álvarez

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

import sys, os
#sys.path.append(os.path.dirname(os.getcwd()) + "/server")
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../server")))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "website.settings")

from django.core import management

from twisted.internet import defer, protocol
from twisted.trial import unittest
from twisted.cred.portal import Portal
from twisted.internet import reactor, ssl

from ampauth.credentials import *
from ampauth.server import *
from ampauth.client import login
from ampauth.server import CredReceiver
from client_amp import ClientProtocol

from services.common.testing import helpers as db_tools

"""
To perform correct end to end tests:
1. The server must stop listening.
2. The client connection must disconnect.
3. The server connection must disconnect.

In this case, because there are two different clients connected
to the server, the server disconnection is not called after a client
disconnects to avoid duplicated fires of a same deferred

For more information about how to perform end to end
unit tests check http://blackjml.livejournal.com/23029.html
"""


class ClientProtocolTest(ClientProtocol):

    def connectionMade(self):
        self.factory.protoInstance = self
        self.factory.onConnectionMade.callback(self)

    def connectionLost(self, reason):
        self.factory.onConnectionLost.callback(self)


class TestMultipleClients(unittest.TestCase):

    """
    Testing multiple client connections
    TDOD. Test multiple valid connections
    """
    def _setUp_databases(self):
        """
        This method populates the database with some information to be used
        only for this test suite.
        """
        #self.__verbose_testing = False
        username_1 = 'xabi'
        password_1 = 'pwdxabi'
        email_1 = 'xabi@aguarda.es'

        username_2 = 'marti'
        password_2 = 'pwdmarti'
        email_2 = 'marti@montederramo.es'

        db_tools.create_user_profile(
            username=username_1, password=password_1, email=email_1)
        db_tools.create_user_profile(
            username=username_2, password=password_2, email=email_2)

    def setUp(self):
        log.startLogging(sys.stdout)

        log.msg(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Flushing database")
        management.execute_from_command_line(['manage.py', 'flush', '--noinput'])
        
        log.msg(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Populating database")        
        management.execute_from_command_line(['manage.py', 'createsuperuser', '--username', 'crespum', '--email', 'crespum@humsat.org', '--noinput'])
        self._setUp_databases()
        
        log.msg(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Running tests")
        self.serverDisconnected = defer.Deferred()
        self.serverPort = self._listenServer(self.serverDisconnected)

        self.connected1 = defer.Deferred()
        self.clientDisconnected1 = defer.Deferred()
        self.factory1 = protocol.ClientFactory.forProtocol(ClientProtocolTest)
        self.clientConnection1 = self._connectClients(self.factory1, self.connected1,
                                                      self.clientDisconnected1)

        self.connected2 = defer.Deferred()
        self.clientDisconnected2 = defer.Deferred()
        self.factory2 = protocol.ClientFactory.forProtocol(ClientProtocolTest)
        self.clientConnection2 = self._connectClients(self.factory2, self.connected2,
                                                      self.clientDisconnected2)

        return defer.gatherResults([self.connected1, self.connected2])

    def _listenServer(self, d):
        checker = DjangoAuthChecker()
        realm = Realm()
        portal = Portal(realm, [checker])
        pf = CredAMPServerFactory(portal)
        pf.protocol = CredReceiver
        pf.onConnectionLost = d
        cert = ssl.PrivateCertificate.loadPEM(
            open('../key/server.pem').read())
        return reactor.listenSSL(1234, pf, cert.options())

    def _connectClients(self, factory, d1, d2):
        factory.onConnectionMade = d1
        factory.onConnectionLost = d2

        cert = ssl.Certificate.loadPEM(open('../key/public.pem').read())
        options = ssl.optionsForClientTLS(u'example.humsat.org', cert)

        return reactor.connectSSL("localhost", 1234, factory, options)

    def tearDown(self):
        d = defer.maybeDeferred(self.serverPort.stopListening)
        self.clientConnection1.disconnect()
        self.clientConnection2.disconnect()

        return defer.gatherResults([d,
                                    self.clientDisconnected1, self.clientDisconnected2
                                    ])

    """
    Log in two different clients with the same credentials. The server should 
    raise UnauthorizedLogin with 'Client already logged in' message
    """
    def test_duplicatedUser(self):

        d1 = login(self.factory1.protoInstance, UsernamePassword(
            'xabi', 'pwdxabi'))
        d1.addCallback(lambda res : self.assertTrue(res['bAuthenticated']))

        d2 = login(self.factory2.protoInstance, UsernamePassword(
            'xabi', 'pwdxabi'))

        def checkError(result):
            self.assertEqual(result.message, 'Client already logged in')
        d2 = self.assertFailure(d2, UnauthorizedLogin).addCallback(checkError)
        return defer.gatherResults([d1, d2])


    def test_simultaneousUsers(self):

        d1 = login(self.factory1.protoInstance, UsernamePassword(
            'xabi', 'pwdxabi'))
        d1.addCallback(lambda res : self.assertTrue(res['bAuthenticated']))

        d2 = login(self.factory2.protoInstance, UsernamePassword(
            'marti', 'pwdmarti'))
        d2.addCallback(lambda res : self.assertTrue(res['bAuthenticated']))

        return defer.gatherResults([d1, d2])

if __name__ == '__main__':
    unittest.main()  
