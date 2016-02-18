# coding=utf-8

import base64
import requests
import json

from tinyrpc.protocols.jsonrpc import JSONRPCProtocol
from tinyrpc.transports.http import HttpPostClientTransport
from tinyrpc.client import RPCClient
from twisted.python import log

from errors import BadCredentials

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


class HttpSessionTransport(HttpPostClientTransport):
    """
    Transport layer that handles sessions to allow the execution
    of login protected RPC methods
    """

    def __init__(self, user, pwd, endpoint='https://localhost/jrpc/'):
	"""
	:param endpoint:
            URL to send "POST" data to.
    	:type endpoint:
    	    L{String}
	"""
        super(HttpSessionTransport, self).__init__(endpoint)
        self.s = requests.Session()
	self.s.auth = (user, pwd)

    def send_message(self, message, expect_reply=True):
        if not isinstance(message, str):
            raise TypeError('str expected')

        r = self.s.post(
	    self.endpoint, data=message,
	    headers={'content-type': 'application/json'},
	    verify=False
	)

	log.msg('>>> r = ' + str(r))

        if expect_reply:
            return r.content


class JSONRPCProtocolFix(JSONRPCProtocol):
    """
    Workaround to solve a bug in rpc4django. This problem is
    detailed in https://github.com/davidfischer/rpc4django/issues/32.
    As soon as pull request #39 is accepted the parent class must be
    used instead.
    """
    def __init__(self, *args):
        super(JSONRPCProtocolFix, self).__init__(*args)

    def parse_reply(self, data):
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


class Satnet_RPC(object):

    def __init__(self, user, pwd):
	"""
	Start RPC connection and keep session open.

	Example:
	rpc = Satnet_RPC('crespum', 'solutions')
	print rpc.call('configuration.sc.list')

	:param user:
 	   SatNet username.
 	:type user:
	   L{String}

	:param pwd:
            SatNet password for this user.
	:type pwd:
            L{String}
	"""
        self._rpc_client = RPCClient(
            JSONRPCProtocolFix(), HttpSessionTransport(user, pwd)
	)
        #if not self.login(user, pwd):
        #    raise BadCredentials()
        #else:
        #    log.msg('System login confirmed!')

    def call(self, call, *args):
	"""
        Make an RPC call to the SatNet server.

        :param call:
            Name of the methods
        :type call:
            L{String}

        :param args:
            Arguments required by the method to be invocked.
	"""
        return self._rpc_client.call(call, args, None)

    def login(self, user, pwd):
	"""system.login
	"""
	return self.call('system.login', user, pwd)

    def getSlot(self, slot_id):
	"""scheduling.slot.get
	"""
	return self.call('scheduling.slot.get', slot_id)

    def storeMessage(self, slot_id, upwards, forwarded, timestamp, message):
	"""communications.storeMessage
	"""
        base64Message = base64.b64encode(message)
        slot_id = str(slot_id)

        self.call(
	    'communications.storeMessage',
	    slot_id, upwards, forwarded, timestamp, base64Message
	)

    def storeUnconnectedMessage(self, message):
	"""Stores messages for unconnected spacecraft operators
	TODO Find out proper values for the parameters
	"""
	self.storePassiveMessage(0, 0, 0.0, base64.b64encode(message))

    def storePassiveMessage(self, groundstation_id, timestamp, doppler_shift, message):
	"""communications.gs.storePassiveMessage
	"""
        base64Message = base64.b64encode(message)
        slot_id = str(slot_id)

        self.call(
	    'communications.gs.storePassiveMessage',
	    groundstation_id, timestamp, doppler_shift, base64Message
	)

