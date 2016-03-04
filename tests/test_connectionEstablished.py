# coding=utf-8
import os
import sys

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


class TestServerProtocolConnectionEstablished(TestCase):

    """
    Testing multiple client connections
    TDOD. Test multiple valid connections
    """

    def setUp(self):
        self.sp = CredReceiver()
        self.sp.factory = CredAMPServerFactory()
        self.transport = StringTransportWithDisconnection()

    def tearDown(self):
        self.transport.loseConnection()

    def test_connectionProtocolEstablished(self):
        """
        Checks if transport is working an clients list has the last client.
        :return:
        """
        self.sp.makeConnection(self.transport)
        self.transport.protocol = self.sp

        return self.assertTrue(self.transport.connected),\
               self.assertEqual(len(self.sp.factory.clients), 1)
