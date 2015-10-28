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
import logging

from twisted.python import log
from twisted.internet import reactor
from twisted.internet import ssl
from twisted.internet import protocol

from ampauth.server import *
from clientErrors import SlotErrorNotification

from rpcrequests import Satnet_GetSlot 
from rpcrequests import Satnet_StoreMessage 
from rpcrequests import Satnet_StorePassiveMessage
from ampCommands import StartRemote, EndRemote, SendMsg

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class SATNETServer(protocol.Protocol):

    """
    Integration between AMP and L{twisted.cred}. This class is only intended
    to be used for credentials purposes. The specific SATNET protocol will be
    implemented in L{SATNETServer} (see server_amp.py).

    :ivar sUsername:
        Each protocol belongs to a User. This field represents User.username
    :type sUsername:
        L{String}

    :ivar factory:
        CredAMPServerFactory instance which handles SATNETServer instances as well
        as CredReceiver instances    
    :type factory:
        L{ServerFactory}

    :ivar credProto:
        Used to disconnect the users from the servers (via credProto.loseConnection())
    :type credProto:
        L{CredReceiver}

    :ivar bGSuser:
        Indicates if the current user is a GS user (True) or a SC user (false). If this
        variable is None, it means that it has not been yet connected.
    :type bGSuser:
        L{boolean}

    """

    factory = None
    sUsername = ""
    credProto = None
    bGSuser = None
    slot = None


    def dataReceived(self, data):
        log.msg(self.sUsername + ' session timeout reset')
        self.resetTimeout()
        super(SATNETServer, self).dataReceived(data)

    def iStartRemote(self, iSlotId):
        log.msg("(" + self.sUsername + ") --------- Start Remote ---------")

        # self.slot = Satnet_GetSlot(str(iSlotId), debug = True)

        # For tests only
        from time import time
        timestamp = int(time())
        timestamp = timestamp + 60

        # For tests only.
        self.slot = {'state': 'RESERVED',\
         'gs_username': 's.gongoragarcia@gmail.com',\
          'sc_username': 'spacecraft', 'starting_time': 1576836800,\
           'ending_time': timestamp }

        # If slot NOT operational yet...
        if not self.slot:
            log.err('Slot ' + str(iSlotId) + ' is not yet operational')
            raise SlotErrorNotification(
                'Slot ' + str(iSlotId) + ' is not yet operational')
        else:
            # If it is too soon to connect to this slot...
            if self.slot['state'] != 'RESERVED':
                log.err('Slot ' + str(iSlotId) + ' has not yet been reserved')
                raise SlotErrorNotification('Slot ' + str(iSlotId) +\
                 ' has not yet been reserved')

            gs_user = self.slot['gs_username']            
            sc_user = self.slot['sc_username']
            
            # If this slot has not been assigned to this user...
            if gs_user != self.sUsername and sc_user != self.sUsername:
                log.err('This slot has not been assigned to this user')
                
                raise SlotErrorNotification(
                    'This user is not assigned to this slot')
            #... if the GS user and the SC user belong to the same client...
            elif gs_user == self.sUsername and sc_user == self.sUsername:
                log.msg('Both MCC and GSS belong to the same client')
                
                return {'iResult': StartRemote.CLIENTS_COINCIDE}
            #... if the remote client is the SC user...
            elif gs_user == self.sUsername:
                self.bGSuser = True

                return self.CreateConnection(self.slot['ending_time'],\
                 iSlotId, sc_user, gs_user)

            #... if the remote client is the GS user...
            elif sc_user == self.sUsername:
                self.bGSuser = False

                return self.CreateConnection(self.slot['ending_time'],\
                 iSlotId, gs_user, sc_user)

    StartRemote.responder(iStartRemote)

    # TO-DO
    # Check what kind of list, or dict, do we need.
    # Maybe it's wrong!
    #
    def vEndRemote(self):
        log.msg("(" + self.sUsername + ") --------- End Remote ---------")
        # Disconnect both users (need to be done from the CredReceiver
        # instance)
        # self.credProto.transport.loseConnection()
        self.transport.loseConnection()
        # If the client is still in active_connections (only true when he
        # was in a remote connection and he was disconnected in the first
        # place)
        # if self.factory.active_connections[self.sUsername]:
        if self.factory.active_connections['localUsr'] == self.sUsername:

            # Notify the remote client about this disconnection. The
            # notification is sent through the SATNETServer instance
            self.factory.active_protocols[self.factory.active_connections[
                self.sUsername]].callRemote(NotifyEvent,\
                 iEvent=NotifyEvent.END_REMOTE, sDetails=None)

            # Close connection
            self.factory.active_protocols[self.factory.active_connections[
                self.sUsername]].credProto.transport.loseConnection()

            # Remove active connection
            self.factory.active_connections.pop(
                self.factory.active_connections[self.sUsername])

        return {'bResult': True}

    EndRemote.responder(vEndRemote)

    def vSendMsg(self, sMsg, iTimestamp):

        # For tests only, where can I get the current channel?
        slot_id = 2
        slot = {'state': 'RESERVED',\
         'gs_channel': 'groundstation_channel',\
          'sc_channel': 'spacecraft_channel',\
           'starting_time': 1576836800, 'ending_time': 1677850000 }

        log.msg("(" + self.sUsername + ") --------- Send Message ---------")
        # If the client haven't started a connection via StartRemote command...
        # TODO. Never enters because the clients are in active_protocols as 
        # soon as they log in

        if self.sUsername not in self.factory.active_connections['localUsr']:
        # if self.sUsername not in self.factory.active_connections:
            log.msg('Connection not available. Call StartRemote command first')
            raise SlotErrorNotification(
                'Connection not available. Call StartRemote command first.')
        # ... if the SC operator is not connected, sent messages will be saved
        # as passive messages...
        elif self.factory.active_connections['localUsr'] == False:
            if self.bGSuser == True:
                # elif self.factory.active_connections[self.sUsername] == None\
                # and self.bGSuser == True:
                PassiveMessage = Satnet_StorePassiveMessage(groundstation_id =\
                 'groundstation_id', timestamp = 'timestamp', doppler_shift =\
                  'doppler_shift', message = sMsg, debug = True)

                """
                Old method. Should be maintained until the system runs without problems.
                """
                # Message.objects.create(operational_slot=self.slot[0],\
                #  gs_channel=gs_channel, sc_channel=sc_channel,\
                #   upwards=self.bGSuser, forwarded=False, tx_timestamp=iTimestamp,\
                #    message=sMsg)

                log.msg('Message saved on server')

                # ... if the GS operator is not connected, the remote SC client 
                # will be notified to wait for the GS to connect...
            elif self.bGSuser == False:
                self.callRemote(NotifyEvent,\
                 iEvent=NotifyEvent.REMOTE_DISCONNECTED, sDetails=None)
                # ... else, send the message to the remote and store it in the DB
        else:
            # NotifyMsg is a class from client_amp
            #
            # send message to remote client
            # self.factory.active_protocols[self.factory.active_connections[self.sUsername]].callRemote(NotifyMsg, sMsg=sMsg)

            # store messages in the DB (as already forwarded)
            gs_channel = slot['gs_channel']
            sc_channel = slot['sc_channel']

            # OWld method
            # Message = Satnet_StoreMessage(operational_slot = slot_id,\
            #  gs_channel = gs_channel, sc_channel = sc_channel,\
            #   upwards = self.bGSuser, forwarded = True,\
            #    tx_timestamp = iTimestamp, message = sMsg)
            
            slot_id = 2
            upwards = True
            forwarded = True
            timestamp = 1677850000

            Message = Satnet_StoreMessage(slot_id, upwards, forwarded,\
             timestamp, sMsg, debug = True)

            # Old method. Should be maintained until the system runs 
            # without problems.
            # gs_channel = self.slot[0].groundstation_channel
            # sc_channel = self.slot[0].spacecraft_channel

            # Message.objects.create(operational_slot=self.slot[0],\
            #  gs_channel=gs_channel, sc_channel=sc_channel,\
            #   upwards=self.bGSuser, forwarded=True, tx_timestamp=iTimestamp,\
            #    message=sMsg)

        return {'bResult': True}
    SendMsg.responder(vSendMsg)

    # # TO-DO
    # def vSlotEnd(self, iSlotId):
    #     log.msg(
    #         "(" + self.sUsername + ") Slot " + str(iSlotId) + ' has finished')
    #     self.callRemote(
    #         NotifyEvent, iEvent=NotifyEvent.SLOT_END, sDetails=None)
    #     # Remove the timer ID reference to avoid it to be canceled
    #     # a second time when the client disconnects
    #     self.credProto.session = None


def main():
    logger = logging.getLogger('server')

    log.startLogging(sys.stdout)

    pf = CredAMPServerFactory()
    # cert = ssl.PrivateCertificate.loadPEM(open('key/server.pem').read())

    # connector = reactor.listenSSL(1234, pf, cert.options())
 
    from twisted.internet import reactor, ssl
    sslContext = ssl.DefaultOpenSSLContextFactory('key/server.pem',\
     'key/public.pem',)
    connector = reactor.listenSSL(1234, pf, contextFactory = sslContext,)

    log.msg('Server running...')
    reactor.run()

if __name__ == '__main__':
    main()
