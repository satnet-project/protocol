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


from tinyrpc.protocols.jsonrpc import JSONRPCProtocol
from tinyrpc.transports.http import HttpPostClientTransport
from tinyrpc.client import RPCClient
import requests, json, threading
from errors import BadCredentials

class HttpSessionTransport(HttpPostClientTransport):
    """
    Transport layer that handles sessions to allow the execution
    of login protected RPC methods
    
    :param endpoint:
        URL to send "POST" data to.
    :type endpoint:
        L{String}
    """
    def __init__(self, endpoint):
        super(HttpSessionTransport, self).__init__(endpoint)
        self.s = requests.Session()

    def send_message(self, message, expect_reply=True):
        if not isinstance(message, str):
            raise TypeError('str expected')

        r = self.s.post(self.endpoint, data=message, **self.request_kwargs)

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
        except Exception as e:
            print "Error loading JSON response"
            print e

        return super(JSONRPCProtocolFix, self).parse_reply(json.dumps(req))

class Satnet_RPC():
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
    def __init__(self, user, pwd, debug=False):
        if not debug:
            self._rpc_client = RPCClient(
                JSONRPCProtocolFix(),
                HttpSessionTransport('https://satnet.aero.calpoly.edu/jrpc/')
            )
        else:
            self._rpc_client = RPCClient(
                JSONRPCProtocolFix(),
                HttpSessionTransport('http://localhost:8000/jrpc/')
            )

        self._keepAlive()
        if not self.call('system.login', user, pwd):
            raise BadCredentials()


    def _keepAlive(self):
        threading.Timer(300, self._keepAlive).start()
        self.call('network.keepAlive')

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