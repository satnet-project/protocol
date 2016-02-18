# coding=utf-8
import sys
import logging

from ampauth.server import *
from ampauth import misc
from twisted.python import log
from twisted.internet import reactor
from twisted.internet import ssl


def main(dataDict):

    logging.getLogger('SatNet protocol')
    log.startLogging(sys.stdout)

    CONNECTION_INFO = misc.get_configuration_local_file(
        settingsFile='.settings')

    pf = CredAMPServerFactory()

    sslContext = ssl.DefaultOpenSSLContextFactory(CONNECTION_INFO['serverkey'],
                                                  CONNECTION_INFO['publickey'])

    reactor.listenSSL(int(CONNECTION_INFO['port']), pf,
                      contextFactory=sslContext)
    log.msg('SatNet protocol running at', CONNECTION_INFO['name'])
    log.msg()
    reactor.run()

if __name__ == '__main__':

    try:
        if sys.argv[1] == '--debug':
            from twisted.internet import defer
            defer.setDebugging((True))

            dataDict = readData()
            main(dataDict)

        if sys.argv[1] == '--help':
            print "Help"
    except:
        dataDict = readData()
        main(dataDict)
