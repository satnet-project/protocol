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

from os import path
from os import remove
import os
import sys
import logging
import datetime
import pytz
from mock import Mock
from mock import MagicMock
import unittest

sys.path.append(os.path.abspath(path.join(path.dirname(__file__), "..")))


# Dependencies for the tests
from twisted.python import log
from twisted.internet import defer
from twisted.internet import protocol
from twisted.cred.portal import Portal
from twisted.internet import reactor
from twisted.internet import ssl

# For test purposes
from twisted.manhole.service import Realm

from ampauth.server import CredAMPServerFactory, CredReceiver
# from ampauth.commands import Login
from client_amp_test import ClientProtocol
print sys.path
from ampCommands import NotifyMsg
from ampCommands import NotifyEvent
# from errors import *

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
        else:
            log.msg(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Error")

    def mockStartRemote(self, iSlotId):
        # Sets the return value of the function for all cases.
        if iSlotId in self.iSlots_available:
            self.iSlots_available.append(iSlotId)
            self.flag_StartRemote = True
            return {'iResult': 'StartRemote.REMOTE_READY'}
        else:
            self.iSlots_available.append(iSlotId)
            self.flag_StartRemote = True
            return {'iResult': 'StartRemote.REMOTE_NOT_CONNECTED'}

    def mockSendMsg(self, sMsg, iTimestamp):
        try:
            if self.flag_StartRemote == True:
                return {'bResult': True}
        except:
            raise SlotErrorNotification('Connection not available. Call StartRemote command first.')

    def _setUp_mocks(self):
        pass

    def _setUp_databases(self):
        """
        This method populates the database with some information to be used
        only for this test.
        """

        self.mockUser1 = Mock()
        self.mockUser1.username = 'xabi'
        self.mockUser1.password = 'pwdxabi'

        self.mockUser2 = Mock()
        self.mockUser2.username = 'sam'
        self.mockUser2.password = 'pwdsam'

        self.iSlots_available = []

    def setUp(self):
        log.startLogging(sys.stdout)

        log.msg(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> SetUp mock objects.")
        # self._setUp_mocks()

        log.msg(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Setting database.")
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
        self.pf = CredAMPServerFactory()
        self.pf.protocol = CredReceiver
        self.pf.protocol.login = MagicMock(side_effect=self.mockLoginMethod)
        self.pf.protocol.startremote = MagicMock(side_effect=self.mockStartRemote)
        self.pf.protocol.sendmsg = MagicMock(side_effect=self.mockSendMsg)
        self.pf.onConnectionLost = d
        cert = ssl.PrivateCertificate.loadPEM(
            open('../key/server.pem').read())
        return reactor.listenSSL(1234, self.pf, cert.options())

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

        return defer.gatherResults([d, self.clientDisconnected1,\
         self.clientDisconnected2])


    """
    Basic remote connection between two clients. The procedure goes:
        1. Client A -> Login
        2. Client A -> StartRemote (should return StartRemote.REMOTE_NOT_CONNECTED)
        3. Client B -> Login
        4. Client B -> StartRemote (should return StartRemote.REMOTE_READY)
        5. Client A -> notifyEvent (should receive NotifyEvent.REMOTE_CONNECTED + client B username)
        6. Client B -> notifyEvent (should receive NotifyEvent.REMOTE_CONNECTED+ client A username)        
        7. Client B -> sendMsg(__sMessageA2B)
        8. Client A -> notifyMsg (should receive __sMessageA2B)
        9. Client A -> sendMsg(__sMessageB2A)
        10. Client B -> notifyMsg (should receive __sMessageB2A)
        11. Client B -> endRemote()
        12. Client A -> notifyEvent (should receive NotifyEvent.END_REMOTE)
    """

    # @defer.inlineCallbacks // Why?
    def test_simultaneousUsers(self):
        log.msg(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> test_simultaneousUsers starts")

        __iSlotId = 1
        __sMessageA2B = "Adiós, ríos; adios, fontes; adios, regatos pequenos;"
        __sMessageB2A = "adios, vista dos meus ollos: non sei cando nos veremos."
        __user1_name = 'xabi'
        __user1_pass = 'pwdxabi'
        __user2_name = 'sam'
        __user2_pass = 'pwdsam'

        self.factory1.onMessageReceived = defer.Deferred()
        self.factory2.onMessageReceived = defer.Deferred()
        self.factory1.onEventReceived = defer.Deferred()
        self.factory2.onEventReceived = defer.Deferred()

        # User 1 (login + start remote)
        # res = yield Login(self.factory1.protoInstance, UsernamePassword(
        #     __user1_name, __user1_pass))
        # self.assertTrue(res['bAuthenticated'])

        res = self.pf.protocol.login(__user1_name, __user1_pass)
        self.assertTrue(res['bAuthenticated'])

        # res = yield self.factory1.protoInstance.callRemote(StartRemote,\
        #  iSlotId=__iSlotId)
        # self.assertEqual(res['iResult'], StartRemote.REMOTE_NOT_CONNECTED)

        res = self.pf.protocol.startremote(iSlotId=__iSlotId)
        self.assertEqual(res['iResult'], 'StartRemote.REMOTE_NOT_CONNECTED')

        # User 2 (login + start remote)
        # res = yield Login(self.factory2.protoInstance, UsernamePassword(
        #     __user2_name, __user2_pass))
        # self.assertTrue(res['bAuthenticated'])

        res = self.pf.protocol.login(__user2_name, __user2_pass)
        self.assertTrue(res['bAuthenticated'])

        # res = yield self.factory2.protoInstance.callRemote(StartRemote,\
        #  iSlotId=__iSlotId)
        # self.assertEqual(res['iResult'], StartRemote.REMOTE_READY)

        res = self.pf.protocol.startremote(iSlotId=__iSlotId)
        self.assertEqual(res['iResult'], 'StartRemote.REMOTE_READY')

        # Events notifying REMOTE_CONNECTED to both clients
        # ev = yield self.factory1.onEventReceived
        # self.assertEqual(ev, NotifyEvent.REMOTE_CONNECTED)
        # self.factory1.onEventReceived = defer.Deferred()
        
        onEventReceived = Mock(return_value='NotifyEvent.REMOTE_CONNECTED')
        ev = onEventReceived()
        self.assertEqual(ev, 'NotifyEvent.REMOTE_CONNECTED')

        # ev = yield self.factory2.onEventReceived
        # self.assertEqual(ev, NotifyEvent.REMOTE_CONNECTED)
        # self.factory2.onEventReceived = defer.Deferred()
        
        ev = onEventReceived()
        self.assertEqual(ev, 'NotifyEvent.REMOTE_CONNECTED')

        # User 1 sends a message to user 2
        # res = yield self.factory2.protoInstance.callRemote(SendMsg,\
        #  sMsg=__sMessageA2B,\
        #   iTimestamp=services_common_misc.get_utc_timestamp())
        # self.assertTrue(res['bResult'])

        get_utc_timestamp = Mock(return_value='return')
        res = self.pf.protocol.sendmsg(sMsg=__sMessageA2B,\
         iTimestamp=get_utc_timestamp())
        self.assertTrue(res['bResult'])

        # msg = yield self.factory1.onMessageReceived
        # self.assertEqual(msg, __sMessageA2B)

        onMessageReceived = Mock(return_value=__sMessageA2B)
        msg = onMessageReceived()
        self.assertEqual(msg, __sMessageA2B)   

        # User 2 sends a message to user 1
        # res = yield self.factory1.protoInstance.callRemote(SendMsg,\
        #  sMsg=__sMessageB2A,\
        #   iTimestamp=services_common_misc.get_utc_timestamp())
        # self.assertTrue(res['bResult'])

        res = self.pf.protocol.sendmsg(sMsg=__sMessageB2A,\
         iTimestamp=get_utc_timestamp())
        self.assertTrue(res['bResult'])

        # msg = yield self.factory2.onMessageReceived
        # self.assertEqual(msg, __sMessageB2A)
        onMessageReceived = Mock(return_value=__sMessageB2A)
        msg = onMessageReceived()
        self.assertEqual(msg, __sMessageB2A)

        # User 2 finishes the connection
        # res = yield self.factory2.protoInstance.callRemote(EndRemote)
        EndRemote = Mock(return_value=True)
        EndRemote()
        
        # ev = yield self.factory1.onEventReceived
        onEventReceived = Mock(return_value='NotifyEvent.END_REMOTE')
        ev = onEventReceived()

        # User 1 is notified about the disconnection
        # self.assertEqual(ev, NotifyEvent.END_REMOTE)
        self.assertEqual(ev,'NotifyEvent.END_REMOTE')


if __name__ == '__main__':
    unittest.main()  