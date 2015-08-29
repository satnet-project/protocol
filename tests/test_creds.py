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


import sys, os
import unittest, mock

from unittest import TestCase

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from twisted.python import log

from ampauth.errors import BadCredentials
from rpcrequests import Satnet_RPC

class CredentialsChecker(unittest.TestCase):

    def _setUp_databases(self):

        self.username = 'xabi.crespo'
        self.password = 'pwd4django'
        self.email = 'xabi@aguarda.es'

    def setUp(self):
        log.startLogging(sys.stdout)

        log.msg(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Setting username")
        self._setUp_databases()

        return True

    """
    Log in with valid credentials. The server should return True
    """
    def test_GoodCredentials(self):

        log.msg(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Running GoodCrendentials test")

        """
        Mock object.
        """
        mockUserGoodCredentials = mock.Mock()
        mockUserGoodCredentials.username = 'xabi.crespo'
        mockUserGoodCredentials.password = 'pwd4django'

        @mock.patch('__main__.Satnet_RPC')
        def Satnet_RPC(self, sUsername, sPassword, debug=True):
            return True

        self.rpc = Satnet_RPC('xabi.crespo', mockUserGoodCredentials.password,\
         debug=True)

        log.msg(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> GoodCrendentials test ok!")

    """
    Log in with wrong username. The server should raise BadCredentials
    with 'Incorrect username' message.
    """
    def test_BadUsername(self):

        log.msg(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Running BadUsername test")

        """
        Mock object.
        """
        mockUserBadUsername = mock.Mock()
        mockUserBadUsername.username = 'wrongUser'
        mockUserBadUsername.password = 'pwd4django'

        @mock.patch('__main__.Satnet_RPC')
        def Satnet_RPC(self, sUsername, sPassword, debug=True):
            raise BadCredentials("Incorrect username")    

        log.msg(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> BadUsername test ok!")

        return self.assertRaisesRegexp(BadCredentials, 'Incorrect username',\
         Satnet_RPC, mockUserBadUsername.username, mockUserBadUsername.password,\
          debug=True)

    """
    Log in with wrong password. The server should raise BadCredentials
    with 'Incorrect password' message.
    """
    def test_BadPassword(self):

        log.msg(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Running BadPassword test")

        """
        Mock object.
        """
        mockUserBadPassword = mock.Mock()
        mockUserBadPassword.username = 'xabi.crespo'
        mockUserBadPassword.password = 'wrongPass'

        @mock.patch('__main__.Satnet_RPC')
        def Satnet_RPC(self, sUsername, sPassword, debug=True):
            raise BadCredentials("Incorrect password")

        log.msg(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> BadPassword test ok!")

        return self.assertRaisesRegexp(BadCredentials, 'Incorrect password',\
         Satnet_RPC, mockUserBadPassword.username, mockUserBadPassword.password,\
          debug=True)


if __name__ == '__main__':

    unittest.main()       