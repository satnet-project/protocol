# coding=utf-8
import os
import sys
import time

from datetime import datetime

# Dependencies for the tests
from mock import patch, Mock, MagicMock
from twisted.trial.unittest import TestCase

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),
                                "../ampauth")))
from server import CredReceiver, CredAMPServerFactory
from errors import BadCredentials, SlotErrorNotification

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),
                                "../")))
import rpcrequests
import misc



"""
   Copyright 2016 Samuel Góngora García
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
    Samuel Góngora García (s.gongoragarcia@gmail.com)
"""
__author__ = 's.gongoragarcia@gmail.com'


class TestProtocolLogin(TestCase):

    def setUp(self):
        self.sp = CredReceiver()
        self.sp.factory = CredAMPServerFactory()

    def tearDown(self):
        self.sp.factory.active_protocols = {}
        self.sp.factory.active_connections = {}

    def test_successfulLoginWithTestUser(self):
        print ""
        res = self.sp.login('test-user-sc', 'test-password')
        return self.assertTrue(res['bAuthenticated'])

    def test_unsuccessfulLoginWithTestUser(self):
        print ""
        self.sp.rpc = MagicMock(return_value=False)
        res = self.sp.login('wrong-user', 'wrong-pass')
        return self.assertFalse(res['bAuthenticated'])

    @patch.object(CredReceiver, 'start_remote_user', return_value=[{'ending_time': 1234, 'id': '-1'},
                                                                   'gs', 'sc', 'client_a', 'client_c'])
    @patch.object(CredReceiver, 'check_expiration', return_value=1000)
    def _test_startRemoteSucessful(self, start_remote_user, check_expiration):
        res = self.sp.iStartRemote()

        return self.assertEqual(str(res['iResult']), '-2')


class TestProtocolLoginAuxiliarMethods(TestCase):

    def setUp(self):
        self.sp = CredReceiver()
        self.sp.factory = CredAMPServerFactory()


    def tearDown(self):
        self.sp.factory.active_protocols = {}
        self.sp.factory.active_connections = {}

    def test_getsASlotUsingARPCCall(self):
        self.sp.username = 'test-user-sc'
        self.sp.rpc = Mock()
        self.sp.rpc.testing = Mock

        print ""
        response = self.sp.start_remote_user()
        value = ['test-user-gs', 'test-user-sc', 'test-user-sc', 'test-user-gs']

        self.assertIs(type(response[0]), dict)
        self.assertEqual(str(response[1]), str(value[0]))
        self.assertEqual(str(response[2]), str(value[1]))
        self.assertEqual(str(response[3]), str(value[2]))
        self.assertEqual(str(response[4]), str(value[3]))


    def test_decodeUserWithSlotUserIsSC(self):
        test_slot = {'gs_username': 'gs_user_test', 'sc_username': 'sc_user_test'}
        self.sp.username = 'sc_user_test'
        response = self.sp.decode_user(test_slot)

        value = ['gs_user_test', 'sc_user_test', 'sc_user_test', 'gs_user_test']

        for i in range(len(response)):
            self.assertIs(value[i], response[i])

    def test_decodeUserWithSlotUserIsGS(self):
        test_slot = {'gs_username': 'gs_user_test', 'sc_username': 'sc_user_test'}
        self.sp.username = 'gs_user_test'
        response = self.sp.decode_user(test_slot)

        value = ['gs_user_test', 'sc_user_test', 'gs_user_test', 'sc_user_test']

        for i in range(len(response)):
            self.assertIs(value[i], response[i])

    def test_decodeUserWithoutSlot(self):
        """
        Tries to decode an user without having a slot.
        :return: assertRaises statement.
        """
        return self.assertRaises(SlotErrorNotification, self.sp.decode_user, slot=None)

    def test_checkSlotOwnershipRight(self):
        """
        Checks if the current slot belongs to spacecraft user or groundstation user.
        :return: assertIsNone statement.
        """
        self.sp.username = 'sc_user_test'

        sc_user = 'sc_user_test'
        gs_user = 'gs_user_test'

        print ""
        return self.assertIsNone(self.sp.check_slot_ownership(sc_user, gs_user))

    def test_checkSlotOwnershipWrong(self):
        """
        Checks if the current slot belongs to spacecraft user or groundstation user.
        :return: assertRaises statement.
        """
        self.sp.username = 'sc_user_test'

        sc_user = 'sc_user_test_wrong'
        gs_user = 'gs_user_test_wrong'

        print ""
        return self.assertRaises(SlotErrorNotification, self.sp.check_slot_ownership,
                                 sc_user, gs_user)

    def test_checkExpirationSlotOnTime(self):
        time_now = misc.localize_datetime_utc(datetime.utcnow())
        time_now = int(time.mktime(time_now.timetuple()))
        time_now = time_now + 60

        return self.assertEqual(self.sp.check_expiration(-1, time_now), 60)

    def test_checkExpirationSlotExpired(self):
        time_now = misc.localize_datetime_utc(datetime.utcnow())
        time_now = int(time.mktime(time_now.timetuple()))
        time_now = time_now - 60

        return self.assertRaises(SlotErrorNotification, self.sp.check_expiration, -1, time_now)
