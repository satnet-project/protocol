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

from os import path, remove
import sys
import logging
import datetime
import django
import pytz
from django.core import management
from mock import Mock, MagicMock
import unittest

sys.path.append(os.path.abspath(path.join(path.dirname(__file__), "..")))

from ampauth.testing import DjangoAuthChecker, Testing
from django.db import models

# Dependencies for _setUp_databases
# from services.common import misc
services_common_misc = Mock()
services_common_misc.localize_time_utc =\
 MagicMock(return_value = 'test')

services_common_misc.get_utc_timestamp =\
 MagicMock(return_value = 'test')

# from services.common.testing import helpers
services_common_testing_helpers = Mock()

services_common_testing_helpers.create_jrpc_daily_rule =\
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
# services_scheduling_jrpc_views_spacecraft.get_operational_slots =\
#  MagicMock(return_value = 'test')

services_scheduling_jrpc_views_spacecraft.select_slots =\
 MagicMock('test1', 'test2')
services_scheduling_jrpc_views_spacecraft.return_value = '2'

# from services.configuration.models import rules
services_configuration_models_rules = Mock()
services_configuration_models_rules.add_rule = MagicMock(return_value = 'test')

# from services.configuration.models import channels
services_configuration_models_channels = Mock()

services_configuration_models_channels.sc_channel_create =\
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
 MagicMock(return_value = '>>> Local server NOT found, creating instance')


# Dependencies for the tests
from twisted.python import log
from twisted.internet import defer, protocol
from twisted.cred.portal import Portal
from twisted.internet import reactor, ssl

# For test purposes
from twisted.manhole.service import Realm

from ampauth.server import CredAMPServerFactory, CredReceiver
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

from django.contrib.auth.models import User

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

    def load_local_server(self):
        print "load_local_server"

    def create_user_profile(self, username, password, email):
        from sqlite3 import connect, PARSE_DECLTYPES, OperationalError

        try:
            """
            Table.
            """

            column = ['id', 'username', 'first_name', 'last_name', 'email',\
             'password', 'groups', 'user_permissions', 'is_staff', 'is_active',\
              'is_superuser', 'last_login', 'date_joined']

            _type = 'INTEGER'
            _typetext = 'INTEGER'
            _datetimetype = 'TEXT'

            self.connection = connect('test.db', detect_types = PARSE_DECLTYPES)

            self.connection.execute('CREATE TABLE {tn} ({nf} {ft}) '\
                                .format(tn='auth_user', nf=column[0], ft=_type))

            self.connection.execute("ALTER TABLE {tn} ADD COLUMN '{cn}' {ct}"\
                                .format(tn='auth_user', cn=column[1], ct=_typetext))

            self.connection.execute("ALTER TABLE {tn} ADD COLUMN '{cn}' {ct}"\
                                .format(tn='auth_user', cn=column[2], ct=_typetext))

            self.connection.execute("ALTER TABLE {tn} ADD COLUMN '{cn}' {ct}"\
                                .format(tn='auth_user', cn=column[3], ct=_typetext))

            self.connection.execute("ALTER TABLE {tn} ADD COLUMN '{cn}' {ct}"\
                                .format(tn='auth_user', cn=column[4], ct=_typetext))

            self.connection.execute("ALTER TABLE {tn} ADD COLUMN '{cn}' {ct}"\
                                .format(tn='auth_user', cn=column[5], ct=_typetext))

            self.connection.execute("ALTER TABLE {tn} ADD COLUMN '{cn}' {ct}"\
                                .format(tn='auth_user', cn=column[6], ct=_typetext))

            self.connection.execute("ALTER TABLE {tn} ADD COLUMN '{cn}' {ct}"\
                                .format(tn='auth_user', cn=column[7], ct=_typetext))

            self.connection.execute("ALTER TABLE {tn} ADD COLUMN '{cn}' {ct}"\
                                .format(tn='auth_user', cn=column[8], ct=_typetext))

            self.connection.execute("ALTER TABLE {tn} ADD COLUMN '{cn}' {ct}"\
                                .format(tn='auth_user', cn=column[9], ct=_typetext))

            self.connection.execute("ALTER TABLE {tn} ADD COLUMN '{cn}' {ct}"\
                                .format(tn='auth_user', cn=column[10], ct=_typetext))

            self.connection.execute("ALTER TABLE {tn} ADD COLUMN '{cn}' {ct}"\
                                .format(tn='auth_user', cn=column[11], ct=_typetext))

            self.connection.execute("ALTER TABLE {tn} ADD COLUMN '{cn}' {ct}"\
                                .format(tn='auth_user', cn=column[12], ct=_datetimetype))

        except OperationalError:
            log.msg(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Table already created.")

        user = User.objects.create_user(username, email, password)
        print "User %s created" %(username)
        return user


    """
    user = models.ForeignKey
    identifier = models.CharField
    callsign = models.CharField
    channels = models.ManyToManyField
    tle = models.ForeignKey
    is_cluster = models.BooleanField
    is_ufo = models.BooleanField
    """
    def create_sc(self, user_profile, identifier, tle_id):

        from sqlite3 import connect, PARSE_DECLTYPES, OperationalError

        try:
            """
            Table.
            """

            column = ['user_profile', 'identifier', 'callsign', 'channels', 'tle_id',\
             'is_cluster', 'is_ufo']

            _typeText = 'TEXT'
            _typeInteger = 'INTEGER'

            self.connection.execute("ALTER TABLE {tn} ADD COLUMN '{cn}' {ct}"\
                .format(tn='auth_user', cn=column[0], ct=_typeText))

            self.connection.execute("ALTER TABLE {tn} ADD COLUMN '{cn}' {ct}".\
                format(tn='auth_user', cn=column[1], ct=_typeText))
            
            self.connection.execute("ALTER TABLE {tn} ADD COLUMN '{cn}' {ct}".\
                format(tn='auth_user', cn=column[2], ct=_typeText))

            self.connection.execute("ALTER TABLE {tn} ADD COLUMN '{cn}' {ct}".\
                format(tn='auth_user', cn=column[3], ct=_typeText))
            
            self.connection.execute("ALTER TABLE {tn} ADD COLUMN '{cn}' {ct}".\
                format(tn='auth_user', cn=column[4], ct=_typeText))

            self.connection.execute("ALTER TABLE {tn} ADD COLUMN '{cn}' {ct}".\
                format(tn='auth_user', cn=column[5], ct=_typeInteger))

            self.connection.execute("ALTER TABLE {tn} ADD COLUMN '{cn}' {ct}".\
                format(tn='auth_user', cn=column[6], ct=_typeInteger))

            log.msg(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Spacecraft fields created.", system = "database-test")

        except OperationalError:
            log.msg(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Spacecraft fields already created.", system = "database-test")

        spacecraft = User.objects.create_user(user_profile, identifier, tle_id)

        print "Spacecraft %s created" %(identifier)

    def sc_channel_create(self, spacecraft_id, channel_id, configuration):
        print "sc_channel_create"
        print spacecraft_id
        print channel_id
        print configuration

    def create_gs(self, user_profile, identifier):
        print "create_gs"
        print user_profile
        print identifier

    def gs_channel_create(self, ground_station_id, channel_id, configuration):
        print "create_gs_channel"
        print ground_station_id
        print channel_id
        print configuration

    def get_simulator_set_debug(self):
        print "get_simulator_set_debug"

    def set_debug(self):
        print "set_debug"

    def init_available(self):
        print "init_available"

    def init_tles_database(self):
        print "init_tles_database"

    def create_band(self):
        print "create_band"

    def connect_availability_2_operational(self):
        print "connect_availability_2_operational"

    def connect_channels_2_compatibility(self):
        print "connect_channels_2_compatibility"

    def connect_compatibility_2_operational(self):
        print "connect_compatibility_2_operational"

    def connect_rules_2_availability(self):
        print "connect_rules_2_availability"

    def get_operational_slots(self, __sc_id):
        print "get_operational_slots"
        print __sc_id

        prueba_texto = "loleilo"

        return prueba_texto

    def _setUp_mocks(self):
        self.services_scheduling_jrpc_views_spacecraft_get_operational_slots =\
         Mock()
        self.services_scheduling_jrpc_views_spacecraft_get_operational_slots.side_effect =\
         self.get_operational_slots

        self.services_configuration_signals_models_models_connect_availability_2_operational =\
         Mock()
        self.services_configuration_signals_models_models_connect_availability_2_operational.side_effect =\
         self.connect_availability_2_operational      

        self.services_configuration_signals_models_models_connect_channels_2_compatibility =\
         Mock()
        self.services_configuration_signals_models_models_connect_channels_2_compatibility.side_effect =\
         self.connect_channels_2_compatibility

        self.services_configuration_signals_models_models_connect_compatibility_2_operational =\
         Mock()
        self.services_configuration_signals_models_models_connect_compatibility_2_operational.side_effect =\
         self.connect_compatibility_2_operational

        self.services_configuration_signals_models_models_connect_rules_2_availability =\
         Mock()
        self.services_configuration_signals_models_models_connect_rules_2_availability.side_effect =\
         self.connect_rules_2_availability

        self.services_network_models_server_Server_objects_load_local_server =\
         Mock()
        self.services_network_models_server_Server_objects_load_local_server.side_effect =\
         self.load_local_server

        self.services_common_testing_helpers_init_available = Mock()
        self.services_common_testing_helpers_init_available.side_effect =\
         self.init_available

        self.services_common_testing_helpers_init_tles_database = Mock()
        self.services_common_testing_helpers_init_tles_database.side_effect =\
         self.init_tles_database
        
        self.services_common_testing_helpers_create_band = Mock()
        self.services_common_testing_helpers_create_band.side_effect =\
         self.create_band

        self.services_common_testing_helpers_create_user_profile = Mock()
        self.services_common_testing_helpers_create_user_profile.side_effect =\
         self.create_user_profile

        self.services_common_testing_helpers_create_sc = Mock()
        self.services_common_testing_helpers_create_sc.side_effect =\
         self.create_sc

        self.services_common_testing_helpers_create_gs = Mock()
        self.services_common_testing_helpers_create_gs.side_effect =\
         self.create_gs

        self.services_configuration_models_channels_gs_channel_create = Mock()
        self.services_configuration_models_channels_gs_channel_create.side_effect =\
         self.gs_channel_create

        self.services_configuration_models_channels_sc_channel_create = Mock()
        self.services_configuration_models_channels_sc_channel_create.side_effect =\
         self.sc_channel_create

        self.operational_OperationalSlot_objects_get_simulator_set_debug = Mock()
        self.operational_OperationalSlot_objects_get_simulator_set_debug.side_effect =\
         self.get_simulator_set_debug

        self.operational_OperationalSlot_objects_set_debug = Mock()
        self.operational_OperationalSlot_objects_set_debug.side_effect =\
         self.set_debug

    def _setUp_databases(self):
        """
        This method populates the database with some information to be used
        only for this test.
        """

        """ TO-DO
        This method loads the information for the local server, updating any
        change in the IP address that may have happened. In case the server
        does not exist in the database, it creates the local server for the
        very first time.
        """
        self.services_network_models_server_Server_objects_load_local_server() 

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
        # asigna a cada variable una "key" para asi poder crear un diccionario
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

        self.services_configuration_signals_models_models_connect_availability_2_operational()
        self.services_configuration_signals_models_models_connect_channels_2_compatibility()
        self.services_configuration_signals_models_models_connect_compatibility_2_operational()
        self.services_configuration_signals_models_models_connect_rules_2_availability()
        #services_configuration_signals_models.connect_segments_2_booking_tle()

        self.services_common_testing_helpers_init_available()
        self.services_common_testing_helpers_init_tles_database()
        __band = self.services_common_testing_helpers_create_band()

        __usr_1_name = 'crespo'
        __usr_1_pass = 'cre.spo'
        __usr_1_mail = 'crespo@crespo.gal'

        __usr_2_name = 'tubio'
        __usr_2_pass = 'tu.bio'
        __usr_2_mail = 'tubio@tubio.gal'

        # Default values: username=testuser, password=testuser.
        # __user_def = services_common_testing_helpers.create_user_profile()
        __usr_1 = self.services_common_testing_helpers_create_user_profile(\
            username=__usr_1_name, password=__usr_1_pass, email=__usr_1_mail)
        __usr_2 = self.services_common_testing_helpers_create_user_profile(\
            username=__usr_2_name, password=__usr_2_pass, email=__usr_2_mail)

        __sc_1 = self.services_common_testing_helpers_create_sc(
            user_profile=__usr_1,
            identifier=__sc_1_id,
            tle_id=__sc_1_tle_id,
        )

        __sc_2 = self.services_common_testing_helpers_create_sc(
            user_profile=__usr_2,
            identifier=__sc_2_id,
            tle_id=__sc_2_tle_id,
        )

        __gs_1 = self.services_common_testing_helpers_create_gs(
            user_profile=__usr_2, 
            identifier=__gs_1_id,
        )

        # operational.OperationalSlot.objects.get_simulator().set_debug()
        self.operational_OperationalSlot_objects_get_simulator_set_debug()
        self.operational_OperationalSlot_objects_set_debug()

        self.services_configuration_models_channels_gs_channel_create(
            ground_station_id=__gs_1_id,
            channel_id=__gs_1_ch_1_id,
            configuration=__gs_1_ch_1_cfg
        )

        """ TO-DO
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
        """

        self.services_configuration_models_channels_sc_channel_create(
            spacecraft_id=__sc_1_id,
            channel_id=__sc_1_ch_1_id,
            configuration=__sc_1_ch_1_cfg
        )

        self.services_configuration_models_channels_sc_channel_create(
            spacecraft_id=__sc_2_id,
            channel_id=__sc_2_ch_1_id,
            configuration=__sc_2_ch_1_cfg
        )

        sc_1_o_slots =\
         self.services_scheduling_jrpc_views_spacecraft_get_operational_slots(__sc_1_id)
        sc_2_o_slots =\
         self.services_scheduling_jrpc_views_spacecraft_get_operational_slots(__sc_2_id)

        # TypeError: string indices must be integers, not str
        """
        JRPC method that permits obtaining all the OperationalSlots for all the
        channels that belong to the Spacecraft with the given identifier.
        :param spacecraft_id: Identifier of the spacecraft.
        :return: JSON-like structure with the data serialized.
        """

        """ TO-DO

        # sc_1_s_slots = services_scheduling_jrpc_views_spacecraft.select_slots(
        #     __sc_1_id, [int(slot['identifier']) for slot in sc_1_o_slots])

        # sc_2_s_slots = services_scheduling_jrpc_views_spacecraft.select_slots(
        #     __sc_2_id, [int(slot['identifier']) for slot in sc_2_o_slots])

        # gs_1_o_slots = services_scheduling_jrpc_views_groundstations.get_operational_slots(__gs_1_id)

        # gs_c_slots = services_scheduling_jrpc_views_groundstations.confirm_selections(
        #     __gs_1_id, [int(slot['identifier']) for slot in gs_1_o_slots])

        """

    def setUp(self):
        # log.msg(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Flushing database")
        # management.execute_from_command_line(['manage.py', 'flush', '--noinput'])
        
        # log.msg(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Populating database")        
        # management.execute_from_command_line(['manage.py', 'createsuperuser',
        #     '--username', 'crespum', '--email', 'crespum@humsat.org', '--noinput'])

        log.startLogging(sys.stdout)

        log.msg(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> SetUp mock objects.")
        self._setUp_mocks()

        log.msg(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Setting database.")
        self._setUp_databases()
        
        log.msg(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Running tests")

        """
        Server connection
        """
        self.serverDisconnected = defer.Deferred()
        self.serverPort = self._listenServer(self.serverDisconnected)
 
        """
        Client A connection
        """
        self.connected1 = defer.Deferred()
        self.clientDisconnected1 = defer.Deferred()
        self.factory1 = protocol.ClientFactory.forProtocol(ClientProtocolTest)
        self.clientConnection1 = self._connectClients(self.factory1, self.connected1,
                                                      self.clientDisconnected1)
        """
        Client B connection
        """
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
        # Creacion de la factoria
        pf = CredAMPServerFactory(portal)
        pf.protocol = CredReceiver
        pf.onConnectionLost = d
        cert = ssl.PrivateCertificate.loadPEM(
            open('../key/server.pem').read())
        # Le pasa el puerto, factor y certificado.
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

        self.connection.close()
        remove('test.db')
        log.msg(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Deleting database.")

    """
    Basic remote connection between two clients. The procedure goes:
        1. Client A -> Login
        2. Client A -> StartRemote (should return StartRemote.REMOTE_NOT_CONNECTED)
        3. Client B -> Login
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
        res = yield Login(self.factory1.protoInstance, UsernamePassword(
            __user1_name, __user1_pass))
        self.assertTrue(res['bAuthenticated'])

        res = yield self.factory1.protoInstance.callRemote(StartRemote, iSlotId=__iSlotId)
        self.assertEqual(res['iResult'], StartRemote.REMOTE_NOT_CONNECTED)

        # User 2 (login + start remote)
        res = yield Login(self.factory2.protoInstance, UsernamePassword(
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