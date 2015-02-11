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


from twisted.internet import defer, protocol
from twisted.trial import unittest
from twisted.cred.portal import Portal
from twisted.internet import reactor, ssl

from ampauth.credentials import *
from ampauth.server import *
from ampauth.client import login
from ampauth.server import CredReceiver
from client_amp import ClientProtocol
from commands import *
from errors import *

from services.common import misc

import pytz
import datetime

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

    def vNotifyMsg(self, sMsg):
        log.msg("--------- Notify Message ---------")
        self.factory.onMessageReceived.callback(sMsg)
        return {}
    NotifyMsg.responder(vNotifyMsg)

    def vNotifyEvent(self, iEvent, sDetails):
        log.msg("--------- Notify Event ---------")
        if iEvent == NotifyEvent.SLOT_END:
            log.msg("Disconnection because the slot has ended")
        elif iEvent == NotifyEvent.REMOTE_DISCONNECTED:
            log.msg("Remote client has lost the connection")
        elif iEvent == NotifyEvent.END_REMOTE:
            log.msg(
                "Disconnection because the remote client has been disconnected")
        elif iEvent == NotifyEvent.REMOTE_CONNECTED:
            log.msg("The remote client (" + sDetails + ") has just connected")

        self.factory.onEventReceived = self.factory.onEventReceived.callback(
            iEvent)
        return {}
    NotifyEvent.responder(vNotifyEvent)


class TestMultipleClients(unittest.TestCase):

    """
    Testing multiple client connections
    TDOD. Test multiple valid connections
    """

    def setUp(self):
        log.startLogging(sys.stdout)
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
    Basic remote connection between two clients. The procedure goes:
        1. Client A -> login
        2. Client A -> StartRemote (should return StartRemote.REMOTE_NOT_CONNECTED)
        3. Client B -> login
        4. Client B -> StartRemote (should return StartRemote.REMOTE_READY)
        5. Client A -> notifyEvent (should receive NotifyEvent.REMOTE_CONNECTED)
        6. Client B -> sendMsg(__sMessageA2B)
        7. Client A -> notifyMsg (should receive __sMessageA2B)
        8. Client A -> sendMsg(__sMessageB2A)
        9. Client B -> notifyMsg (should receive __sMessageB2A)
        10. Client B -> endRemote()
        11. Client A -> notifyEvent (should receive NotifyEvent.END_REMOTE). This last step
        is not being checked due to dificulties with Twisted trial methods
    """

    def test_simultaneousUsers(self):
        __iSlotId = 1
        __sMessageA2B = "Adiós, ríos; adios, fontes; adios, regatos pequenos;"
        __sMessageB2A = "adios, vista dos meus ollos: non sei cando nos veremos."
        # To notify when a new message is received by the client
        self.factory1.onMessageReceived = defer.Deferred()
        self.factory2.onMessageReceived = defer.Deferred()
        self.factory1.onEventReceived = defer.Deferred()

        d1 = login(self.factory1.protoInstance, UsernamePassword(
            'crespo', 'cre.spo'))
        d1.addCallback(lambda res: self.assertTrue(res['bAuthenticated']))

        d1.addCallback(lambda l: self.factory1.protoInstance.callRemote(
            StartRemote, iSlotId=__iSlotId))
        d1.addCallback(lambda res: self.assertEqual(
            res['iResult'], StartRemote.REMOTE_NOT_CONNECTED))

        d2 = d1.addCallback(lambda _ignored: login(self.factory2.protoInstance, UsernamePassword(
            'tubio', 'tu.bio')))
        d2.addCallback(lambda res: self.assertTrue(res['bAuthenticated']))

        d2.addCallback(lambda l: self.factory2.protoInstance.callRemote(
            StartRemote, iSlotId=__iSlotId))
        d2.addCallback(
            lambda res: self.assertEqual(res['iResult'], StartRemote.REMOTE_READY))
        self.factory1.onEventReceived.addCallback(
            lambda iEvent: self.assertEqual(iEvent, NotifyEvent.REMOTE_CONNECTED))

        d2.addCallback(lambda l: self.factory2.protoInstance.callRemote(
            SendMsg, sMsg=__sMessageA2B, iTimestamp=misc.get_utc_timestamp()))

        self.factory1.onMessageReceived.addCallback(
            lambda sMsg: self.assertEqual(sMsg, __sMessageA2B))

        d1.addCallback(lambda l: self.factory1.protoInstance.callRemote(
            SendMsg, sMsg=__sMessageB2A, iTimestamp=misc.get_utc_timestamp()))

        self.factory2.onMessageReceived.addCallback(
            lambda sMsg: self.assertEqual(sMsg, __sMessageB2A))

        d = defer.gatherResults(
            [d2, self.factory2.onMessageReceived, self.factory1.onEventReceived])
        d.addCallback(
            lambda l: self.factory2.protoInstance.callRemote(EndRemote))
        
        return defer.gatherResults([d1, self.factory1.onMessageReceived, d, self.factory1.onEventReceived])

    """
    Call StartRemote method with a non existing slot id
    """

    def test_wrongSlot(self):
        __iSlotId = 100

        d1 = login(self.factory1.protoInstance, UsernamePassword(
            'crespo', 'cre.spo'))
        d1.addCallback(lambda l: self.factory1.protoInstance.callRemote(
            StartRemote, iSlotId=__iSlotId))

        def checkError(result):
            self.assertEqual(
                result.message, 'Slot ' + str(__iSlotId) + ' not operational yet')
        return self.assertFailure(d1, SlotErrorNotification).addCallback(checkError)

    """
    Basic remote connection when GSS and MCC clients correspond to the same user
    """

    def test_localClient(self):
        __iSlotId = 3

        d1 = login(self.factory1.protoInstance, UsernamePassword(
            'tubio', 'tu.bio'))
        d1.addCallback(lambda l: self.factory1.protoInstance.callRemote(
            StartRemote, iSlotId=__iSlotId))
        d1.addCallback(lambda res: self.assertEqual(
            res['iResult'], StartRemote.CLIENTS_COINCIDE))

        return d1

    """
    Wrong procedure. The client tries to send a message before invoking StartRemote command. 
    The procedure goes:
        1. Client A -> login
        2. Client A -> sendMsg(__sMessageA2B) (should raise SlotErrorNotification(
                'Connection not available. Call StartRemote command first.'))
    """

    def test_wrongMessageProcedure(self):
        __iSlotId = 1
        __sMessageA2B = "Adiós, ríos; adios, fontes; adios, regatos pequenos;"
        # To notify when a new message is received by the client
        self.factory1.onMessageReceived = defer.Deferred()
        self.factory1.onEventReceived = defer.Deferred()

        d1 = login(self.factory1.protoInstance, UsernamePassword(
            'crespo', 'cre.spo'))
        d1.addCallback(lambda l: self.factory1.protoInstance.callRemote(
            SendMsg, sMsg=__sMessageA2B, iTimestamp=misc.get_utc_timestamp()))

        def checkError(result):
            self.assertEqual(
                result.message, 'Connection not available. Call StartRemote command first.')
        return self.assertFailure(d1, SlotErrorNotification).addCallback(checkError)