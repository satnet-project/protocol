# coding=utf-8
from ampauth.server import CredAMPServerFactory
from ampauth import misc

from twisted.application import service
from twisted.internet import ssl, reactor

from os import path

workingDir = path.dirname(path.realpath(__file__))

CONNECTION_INFO = misc.get_configuration_local_file(str(workingDir) + '/.settings')

application = service.Application('satnetProtocol')
pf = CredAMPServerFactory()

sslContext = ssl.DefaultOpenSSLContextFactory(str(workingDir) + '/' + CONNECTION_INFO['serverkey'], str(workingDir) + '/' + CONNECTION_INFO['publickey'])

reactor.listenSSL(int(CONNECTION_INFO['port']), pf, contextFactory=sslContext)

