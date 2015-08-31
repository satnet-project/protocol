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
from mock import Mock, MagicMock
import unittest

sys.path.append(path.abspath(path.join(path.dirname(__file__), "..")))

from twisted.internet import defer, protocol
from twisted.cred.portal import Portal
from twisted.internet import reactor, ssl
from twisted.python import log

from client_amp import ClientProtocol
from ampauth.server import CredReceiver, CredAMPServerFactory
from ampauth.commands import Login
from ampauth.testing import Realm

from rpcrequests import Satnet_RPC
from ampauth.errors import BadCredentials

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

    def funcion(self, username, password):
        if username == self.mockUserGoodCredentials.username:
            if password == self.mockUserGoodCredentials.password:
                log.msg(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> GoodCredentials")
                return True
            elif password != self.mockUserGoodCredentials.password:
                log.msg(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Wrong password test ok!")
                raise BadCredentials("Incorrect username and/or password")
            else:
                log.msg(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Error")
        elif username != self.mockUserGoodCredentials.username:
            log.msg(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Wrong username test ok!")
            raise BadCredentials("Incorrect username and/or password")
        else:
            log.msg(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Error")
        
    def _setUp_databases(self):
        """
        This method populates the database with some information to be used
        only for this test suite.
        """
        self.mockUserGoodCredentials = Mock()
        self.mockUserGoodCredentials.username = 's.gongoragarcia@gmail.com'
        self.mockUserGoodCredentials.password = 'sgongarpass'
        
        self.mockUserBadUsername = Mock()
        self.mockUserBadUsername.username = 'WrongUser'
        self.mockUserBadUsername.password = 'sgongarpass'

        self.mockUserBadPassword = Mock()
        self.mockUserBadPassword.username = 's.gongoragarcia@gmail.com'
        self.mockUserBadPassword.password = 'WrongPass'

    def setUp(self):
        log.startLogging(sys.stdout)
        
        log.msg(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Populating database")        
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
        # checker = DjangoAuthCheckers()
        # print checker
        # """
        # Realm?
        # """
        # realm = Realm()
        # """
        # Class Portal. A mediator between clients and a realm.

        # A portal is associated with one Realm and zero or more credentials checkers.
        # When a login is attempted, the portal finds the appropriate credentials
        # checker for the credentials given, invokes it, and if the credentials are
        # valid, retrieves the appropriate avatar from the Realm.
        # """
        # portal = Portal(realm, [checker])

        # print portal

        # pf = CredAMPServerFactory(portal)

        self.pf = CredAMPServerFactory()
        self.pf.protocol = CredReceiver()
        # Patch!
        self.pf.protocol.login = MagicMock(side_effect=self.funcion)
        # self.pf.onConnectionLost = d
        cert = ssl.PrivateCertificate.loadPEM(
            open('../key/server.pem').read())
        return reactor.listenSSL(1234, self.pf, cert.options())

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

    """
    Log in with valid credentianls. The server should return True
    """
    # def test_validLogin(self):

    #     # d = Login(self.factory.protoInstance, UsernamePassword(
    #     #     'xabi', 'pwdxabi'))
    #     # d.addCallback(lambda res : self.assertTrue(res['True']))

    #     # objeto = CredReceiver()

    #     # d = self.pf.protocol.login(mockUserGoodCredentials.username,\
    #     #  mockUserGoodCredentials.password)
    #     # print "d"
    #     # print d
    #     # d.addCallback(lambda res : self.assertTrue(res['bAuthenticated']))

    #     return self.assertTrue(self.pf.protocol.login(self.mockUserGoodCredentials.username,\
    #      self.mockUserGoodCredentials.password)) 

    """
    Log in with wrong username. The server should raise UnauthorizedLogin
    with 'Incorrect username' message
    """
    def test_wrongUsername(self):

    # #     d = login(self.factory.protoInstance, UsernamePassword(
    # #         'wrongUser', 'pwdxabi'))

    # #     def checkError(result):
    # #         self.assertEqual(result.message, 'Incorrect username')
    # #     return self.assertFailure(d, UnauthorizedLogin).addCallback(checkError)


        log.msg(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Wrong username test starts!")

        return self.assertRaisesRegexp(BadCredentials, 'Incorrect username and/or password',\
         self.pf.protocol.login, self.mockUserBadUsername.username,\
          self.mockUserBadUsername.password)

    """
    Log in with wrong password. The server should raise UnauthorizedLogin
    with 'Incorrect password' message
    """
    def test_wrongPassword(self):
    #     d = login(self.factory.protoInstance, UsernamePassword(
    #         'xabi', 'wrongPass'))

        log.msg(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Wrong password test starts!")

        return self.assertRaisesRegexp(BadCredentials, 'Incorrect username and/or password',\
         self.pf.protocol.login, self.mockUserBadPassword.username, self.mockUserBadPassword.password)

if __name__ == '__main__':
    unittest.main()  