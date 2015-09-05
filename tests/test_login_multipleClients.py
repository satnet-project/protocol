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
import unittest
from os import path
from mock import Mock, MagicMock

sys.path.append(path.abspath(path.join(path.dirname(__file__), "..")))

from twisted.internet import defer, protocol, reactor, ssl
from twisted.internet.error import CannotListenError
from twisted.cred.portal import Portal
from twisted.python import log

from ampauth.commands import Login
from ampauth.errors import BadCredentials, UnauthorizedLogin
from ampauth.server import CredReceiver, CredAMPServerFactory
from ampauth.testing import Realm
from client_amp import ClientProtocol
from rpcrequests import Satnet_RPC


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

    def mockLoginMethod(self, username, password):
        if username == self.mockUser1.username:
            if password == self.mockUser1.password:

                if username in self.active_users:
                    log.msg(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Client already logged in")
                    raise UnauthorizedLogin("Client already logged in")
                else:
                    self.active_users.append(username)

                log.msg(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> User1 logged")
                bAuthenticated = True
                return bAuthenticated
                # return bAuthenticate = True
            else:
                log.msg(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Error")
        elif username == self.mockUser2.username:
            if password == self.mockUser2.password:

                if username in self.active_users:
                    log.msg(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Client already logged in")
                    raise UnauthorizedLogin("Client already logged in")
                else:
                    self.active_users.append(username)

                log.msg(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> User2 logged")
                bAuthenticated = True
                return bAuthenticated
                # return defer.Deferred('bAuthenticate')
            else:
                log.msg(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Error")
        else:
            log.msg(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Error")

    def _setUp_databases(self):
        """
        This method populates the database with some information to be used
        only for this test suite.
        """
        self.mockUser1 = Mock()
        self.mockUser1.username = 'xabi'
        self.mockUser1.password = 'pwdxabi'

        self.mockUser2 = Mock()
        self.mockUser2.username = 'sam'
        self.mockUser2.password = 'pwdsam'

        self.active_users = []

    def setUp(self):
        log.startLogging(sys.stdout)
        
        log.msg(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Populating database")        
        self._setUp_databases()
        
        log.msg(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Running tests")

        self.serverDisconnected = defer.Deferred()
        self.serverPort = self._listenServer(self.serverDisconnected)

        self.connected1 = defer.Deferred()
        self.clientDisconnected1 = defer.Deferred()
        self.factory1 = protocol.ClientFactory.forProtocol(ClientProtocolTest)
        self.clientConnection1 = self._connectClients(self.factory1,\
         self.connected1, self.clientDisconnected1)

        self.connected2 = defer.Deferred()
        self.clientDisconnected2 = defer.Deferred()
        self.factory2 = protocol.ClientFactory.forProtocol(ClientProtocolTest)
        self.clientConnection2 = self._connectClients(self.factory2,\
         self.connected2, self.clientDisconnected2)

        return defer.gatherResults([self.connected1, self.connected2])

    def _listenServer(self, d):
        # checker = DjangoAuthChecker()
        # realm = Realm()
        # portal = Portal(realm, [checker])
        # pf = CredAMPServerFactory(portal)
        try:
            self.pf = CredAMPServerFactory()
            self.pf.protocol = CredReceiver
            self.pf.protocol.login = MagicMock(side_effect=self.mockLoginMethod)
            self.pf.onConnectionLost = d
            cert = ssl.PrivateCertificate.loadPEM(
                open('../key/server.pem').read())
            return reactor.listenSSL(1234, self.pf, cert.options())
        except CannotListenError:
            log.msg("Server already initialized")

    def _connectClients(self, factory, d1, d2):
        factory.onConnectionMade = d1
        factory.onConnectionLost = d2

        cert = ssl.Certificate.loadPEM(open('../key/public.pem').read())
        options = ssl.optionsForClientTLS(u'example.humsat.org', cert)

        return reactor.connectSSL("localhost", 1234, factory, options)

    def tearDown(self):
        try:
            d = defer.maybeDeferred(self.serverPort.stopListening)
            self.clientConnection1.disconnect()
            self.clientConnection2.disconnect()
            return defer.gatherResults([d, self.clientDisconnected1,\
             self.clientDisconnected2])
        except AttributeError:
            self.clientConnection1.disconnect()
            self.clientConnection2.disconnect()
            return defer.gatherResults([self.clientDisconnected1,\
             self.clientDisconnected2])

    """
    Log in two different clients with the same credentials. The server should 
    raise UnauthorizedLogin with 'Client already logged in' message
    """
    def test_duplicatedUser(self):

        # d1 = login(self.factory1.protoInstance, UsernamePassword(
        #     'xabi', 'pwdxabi'))
        # d1.addCallback(lambda res : self.assertTrue(res['bAuthenticated']))

        # d2 = login(self.factory2.protoInstance, UsernamePassword(
        #     'xabi', 'pwdxabi'))

        # def checkError(result):
        #     self.assertEqual(result.message, 'Client already logged in')
        # d2 = self.assertFailure(d2, UnauthorizedLogin).addCallback(checkError)
        # return defer.gatherResults([d1, d2])

        d1 = self.pf.protocol.login('xabi', 'pwdxabi')
        self.assertTrue(d1)

        return self.assertRaisesRegexp(UnauthorizedLogin, 'Client already logged in',\
         self.pf.protocol.login, 'xabi', 'pwdxabi')

    """
    Log in two different clients with good credentials. The server should
    return True.
    """
    def test_simultaneousUsers(self):

        d1 = self.pf.protocol.login('xabi', 'pwdxabi')
        self.assertTrue(d1)

        d2 = self.pf.protocol.login('sam', 'pwdsam')
        self.assertTrue(d2)


if __name__ == '__main__':
    unittest.main()  
