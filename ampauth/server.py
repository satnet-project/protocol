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
        # Y si cada vez recibo "data" lo reenvio desde aqui?
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

        log.msg('Active clients: ')
        #  divided by 2 because the dictionary is doubly linked
        log.msg('Active connections: ')

        self.setTimeout(None)  # Cancel the pending timeout
        self.transport.loseConnection()

        super(CredReceiver, self).connectionLost(reason)

    def login(self, sUsername, sPassword):

        self.sUsername = sUsername
        self.factory = CredAMPServerFactory()
        #
        #  Don't mix asynchronus and syncronus code.
        #  Try-except sentences aren't allowed.
        #

        # Comprueba si el cliente A o B está logueado viendo
        # si sUsername está disponible
        try:
            print d
        except NameError:
            log.msg("d no creado")

        """
        if sUsername in self.factory.active_protocols['localUsr']:
            log.err('Client already logged in')
            raise UnauthorizedLogin('Client already logged in')
        """

        try:
            self.rpc = Satnet_RPC(sUsername, sPassword)
            log.msg('Connection made')

            self.logger = MessageLogger(open(self.factory.filename, "a"))
            self.logger.log("User %s" % sUsername)

            return {'bAuthenticated': True}

        except BadCredentials:
            log.err('Incorrect username and/or password')
            raise BadCredentials("Incorrect username and/or password")

    Login.responder(login)

    # Check user name
    def iStartRemote(self, iSlotId):
        log.msg("(" + self.sUsername + ") --------- Start Remote ---------")

        self.iSlotId = iSlotId

        slot = Satnet_GetSlot(iSlotId)
        self.slot = slot.slot

        import shelve
        d = shelve.open('test')

        #  If slot NOT operational yet...
        if not self.slot:
            log.err('Slot ' + str(iSlotId) + ' is not yet operational')
            raise SlotErrorNotification(
                'Slot ' + str(iSlotId) + ' is not yet operational')
        else:
            #  If it is too soon to connect to this slot...
            if self.slot['state'] != 'TEST':
                log.err('Slot ' + str(iSlotId) + ' has not yet been reserved')
                raise SlotErrorNotification('Slot ' + str(iSlotId) +
                                            ' has not yet been reserved')

            clientA = self.slot['gs_username']
            clientB = self.slot['sc_username']

            print clientA
            print clientB

            #  If this slot has not been assigned to this user...
            if clientA != self.sUsername and clientB != self.sUsername:
                log.err('This slot has not been assigned to this user')
                raise SlotErrorNotification('This user is not ' +
                                            'assigned to this slot')
            #  if the GS user and the SC user belong to the same client...
            elif clientA == self.sUsername and clientB == self.sUsername:
                log.msg('Both MCC and GSS belong to the same client')
                return {'iResult': StartRemote.CLIENTS_COINCIDE}
            #  if the remote client is the SC user... ClientA
            elif clientA == self.sUsername:
                self.bGSuser = True
                return self.CreateConnection(self.slot['ending_time'],
                                             iSlotId, clientB, clientA)
            #  if the remote client is the GS user...
            elif clientB == self.sUsername:
                self.bGSuser = False
                return self.CreateConnection(self.slot['ending_time'],
                                             iSlotId, clientA, clientB)

    StartRemote.responder(iStartRemote)

    def CreateConnection(self, iSlotEnd, iSlotId, clientA, clientC):
        """
        Create a new connection checking the time slot.
        """
        self.remoteUsr = remoteUsr

        import dateutil.parser
        iSlotEnd = dateutil.parser.parse(iSlotEnd)
        iSlotEnd = int(time.mktime(iSlotEnd.timetuple()))

        timeNow = misc.localize_datetime_utc(datetime.utcnow())
        timeNow = int(time.mktime(timeNow.timetuple()))

        # For tests only
        iSlotEnd = timeNow + 480

        slot_remaining_time = iSlotEnd - timeNow
        log.msg('Slot remaining time: ' + str(slot_remaining_time))

        if (slot_remaining_time <= 0):
            log.err('This slot (' + str(iSlotId) + ') has expired')

            raise SlotErrorNotification('This slot (' + str(iSlotId) +
                                        ') has expired')
            # If time is correct, attach remote user to active_protocols

        #  Create an instante for finish the slot at correct time.
        self.session = reactor.callLater(slot_remaining_time,
                                         self.vSlotEnd, iSlotId)

        # Check if remote is on available list
        # Not in list, raise error
        """
        if clientB not in self.factory.active_protocols['remoteUsr']:
            return {'iResult': StartRemote.REMOTE_NOT_CONNECTED}

        # Available. Attach to list
        elif clientB in self.factory.active_protocols['remoteUsr']:

            self.factory.active_connections['remoteUsr'].append(remoteUsr)
            self.factory.active_connections['localUsr'].append(localUsr)

            notification = self.callRemote(NotifyEvent,
                                           Event=NotifyEvent.REMOTE_CONNECTED,
                                           sDetails=str(remoteUsr))
            log.msg(notification)

            log.msg('Active clients: ')
            log.msg('Active connections: ')

            return {'iResult': StartRemote.REMOTE_READY}
        """



    def vSlotEnd(self, iSlotId):
        log.msg("(" + self.sUsername + ") Slot " +
                str(iSlotId) + ' has finished')
        self.callRemote(NotifyEvent, iEvent=NotifyEvent.SLOT_END,
                        sDetails=None)

        #  Session is an instance of
        self.session = None

    # TO-DO
    # Check what kind of list, or dict, do we need.
    # Maybe it's wrong!
    def vEndRemote(self):
        log.msg("hola endRemote")
        # log.msg("(" + self.sUsername + ") --------- End Remote ---------")
        # # Disconnect both users (need to be done from the CredReceiver
        # # instance)
        # # self.credProto.transport.loseConnection()
        # self.transport.loseConnection()
        # # If the client is still in active_connections (only true when he
        # # was in a remote connection and he was disconnected in the first
        # # place)
        # # if self.factory.active_connections[self.sUsername]:
        # if self.factory.active_connections['localUsr'] == self.sUsername:

        #     # Notify the remote client about this disconnection. The
        #     # notification is sent through the SATNETServer instance
        #     self.factory.active_protocols[self.factory.active_connections[
        #         self.sUsername]].callRemote(NotifyEvent,\
        #          iEvent=NotifyEvent.END_REMOTE, sDetails=None)

        #     # Close connection
        #     self.factory.active_protocols[self.factory.active_connections[
        #         self.sUsername]].credProto.transport.loseConnection()

        #     # Remove active connection
        #     self.factory.active_connections.pop(
        #         self.factory.active_connections[self.sUsername])

        return {'bResult': True}

    EndRemote.responder(vEndRemote)

class MessageLogger:
    """
    An independent logger class (because separation of application
    and protocol logic is a good thing).
    """
    def __init__(self, file):
        self.file = file

    def log(self, message):
        """Write a message to the file."""
        timestamp = time.strftime("[%H:%M:%S]", time.localtime(time.time()))
        self.file.write('%s %s\n' % (timestamp, message))
        self.file.flush()

    def close(self):
        self.file.close()


class CredAMPServerFactory(ServerFactory):

    """
    Server factory useful for creating L{CredReceiver} instances.

    """
    clients = []
    protocol = CredReceiver

    def __init__(self):
        self.filename = 'patata'
