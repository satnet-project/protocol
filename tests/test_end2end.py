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

from os import path
import os, sys, logging, datetime, django, pytz
from django.core import management
from mock import Mock, MagicMock
import unittest

sys.path.append(os.path.abspath(path.join(path.dirname(__file__), "..")))

#os.environ.setdefault("DJANGO_SETTINGS_MODULE", "website.settings")
#django.setup() #To avoid the error "django.core.exceptions.AppRegistryNotReady: Models aren't loaded yet."

# Dependencies for _setUp_databases
# from services.common import misc
services_common_misc = Mock()
services_common_misc.localize_time_utc =\
 MagicMock(return_value = 'test')

services_common_misc.get_utc_timestamp =\
 MagicMock(return_value = 'test')

# from services.common.testing import helpers
services_common_testing_helpers = Mock()
services_common_testing_helpers.init_available =\
 MagicMock(return_value = 'test')

services_common_testing_helpers.init_tles_database =\
 MagicMock(return_value = 'test')

services_common_testing_helpers.create_band =\
 MagicMock(return_value = 'test')

services_common_testing_helpers.create_user_profile =\
 MagicMock(return_value = 'test')

services_common_testing_helpers.create_sc =\
 MagicMock(return_value = 'test')

services_common_testing_helpers.create_gs =\
 MagicMock(return_value = 'test')

services_common_testing_helpers.create_jrpc_daily_rule =\
 MagicMock(return_value = 'test')

# from services.configuration.jrpc.views import channels
services_configuration_jrpc_views_channels = Mock()
services_configuration_jrpc_views_channels.gs_channel_create =\
 MagicMock(return_value = 'test')

services_configuration_jrpc_views_channels.sc_channel_create =\
 MagicMock(return_value = 'test')

# from services.configuration.jrpc.views import rules
services_configuration_jrpc_views_rules = Mock()
services_configuration_jrpc_views_rules.add_rule =\
 MagicMock(return_value = 'test')

# from services.configuration.jrpc.serializers import serialization as services_configuration_jrpc_serializers_serialization
# TO-DO How does it work?
services_configuration_jrpc_serializers_serialization = Mock()
services_configuration_jrpc_serializers_serialization.FREQUENCY_K = 'testData'
services_configuration_jrpc_serializers_serialization.MODULATION_K = 'testData'
services_configuration_jrpc_serializers_serialization.POLARIZATION_K = 'testData'
services_configuration_jrpc_serializers_serialization.BITRATE_K = 'testData'
services_configuration_jrpc_serializers_serialization.BANDWIDTH_K = 'testData'
services_configuration_jrpc_serializers_serialization.BAND_K = 'testData'
services_configuration_jrpc_serializers_serialization.AUTOMATED_K = 'testData'
services_configuration_jrpc_serializers_serialization.MODULATIONS_K = 'testData'
services_configuration_jrpc_serializers_serialization.BITRATES_K = 'testData'
services_configuration_jrpc_serializers_serialization.BANDWIDTHS_K = 'testData'

# from services.scheduling.jrpc.views import groundstations as jrpc_gs_scheduling
services_scheduling_jrpc_views_groundstations = Mock()
services_scheduling_jrpc_views_groundstations.get_operational_slots =\
 MagicMock(return_value = 'test')

services_scheduling_jrpc_views_groundstations.confirm_selections =\
 MagicMock(return_value = 'test')

# from services.scheduling.jrpc.views import spacecraft
services_scheduling_jrpc_views_spacecraft = Mock()
services_scheduling_jrpc_views_spacecraft.get_operational_slots =\
 MagicMock(return_value = 'test')

services_scheduling_jrpc_views_spacecraft.select_slots =\
 MagicMock(return_value = 'test') 

# from services.configuration.models import rules
services_configuration_models_rules = Mock()
services_configuration_models_rules.add_rule = MagicMock(return_value = 'test')

# from services.configuration.models import availability - Not used.
# services_configuration_models_availability = Mock()

# from services.configuration.models import channels
services_configuration_models_channels = Mock()
services_configuration_models_channels.gs_channel_create =\
 MagicMock(return_value = 'test')

services_configuration_models_channels.sc_channel_create =\
 MagicMock(return_value = 'test')

# from services.configuration.signals import models
services_configuration_signals_models = Mock()
services_configuration_signals_models.connect_availability_2_operational =\
 MagicMock(return_value = 'test')

services_configuration_signals_models.connect_channels_2_compatibility =\
 MagicMock(return_value = 'test')

services_configuration_signals_models.connect_compatibility_2_operational =\
 MagicMock(return_value = 'test')

services_configuration_signals_models.connect_rules_2_availability =\
 MagicMock(return_value = 'test')

# operational.OperationalSlot.objects.get_simulator().set_debug() - TO-DO
operational_OperationalSlot_objects_get_simulator = Mock()
operational_OperationalSlot_objects_get_simulator.set_debug =\
 MagicMock(return_value = 'test')

# operational.OperationalSlot.objects.set_debug()
operational_OperationalSlot_objects = Mock()
operational_OperationalSlot_objects.set_debug =\
 MagicMock(return_value = 'test')

# from services.scheduling.models.operational.OperationalSlot import objects
services_scheduling_models_operational_OperationalSlot_objects = Mock()
services_scheduling_models_operational_OperationalSlot_objects.set_debug =\
 MagicMock(return_value = 'test')

# from services.network.models.server.Server import objects
services_network_models_server_Server_objects = Mock()
services_network_models_server_Server_objects.load_local_server =\
 MagicMock(return_value = 'ReturnValueOfLoadLocalServer')

# Dependencies for the tests
from twisted.python import log
from twisted.internet import defer, protocol
from twisted.cred.portal import Portal
from twisted.internet import reactor, ssl

from ampauth.server import *
from ampauth.commands import Login
from client_amp import ClientProtocol
from _commands import NotifyMsg, NotifyEvent
from errors import *

"""
Configuration settings.
"""
BASE_DIR = path.abspath(path.join(path.dirname(__file__), "."))
from django.conf import settings
settings.configure(DEBUG=True, 
  DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3',
      'NAME': path.join(BASE_DIR, 'test.db'),
    'TEST_NAME': path.join(BASE_DIR, 'test.db'),}},
    INSTALLED_APPS = ('django.contrib.auth',))

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
        self.factory.onEventReceived.callback(iEvent)
        return {}
    NotifyEvent.responder(vNotifyEvent)


class TestStartRemote(unittest.TestCase):

    """
    Testing multiple client connections
    TODO. Test multiple valid connections
    """

    def _setUp_databases(self):
        """
        This method populates the database with some information to be used
        only for this test.
        """

        # TO-DO
        services_network_models_server_Server_objects.load_local_server() 

        __sc_1_id = 'humsat-sc'
        __sc_1_tle_id = 'HUMSAT-D'
        __sc_1_ch_1_id = 'humsat-fm'
        __sc_1_ch_1_cfg = {
            services_configuration_jrpc_serializers_serialization.FREQUENCY_K: '437000000',
            services_configuration_jrpc_serializers_serialization.MODULATION_K: 'FM',
            services_configuration_jrpc_serializers_serialization.POLARIZATION_K: 'LHCP',
            services_configuration_jrpc_serializers_serialization.BITRATE_K: '300',
            services_configuration_jrpc_serializers_serialization.BANDWIDTH_K: '12.500000000'
        }

        __sc_2_id = 'beesat-sc'
        __sc_2_tle_id = 'BEESAT-2'
        __sc_2_ch_1_id = 'beesat-fm'
        __sc_2_ch_1_cfg = {
            services_configuration_jrpc_serializers_serialization.FREQUENCY_K: '437000000',
            services_configuration_jrpc_serializers_serialization.MODULATION_K: 'FM',
            services_configuration_jrpc_serializers_serialization.POLARIZATION_K: 'LHCP',
            services_configuration_jrpc_serializers_serialization.BITRATE_K: '300',
            services_configuration_jrpc_serializers_serialization.BANDWIDTH_K: '12.500000000'
        }

        __gs_1_id = 'gs-la'
        __gs_1_ch_1_id = 'gs-la-fm'
        __gs_1_ch_1_cfg = {
            services_configuration_jrpc_serializers_serialization.BAND_K:
            'UHF / U / 435000000.000000 / 438000000.000000',
            services_configuration_jrpc_serializers_serialization.AUTOMATED_K: False,
            services_configuration_jrpc_serializers_serialization.MODULATIONS_K: ['FM'],
            services_configuration_jrpc_serializers_serialization.POLARIZATIONS_K: ['LHCP'],
            services_configuration_jrpc_serializers_serialization.BITRATES_K: [300, 600, 900],
            services_configuration_jrpc_serializers_serialization.BANDWIDTHS_K: [12.500000000, 25.000000000]
        }
        __gs_1_ch_2_id = 'gs-la-fm-2'
        __gs_1_ch_2_cfg = {
            services_configuration_jrpc_serializers_serialization.BAND_K:
            'UHF / U / 435000000.000000 / 438000000.000000',
            services_configuration_jrpc_serializers_serialization.AUTOMATED_K: False,
            services_configuration_jrpc_serializers_serialization.MODULATIONS_K: ['FM'],
            services_configuration_jrpc_serializers_serialization.POLARIZATIONS_K: ['LHCP'],
            services_configuration_jrpc_serializers_serialization.BITRATES_K: [300, 600, 900],
            services_configuration_jrpc_serializers_serialization.BANDWIDTHS_K: [12.500000000, 25.000000000]
        }

        services_configuration_signals_models.models.connect_availability_2_operational()
        services_configuration_signals_models.models.connect_channels_2_compatibility()
        services_configuration_signals_models.models.connect_compatibility_2_operational()
        services_configuration_signals_models.models.connect_rules_2_availability()
        #services_configuration_signals_models.connect_segments_2_booking_tle()

        services_common_testing_helpers.init_available()
        services_common_testing_helpers.init_tles_database()
        __band = services_common_testing_helpers.create_band()

        __usr_1_name = 'crespo'
        __usr_1_pass = 'cre.spo'
        __usr_1_mail = 'crespo@crespo.gal'

        __usr_2_name = 'tubio'
        __usr_2_pass = 'tu.bio'
        __usr_2_mail = 'tubio@tubio.gal'

        # Default values: username=testuser, password=testuser.
        __user_def = services_common_testing_helpers.create_user_profile()
        __usr_1 = services_common_testing_helpers.create_user_profile(
            username=__usr_1_name, password=__usr_1_pass, email=__usr_1_mail)
        __usr_2 = services_common_testing_helpers.create_user_profile(
            username=__usr_2_name, password=__usr_2_pass, email=__usr_2_mail)

        __sc_1 = services_common_testing_helpers.create_sc(
            user_profile=__usr_1,
            identifier=__sc_1_id,
            tle_id=__sc_1_tle_id,
        )

        __sc_2 = services_common_testing_helpers.create_sc(
            user_profile=__usr_2,
            identifier=__sc_2_id,
            tle_id=__sc_2_tle_id,
        )
        __gs_1 = services_common_testing_helpers.create_gs(
            user_profile=__usr_2, identifier=__gs_1_id,
        )

        # operational.OperationalSlot.objects.get_simulator().set_debug()
        operational_OperationalSlot_objects_get_simulator.set_debug()
        operational_OperationalSlot_objects.set_debug()

        services_configuration_models_channels.gs_channel_create(
            ground_station_id=__gs_1_id,
            channel_id=__gs_1_ch_1_id,
            configuration=__gs_1_ch_1_cfg
        )

        services_configuration_jrpc_views_rules.add_rule(
            __gs_1_id, __gs_1_ch_1_id,
            services_common_testing_helpers.create_jrpc_daily_rule(
                starting_time=services_common_misc.localize_time_utc(datetime.time(
                    hour=8, minute=0, second=0
                )),
                ending_time=services_common_misc.localize_time_utc(datetime.time(
                    hour=23, minute=55, second=0
                ))
            )
        )

        services_configuration_models_channels.sc_channel_create(
            spacecraft_id=__sc_1_id,
            channel_id=__sc_1_ch_1_id,
            configuration=__sc_1_ch_1_cfg
        )

        services_configuration_models_channels.sc_channel_create(
            spacecraft_id=__sc_2_id,
            channel_id=__sc_2_ch_1_id,
            configuration=__sc_2_ch_1_cfg
        )

        sc_1_o_slots = services_scheduling_jrpc_views_spacecraft.get_operational_slots(__sc_1_id)
        sc_2_o_slots = services_scheduling_jrpc_views_spacecraft.get_operational_slots(__sc_2_id)

        sc_1_s_slots = services_scheduling_jrpc_views_spacecraft.select_slots(
            __sc_1_id, [int(slot['identifier']) for slot in sc_1_o_slots])

        sc_2_s_slots = services_scheduling_jrpc_views_spacecraft.select_slots(
            __sc_2_id, [int(slot['identifier']) for slot in sc_2_o_slots])

        gs_1_o_slots = services_scheduling_jrpc_views_groundstations.get_operational_slots(__gs_1_id)

        gs_c_slots = services_scheduling_jrpc_views_groundstations.confirm_selections(
            __gs_1_id, [int(slot['identifier']) for slot in gs_1_o_slots])

    def setUp(self):
        # log.msg(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Flushing database")
        # management.execute_from_command_line(['manage.py', 'flush', '--noinput'])
        
        # log.msg(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Populating database")        
        # management.execute_from_command_line(['manage.py', 'createsuperuser',
        #     '--username', 'crespum', '--email', 'crespum@humsat.org', '--noinput'])

        log.startLogging(sys.stdout)

        log.msg(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Setting database")
        self._setUp_databases()
        
        log.msg(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Running tests")
        self.serverDisconnected = defer.Deferred()
        self.serverPort = self._listenServer(self.serverDisconnected)

        self.connected1 = defer.Deferred()
        self.clientDisconnected1 = defer.Deferred()
        self.factory1 = protocol.ClientFactory.forProtocol(ClientProtocolTest)
        self.clientConnection1 = self._connectClients(self.factory1, self.connected1,
                                                      self.clientDisconnected1)

        self.connected2 = defer.Deferred()
        self.clientDisconnected2 = defer.Deferred()
        self.factory2 = protocol.ClientFactory.forProtocol(ClientProtocolTest)
        self.clientConnection2 = self._connectClients(self.factory2, self.connected2,
                                                      self.clientDisconnected2)

        return defer.gatherResults([self.connected1, self.connected2])

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

    def _connectClients(self, factory, d1, d2):
        factory.onConnectionMade = d1
        factory.onConnectionLost = d2

        cert = ssl.Certificate.loadPEM(open('../key/public.pem').read())
        options = ssl.optionsForClientTLS(u'example.humsat.org', cert)

        return reactor.connectSSL("localhost", 1234, factory, options)

    def tearDown(self):
        d = defer.maybeDeferred(self.serverPort.stopListening)
        self.clientConnection1.disconnect()
        self.clientConnection2.disconnect()

        return defer.gatherResults([d,
                                    self.clientDisconnected1, self.clientDisconnected2])

    """
    Basic remote connection between two clients. The procedure goes:
        1. Client A -> login
        2. Client A -> StartRemote (should return StartRemote.REMOTE_NOT_CONNECTED)
        3. Client B -> login
        4. Client B -> StartRemote (should return StartRemote.REMOTE_READY)
        5. Client A -> notifyEvent (should receive NotifyEvent.REMOTE_CONNECTED + client B username)
        6. Client B -> notifyEvent (should receive NotifyEvent.REMOTE_CONNECTED+ client A username)        
        7. Client B -> sendMsg(__sMessageA2B)
        8. Client A -> notifyMsg (should receive __sMessageA2B)
        9. Client A -> sendMsg(__sMessageB2A)
        10. Client B -> notifyMsg (should receive __sMessageB2A)
        11. Client B -> endRemote()
        12. Client A -> notifyEvent (should receive NotifyEvent.END_REMOTE)
    """

    @defer.inlineCallbacks
    def test_simultaneousUsers(self):
        __iSlotId = 1
        __sMessageA2B = "Adiós, ríos; adios, fontes; adios, regatos pequenos;"
        __sMessageB2A = "adios, vista dos meus ollos: non sei cando nos veremos."
        __user1_name = 'crespo'
        __user1_pass = 'cre.spo'
        __user2_name = 'tubio'
        __user2_pass = 'tu.bio'

        self.factory1.onMessageReceived = defer.Deferred()
        self.factory2.onMessageReceived = defer.Deferred()
        self.factory1.onEventReceived = defer.Deferred()
        self.factory2.onEventReceived = defer.Deferred()

        # User 1 (login + start remote)
        res = yield login(self.factory1.protoInstance, UsernamePassword(
            __user1_name, __user1_pass))
        self.assertTrue(res['bAuthenticated'])

        res = yield self.factory1.protoInstance.callRemote(StartRemote, iSlotId=__iSlotId)
        self.assertEqual(res['iResult'], StartRemote.REMOTE_NOT_CONNECTED)

        # User 2 (login + start remote)
        res = yield login(self.factory2.protoInstance, UsernamePassword(
            __user2_name, __user2_pass))
        self.assertTrue(res['bAuthenticated'])

        res = yield self.factory2.protoInstance.callRemote(StartRemote, iSlotId=__iSlotId)
        self.assertEqual(res['iResult'], StartRemote.REMOTE_READY)

        # Events notifying REMOTE_CONNECTED to both clients
        ev = yield self.factory1.onEventReceived
        self.assertEqual(ev, NotifyEvent.REMOTE_CONNECTED)
        self.factory1.onEventReceived = defer.Deferred()
        ev = yield self.factory2.onEventReceived
        self.assertEqual(ev, NotifyEvent.REMOTE_CONNECTED)
        self.factory2.onEventReceived = defer.Deferred()

        # User 1 sends a message to user 2
        res = yield self.factory2.protoInstance.callRemote(
            SendMsg, sMsg=__sMessageA2B, iTimestamp=services_common_misc.get_utc_timestamp())
        self.assertTrue(res['bResult'])

        msg = yield self.factory1.onMessageReceived
        self.assertEqual(msg, __sMessageA2B)

        # User 2 sends a message to user 1
        res = yield self.factory1.protoInstance.callRemote(
            SendMsg, sMsg=__sMessageB2A, iTimestamp=services_common_misc.get_utc_timestamp())
        self.assertTrue(res['bResult'])

        msg = yield self.factory2.onMessageReceived
        self.assertEqual(msg, __sMessageB2A)

        # User 2 finishes the connection
        res = yield self.factory2.protoInstance.callRemote(EndRemote)
        ev = yield self.factory1.onEventReceived

        # User 1 is notified about the disconnection
        self.assertEqual(ev, NotifyEvent.END_REMOTE)

if __name__ == '__main__':
    unittest.main()  