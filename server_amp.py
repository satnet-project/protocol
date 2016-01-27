# coding=utf-8
import sys
import logging

from ampauth.server import *
from twisted.python import log
from twisted.internet import reactor
from twisted.internet import ssl


def main():

    logging.getLogger('server')
    log.startLogging(sys.stdout)

    pf = CredAMPServerFactory()

    sslContext = ssl.DefaultOpenSSLContextFactory(
        'key/server.pem', 'key/public.pem'
    )

    reactor.listenSSL(1234, pf, contextFactory=sslContext)
    log.msg('Server running...')
    reactor.run()

if __name__ == '__main__':

    try:
        if sys.argv[1] == '--debug':
            from twisted.internet import defer
            defer.setDebugging((True))

            main()

        if sys.argv[1] == '--help':
            print "Help"
    except:
        main()
