# coding=utf-8

import time
import misc
import arrow

from datetime import datetime
from login import Login
from errors import BadCredentials, SlotErrorNotification

from twisted.internet import reactor
from twisted.internet.protocol import ServerFactory
from twisted.cred.error import UnauthorizedLogin
from twisted.protocols.amp import AMP
from twisted.protocols.policies import TimeoutMixin
from twisted.python import log

from ampCommands import StartRemote
from ampCommands import EndRemote
from ampCommands import SendMsg
from ampCommands import NotifyMsg
from ampCommands import NotifyEvent
from rpcrequests import SatnetRPC


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


class CredReceiver(AMP, TimeoutMixin):
    """
    Integration between AMP and L{twisted.cred}. This class is only intended
    to be used for credentials purposes. The specific SATNET protocol will be
    implemented in L{SATNETServer} (see server.py).
    """

    rpc = None
    slot_id = -1
    is_user_gs = None

    logout = None
    session = None

    username = ''
    timeout = 600  # seconds
    # ### FIXED :: Added 'password' field to store the password after login
    password = ''

    # Metodo que comprueba cuando una conexion se ha realizado con twisted
    def connectionMade(self):
        self.setTimeout(self.timeout)
        super(CredReceiver, self).connectionMade()
        self.factory.clients.append(self)

    def dataReceived(self, data):
        log.msg(self.username + ' session timeout reset')
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

        if sUsername in self.factory.active_protocols:
            log.err("Client already logged in.")
            raise UnauthorizedLogin("Client already logged in.")
        else:
            self.username = sUsername
            self.password = sPassword
            self.factory.active_protocols[sUsername] = None

        # TODO Find out what the comment below means
        # Don't mix asynchronus and syncronus code.
        # Try-except sentences aren't allowed.
        try:
	    print '>>> @login: sUsername = ' + str(sUsername) + ', ' + str(sPassword)
            self.rpc = SatnetRPC(sUsername, sPassword)
            self.factory.active_protocols[sUsername] = self
            log.msg('Connection made')
            log.msg('Active clients: ' +
                    str(len(self.factory.active_protocols)))
            log.msg('Active connections: ' +
                    str(len(self.factory.active_connections)))

            return {'bAuthenticated': True}

        except BadCredentials:
            log.err('Incorrect username and/or password')
            log.msg(self.factory.active_protocols)
            raise BadCredentials("Incorrect username and/or password")

    def decode_user(self, slot_id, slot):
        """Decodes the information of the client
        :param slot_id: Identifier of the slot
        :param slot:
        :return:
        """

        if not slot:
            err_msg = 'Slot NOT operational, id = ' + str(slot_id)
            log.err('Slot ' + str(slot_id) + ' is not yet operational')
            raise SlotErrorNotification(
                'Not operational slot, id = ' + str(slot_id)
            )

        gs_user = slot['gs_username']
        sc_user = slot['sc_username']

        client_a = sc_user
        client_b = gs_user
        if gs_user == self.username:
            client_a = gs_user
            client_b = sc_user

        return gs_user, sc_user, client_a, client_b

    def check_slot_ownership(self, gs_user, sc_user):
        """Checks if this slot has not been assigned to this user
        :param gs_user: Username of the groundstation user
        :param sc_user: Username of the spacecraft user
        """
        if gs_user != self.username and sc_user != self.username:
            err_msg = 'This slot has not been assigned to this user'
            log.err(err_msg)
            raise SlotErrorNotification(err_msg)

    # Check user name
    def iStartRemote(self, iSlotId):
        log.msg("(" + self.username + ") --------- Start Remote ---------")

        slot = self.rpc.get_slot(iSlotId)
        gs_user, sc_user, client_a, client_c = self.decode_user(iSlotId, slot)
        log.msg('>>> @iStartRemote.slot = ' + str(slot))

        if slot['state'] != 'TEST':
            self.check_slot_ownership(gs_user, sc_user)

        return self.create_connection(
            slot['ending_time'], iSlotId, client_a, client_c
        )

    @staticmethod
    def check_expiration(slot_id, slot_end):
        """Check slot's expiration
        :param slot_id: Identifier of the slot
        :param slot_end: Datetime end of the slot
        """
        time_now = misc.localize_datetime_utc(datetime.utcnow())
        time_now = int(time.mktime(time_now.timetuple()))
        time_end = arrow.get(str(slot_end))
        time_end = time_end.timestamp

        slot_remaining_time = int(time_end) - time_now
        log.msg('Slot remaining time: ' + str(slot_remaining_time))

        if slot_remaining_time <= 0:
            err_msg = "Slot EXPIRED, id = " + str(slot_id)
            log.err(err_msg)
            raise SlotErrorNotification(err_msg)

        return slot_remaining_time

    # noinspection PyUnresolvedReferences
    def create_connection(self, slot_end, slot_id, client_a, client_c):
        """
        Create a new connection checking the time slot: clientA sends data,
        clientC receives data.
        :param slot_end: end of the slot
        :param slot_id: identifier of the slot
        :param client_a: Client A
        :param client_c: Client C
        """
        client_a = str(client_a)
        client_c = str(client_c)

        if slot_id != -1:
            slot_remaining_time = CredReceiver.check_expiration(
                slot_id, slot_end
            )
            self.session = reactor.callLater(
                slot_remaining_time, self.slot_end, slot_id
            )

        if client_c not in self.factory.active_protocols:
            log.msg("Remote user " + client_c + " not connected yet.")
            self.factory.active_connections[client_a] = None
            return {'iResult': StartRemote.REMOTE_NOT_CONNECTED}

        log.msg("Remote user " + client_c + ".")
        self.factory.active_connections[client_c] = client_a
        self.factory.active_connections[client_a] = client_c
        self.factory.active_protocols[client_c].callRemote(
            NotifyEvent,
            iEvent=NotifyEvent.REMOTE_CONNECTED,
            sDetails=str(client_a)
        )
        self.callRemote(
            NotifyEvent,
            iEvent=NotifyEvent.REMOTE_CONNECTED,
            sDetails=str(client_c)
        )
        return {'iResult': StartRemote.REMOTE_READY}

    def slot_end(self, slot_id):
        log.msg(
            "(" + self.username + ") Slot " + str(slot_id) + ' has finished'
        )
        self.callRemote(
            NotifyEvent, iEvent=NotifyEvent.SLOT_END, sDetails=None
        )

        #  Session is an instance of
        self.session = None

    def vEndRemote(self):

        log.msg("(" + self.username + ") --------- End Remote ---------")
        # Disconnect local user
        self.transport.loseConnection()

        # FIXME self.factory.active_protocols.pop(self.sUsername)
        # FIXME Try to remove the remote connection but the former is not there

        try:
            # Notify remote user
            self.factory.active_protocols[self.factory.active_connections[
                self.username
            ]].callRemote(
                NotifyEvent,
                iEvent=NotifyEvent.END_REMOTE,
                sDetails=None
            )

            # Close remote connection
            self.factory.active_protocols[self.factory.active_connections[
                self.username
            ]].transport.loseConnection()

            # Remove remove factory
            self.factory.active_connections.pop(
                self.factory.active_connections[self.username]
            )
            self.factory.active_connections.pop(self.username)

        except Exception as ex:
            log.msg("Connections already cleared, ex = " + str(ex))

        return {'bResult': True}

    def vSendMsg(self, sMsg, iTimestamp):

        log.msg("SEND (" + self.username + ") = " + str(sMsg))
        # If the client haven't started a connection via StartRemote command...

        if self.username not in self.factory.active_connections:
            err_msg = 'Connection not available.'
            log.msg(err_msg)
            raise SlotErrorNotification(err_msg)

        # ... if the SC operator is not connected, sent messages will be saved
        # as passive messages...
        elif (
            self.factory.active_connections[self.username] is None and
            self.is_user_gs is True
        ):
            log.msg("No SC operator connected, stored as a passive message")
            self.rpc.store_message_unconnected(sMsg)

        # ... if the GS operator is not connected, the remote SC client will be
        # notified to wait for the GS to connect...
        elif (
            self.factory.active_connections[self.username] is None and
            self.is_user_gs is False
        ):
            self.callRemote(
                NotifyEvent,
                iEvent=NotifyEvent.REMOTE_DISCONNECTED,
                sDetails=None
            )

        else:
            # Try to send a message to remote client
            try:
                self.factory.active_protocols[self.factory.active_connections[
                    self.username
                ]].callRemote(NotifyMsg, sMsg=sMsg)
            except:
                raise ValueError("Error forwarding frame to remote user.")
            # Try to store the message in the remote SatNet server
            forwarded = ''

        self.rpc.store_message(
            self.slot_id, self.is_user_gs, False, iTimestamp, sMsg
        )

        return {'bResult': True}

    Login.responder(login)
    StartRemote.responder(iStartRemote)
    SendMsg.responder(vSendMsg)
    EndRemote.responder(vEndRemote)


class CredAMPServerFactory(ServerFactory):
    """Server factory useful for creating L{CredReceiver} instances.
    """
    clients = []
    active_protocols = {}
    active_connections = {}
    protocol = CredReceiver

