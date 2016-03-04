# coding=utf-8

import base64
import requests
import json

from tinyrpc.protocols.jsonrpc import JSONRPCProtocol
from tinyrpc.transports.http import HttpPostClientTransport
from tinyrpc.client import RPCClient
from twisted.python import log as tw_log

from errors import BadCredentials

# from xmlrpclib import ServerProxy
# from rpc4django.utils import CookieTransport

"""
     Copyright 2015, 2016 Xabier Crespo Álvarez

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

ENDPOINT_PRODUCTION = 'https://localhost/jrpc/'
ENDPOINT_TESTING = 'http://localhost:8000/jrpc/'

RPC_TEST_USER_GS = 'test-user-gs'
RPC_TEST_USER_SC = 'test-user-sc'


class HttpSessionTransport(HttpPostClientTransport):
    """
    Transport layer that handles sessions to allow the execution
    of login protected RPC methods
    """

    def __init__(self, user, pwd, endpoint=ENDPOINT_PRODUCTION):
        """INIT
        :param endpoint: URL to send "POST" data to.
        :type endpoint: L{String}
        """
        super(HttpSessionTransport, self).__init__(endpoint)
        self.s = requests.Session()
        self.s.auth = (user, pwd)

    def send_message(self, message, expect_reply=True):
        """request sends message
        :param message: Message to be sent
        :param expect_reply: Flag that indicates whether the response should
                                be returned or not
        """
        if not isinstance(message, str):
            raise TypeError('str expected')

        r = self.s.post(
            self.endpoint, data=message,
            headers={'content-type': 'application/json'},
            verify=False
        )

        tw_log.msg('>>> r = ' + str(r))

        if expect_reply:
            return r.content


class JSONRPCProtocolFix(JSONRPCProtocol):
    """
    Workaround to solve a bug in RPC4Django. This problem is detailed in:
    https://github.com/davidfischer/rpc4django/issues/32.
    As soon as pull request #39 is accepted the parent class must be used
    instead.
    """
    def __init__(self, *args):
        """Overriden
        """
        super(JSONRPCProtocolFix, self).__init__(*args)

    def parse_reply(self, data):
        """Overriden
        :param data: Serialized JSON data
        """

        try:

            req = json.loads(data)
            if req['error'] is None:
                req.pop('error')
            if req['result'] is None:
                req.pop('result')
            return super(JSONRPCProtocolFix,
                         self).parse_reply(json.dumps(req))
        except Exception as e:
            print "Error loading JSON response"
            print e

            if 'error' in req and not req['error']and req['error'] is None:
                del req['error']

            if 'result' in req and not req['result'] and req['result'] is None:
                del req['result']

            return super(JSONRPCProtocolFix, self).parse_reply(json.dumps(req))

        except Exception as e:
            print "Error loading JSON response, ex = " + str(e)


class SatnetRPC(object):

    testing = False

    def __init__(self, user, pwd):
        """Start RPC connection and keep session open
        Example:
        rpc = Satnet_RPC('crespum', 'solutions')
        print rpc.call('configuration.sc.list')

        :param user: SatNet username.
        :type user: L{String}
        :param pwd: SatNet password for this user.
        :type pwd: L{String}
        """
        self._rpc_client = RPCClient(
            JSONRPCProtocolFix(), HttpSessionTransport(user, pwd)
        )
        self.detect_test(user)

        if self.testing:
            return

        if not self.login(user, pwd):
            raise BadCredentials()

        tw_log.msg('System login confirmed!')

    def detect_test(self, username):
        """Detects the test mode
        This function sets the object into testing mode if the name of the
        users coincides with any of the TEST_USER names enabled for that
        purpose.
        :param username: The current username
        """
        if username == RPC_TEST_USER_GS or username == RPC_TEST_USER_SC:
            self.testing = True
            tw_log.msg('>>> Testing user detected, running in TESTING MODE')

    def call(self, call, *args):
        """Make an RPC call to the SatNet server

        :param call: Name of the methods
        :type call: L{String}
        :param args: Arguments required by the method to be invocked.
        """

        return self._rpc_client.call(call, args, None)

    def login(self, user, pwd):
        """system.login
        :param user: String with the username of the currently logged in user
        :param pwd: String with the password for the currently logged in user
        """
        tw_log.msg(
            '@@@@ system.login, user = ' + str(user) + ', pwd = ' + str(pwd)
        )
        return self.call('system.login', str(user), str(pwd))

    def get_slot(self, slot_id):
        """scheduling.slot.get
        :param slot_id: Identifier of the slot
        """
        return self.call('scheduling.slot.get', slot_id)

    def get_next_slot(self, user_email):
        """scheduling.slot.next
        :param user_email: Identifier of the slot
        """
        return self.call('scheduling.slot.next', user_email)

    def store_message(self, slot_id, upwards, forwarded, timestamp, message):
        """communications.storeMessage
        :param slot_id: Identifier of the slot
        :param upwards: Flag that indicates the direction of the message
        :param forwarded: Flat that indicates whether this message has already
                            been forwarded or not
        :param timestamp: Unix timestamp for the reception of the package
        :param message: String with the message received from the client
        """
        base_64_message = base64.b64encode(message)
        slot_id = str(slot_id)

        self.call(
            'communications.storeMessage',
            slot_id, upwards, forwarded, timestamp, base_64_message
        )

    def store_message_unconnected(self, message):
        """Stores messages for unconnected spacecraft operators
        TODO Find out proper values for the parameters
        :param message: String with the message received from the client
        """
        self.store_message_passive(0, 0, 0.0, base64.b64encode(message))

    def store_message_passive(
        self, groundstation_id, timestamp, doppler_shift, message
    ):
        """communications.gs.storePassiveMessage
        :param groundstation_id: Identifier of the groundstation
        :param timestamp: Unix timestamp for the reception of the package
        :param doppler_shift: Estimation of the Doppler shift
        :param message: String with the message received from the client
        """
        base_64_message = base64.b64encode(message)

        self.call(
            'communications.gs.storePassiveMessage',
            groundstation_id, timestamp, doppler_shift, base_64_message
        )
