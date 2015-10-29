# coding=utf-8
"""
   Copyright 2014, 2015 Xabier Crespo Álvarez

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


import os
import sys

from login import Login
from errors import BadCredentials

from twisted.internet import reactor
from twisted.internet.protocol import ServerFactory
from twisted.cred.error import UnauthorizedLogin
from twisted.protocols.amp import AMP
from twisted.protocols.policies import TimeoutMixin
from twisted.python import log

import misc
from datetime import datetime
import pytz

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ampCommands import StartRemote
from ampCommands import NotifyEvent
from ampCommands import EndRemote
from clientErrors import SlotErrorNotification
from rpcrequests import Satnet_RPC
from server_amp import SATNETServer


class CredReceiver(AMP, TimeoutMixin):

    """
    Integration between AMP and L{twisted.cred}. This class is only intended
    to be used for credentials purposes. The specific SATNET protocol will be
    implemented in L{SATNETServer} (see server_amp.py).

    :ivar rpc_if: 
        Endpoint to make RPC calls.
    :type rpc_if:
        L{Satnet_RPC}

    :ivar sUsername:
        Each protocol belongs to a User. This field represents User.username
    :type sUsername:
        L{String}

    :ivar iTimeOut:
        The duration of the session timeout in seconds. After this time the user
        will be automagically disconnected.
    :type iTimeOut:
        L{int}

    :ivar session:
        Reference to a object in charge of removing the user from active_protocols
        when it is inactive.
    :type session:
        L{IDelayedCall}

    """

    rpc_if = None
    logout = None
    sUsername = ''
    iTimeOut = 300  # seconds
    session = None

    avatar = None

    def connectionMade(self):
        self.setTimeout(self.iTimeOut)
        super(CredReceiver, self).connectionMade()

    def dataReceived(self, data):
        log.msg(self.sUsername + ' session timeout reset')
        self.resetTimeout()
        super(CredReceiver, self).dataReceived(data)

    def timeoutConnection(self):
        log.err('Session timeout expired')
        # self.transport.abortConnection()
        self.transport.loseConnection()

    def connectionLost(self, reason):
        if self.sUsername in self.factory.active_protocols['localUsr']:
            self.factory.active_protocols['localUsr'] = []
        if self.remoteUsr in self.factory.active_protocols['remoteUsr']:
            self.factory.active_protocols['remoteUsr'] = []
        if self.sUsername in self.factory.active_connections['localUsr']:
            self.factory.active_connections['localUsr'] = []
        if self.remoteUsr in self.factory.active_connections['remoteUsr']:
            self.factory.active_connections['remoteUsr'] = []

        if self.session is not None:
            self.session.cancel()

        log.err(reason.getErrorMessage())

        active_protocols = len(self.factory.active_protocols['localUsr']) +\
         len(self.factory.active_protocols['remoteUsr'])
        active_connections = len(self.factory.active_connections['localUsr']) +\
         len(self.factory.active_connections['remoteUsr'])

        log.msg('Active clients: ' + str(active_protocols))
        # divided by 2 because the dictionary is doubly linked
        log.msg('Active connections: ' + str(active_connections))

        # log.msg('Antes de EndRemote')
        # # res = yield self.callRemote(EndRemote)
        # # log.msg(res)
        # log.msg(self.test)
        # res = self.test()
        # log.msg(res)
        # log.msg('Despues de EndRemote')


        # notification = self.callRemote(
        #     NotifyEvent, iEvent=NotifyEvent.REMOTE_CONNECTED,\
        #      sDetails=str(remoteUsr))


        self.setTimeout(None)  # Cancel the pending timeout
        self.transport.loseConnection()

        super(CredReceiver, self).connectionLost(reason)

    def test(self):
        log.msg('estoy dentro de test')
        log.msg(EndRemote)
        # res = yield self.callRemote(EndRemote)


    def login(self, sUsername, sPassword):
        """
        Generate a new challenge for the given username.
        """
        self.factory = CredAMPServerFactory()
        #
        # Don't mix asynchronus and syncronus code.
        # Try-except sentences aren't allowed.
        #

        try:
            if self.factory.active_connections:
                log.msg('Active connections dictionary already created')
        except Exception as e:
            self.factory.active_connections = {}
            self.factory.active_connections.setdefault('localUsr', [])
            self.factory.active_connections.setdefault('remoteUsr', [])

        try:
            if self.factory.active_protocols:
                log.msg('Active protocols dictionary already created')
        except Exception as e:
            self.factory.active_protocols = {}
            self.factory.active_protocols.setdefault('localUsr', [])
            self.factory.active_protocols.setdefault('remoteUsr', [])

        if sUsername in self.factory.active_protocols['localUsr']:
            log.err('Client already logged in')
            raise UnauthorizedLogin('Client already logged in')
        else:
            # Attach local user to active protocols list.
            self.sUsername = sUsername
            self.factory.active_protocols['localUsr'].append(self.sUsername)

        try:
            self.rpc = Satnet_RPC(sUsername, sPassword, debug=True)
            self.protocol = SATNETServer
            # avatar.factory = self.factory
            # avatar.credProto = self
            # avatar.sUsername = sUsername
            # self.active_protocols[sUsername] = self
            log.msg('Connection made')
            active_protocols = len(self.factory.active_protocols['localUsr']) +\
             len(self.factory.active_protocols['remoteUsr'])
            active_connections = len(self.factory.active_connections['localUsr']) +\
             len(self.factory.active_connections['remoteUsr'])
            
            log.msg('Active clients: ' + str(active_protocols))
            log.msg('Active connections: ' + str(active_connections))

            return {'bAuthenticated': True}

        except BadCredentials:
            log.err('Incorrect username and/or password')
            raise BadCredentials("Incorrect username and/or password")

    Login.responder(login)

    def CreateConnection(self, iSlotEnd, iSlotId, remoteUsr, localUsr):
        """
        Create a new connection checking the time slot.
        """
        self.remoteUsr = remoteUsr

        iSlotEnd = datetime.utcfromtimestamp(iSlotEnd).replace(tzinfo=pytz.utc)

        slot_remaining_time = int((iSlotEnd -\
         misc.localize_datetime_utc(datetime.utcnow())).total_seconds())
        log.msg('Slot remaining time: ' + str(slot_remaining_time))

        if (slot_remaining_time <= 0):
            log.err('This slot (' + str(iSlotId) + ') has expired')

            raise SlotErrorNotification('This slot (' + str(iSlotId) +\
             ') has expired')
        elif (slot_remaining_time > 0):

            # If time is correct, attach remote user to active_protocols
            self.factory.active_protocols['remoteUsr'].append(remoteUsr)
        else:
            log.msg('Time error.')
     
        # Create an instante for finish the slot at correct time.  
        self.session = reactor.callLater(slot_remaining_time,\
         self.vSlotEnd, iSlotId)

        if remoteUsr not in self.factory.active_protocols['remoteUsr']:

            # If remoteUsr is not available remove localUsr from active_protocols
            # dictionary.

            log.msg('Remote user ' + remoteUsr + ' not connected yet')
            self.factory.active_connections[localUsr] = None          
            return {'iResult': StartRemote.REMOTE_NOT_CONNECTED}

        elif remoteUsr in self.factory.active_protocols['remoteUsr']:
            log.msg('Remote user is ' + remoteUsr)
            log.msg('Local user is ' + localUsr)
            self.factory.active_connections['remoteUsr'].append(remoteUsr)
            self.factory.active_connections['localUsr'].append(localUsr)

            notification = self.callRemote(
                NotifyEvent, iEvent=NotifyEvent.REMOTE_CONNECTED,\
                 sDetails=str(remoteUsr))

            log.msg('Active clients: ' +\
             str(len(self.factory.active_protocols)))           
            # divided by 2 because the dictionary is doubly linked
            log.msg('Active connections: ' +\
             str(len(self.factory.active_connections) / 2))
            return {'iResult': StartRemote.REMOTE_READY}


    def vSlotEnd(self, iSlotId):
        log.msg(
            "(" + self.sUsername + ") Slot " + str(iSlotId) + ' has finished')
        self.callRemote(
            NotifyEvent, iEvent=NotifyEvent.SLOT_END, sDetails=None)
        # Remove the timer ID reference to avoid it to be canceled
        # a second time when the client disconnects
        
        # To-do. What happens?
        self.session = None


class CredAMPServerFactory(ServerFactory):

    """
    Server factory useful for creating L{CredReceiver} and L{SATNETServer} instances.

    This factory takes care of associating a L{Portal} with the L{CredReceiver}
    instances it creates. If the login is succesfully achieved, a L{SATNETServer}
    instance is also created.
    """
    protocol = CredReceiver
