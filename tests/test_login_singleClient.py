import sys 

from django.core import management

from twisted.internet import defer, protocol
from twisted.trial import unittest
from twisted.cred.portal import Portal
from twisted.internet import reactor, ssl

from client_amp import ClientProtocol
from ampauth.server import CredReceiver
from ampauth.credentials import *
from ampauth.server import *
from ampauth.client import login

from services.common.testing import helpers as db_tools

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
        self.connected = defer.Deferred()
        self.clientDisconnected = defer.Deferred()
        self.clientConnection = self._connectClient(self.connected,
                                                    self.clientDisconnected)
        return self.connected

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

    def test_validLogin(self):
        d = login(self.factory.protoInstance, UsernamePassword(
            'xabi', 'pwdxabi'))
        d.addCallback(lambda res : self.assertTrue(res['bAuthenticated']))
        return d

    """
    Log in with wrong username. The server should raise UnauthorizedLogin
    with 'Incorrect username' message
    """

    def test_wrongUsername(self):
        d = login(self.factory.protoInstance, UsernamePassword(
            'wrongUser', 'pwdxabi'))

        def checkError(result):
            self.assertEqual(result.message, 'Incorrect username')
        return self.assertFailure(d, UnauthorizedLogin).addCallback(checkError)

    """
    Log in with wrong password. The server should raise UnauthorizedLogin
    with 'Incorrect password' message
    """

    def test_wrongPassword(self):
        d = login(self.factory.protoInstance, UsernamePassword(
            'xabi', 'wrongPass'))

        def checkError(result):
            self.assertEqual(result.message, 'Incorrect password')
        return self.assertFailure(d, UnauthorizedLogin).addCallback(checkError)