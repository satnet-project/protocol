# coding=utf-8
import os
import sys
import time
import misc

from datetime import datetime
from login import Login
from errors import BadCredentials

from twisted.internet import reactor
from twisted.internet.protocol import ServerFactory
from twisted.cred.error import UnauthorizedLogin
from twisted.protocols.amp import AMP
from twisted.protocols.policies import TimeoutMixin
from twisted.python import log
from twisted.internet import protocol

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ampCommands import StartRemote
from ampCommands import EndRemote
from ampCommands import SendMsg
from ampCommands import NotifyMsg
from ampCommands import NotifyEvent
from clientErrors import SlotErrorNotification
from rpcrequests import Satnet_RPC
from server_amp import *

from rpcrequests import Satnet_GetSlot
from rpcrequests import Satnet_StorePassiveMessage
from rpcrequests import Satnet_StoreMessage


"""
   Copyright 2014, 2015, 2016 Xabier Crespo Álvarez, Samuel Góngora García

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
    Samuel Góngora García (s.gongoragarcia@gmail.com)
"""
__author__ = 'xabicrespog@gmail.com'
__author__ = 's.gongoragarcia@gmail.com'


class CredReceiver(AMP, TimeoutMixin):

    """
    Integration between AMP and L{twisted.cred}. This class is only intended
    to be used for credentials purposes. The specific SATNET protocol will be
    implemented in L{SATNETServer} (see server_amp.py).

    :ivar sUsername:
        Each protocol belongs to a User. This field represents User.username
    :type sUsername:
        L{String}

    :ivar iTimeOut:
        The duration of the session timeout in seconds. After this
        time the user will be automatically disconnected.
    :type iTimeOut:
        L{int}

    :ivar session:
        Reference to a object in charge of removing the user from
        active_protocols when it is inactive.
    :type session:
        L{IDelayedCall}

    :ivar clientA
        Groundstation user
    :type clientA
        L{String}

    :ivar clientB
        Spacecraft user
    :type clientB
        L{String}

    :ivar bGSuser
        Indicates if the current user is a GS user (True) or a SC user (false).
        If this variable is None, it means that it has not been yet connected.
    :type bGSuser
        L{Boolean}
    """

    logout = None
    sUsername = ''
    iTimeOut = 300  # seconds
    session = None

    avatar = None

    # Metodo que comprueba cuando una conexion se ha realizado con twisted
    def connectionMade(self):
        self.setTimeout(self.iTimeOut)
        super(CredReceiver, self).connectionMade()
        self.factory.clients.append(self)

    def dataReceived(self, data):
        log.msg(self.sUsername + ' session timeout reset')
        self.resetTimeout()
        super(CredReceiver, self).dataReceived(data)

    def timeoutConnection(self):
        log.err('Session timeout expired')
        self.transport.loseConnection()

    def connectionLost(self, reason):
        # Remove client from active users
        if self.session is not None:
            self.session.cancel()

        log.err(reason.getErrorMessage())

        log.msg('Active clients: ' +
                str(len(self.factory.active_protocols)))
        log.msg('Active connections: ' +
                str(len(self.factory.active_connections)/2))

        self.setTimeout(None)  # Cancel the pending timeout
        self.transport.loseConnection()

        super(CredReceiver, self).connectionLost(reason)

    def login(self, sUsername, sPassword):
        # self.factory = CredAMPServerFactory() ¿?
        if sUsername in self.factory.active_protocols:
            log.err("Client already logged in.")
            raise UnauthorizedLogin("Client already logged in.")
        else:
            self.sUsername = sUsername
            # Clean previous registers
            self.factory.active_protocols[sUsername] = None
        #
        #  Don't mix asynchronus and syncronus code.
        #  Try-except sentences aren't allowed.
        #
        try:
            self.rpc = Satnet_RPC(sUsername, sPassword)
            self.factory.active_protocols[sUsername] = self
            log.msg('Connection made')
            log.msg('Active clients: ' +
                    str(len(self.factory.active_protocols)))
            log.msg('Active connections: ' +
                    str(len(self.factory.active_connections)))

            return {'bAuthenticated': True}

        except BadCredentials:
            log.err('Incorrect username and/or password')
            raise BadCredentials("Incorrect username and/or password")

    Login.responder(login)

    # Check user name
    def iStartRemote(self, iSlotId):
        log.msg("(" + self.sUsername + ") --------- Start Remote ---------")

        self.iSlotId = iSlotId

        slot = Satnet_GetSlot(self.iSlotId)
        self.slot = slot.slot

        #  If slot NOT operational yet...
        if not self.slot:
            log.err('Slot ' + str(iSlotId) + ' is not yet operational')
            raise SlotErrorNotification(
                'Slot ' + str(iSlotId) + ' is not yet operational')
        else:
            #  Now only works in test cases
            if self.slot['state'] != 'TEST':
                log.err('Slot ' + str(iSlotId) + ' has not yet been reserved')
                raise SlotErrorNotification('Slot ' + str(iSlotId) +
                                            ' has not yet been reserved')

            gs_user = self.slot['gs_username']
            sc_user = self.slot['sc_username']

            #  If this slot has not been assigned to this user...
            if gs_user != self.sUsername and sc_user != self.sUsername:
                log.err('This slot has not been assigned to this user')
                raise SlotErrorNotification('This user is not ' +
                                            'assigned to this slot')
            #  if the GS user and the SC user belong to the same client...
            elif gs_user == self.sUsername and sc_user == self.sUsername:
                log.msg('Both MCC and GSS belong to the same client')
                return {'iResult': StartRemote.CLIENTS_COINCIDE}
            #  if the remote client is the SC user...
            elif gs_user == self.sUsername:
                self.bGSuser = True
                return self.iCreateConnection(self.slot['ending_time'],
                                              iSlotId, gs_user, sc_user)
            #  if the remote client is the GS user...
            elif sc_user == self.sUsername:
                self.bGSuser = False
                return self.iCreateConnection(self.slot['ending_time'],
                                              iSlotId, sc_user, gs_user)

    StartRemote.responder(iStartRemote)

    def iCreateConnection(self, iSlotEnd, iSlotId, clientA, clientC):
        """
        Create a new connection checking the time slot.
        ClientA sends data
        ClientC receive data
        """

        clientA = str(clientA)
        clientC = str(clientC)

        import dateutil.parser
        iSlotEnd = dateutil.parser.parse(iSlotEnd)
        iSlotEnd = int(time.mktime(iSlotEnd.timetuple()))

        timeNow = misc.localize_datetime_utc(datetime.utcnow())
        timeNow = int(time.mktime(timeNow.timetuple()))

        # For tests only
        iSlotEnd = timeNow + 86400

        slot_remaining_time = iSlotEnd - timeNow
        log.msg('Slot remaining time: ' + str(slot_remaining_time))

        if (slot_remaining_time <= 0):
            log.err("This slot (" + str(iSlotId) + ") has expired.")

            raise SlotErrorNotification("This slot (" + str(iSlotId) +
                                        " has expired.")

        #  Create an instante for finish the slot at correct time.
        self.session = reactor.callLater(slot_remaining_time,
                                         self.vSlotEnd, iSlotId)

        if clientC not in self.factory.active_protocols:
            log.msg("Remote user " + clientC + " not connected yet.")
            # if remote user ins't available remove local user from
            # active connections list
            self.factory.active_connections[clientA] = None
            return {'iResult': StartRemote.REMOTE_NOT_CONNECTED}

        else:
            log.msg("Remote user " + clientC + ".")
            self.factory.active_connections[clientC] = clientA
            self.factory.active_connections[clientA] = clientC
            self.factory.active_protocols[clientC].callRemote(
                NotifyEvent, iEvent=NotifyEvent.REMOTE_CONNECTED,
                sDetails=str(clientA))
            self.callRemote(
                NotifyEvent, iEvent=NotifyEvent.REMOTE_CONNECTED,
                sDetails=str(clientC))
            return {'iResult': StartRemote.REMOTE_READY}

    def vSlotEnd(self, iSlotId):
        log.msg("(" + self.sUsername + ") Slot " +
                str(iSlotId) + ' has finished')
        self.callRemote(NotifyEvent, iEvent=NotifyEvent.SLOT_END,
                        sDetails=None)

        #  Session is an instance of
        self.session = None

    def vEndRemote(self):
        log.msg("(" + self.sUsername + ") --------- End Remote ---------")
        # Disconnect local user
        self.transport.loseConnection()

        # Try to remove the remote connection
        try:
            # Notify remote user
            self.factory.active_protocols[self.factory.active_connections[
                self.sUsername]].callRemote(NotifyEvent,
                                            iEvent=NotifyEvent.END_REMOTE,
                                            sDetails=None)

            # Close remote connection
            self.factory.active_protocols[self.factory.active_connections[
                self.sUsername]].transport.loseConnection()

            # Remove remove factory
            self.factory.active_connections.pop(
                self.factory.active_connections[self.sUsername])

        except:
            # Remove local factory
            self.factory.active_protocols.pop(self.sUsername)

        return {'bResult': True}

    EndRemote.responder(vEndRemote)

    def vSendMsg(self, sMsg, iTimestamp):
        log.msg("(" + self.sUsername + ") --------- Send Message ---------")
        # If the client haven't started a connection via StartRemote command...
        if self.sUsername not in self.factory.active_connections:
            log.msg('Connection not available. Call StartRemote command first')
            raise SlotErrorNotification(
                'Connection not available. Call StartRemote command first.')

        # ... if the SC operator is not connected, sent messages will be saved
        # as passive messages...
        elif self.factory.active_connections[self.sUsername] == None and self.bGSuser == True:
            log.msg("RPC Call to Satnet_StorePassiveMessage")

        # ... if the GS operator is not connected, the remote SC client will be
        # notified to wait for the GS to connect...
        elif self.factory.active_connections[self.sUsername] == None and self.bGSuser == False:
            self.callRemote(NotifyEvent,
                            iEvent=NotifyEvent.REMOTE_DISCONNECTED,
                            sDetails=None)
        else:
            # Try to send a message to remote client
            log.msg("Enter send message")
            try:
                self.factory.active_protocols[self.factory.active_connections[
                    self.sUsername]].callRemote(NotifyMsg, sMsg=sMsg)
            except:
                raise WrongFormatNotification("Error forwarding frame to remote user.")
            # Try to store the message in the remote SatNet server
            forwarded = ''
            self.storeMessage = Satnet_StoreMessage(self.iSlotId, self.bGSuser,
                                                    forwarded, iTimestamp,
                                                    sMsg)

        return {'bResult': True}
    SendMsg.responder(vSendMsg)


class CredAMPServerFactory(ServerFactory):

    """
    Server factory useful for creating L{CredReceiver} instances.

    """
    clients = []
    active_protocols = {}
    active_connections = {}
    protocol = CredReceiver

    def __init__(self):
        self.filename = 'patata'
