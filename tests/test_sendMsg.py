# coding=utf-8
import os
import sys

# Dependencies for the tests
from mock import Mock, MagicMock

from twisted.trial.unittest import TestCase

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),
                                "../ampauth")))
from server import CredReceiver, CredAMPServerFactory
import misc
import errors

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


class TestManageMessages(TestCase):

    def setUp(self):
        self.sp = CredReceiver()
        self.sp.factory = CredAMPServerFactory()

        self.correctFrame = ("00:82:a0:00:00:53:45:52:50:2d:42:30:91:1d:1b:03:" +
                             "8d:0b:5c:03:02:28:01:9c:01:ab:02:4c:02:98:01:da:" +
                             "02:40:00:00:00:10:0a:46:58:10:00:c4:9d:cb:a2:21:39")

    def tearDown(self):
        self.sp.factory.active_protocols = {}
        self.sp.factory.active_connections = {}
        self.sp.username = None

    def test_messageSentLocalAndRemoteUserOk(self):
        """
        Remove local protocol and the active connections which are involving it.
        callRemote methods are mocked for testing purposes.

        :return: assertTrue statement
        """
        sc_user = 'test-user-sc'
        gs_user = 'test-user-gs'
        username_test = 'test-user-sc'

        mockSC = Mock()
        mockSC.callRemote = MagicMock(return_value=True)
        mockGS = Mock()

        self.sp.factory.active_protocols[str(sc_user)] = mockSC
        self.sp.factory.active_protocols[str(gs_user)] = mockGS
        self.sp.factory.active_connections[str(sc_user)] = str(gs_user)
        self.sp.factory.active_connections[str(gs_user)] = str(sc_user)
        self.sp.username = username_test

        self.sp.rpc = Mock()
        self.sp.rpc.testing = MagicMock(return_value=True)

        time = misc.get_utc_timestamp()

        res = self.sp.vSendMsg(self.correctFrame, time)
        return self.assertTrue(res['bResult'])

    def test_messageNotSentLocalProtocolNotConnected(self):
        """
        Remove local protocol and the active connections which are involving it.
        callRemote methods are mocked for testing purposes.

        :return: assertRaises statement
        """
        sc_user = 'test-user-sc'
        username_test = 'test-user-sc'

        mockGS = Mock()
        mockGS.callRemote = MagicMock(return_value=True)

        self.sp.factory.active_protocols[str(sc_user)] = mockGS
        self.sp.username = username_test

        self.sp.rpc = Mock()
        self.sp.rpc.testing = Mock()
        self.sp.rpc.store_message = MagicMock(return_value=True)

        time = misc.get_utc_timestamp()

        return self.assertRaises(errors.SlotErrorNotification, self.sp.vSendMsg,
                                 self.correctFrame, time)

    # FIX-ME When it's run with the complete tests bunch raises True instead ValueError
    def _test_messageNotSentRemoteProtocolNotConnected(self):
        """
        Remove local protocol and the active connections which are involving it.
        callRemote methods are mocked for testing purposes.

        :return: assertRaises statement
        """
        sc_user = 'test-user-sc'
        gs_user = 'test-user-gs'
        username_test = 'test-user-sc'

        mockSC = Mock()
        mockSC.callRemote = MagicMock(return_value=True)

        self.sp.factory.active_protocols[str(sc_user)] = mockSC
        self.sp.factory.active_connections[str(sc_user)] = str(gs_user)
        self.sp.factory.active_connections[str(gs_user)] = str(sc_user)
        self.sp.username = username_test

        self.sp.rpc = Mock()
        self.sp.rpc.testing = Mock()
        self.sp.rpc.store_message = MagicMock(return_value=True)

        time = misc.get_utc_timestamp()

        return self.assertRaises(errors.ValueError, self.sp.vSendMsg,
                                 self.correctFrame, time)
