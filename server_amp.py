# coding=utf-8
import sys
import logging

from twisted.python import log
from twisted.internet import reactor
from twisted.internet import ssl
from twisted.internet import protocol

from ampauth.server import *
from clientErrors import SlotErrorNotification

from rpcrequests import Satnet_GetSlot
from rpcrequests import Satnet_StorePassiveMessage
from ampCommands import StartRemote
from ampCommands import EndRemote
from ampCommands import SendMsg
from ampCommands import NotifyMsg


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
        Used to disconnect the users from the servers
        (via credProto.loseConnection())
    :type credProto:
        L{CredReceiver}

    :ivar bGSuser:
        Indicates if the current user is a GS user (True) or a SC user
        (false). If this variable is None, it means that it has not been
        yet connected.
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
        # self.resetTimeout()
        super(SATNETServer, self).dataReceived(data)

    # Neceito corregir el tema del slot nuevo.
    def iStartRemote(self, iSlotId):
        log.msg("(" + self.sUsername + ") --------- Start Remote ---------")

        iSlotId = -1
        self.iSlotId = iSlotId

        slot = Satnet_GetSlot(iSlotId, debug=True)
        self.slot = slot.slot

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

            gs_user = self.slot['gs_username']           
            sc_user = self.slot['sc_username']
            
            #  If this slot has not been assigned to this user...
            if gs_user != self.sUsername and sc_user != self.sUsername:
                log.err('This slot has not been assigned to this user')              
                raise SlotErrorNotification('This user is not assigned to this slot')
            #  if the GS user and the SC user belong to the same client...
            elif gs_user == self.sUsername and sc_user == self.sUsername:
                log.msg('Both MCC and GSS belong to the same client')              
                return {'iResult': StartRemote.CLIENTS_COINCIDE}
            #  if the remote client is the SC user...
            elif gs_user == self.sUsername:
                self.bGSuser = True

                return self.CreateConnection(self.slot['ending_time'], iSlotId,
                                             sc_user, gs_user)

            #  if the remote client is the GS user...
            elif sc_user == self.sUsername:
                self.bGSuser = False

                return self.CreateConnection(self.slot['ending_time'],
                                             iSlotId, gs_user, sc_user)

    StartRemote.responder(iStartRemote)

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

    def vSendMsg(self, sMsg, iTimestamp):
        log.msg("(" + self.sUsername + ") --------- Send Message ---------")
        # If the client haven't started a connection via StartRemote command
        # TODO. Never enters because the clients are in active_protocols as 
        # soon as they log in

        if self.sUsername not in self.factory.active_connections['localUsr']:
            log.msg('Connection not available. Call StartRemote command first')
            raise SlotErrorNotification(
                'Connection not available. Call StartRemote command first.')
        #  if the SC operator is not connected, sent messages will be saved
        #  as passive messages...
        elif self.factory.active_connections['localUsr'] is False:
            return {'bResult': False}

            if self.bGSuser is True:
                PassiveMessage = Satnet_StorePassiveMessage(
                    groundstation_id='groundstation_id',
                    timestamp='timestamp',
                    doppler_shift='doppler_shift',
                    message=sMsg, debug=True)
                log.msg(PassiveMessage)
                log.msg('Message saved on server')
            elif self.bGSuser is False:
                self.callRemote(NotifyEvent,
                                iEvent=NotifyEvent.REMOTE_DISCONNECTED,
                                sDetails=None)
                return {'bResult': False}
        else:
            self.callRemote(NotifyMsg,
                            sMsg="Protocol has received the message")

            upwards = True
            forwarded = True

            # Timestamp = Actual time
            timestamp = misc.localize_datetime_utc(datetime.utcnow())
            timestamp = int(time.mktime(timestamp.timetuple()))

            #  the remote client is online so the message will be send
            Satnet_StoreMessage(self.iSlotId, upwards, forwarded,
                                timestamp, sMsg, debug=True)
            log.msg(Satnet_StoreMessage)

            return {'bResult': True}

    SendMsg.responder(vSendMsg)


def main():
    logging.getLogger('server')

    log.startLogging(sys.stdout)

    pf = CredAMPServerFactory()

    sslContext = ssl.DefaultOpenSSLContextFactory('key/server.pem',
                                                    'key/public.pem',)

    reactor.listenSSL(1234, pf, contextFactory=sslContext,)

    log.msg('Server running...')
    reactor.run()

if __name__ == '__main__':

    try:
        if sys.argv[1] == '--debug':
            from twisted.internet import defer
            defer.setDebugging((True))

            main()

        if sys.argv[1] == '--help':
            print "Help"
    except:
        main()
