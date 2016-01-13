# coding=utf-8

from ampauth.server import CredAMPServerFactory

from twisted.application import service
from twisted.internet import ssl, reactor

"""
     Copyright 2016 Samuel Góngora García

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
    Samuel Góngora García (s.gongoragarcia@gmail.com)
"""
__author__ = 's.gongoragarcia@gmail.com'


application = service.Application('satnetProtocol')
# internet.TCPServer(5280, site).setServiceParent(application)

pf = CredAMPServerFactory()

sslContext = ssl.DefaultOpenSSLContextFactory(
        'key/server.pem', 'key/public.pem')

reactor.listenSSL(1234, pf, contextFactory=sslContext)
reactor.run()
