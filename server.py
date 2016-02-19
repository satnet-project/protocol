# coding=utf-8

import sys
from ampauth.server import *
from twisted.python import log as tw_log
from twisted.internet import reactor
from twisted.internet import ssl

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
    Ricardo Tubío Pardavila (rtpardavila@gmail.com)
"""
__author__ = 'xabicrespog@gmail.com'


DEFAULT_SETTINGS_FILE = '.settings'


def read_configuration(cwd=None):
    """Read configuration
    This function reads the configuration file for the protocol.
    :param cwd: Path to the directory (String) where the settings file is
    :return: Dictionary with the pairs key, values as read from the file
    """

    configuration = {}
    settings_path = DEFAULT_SETTINGS_FILE

    if dir:
        settings_path = cwd + '/' + DEFAULT_SETTINGS_FILE

    import ConfigParser
    config = ConfigParser.ConfigParser()
    config.read(settings_path)

    configuration['server'] = config.get('protocol', 'host')
    configuration['port'] = config.get('protocol', 'port')
    configuration['name'] = config.get('protocol', 'name')
    configuration['serverkey'] = config.get('protocol', 'serverkey')
    configuration['publickey'] = config.get('protocol', 'publickey')

    return configuration


# noinspection PyUnresolvedReferences
def main(cwd=None):
    """Main program
    Function that creates the main execution environment for the protocol.
    :param cwd: Path to the directory (String) where the settings file is
    """
    tw_log.startLogging(sys.stdout)
    tw_log.msg('SatNet protocol starting...')

    configuration = read_configuration(cwd=cwd)
    tw_log.msg('>>> configuration = ' + str(configuration))

    reactor.listenSSL(
        int(configuration['port']),
        CredAMPServerFactory(),
        contextFactory=ssl.DefaultOpenSSLContextFactory(
            configuration['serverkey'],
            configuration['publickey']
        )
    )
    tw_log.msg('>>> SSL AMP Server configured, starting reactor...')
    reactor.run()

    tw_log.msg('>>> Twisted Reactor FINISHED')


if __name__ == '__main__':

    if sys.argv[1] == '--help':
        print "Help"
        exit()

    if sys.argv[1] == '--debug':

        from twisted.internet import defer
        defer.setDebugging(True)

    main()
