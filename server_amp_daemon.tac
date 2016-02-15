# coding=utf-8
from ampauth.server import CredAMPServerFactory

from twisted.application import service
from twisted.internet import ssl, reactor

from ConfigParser import ConfigParser

from os import path

dataDict = {}

config = ConfigParser()

workingDir = path.dirname(path.realpath(__file__))

config.read(str(workingDir) + '/.settings')

dataDict['server'] = config.get('protocol', 'host')
dataDict['port'] = config.get('protocol', 'port')
dataDict['name'] = config.get('protocol', 'name')
dataDict['serverkey'] = config.get('protocol', 'serverkey')
dataDict['publickey'] = config.get('protocol', 'publickey')

application = service.Application('satnetProtocol')
pf = CredAMPServerFactory()

sslContext = ssl.DefaultOpenSSLContextFactory(str(workingDir) + '/' + dataDict['serverkey'], str(workingDir) + '/' + dataDict['publickey'])

reactor.listenSSL(int(dataDict['port']), pf, contextFactory=sslContext)

