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


from twisted.internet.protocol import ServerFactory
from twisted.protocols.amp import AMP
from twisted.cred.credentials import UsernamePassword
from twisted.protocols.amp import IBoxReceiver
from twisted.python import log
from twisted.protocols.policies import TimeoutMixin

from commands import Login
from twisted.cred.error import UnauthorizedLogin
from errors import BadCredentials
from rpcrequests import Satnet_RPC


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

    :ivar factory:
        The duration of the session timeout in seconds. After this time the user
        will be automagically disconnected.
    :type factory:
        L{CredAMPServerFactory}        
    """

    rpc_if = None
    logout = None
    sUsername = ''
    iTimeOut = 300  # seconds
    session = None
    factory = None

    def connectionMade(self):
        self.setTimeout(self.iTimeOut)
        super(CredReceiver, self).connectionMade()

    def dataReceived(self, data):
        log.msg(self.sUsername + ' session timeout reset')
        self.resetTimeout()
        super(CredReceiver, self).dataReceived(data)

    def timeoutConnection(self):
        log.err('Session timeout expired')
        self.transport.abortConnection()

    def connectionLost(self, reason):
        # Remove the client from active_protocols and/or active_connections
        if self.sUsername != '':
            self.factory.active_protocols.pop(self.sUsername)
            if self.session is not None:
                self.session.cancel()
        log.err(reason.getErrorMessage())
        log.msg('Active clients: ' + str(len(self.factory.active_protocols)))
        # divided by 2 because the dictionary is doubly linked
        log.msg('Active connections: ' + str(len(self.factory.active_connections)/2))
        self.setTimeout(None)  # Cancel the pending timeout
        self.transport.loseConnection()
        super(CredReceiver, self).connectionLost(reason)

    def login(self, sUsername, sPassword):
        """
        Generate a new challenge for the given username.
        """
        if sUsername in self.factory.active_protocols:
            log.err('Client already logged in')
            raise UnauthorizedLogin('Client already logged in')
        else:
            self.sUsername = sUsername
            self.factory.active_protocols[sUsername] = None

        try:
            self.rpc = Satnet_RPC(sUsername, sPassword, debug=True)
            #avatar.factory = self.factory
            #avatar.credProto = self
            #avatar.sUsername = sUsername
            self.factory.active_protocols[sUsername] = self
            log.msg('Connection made')
            log.msg('Active clients: ' + str(len(self.factory.active_protocols)))
            log.msg('Active connections: ' + str(len(self.factory.active_connections)))

            return {'bAuthenticated': True}

        except BadCredentials as e:
            log.err('Incorrect username and/or password')
            log.err(e)
            raise

    Login.responder(login)


class CredAMPServerFactory(ServerFactory):

    """
    Server factory useful for creating L{CredReceiver} and L{SATNETServer} instances.

    This factory takes care of associating a L{Portal} with the L{CredReceiver}
    instances it creates. If the login is succesfully achieved, a L{SATNETServer}
    instance is also created.

    :ivar active_protocols:
        A dictionary containing a reference to all active protocols (clients).
        The dictionary keys are the client usernames and the corresponding values
        are the protocol instances
    :type active_protocols:
        L{Dictionary}

    :ivar active_connections:
        A dictionary containing a reference to all active protocols (clients).
        The dictionary is doubly linked so the keys are whether the GS clients 
        or the SC clients and the values are the remote client usernames
    :type active_connections:
        L{Dictionary}        
    """

    protocol = CredReceiver
    active_protocols = {}
    active_connections = {}

    def __init__(self):
        self.active_protocols = {}
        self.active_connections = {}
