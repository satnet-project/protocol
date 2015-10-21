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

import unittest
from os import path
import sys
import logging
import datetime
import pytz
from mock import Mock, MagicMock

sys.path.append(path.abspath(path.join(path.dirname(__file__), "..")))

from twisted.internet import defer, protocol, reactor, ssl
from twisted.internet.error import CannotListenError
from twisted.python import log

from ampauth.errors import BadCredentials
from ampauth.login import Login
from ampauth.server import CredReceiver, CredAMPServerFactory

from client_amp import ClientProtocol
from ampCommands import NotifyMsg
from ampCommands import NotifyEvent
from clientErrors import SlotErrorNotification, RemoteClientNotification

from server_amp import SATNETServer


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
        self.factory.onEventReceived.callback(iEvent)
        return {}
    NotifyEvent.responder(vNotifyEvent)


class TestStartRemote(unittest.TestCase):

    """
    Testing multiple client connections
    TODO. Test multiple valid connections
    """
    def mockLoginMethod(self, username, password):
        if username == self.mockUser1.username:
            if password == self.mockUser1.password:
                log.msg(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> User1 logged")
                return {'bAuthenticated': True}
            else:
                log.msg(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Error")
        elif username == self.mockUser2.username:
            if password == self.mockUser2.password:
                log.msg(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> User2 logged")
                return {'bAuthenticated': True}
            else:
                log.msg(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Error")
        elif username == self.mockUser3.username:
            if password == self.mockUser3.password:
                log.msg(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> User3 logged")
                return {'bAuthenticated': True}
            else:
                log.msg(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Error")
        else:
            log.msg(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Error")

    def mockStartRemote(self, iSlotId, username, password):
        # Sets the return value of the function for all cases.

        if iSlotId == self.mockUser1.slot:
            if username == self.mockUser1.username and password == self.mockUser1.password:
                return {'iResult': 'StartRemote.CLIENTS_COINCIDE'} # To-do
            elif username == self.mockUser1.username and password == self.mockUser2.password:
                return {'iResult': 'StartRemote.CLIENTS_COINCIDE'}    
            else:
                return {'iResult': 'This user is not assigned to this slot'}
        elif iSlotId == 100:
            raise SlotErrorNotification('Slot ' + str(iSlotId) +\
             ' is not yet operational')
        elif iSlotId == 2:
            raise SlotErrorNotification('Slot ' + str(iSlotId) +\
             ' has not yet been reserved')

    def _setUp_databases(self):
        """
        This method populates the database with some information to be used
        only for this test.
        """

        self.mockUser1 = Mock()
        self.mockUser1.slot = 4
        self.mockUser1.username = 'xabi'
        self.mockUser1.password = 'pwdxabi'

        self.mockUser2 = Mock()
        self.mockUser2.username = 'sam'
        self.mockUser2.password = 'pwdsam'

        self.mockUser3 = Mock()
        self.mockUser3.username = 'user3'
        self.mockUser3.password = 'us.er3'

        # Better create a dict.
        self.iSlots_available = []
        self.iSlots_available.append(self.mockUser1.slot)

        self.iSlots_connected = []

    def setUp(self):
        log.startLogging(sys.stdout)

        # log.msg(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Flushing database")
        # management.execute_from_command_line(['manage.py', 'flush', '--noinput'])
        
        log.msg(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Populating database")        
        # management.execute_from_command_line(['manage.py', 'createsuperuser',
        #     '--username', 'crespum', '--email', 'crespum@humsat.org', '--noinput'])
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
        # checker = DjangoAuthChecker()
        # realm = Realm()
        # portal = Portal(realm, [checker])
        # pf = CredAMPServerFactory(portal)
        try:
            self.pf = CredAMPServerFactory()
            self.pf.protocol = CredReceiver
            self.pf.protocol.login = MagicMock(side_effect=self.mockLoginMethod)
            self.pf.protocol.startremote = MagicMock(side_effect=self.mockStartRemote)
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
    Call StartRemote method with a non existing slot id
    """
    def test_wrongSlot(self):
        __iSlotId = 100

        # d1 = login(self.factory1.protoInstance, UsernamePassword(
        #     'crespo', 'cre.spo'))
        # d1.addCallback(lambda l: self.factory1.protoInstance.callRemote(
        #     StartRemote, iSlotId=__iSlotId))

        # def checkError(result):
        #     self.assertEqual(
        #         result.message, 'Slot ' + str(__iSlotId) +\
        #          ' is not yet operational')
        # return self.assertFailure(d1,\
        #  SlotErrorNotification).addCallback(checkError)

        res = self.pf.protocol.login(self.mockUser1.username,\
         self.mockUser1.password)

        self.assertTrue(res['bAuthenticated'])

        self.assertRaisesRegexp(SlotErrorNotification,\
         'Slot ' + str(__iSlotId) + ' is not yet operational',\
          self.pf.protocol.startremote, iSlotId=__iSlotId,\
           username=self.mockUser1.username, password=self.mockUser1.password)

    """
    Basic remote connection when GSS and MCC clients correspond to the same user
    """
    def test_localClient(self):
        __iSlotId = 4

        # d1 = login(self.factory1.protoInstance, UsernamePassword(
        #     'tubio', 'tu.bio'))
        # d1.addCallback(lambda l: self.factory1.protoInstance.callRemote(
        #     StartRemote, iSlotId=__iSlotId))
        # d1.addCallback(lambda res: self.assertEqual(
        #     res['iResult'], StartRemote.CLIENTS_COINCIDE))
        # return d1

        res = self.pf.protocol.login(self.mockUser2.username,\
         self.mockUser2.password)
        self.assertTrue(res['bAuthenticated'])

        res = self.pf.protocol.startremote(iSlotId=__iSlotId,\
         username=self.mockUser1.username, password=self.mockUser1.password)

        self.assertEqual(res['iResult'], 'StartRemote.CLIENTS_COINCIDE')

    """
    Call StartRemote method without having reserved previously the slot
    """
    def test_slotNotReserved(self):
        __iSlotId = 2

        # d1 = login(self.factory1.protoInstance, UsernamePassword(
        #     'crespo', 'cre.spo'))
        # d1.addCallback(lambda l: self.factory1.protoInstance.callRemote(
        #     StartRemote, iSlotId=__iSlotId))

        # def checkError(result):
        #     self.assertEqual(
        #         result.message, 'Slot ' + str(__iSlotId) +\
        #          ' has not yet been reserved')
        # return self.assertFailure(d1,\
        #  SlotErrorNotification).addCallback(checkError)

        res = self.pf.protocol.login(self.mockUser1.username,\
         self.mockUser1.password)
        self.assertTrue(res['bAuthenticated'])

        self.assertRaisesRegexp(SlotErrorNotification,\
         'Slot ' + str(__iSlotId) + ' has not yet been reserved',\
          self.pf.protocol.startremote, iSlotId=__iSlotId,\
           username=self.mockUser1.username, password=self.mockUser1.password)

    """
    Call StartRemote method without having selected the slot for this user
    """
    def test_slotNotAssigned(self):
        __iSlotId = 4

        # d1 = login(self.factory1.protoInstance, UsernamePassword(
        #     'user3', 'us.er3'))
        # d1.addCallback(lambda l: self.factory1.protoInstance.callRemote(
        #     StartRemote, iSlotId=__iSlotId))

        # def checkError(result):
        #     self.assertEqual(
        #         result.message, 'This user is not assigned to this slot')
        # return self.assertFailure(d1,\
        #  SlotErrorNotification).addCallback(checkError)

        res = self.pf.protocol.login(self.mockUser3.username,\
         self.mockUser3.password)
        self.assertTrue(res['bAuthenticated'])

        res = self.pf.protocol.startremote(iSlotId=__iSlotId,\
         username=self.mockUser3.username, password=self.mockUser3.password)

        self.assertEqual(res['iResult'],\
         'This user is not assigned to this slot')

if __name__ == '__main__':
    unittest.main()  

