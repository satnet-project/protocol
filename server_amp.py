# coding=utf-8
import sys
import logging
import ConfigParser

from ampauth.server import *
from twisted.python import log
from twisted.internet import reactor
from twisted.internet import ssl


def readData():
    dataDict = {}

    config = ConfigParser.ConfigParser()
    config.read('.settings')

    dataDict['server'] = config.get('protocol', 'host')
    dataDict['port'] = config.get('protocol', 'port')
    dataDict['serverkey'] = config.get('protocol', 'serverkey')
    dataDict['publickey'] = config.get('protocol', 'publickey')
    return dataDict


def main(dataDict):

    logging.getLogger('SatNet protocol')
    log.startLogging(sys.stdout)

    pf = CredAMPServerFactory()

    sslContext = ssl.DefaultOpenSSLContextFactory(dataDict['serverkey'],
                                                  dataDict['publickey'])

    reactor.listenSSL(int(dataDict['port']), pf, contextFactory=sslContext)
    log.msg('SatNet protocol running...')
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
        log.msg(dataDict)
        main(dataDict)
