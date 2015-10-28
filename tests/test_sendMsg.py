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

"""
Simulation of basic functions performed.

To-do.
Check if it needs more simulated functions.
"""

from os import path
import os
import sys
import datetime
import pytz
import unittest
from mock import Mock
from mock import MagicMock

sys.path.append(path.abspath(path.join(path.dirname(__file__), "..")))

from twisted.internet import defer
from twisted.internet import protocol
from twisted.internet import reactor
from twisted.internet import ssl
from twisted.internet.error import CannotListenError
# from twisted.cred.portal import Portal
from twisted.python import log

from ampauth.errors import BadCredentials
from ampauth.errors import UnauthorizedLogin
from ampauth.server import CredReceiver
from ampauth.server import CredAMPServerFactory
from clientErrors import SlotErrorNotification

from ampCommands import SendMsg, StartRemote

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


"""
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
"""


class TestPassiveMessage(unittest.TestCase):

    """
    Testing multiple client connections
    TDOD. Test multiple valid connections
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
            return {'iResult': 'StartRemote.REMOTE_READY'}
        else:
            self.iSlots_available.append(iSlotId)
            return {'iResult': 'StartRemote.REMOTE_NOT_CONNECTED'}

    def mockSendMsg(self, sMsg, iTimestamp):

        return {'bResult': True}

        # try:
        #     if self.flag_StartRemote == True:
        #         return {'bResult': True}
        # except:
        #     raise SlotErrorNotification('Connection not available. Call StartRemote command first.')

    def _setUp_databases(self):
        """
        Users.
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

        # log.msg(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Flushing database")
        # management.execute_from_command_line(['manage.py', 'flush', '--noinput'])
        
        log.msg(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> New test")
        log.msg(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Populating database")        
        self._setUp_databases()
        
        log.msg(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Running tests")
        self.serverDisconnected = defer.Deferred()

        """
        Instancia la creacion del servidor y le pasa la desconexion
        """
        self.serverPort = self._listenServer(self.serverDisconnected)

        """
        Crea dos objetos del tipo deferred para conectar y desconectar
        Uno para cada cliente
        """

        self.connected1 = defer.Deferred()
        self.clientDisconnected1 = defer.Deferred()
        
        """
        Crea una factory. El caso es que la factory que crea yo no
        la creo en mis ejemplos
        """
        # self.factory1 = protocol.ClientFactory.forProtocol(ClientProtocolTest)
        self.factory1 = protocol.ClientFactory.forProtocol(ClientProtocolTest)
        self.clientConnection1 = self._connectClients(self.factory1,\
         self.connected1, self.clientDisconnected1)

        """
        Los dos objetos deferreds mas.
        """
        self.connected2 = defer.Deferred()
        self.clientDisconnected2 = defer.Deferred()
        
        """
        Y la otra factory
        """
        self.factory2 = protocol.ClientFactory.forProtocol(ClientProtocolTest)
        self.clientConnection2 = self._connectClients(self.factory2,\
         self.connected2, self.clientDisconnected2)

        """
        Retorna cuando ambos estan creados, ya lo estan,
        """
        return defer.gatherResults([self.connected1, self.connected2])

    def _listenServer(self, d):
        # checker = DjangoAuthChecker()
        # realm = Realm()
        # portal = Portal(realm, [checker])
        # pf = CredAMPServerFactory(portal)
        try:
            self.pf = CredAMPServerFactory()
            self.pf.protocol = CredReceiver()
            self.pf.protocol.login = MagicMock(side_effect=self.mockLoginMethod)
            """
            StartRemote funciona como una llamada del tipo AMP.
            Esto esta mal.
            """
            self.pf.protocol.startremote = MagicMock(side_effect=self.mockStartRemote)
            """
            SendMsg funciona como una llamada del tipo AMP.
            Esto esta mal.
            """
            self.pf.protocol.sendmsg = MagicMock(side_effect=self.mockSendMsg)
            self.pf.onConnectionLost = d
            cert = ssl.PrivateCertificate.loadPEM(
                open('../key/server.pem').read())
            return reactor.listenSSL(1234, self.pf, cert.options())
        except CannotListenError:
            log.msg("Server already initialized")

    def _connectClients(self, factory, d1, d2):
        """
        Le pasa su factoria correspondiente y los metodos de conexion
        y desconexion correspondientes
        """
        factory.onConnectionMade = d1
        factory.onConnectionLost = d2


        """
        Carga del certificado
        """
        cert = ssl.Certificate.loadPEM(open('../key/public.pem').read())
        """
        Configuracion
        """
        options = ssl.optionsForClientTLS(u'example.humsat.org', cert)

        """
        Inicio del reactor.
        """
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
    A message is sent by A to B, but the last one is not connected yet. The message is stored in 
    the server and marked "forwarded=false". The procedure goes:
        1. Client A -> login
        2. Client A -> StartRemote (should return StartRemote.REMOTE_NOT_CONNECTED)
        3. Client A -> sendMsg(__sMessageA2B) (should return True)
    """

    # get_utc_timestamp use?
    # @defer.inlineCallbacks // Why?
    @defer.inlineCallbacks
    def test_passiveMessage(self):
        log.msg(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> test_passiveMessage starts")
        __iSlotId = 1
        __sMessageA2B = "Adiós, ríos; adios, fontes; adios, regatos pequenos;"


        """
        Conecta
        """
        # # To notify when a new message is received by the client
        # res = yield login(self.factory1.protoInstance, UsernamePassword('tubio', 'tu.bio'))
        # self.assertTrue(res['bAuthenticated'])
        res = self.pf.protocol.login('xabi', 'pwdxabi')
        self.assertTrue(res['bAuthenticated'])

        """
        Inicia startremote
        """
        res = yield self.factory1.protoInstance.callRemote(StartRemote, iSlotId=__iSlotId)
        self.assertEqual(res['iResult'], StartRemote.REMOTE_NOT_CONNECTED)

        print "res"
        print res

        """
        Envia el mensaje
        """
        # res = yield self.factory1.protoInstance.callRemote(
        #     SendMsg, sMsg=__sMessageA2B, iTimestamp=misc.get_utc_timestamp())
        # self.assertTrue(res['bResult'])


        # res = self.pf.protocol.login('xabi', 'pwdxabi')
        # self.assertTrue(res['bAuthenticated'])

        # res = self.pf.protocol.startremote(iSlotId=__iSlotId)
        # self.assertEqual(res['iResult'], 'StartRemote.REMOTE_NOT_CONNECTED')

        # get_utc_timestamp = Mock(return_value='return')

        # res = self.pf.protocol.sendmsg(sMsg=__sMessageA2B,\
        #  iTimestamp=get_utc_timestamp())
        # self.assertTrue(res['bResult'])

        # self.pf.callRemote(SendMsg, sMsg, iTimestamp=get_utc_timestamp) 


    # """
    # Wrong procedure. The client tries to send a message before invoking 
    # StartRemote command. 
    # The procedure goes:
    #     1. Client A -> login
    #     2. Client A -> sendMsg(__sMessageA2B) (should raise 
    #         SlotErrorNotification('Connection not available. 
    #         Call StartRemote command first.'))
    # """

    # # get_utc_timestamp use?
    # def test_wrongMessageProcedure(self):
    #     log.msg(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> test_wrongMessageProcedure starts")
    #     __sMessageA2B = "Adiós, ríos; adios, fontes; adios, regatos pequenos;"

    # #     d1 = login(self.factory1.protoInstance, UsernamePassword(
    # #         'crespo', 'cre.spo'))
    # #     d1.addCallback(lambda l: self.factory1.protoInstance.callRemote(
    # #         SendMsg, sMsg=__sMessageA2B, iTimestamp=misc.get_utc_timestamp()))

    # #     def checkError(result):
    # #         self.assertEqual(
    # #             result.message, 'Connection not available. Call StartRemote command first.')
    # #     return self.assertFailure(d1, SlotErrorNotification).addCallback(checkError)

    #     res = self.pf.protocol.login('xabi', 'pwdxabi')
    #     self.assertTrue(res['bAuthenticated']) 

    #     # misc.get_utc_timestamp, Mock object
    #     get_utc_timestamp = Mock(return_value='return')
        
    #     return self.assertRaisesRegexp(SlotErrorNotification,\
    #      'Connection not available. Call StartRemote command first.',\
    #       self.pf.protocol.sendmsg, sMsg=__sMessageA2B,\
    #        iTimestamp=get_utc_timestamp())


    # """
    # Wrong procedure. The client tries to send a message before invoking 
    # StartRemote command. 
    # The procedure goes:
    #     1. Client A -> login
    #     2. Client A -> sendMsg(__sMessageA2B) (should raise 
    #         SlotErrorNotification('Connection not available. 
    #         Call StartRemote command first.'))
    # """

    # # @defer.inlineCallbacks // Why?
    # def test_SCDisconnecteds(self):
    #     log.msg(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> test_SCDisconnecteds starts")

    #     __iSlotId = 1
    #     __sMessageA2B = "Adiós, ríos; adios, fontes; adios, regatos pequenos;"
        
    #     # self.factory1.onEventReceived = defer.Deferred()

    #     # To notify when a new message is received by the client
    #     # res = yield login(self.factory1.protoInstance,\
    #     #  UsernamePassword('crespo', 'cre.spo'))
    #     # self.assertTrue(res['bAuthenticated'])

    #     # res = yield self.factory1.protoInstance.callRemote(StartRemote,\
    #     #  iSlotId=__iSlotId)
    #     # self.assertEqual(res['iResult'], StartRemote.REMOTE_NOT_CONNECTED)

    #     # res = yield self.factory1.protoInstance.callRemote(
    #     #     SendMsg, sMsg=__sMessageA2B, iTimestamp=misc.get_utc_timestamp())
    #     # self.assertTrue(res['bResult'])

    #     # # Events notifying REMOTE_CONNECTED to both clients
    #     # ev = yield self.factory1.onEventReceived
    #     # self.assertEqual(ev, NotifyEvent.REMOTE_DISCONNECTED)

    #     res = self.pf.protocol.login('xabi', 'pwdxabi')
    #     self.assertTrue(res['bAuthenticated']) 

    #     res = self.pf.protocol.startremote(iSlotId=__iSlotId)
    #     self.assertEqual(res['iResult'], 'StartRemote.REMOTE_NOT_CONNECTED')

    #     get_utc_timestamp = Mock(return_value='return')

    #     res = self.pf.protocol.sendmsg(sMsg=__sMessageA2B,\
    #      iTimestamp=get_utc_timestamp())
    #     self.assertTrue(res['bResult'])


    # """
    # Basic remote connection between two clients. The procedure goes:
    #     1. Client A -> login
    #     2. Client A -> StartRemote (should return 
    #                                 StartRemote.REMOTE_NOT_CONNECTED)
    #     3. Client B -> login
    #     4. Client B -> StartRemote (should return StartRemote.REMOTE_READY)
    #     5. Client A -> notifyEvent (should receive NotifyEvent.REMOTE_CONNECTED 
    #                                 + client B username)
    #     6. Client B -> notifyEvent (should receive NotifyEvent.REMOTE_CONNECTED
    #                                 + client A username)        
    #     7. Client B -> sendMsg(__sMessageA2B)
    #     8. Client A -> notifyMsg (should receive __sMessageA2B)
    #     7. Client B -> sendMsg(__sMessageA2B)
    #     8. Client A -> notifyMsg (should receive __sMessageA2B)

    # """

    # # @defer.inlineCallbacks // Why?
    # def test_sendMsg(self):
    #     log.msg(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> test_sendMsg starts")

    #     __iSlotId = 1
    #     __sMessage1_A2B = "Adiós, ríos; adios, fontes; adios, regatos pequenos;"
    #     __sMessage2_A2B = "adios, vista dos meus ollos: non sei cando nos veremos."
    #     __user1_name = 'xabi'
    #     __user1_pass = 'pwdxabi'
    #     __user2_name = 'sam'
    #     __user2_pass = 'pwdsam'

    #     self.factory1.onMessageReceived = defer.Deferred()
    #     self.factory1.onEventReceived = defer.Deferred()
    #     self.factory2.onEventReceived = defer.Deferred()

    #     # User 1 (login + start remote)
    #     # res = yield login(self.factory1.protoInstance, UsernamePassword(
    #     #     __user1_name, __user1_pass))
    #     # self.assertTrue(res['bAuthenticated'])

    #     res = self.pf.protocol.login(__user1_name, __user1_pass)
    #     self.assertTrue(res['bAuthenticated']) 

    #     # res = yield self.factory1.protoInstance.callRemote(StartRemote,\
    #     #  iSlotId=__iSlotId)
    #     # self.assertEqual(res['iResult'], StartRemote.REMOTE_NOT_CONNECTED)

    #     res = self.pf.protocol.startremote(iSlotId=__iSlotId)
    #     self.assertEqual(res['iResult'], 'StartRemote.REMOTE_NOT_CONNECTED')   

    #     # User 2 (login + start remote)
    #     # res = yield login(self.factory2.protoInstance, UsernamePassword(
    #     #     __user2_name, __user2_pass))
    #     # self.assertTrue(res['bAuthenticated'])

    #     res = self.pf.protocol.login(__user2_name, __user2_pass)
    #     self.assertTrue(res['bAuthenticated']) 

    #     # res = yield self.factory2.protoInstance.callRemote(StartRemote,\
    #     #  iSlotId=__iSlotId)
    #     # self.assertEqual(res['iResult'], StartRemote.REMOTE_READY)

    #     res = self.pf.protocol.startremote(iSlotId=__iSlotId)
    #     self.assertEqual(res['iResult'], 'StartRemote.REMOTE_READY')


    #     # # Events notifying REMOTE_CONNECTED to both clients
    #     # ev = yield self.factory1.onEventReceived
    #     # self.assertEqual(ev, NotifyEvent.REMOTE_CONNECTED)
    #     # self.factory1.onEventReceived = defer.Deferred()
        
    #     onEventReceived = Mock(return_value='NotifyEvent.REMOTE_CONNECTED')
    #     ev = onEventReceived()
    #     self.assertEqual(ev, 'NotifyEvent.REMOTE_CONNECTED')

    #     # ev = yield self.factory2.onEventReceived
    #     # self.assertEqual(ev, NotifyEvent.REMOTE_CONNECTED)
    #     # self.factory2.onEventReceived = defer.Deferred()
        
    #     ev = onEventReceived()
    #     self.assertTrue(ev, 'NotifyEvent.REMOTE_CONNECTED')

    #     # # User 1 sends a message to user 2
    #     # res = yield self.factory2.protoInstance.callRemote(SendMsg,\
    #     #  sMsg=__sMessage1_A2B, iTimestamp=misc.get_utc_timestamp())
    #     # self.assertTrue(res['bResult'])

    #     get_utc_timestamp = Mock(return_value='return')
    #     res = self.pf.protocol.sendmsg(sMsg=__sMessage1_A2B,\
    #      iTimestamp=get_utc_timestamp())
    #     self.assertTrue(res['bResult'])

    #     # msg = yield self.factory1.onMessageReceived
    #     # self.assertEqual(msg, __sMessage1_A2B)
    #     #self.factory1.onMessageReceived = defer.Deferred()

    #     onMessageReceived = Mock(return_value=__sMessage1_A2B)
    #     msg = onMessageReceived()
    #     self.assertEqual(msg, __sMessage1_A2B)

    #     # res = yield self.factory2.protoInstance.callRemote(SendMsg,\
    #     #  sMsg=__sMessage2_A2B, iTimestamp=misc.get_utc_timestamp())
    #     # self.assertTrue(res['bResult'])

    #     d7 = self.pf.protocol.sendmsg(sMsg=__sMessage2_A2B,\
    #      iTimestamp=get_utc_timestamp())
    #     self.assertTrue(res['bResult'])

    #     # msg = yield self.factory1.onMessageReceived
    #     # self.assertEqual(msg, __sMessage2_A2B)

    #     onMessageReceived = Mock(return_value=__sMessage2_A2B)
    #     msg = onMessageReceived()
    #     self.assertEqual(msg, __sMessage2_A2B)


if __name__ == '__main__':
    unittest.main()  