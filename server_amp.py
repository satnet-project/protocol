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


# First of all we need to add satnet-release-1/WebServices to the path
# to import Django modules
import os, sys, logging, django
from datetime import datetime
sys.path.append(os.path.dirname(os.getcwd()) + "/server")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "website.settings")
django.setup()

from twisted.python import log
from twisted.protocols.amp import AMP
from twisted.internet import reactor, ssl
from twisted.internet import protocol
from twisted.cred.portal import Portal

from commands import *
from ampauth.credentials import *
from ampauth.server import *
from errors import *

from services.common import misc
from services.scheduling.models import operational
from services.configuration.models.channels import SpacecraftChannel
from services.communications.models import Message


class SATNETServer(AMP):

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

    def iCreateConnection(self, iSlotEnd, iSlotId, remoteUsr, localUsr):
        slot_remaining_time = int(
            (iSlotEnd - misc.localize_datetime_utc(datetime.utcnow())).total_seconds())
        log.msg('Slot remaining time: ' + str(slot_remaining_time))
        if (slot_remaining_time <= 0):
            log.err('This slot (' + str(iSlotId) + ') has expired')
            raise SlotErrorNotification('This slot (' + str(iSlotId) + ') has expired')
        self.credProto.iSlotEndCallId = reactor.callLater(
            slot_remaining_time, self.vSlotEnd, iSlotId)
        if remoteUsr not in self.factory.active_protocols:
            log.msg('Remote user ' + remoteUsr + ' not connected yet')
            self.factory.active_connections[localUsr] = None            
            return {'iResult': StartRemote.REMOTE_NOT_CONNECTED}
        else:
            log.msg('Remote user is ' + remoteUsr)
            self.factory.active_connections[remoteUsr] = localUsr
            self.factory.active_connections[localUsr] = remoteUsr
            self.factory.active_protocols[remoteUsr].callRemote(
                NotifyEvent, iEvent=NotifyEvent.REMOTE_CONNECTED, sDetails=str(localUsr))
            self.callRemote(
                NotifyEvent, iEvent=NotifyEvent.REMOTE_CONNECTED, sDetails=str(remoteUsr))
            # divided by 2 because the dictionary is doubly linked
            log.msg('Active connections: ' + str(len(self.factory.active_connections) / 2))
            return {'iResult': StartRemote.REMOTE_READY}

    def iStartRemote(self, iSlotId):
        log.msg("(" + self.sUsername + ") --------- Start Remote ---------")
        self.slot = operational.OperationalSlot.objects.filter(id=iSlotId)
        # If slot NOT operational yet...
        if not self.slot:
            log.err('Slot ' + str(iSlotId) + ' is not yet operational')
            raise SlotErrorNotification(
                'Slot ' + str(iSlotId) + ' is not yet operational')
        # ... if multiple slots have the same ID (never should happen)...
        elif len(self.slot) > 1:
            log.err('Multiple slots with the same id: ' + str(iSlotId))
            raise SlotErrorNotification('Incorrect slot number')
        # ... if the ID is correct
        else:
            # If it is too soon to connect to this slot...
            if self.slot[0].state != operational.STATE_RESERVED:
                log.err('Slot ' + str(iSlotId) + ' has not yet been reserved')
                raise SlotErrorNotification('Slot ' + str(iSlotId) + ' has not yet been reserved')
            gs_user = self.slot[
                0].groundstation_channel.groundstation_set.all()[0].user.username
            sc_user = self.slot[
                0].spacecraft_channel.spacecraft_set.all()[0].user.username
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
                return self.iCreateConnection(self.slot[0].end, iSlotId, sc_user, gs_user)
            #... if the remote client is the GS user...
            elif sc_user == self.sUsername:
                self.bGSuser = False
                return self.iCreateConnection(self.slot[0].end, iSlotId, gs_user, sc_user)

    StartRemote.responder(iStartRemote)

    def vEndRemote(self):
        log.msg("(" + self.sUsername + ") --------- End Remote ---------")
        # Disconnect both users (need to be done from the CredReceiver
        # instance)
        self.credProto.transport.loseConnection()
        # If the client is still in active_connections (only true when he
        # was in a remote connection and he was disconnected in the first
        # place)
        if self.sUsername in self.factory.active_connections:
            # Notify the remote client about this disconnection. The notification is
            # sent through the SATNETServer instance
            self.factory.active_protocols[self.factory.active_connections[
                self.sUsername]].callRemote(NotifyEvent, iEvent=NotifyEvent.END_REMOTE, sDetails=None)
            # Close connection
            self.factory.active_protocols[self.factory.active_connections[
                self.sUsername]].credProto.transport.loseConnection()
            # Remove active connection
            self.factory.active_connections.pop(
                self.factory.active_connections[self.sUsername])

        return {}
    EndRemote.responder(vEndRemote)

    def vSendMsg(self, sMsg, iTimestamp):
        log.msg("(" + self.sUsername + ") --------- Send Message ---------")
        # If the client haven't started a connection via StartRemote command...
        # TODO. Never enters because the clients are in active_protocols as soon as they log in
        if self.sUsername not in self.factory.active_connections:
            log.msg('Connection not available. Call StartRemote command first')
            raise SlotErrorNotification(
                'Connection not available. Call StartRemote command first.')
        # ... if the SC operator is not connected, sent messages will be saved
        # as passive messages...
        elif self.factory.active_connections[self.sUsername] == None and self.bGSuser == True:
            gs_channel = self.slot[0].groundstation_channel
            sc_channel = self.slot[0].spacecraft_channel
            Message.objects.create(operational_slot=self.slot[0], gs_channel=gs_channel, 
                                                    sc_channel=sc_channel, upwards=self.bGSuser, forwarded=False,
                                                    tx_timestamp=iTimestamp, message=sMsg)
            log.msg('Message saved on server')

        # ... if the GS operator is not connected, the remote SC client will be
        # notified to wait for the GS to connect...
        elif self.factory.active_connections[self.sUsername] == None and self.bGSuser == False:
            self.callRemote(
                NotifyEvent, iEvent=NotifyEvent.REMOTE_DISCONNECTED, sDetails=None)
        # ... else, send the message to the remote and store it in the DB
        else:
            # send message to remote client
            self.factory.active_protocols[self.factory.active_connections[
                self.sUsername]].callRemote(NotifyMsg, sMsg=sMsg)
            # store messages in the DB (as already forwarded)
            gs_channel = self.slot[0].groundstation_channel
            sc_channel = self.slot[0].spacecraft_channel
            Message.objects.create(operational_slot=self.slot[0], gs_channel=gs_channel, 
                                                    sc_channel=sc_channel, upwards=self.bGSuser, forwarded=True,
                                                    tx_timestamp=iTimestamp, message=sMsg)

        return {'bResult': True}
    SendMsg.responder(vSendMsg)

    def vSlotEnd(self, iSlotId):
        log.msg(
            "(" + self.sUsername + ") Slot " + str(iSlotId) + ' has finished')
        self.callRemote(
            NotifyEvent, iEvent=NotifyEvent.SLOT_END, sDetails=None)
        # Remove the timer ID reference to avoid it to be canceled
        # a second time when the client disconnects
        self.credProto.iSlotEndCallId = None


def main():
    logger = logging.getLogger('server')

    log.startLogging(sys.stdout)

    checker = DjangoAuthChecker()
    realm = Realm()
    portal = Portal(realm, [checker])

    pf = CredAMPServerFactory(portal)
    cert = ssl.PrivateCertificate.loadPEM(open('key/server.pem').read())

    reactor.listenSSL(1234, pf, cert.options())
    log.msg('Server running...')
    reactor.run()

if __name__ == '__main__':
    main()
