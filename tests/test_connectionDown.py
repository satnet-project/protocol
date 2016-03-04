# coding=utf-8
import os
import sys

# Dependencies for the tests
from mock import patch, Mock, MagicMock
from exceptions import KeyError
import exceptions

from twisted.python import log
from twisted.trial.unittest import TestCase

from twisted.test.proto_helpers import StringTransportWithDisconnection

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),
                                "../ampauth")))
from server import CredReceiver, CredAMPServerFactory


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


class TestServerProtocolConnectionDown(TestCase):

    """
    Testing multiple client connections
    TDOD. Test multiple valid connections
    """

    def setUp(self):
        self.sp = CredReceiver()
        self.sp.factory = CredAMPServerFactory()
        self.transport = StringTransportWithDisconnection()
        self.sp.makeConnection(self.transport)

        self.transport.protocol = self.sp

    def tearDown(self):
        self.sp.factory.active_protocols = {}
        self.sp.factory.active_connections = {}

    def test_localProtocolRemovesWhenTimeoutReachesWithRemoteUserConnected(self):
        sc_user = 'test-user-sc'
        gs_user = 'test-user-gs'
        username_test = 'test-user-sc'

        mockSC = Mock()
        mockSC.callRemote = MagicMock(return_value=True)
        mockGS = Mock()
        mockGS.callRemote = MagicMock(return_value=True)

        self.sp.factory.active_protocols[str(sc_user)] = mockSC
        self.sp.factory.active_protocols[str(gs_user)] = mockGS
        self.sp.factory.active_connections[str(sc_user)] = str(gs_user)
        self.sp.factory.active_connections[str(gs_user)] = str(sc_user)
        self.sp.username = username_test

        self.sp.timeoutConnection()

        return self.assertFalse(self.transport.connected), \
               self.assertIs(len(self.sp.factory.active_protocols), 1), \
               self.assertIs(len(self.sp.factory.active_connections), 0)

    def test_localProtocolRemovesWhenTimeoutReachesWithoutRemoteUserDisconnected(self):
        sc_user = 'test-user-sc'
        username_test = 'test-user-sc'

        mockSC = Mock()
        mockSC.callRemote = MagicMock(return_value=True)
        mockGS = Mock()
        mockGS.callRemote = MagicMock(return_value=True)

        # self.sp.factory.active_protocols[str(sc_user)] = mockSC
        self.sp.factory.active_protocols[str(sc_user)] = mockSC
        self.sp.username = username_test
        self.sp.timeoutConnection()

        return self.assertFalse(self.transport.connected), \
               self.assertIs(len(self.sp.factory.active_protocols), 1), \
               self.assertIs(len(self.sp.factory.active_connections), 0)


class TestSlotsNotification(TestCase):

    def setUp(self):
        self.sp = CredReceiver()
        self.sp.factory = CredAMPServerFactory()

    def tearDown(self):
        pass

    @patch.object(CredReceiver, 'callRemote')
    def test_slotEndingCallRemoteCalled(self, callRemote):
        self.sp.slot_end(-1)
        return self.assertEqual(int(callRemote.call_count), 1)


class TestManageActiveConnections(TestCase):

    def setUp(self):
        self.sp = CredReceiver()
        self.sp.factory = CredAMPServerFactory()
        self.sp.factory.sUsername = 'test_name'
        self.transport = StringTransportWithDisconnection()
        self.sp.makeConnection(self.transport)

        self.transport.protocol = self.sp

    def tearDown(self):
        self.sp.factory.active_protocols = {}
        self.sp.factory.active_connections = {}

    def test_localProtocolRemoveWhenSuddenlyDisconnects(self):
        """
        Remove local protocol and the active connections which are involving it.
        callRemote methods are mocked for testing purposes.

        :return: Assertion statement
        """
        sc_user = 'test-user-sc'
        gs_user = 'test-user-gs'
        username_test = 'test-user-sc'

        mockSC = Mock()
        mockSC.callRemote = MagicMock(return_value=True)
        mockGS = Mock()
        mockGS.callRemote = MagicMock(return_value=True)

        self.sp.factory.active_protocols[str(sc_user)] = mockSC
        self.sp.factory.active_protocols[str(gs_user)] = mockGS
        self.sp.factory.active_connections[str(sc_user)] = str(gs_user)
        self.sp.factory.active_connections[str(gs_user)] = str(sc_user)
        self.sp.username = username_test

        res = self.sp.vEndRemote()

        return self.assertTrue(res['bResult']), \
               self.assertIs(len(self.sp.factory.active_protocols), 1), \
               self.assertIs(len(self.sp.factory.active_connections), 0)

    def test_localProtocolRemoveWhenRemoteUserIsDisconnected(self):
        """
        Remove local protocol when remote user has already detached the connection.

        :return: Assertion statement
        """

        # Must fill active_protocols with mock objects
        sc_user = 'test-user-sc'
        username_test = 'test-user-sc'

        mockSC = Mock()
        mockSC.callRemote = MagicMock(return_value=True)
        mockGS = Mock()
        mockGS.callRemote = MagicMock(return_value=True)

        # self.sp.factory.active_protocols[str(sc_user)] = mockSC
        self.sp.factory.active_protocols[str(sc_user)] = mockSC
        self.sp.username = username_test

        res = self.sp.vEndRemote()

        return self.assertTrue(res['bResult']), \
               self.assertIs(len(self.sp.factory.active_protocols), 0), \
               self.assertIs(len(self.sp.factory.active_connections), 0)

