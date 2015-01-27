from twisted.internet import defer, protocol
from twisted.trial import unittest
from twisted.cred.portal import Portal
from twisted.internet import reactor, ssl

from ampauth.credentials import *
from ampauth.server import *
from ampauth.client import login
from ampauth.server import CredReceiver
from client_amp import ClientProtocol

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

    def setUp(self):
        # log.startLogging(sys.stdout)
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
            open('../key/private.pem').read())
        return reactor.listenSSL(1234, pf, cert.options())

    def _connectClients(self, factory, d1, d2):
        factory.onConnectionMade = d1
        factory.onConnectionLost = d2

        cert = ssl.Certificate.loadPEM(open('../key/public.pem').read())
        options = ssl.optionsForClientTLS(u'humsat.org', cert)

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
        d = self.assertFailure(d2, UnauthorizedLogin).addCallback(checkError)
        return defer.gatherResults([d1, d2, d])


    def test_simultaneousUsers(self):

        d1 = login(self.factory1.protoInstance, UsernamePassword(
            'xabi', 'pwdxabi'))
        d1.addCallback(lambda res : self.assertTrue(res['bAuthenticated']))

        d2 = login(self.factory2.protoInstance, UsernamePassword(
            'marti', 'pwdmarti'))
        d2.addCallback(lambda res : self.assertTrue(res['bAuthenticated']))

        return defer.gatherResults([d1, d2])
