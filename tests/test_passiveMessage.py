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

import os, sys, logging, datetime, django, pytz
from django.core import management

sys.path.append(os.path.dirname(os.getcwd()) + "/server")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "website.settings")
django.setup() #To avoid the error "django.core.exceptions.AppRegistryNotReady: Models aren't loaded yet."

# Dependencies for _setUp_databases
from services.common import misc, simulation
from services.common.testing import helpers

from services.configuration.jrpc.views import channels as jrpc_channels_if
from services.configuration.jrpc.views import rules as jrpc_rules_if
from services.configuration.jrpc.serializers import serialization as jrpc_keys
from services.scheduling.jrpc.views import groundstations as jrpc_gs_scheduling
from services.scheduling.jrpc.views import spacecraft as jrpc_sc_scheduling
from services.configuration.models import rules, availability, channels
from services.configuration import signals
from services.scheduling.models import operational
from services.network.models import server as server_models

# Dependencies for the tests
from twisted.internet import defer, protocol
from twisted.trial import unittest
from twisted.cred.portal import Portal
from twisted.internet import reactor, ssl

from ampauth.credentials import *
from ampauth.server import *
from ampauth.client import login
from ampauth.server import CredReceiver
from client_amp import ClientProtocol
from commands import *
from errors import *

from services.common import misc


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

        self.factory.onEventReceived = self.factory.onEventReceived.callback(
            iEvent)
        return {}
    NotifyEvent.responder(vNotifyEvent)


class TestPassiveMessage(unittest.TestCase):

    """
    Testing multiple client connections
    TDOD. Test multiple valid connections
    """

    def _setUp_databases(self):
        """
        This method populates the database with some information to be used
        only for this test.
        """
        server_models.Server.objects.load_local_server()

        __sc_1_id = 'humsat-sc'
        __sc_1_tle_id = 'HUMSAT-D'
        __sc_1_ch_1_id = 'humsat-fm'
        __sc_1_ch_1_cfg = {
            jrpc_keys.FREQUENCY_K: '437000000',
            jrpc_keys.MODULATION_K: 'FM',
            jrpc_keys.POLARIZATION_K: 'LHCP',
            jrpc_keys.BITRATE_K: '300',
            jrpc_keys.BANDWIDTH_K: '12.500000000'
        }

        __gs_1_id = 'gs-la'
        __gs_1_ch_1_id = 'gs-la-fm'
        __gs_1_ch_1_cfg = {
            jrpc_keys.BAND_K:
            'UHF / U / 435000000.000000 / 438000000.000000',
            jrpc_keys.AUTOMATED_K: False,
            jrpc_keys.MODULATIONS_K: ['FM'],
            jrpc_keys.POLARIZATIONS_K: ['LHCP'],
            jrpc_keys.BITRATES_K: [300, 600, 900],
            jrpc_keys.BANDWIDTHS_K: [12.500000000, 25.000000000]
        }
        __gs_1_ch_2_id = 'gs-la-fm-2'
        __gs_1_ch_2_cfg = {
            jrpc_keys.BAND_K:
            'UHF / U / 435000000.000000 / 438000000.000000',
            jrpc_keys.AUTOMATED_K: False,
            jrpc_keys.MODULATIONS_K: ['FM'],
            jrpc_keys.POLARIZATIONS_K: ['LHCP'],
            jrpc_keys.BITRATES_K: [300, 600, 900],
            jrpc_keys.BANDWIDTHS_K: [12.500000000, 25.000000000]
        }

        signals.models.connect_availability_2_operational()
        signals.models.connect_channels_2_compatibility()
        signals.models.connect_compatibility_2_operational()
        signals.models.connect_rules_2_availability()
        #signals.connect_segments_2_booking_tle()

        helpers.init_available()
        helpers.init_tles_database()
        __band = helpers.create_band()

        __usr_1_name = 'crespo'
        __usr_1_pass = 'cre.spo'
        __usr_1_mail = 'crespo@crespo.gal'

        __usr_2_name = 'tubio'
        __usr_2_pass = 'tu.bio'
        __usr_2_mail = 'tubio@tubio.gal'

        # Default values: username=testuser, password=testuser.
        __user_def = helpers.create_user_profile()
        __usr_1 = helpers.create_user_profile(
            username=__usr_1_name, password=__usr_1_pass, email=__usr_1_mail)
        __usr_2 = helpers.create_user_profile(
            username=__usr_2_name, password=__usr_2_pass, email=__usr_2_mail)

        __sc_1 = helpers.create_sc(
            user_profile=__usr_1,
            identifier=__sc_1_id,
            tle_id=__sc_1_tle_id,
        )

        __gs_1 = helpers.create_gs(
            user_profile=__usr_2, identifier=__gs_1_id,
        )

        operational.OperationalSlot.objects.get_simulator().set_debug()
        operational.OperationalSlot.objects.set_debug()

        jrpc_channels_if.gs_channel_create(
            ground_station_id=__gs_1_id,
            channel_id=__gs_1_ch_1_id,
            configuration=__gs_1_ch_1_cfg
        )

        jrpc_rules_if.add_rule(
            __gs_1_id, __gs_1_ch_1_id,
            helpers.create_jrpc_daily_rule(
                starting_time=misc.localize_time_utc(datetime.time(
                    hour=8, minute=0, second=0
                )),
                ending_time=misc.localize_time_utc(datetime.time(
                    hour=23, minute=55, second=0
                ))
            )
        )

        jrpc_channels_if.sc_channel_create(
            spacecraft_id=__sc_1_id,
            channel_id=__sc_1_ch_1_id,
            configuration=__sc_1_ch_1_cfg
        )

        sc_1_o_slots = jrpc_sc_scheduling.get_operational_slots(__sc_1_id)

        sc_1_s_slots = jrpc_sc_scheduling.select_slots(
            __sc_1_id, [int(slot['identifier']) for slot in sc_1_o_slots]
            )

        gs_1_o_slots = jrpc_gs_scheduling.get_operational_slots(__gs_1_id)

        gs_c_slots = jrpc_gs_scheduling.confirm_selections(
            __gs_1_id, [int(slot['identifier']) for slot in gs_1_o_slots])

    def setUp(self):
        log.startLogging(sys.stdout)

        log.msg(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Flushing database")
        #management.execute_from_command_line(['manage.py', 'flush', '--noinput'])
        
        log.msg(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Populating database")        
        #management.execute_from_command_line(['manage.py', 'createsuperuser',
        #    '--username', 'crespum', '--email', 'crespum@humsat.org', '--noinput'])
        #self._setUp_databases()
        
        log.msg(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Running tests")
        self.serverDisconnected = defer.Deferred()
        self.serverPort = self._listenServer(self.serverDisconnected)

        self.connected1 = defer.Deferred()
        self.clientDisconnected1 = defer.Deferred()
        self.factory1 = protocol.ClientFactory.forProtocol(ClientProtocolTest)
        self.clientConnection1 = self._connectClient(self.factory1, self.connected1,
                                                      self.clientDisconnected1)

        return self.connected1

    def _listenServer(self, d):
        checker = DjangoAuthChecker()
        realm = Realm()
        portal = Portal(realm, [checker])
        pf = CredAMPServerFactory(portal)
        pf.protocol = CredReceiver
        pf.onConnectionLost = d
        cert = ssl.PrivateCertificate.loadPEM(
            open('../key/server.pem').read())
        return reactor.listenSSL(1234, pf, cert.options())

    def _connectClient(self, factory, d1, d2):
        factory.onConnectionMade = d1
        factory.onConnectionLost = d2

        cert = ssl.Certificate.loadPEM(open('../key/public.pem').read())
        options = ssl.optionsForClientTLS(u'example.humsat.org', cert)

        return reactor.connectSSL("localhost", 1234, factory, options)

    def tearDown(self):
        d = defer.maybeDeferred(self.serverPort.stopListening)
        self.clientConnection1.disconnect()

        return defer.gatherResults([d, self.clientDisconnected1])

    """
    A message is sent by A to B, but the last one is not connected yet. The message is stored in 
    the server and marked "forwarded=false". The procedure goes:
        1. Client A -> login
        2. Client A -> StartRemote (should return StartRemote.REMOTE_NOT_CONNECTED)
        6. Client A -> sendMsg(__sMessageA2B)


        7. Client A -> notifyMsg (should receive __sMessageA2B)
        8. Client A -> sendMsg(__sMessageB2A)
        9. Client B -> notifyMsg (should receive __sMessageB2A)
        10. Client B -> endRemote()
        11. Client A -> notifyEvent (should receive NotifyEvent.END_REMOTE). This last step
        is not being checked due to dificulties with Twisted trial methods
    """

    def test_simultaneousUsers(self):
        __iSlotId = 1
        __sMessageA2B = "Adiós, ríos; adios, fontes; adios, regatos pequenos;"
        # To notify when a new message is received by the client

        d1 = login(self.factory1.protoInstance, UsernamePassword(
            'tubio', 'tu.bio'))
        d1.addCallback(lambda res: self.assertTrue(res['bAuthenticated']))

        d1.addCallback(lambda l: self.factory1.protoInstance.callRemote(
            StartRemote, iSlotId=__iSlotId))
        d1.addCallback(lambda res: self.assertEqual(
            res['iResult'], StartRemote.REMOTE_NOT_CONNECTED))

        d1.addCallback(lambda l: self.factory1.protoInstance.callRemote(
            SendMsg, sMsg=__sMessageA2B, iTimestamp=misc.get_utc_timestamp()))
        d1.addCallback(lambda res: self.assertTrue(res['bResult']))

        return d1
