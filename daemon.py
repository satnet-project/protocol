# coding=utf-8

from twisted.application import service
from twisted.internet import reactor
from twisted.internet import ssl
from twisted.python import log as tw_log
import ConfigParser
from os import path as os_path
from ampauth import server as amp_server
import sys
import pytz

"""
   Copyright 2015, 2015 Xabier Crespo Álvarez

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

DEFAULT_SETTINGS_FILE = '.settings'


def read_configuration():
    """Read configuration
    This function reads the configuration file for the protocol.
    :return: Dictionary with the pairs key, values as read from the file
    """
    settings_path = DEFAULT_SETTINGS_FILE

    if dir:
        settings_path = cwd + '/' + DEFAULT_SETTINGS_FILE

    config = ConfigParser.ConfigParser()
    config.read(settings_path)

    return {
        'server': config.get('protocol', 'host'),
        'port': config.get('protocol', 'port'),
        'name': config.get('protocol', 'name'),
        'serverkey': config.get('protocol', 'serverkey'),
        'publickey': config.get('protocol', 'publickey')
    }

application = service.Application('satnetProtocol')
# tw_log.startLogging(sys.stdout)
tw_log.msg('SatNet protocol starting...')

cwd = os_path.dirname(os_path.realpath(__file__))
tw_log.msg('>>> cwd = ' + str(cwd))
configuration = read_configuration()
tw_log.msg('>>> configuration = ' + str(configuration))

configuration['serverkey'] = cwd + '/' + configuration['serverkey']
configuration['publickey'] = cwd + '/' + configuration['publickey']

tw_log.msg(configuration['serverkey'])
tw_log.msg(configuration['publickey'])

# noinspection PyUnresolvedReferences
reactor.listenSSL(
    int(configuration['port']),
    amp_server.CredAMPServerFactory(),
    contextFactory=ssl.DefaultOpenSSLContextFactory(
        configuration['serverkey'], configuration['publickey']
    )
)
tw_log.msg('>>> SSL AMP Server configured, starting reactor...')

# noinspection PyUnresolvedReferences
# reactor.run()
