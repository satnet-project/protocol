# coding=utf-8
from tinyrpc.protocols.jsonrpc import JSONRPCProtocol
from tinyrpc.transports.http import HttpPostClientTransport
from tinyrpc.client import RPCClient
import requests
import json
from ampauth.errors import BadCredentials
from twisted.python import log


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

        r = self.s.post(self.endpoint, data=message,
                        headers={'content-type': 'application/json'})

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
    def __init__(self, user, pwd):
        self._rpc_client = RPCClient(
            JSONRPCProtocolFix(),
            HttpSessionTransport('http://localhost:8000/jrpc/'))

        if not self.call('system.login', user, pwd):
            raise BadCredentials()
            # For tests only!
        else:
            log.msg('Keep alive connection')
            # print "keepalive"
            # self.call('network.keepAlive')

    # def _keepAlive(self):
    #     threading.Timer(300, self._keepAlive).start() # set daemon to false
    #     self.call('network.keepAlive')

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


class Satnet_GetSlot(object):

    def __init__(self, slot_id):
        self._rpc_client = RPCClient(JSONRPCProtocolFix(),
                                     HttpSessionTransport(
                                        'http://localhost:8000/jrpc/')
                                     )

        self.slot = self.call('scheduling.slot.get', slot_id)

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


class Satnet_StoreMessage(object):
    """
    @rpc4django.rpcmethod(
        name='communications.storeMessage')

    This method stores a message that just been received by the protocol.

    :ivar slot_id:
        Identifier of the ongoing slot
    :type slot_id:
        L{String}

    :ivar upwards:
        Flag that indicates the direction of the message
    :type upwards:
        L{boolean}

    :ivar forwarded:
        Flag that indicates whether whis message has already been
        successfully forwarded to the other end of the communication or not
    :type forwarded:
        L{boolean}

    :ivar timestamp:
        Timestamp to log the time at which the message was received
    :type timestamp:
        L{int}

    :ivar message:
        Message received as a BASE64 string
    :type message:
        L{String}

    Return the identifier of the message within the system.
    """

    def __init__(self, slot_id, upwards, forwarded, timestamp, message):
        self._rpc_client_ = RPCClient(JSONRPCProtocolFix(),
                                      HttpSessionTransport(
                                        'http://localhost:8000/jrpc/'))

        hMessage = message.replace(":", "")
        bMessage = bytearray.fromhex(hMessage)

        self.call('communications.storeMessage', slot_id, upwards,
                  forwarded, timestamp, bMessage)

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

        return self._rpc_client_.call(call, args, None)


class Satnet_StorePassiveMessage(object):
    """
    @rpc4django.rpcmethod(
        name='communications.gs.storePassiveMessage')

    This method stores a mesage obtained in a passive manner (this is,
    without requiring from any remote operation to be scheduled) by a
    given groundstation in the database.

    :ivar groundstation_id:
        Identifier of the Groundstation
    :type groundstation_id:
        L{String}

    :ivar timestamp:
        Moment of the reception of the message at the remote
        Groundstation
    :type timestamp:
        L{int}

    :ivar doppler_shift:
        Doppler shif during the reception fo the message
    :type doppler_shift:
        L{float}

    :ivar message:
        The message to be stored
    :type message:
        L{String}

    Return 'true' if the message was correctly stored.
    """

    def __init__(self, groundstation_id, timestamp, doppler_shift, message):
        self._rpc_client = RPCClient(JSONRPCProtocolFix(),
                                     HttpSessionTransport(
                                        'http://localhost:8000/jrpc/'))

        self.call('communications.storePassiveMessage', slot_id,
                  upwards, forwarded, timestamp, message)

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
