# coding=utf-8
import os
import sys

# Dependencies for the tests
from twisted.python import log
from twisted.trial.unittest import TestCase

from twisted.test.proto_helpers import StringTransportWithDisconnection
from twisted.internet.protocol import Factory

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


class MockFactory(Factory):

    clients = []
    active_protocols = []
    active_connections = []


class TestProtocolReceiveFrame(TestCase):

    def setUp(self):
        log.msg(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Running tests")

        self.sp = CredReceiver()
        self.sp.factory = MockFactory()
        self.sp.factory.sUsername = 'test_name'
        self.transport = StringTransportWithDisconnection()
        self.sp.makeConnection(self.transport)

        self.transport.protocol = self.sp

        self.testFrame = ("00:82:a0:00:00:53:45:52:50:2d:42:30:91:1d:1b:03:" +
                          "8d:0b:5c:03:02:28:01:9c:01:ab:02:4c:02:98:01:da:" +
                          "02:40:00:00:00:10:0a:46:58:10:00:c4:9d:cb:a2:21:39")

    def tearDown(self):
        pass

    def test_serverSendsAnythingWhenReceiveFrame(self):
        self.sp.dataReceived(self.testFrame)
        self.assertEquals('', self.transport.value())
