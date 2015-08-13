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

#import sys, os
#from twisted.python import log

# sys.path.append(os.path.dirname(os.getcwd()) + "/server")
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "website.settings")
# from django.core import management
# from services.common.testing import helpers as db_tools
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../server")))

import sys, os
import unittest, mock, kiss

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


from sqlite3 import connect, PARSE_DECLTYPES
from datetime import date
from ampauth.users import Employees


from twisted.python import log
from twisted.cred import credentials
from twisted.cred.error import UnauthorizedLogin

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ampauth.testing import DjangoAuthChecker


class CredentialsChecker(unittest.TestCase):

    """
    Testing the server credentials handling
    """

    #@mock.patch.object(services.common.testing.helpers, 'create_user_profile')
    def _setUp_databases(self):
        """
        This method populates the database with some information to be used
        only for this test suite.
        """
        #self.__verbose_testing = False
        self.username = 'xabi.crespo'
        self.password = 'pwd4django'
        self.email = 'xabi@aguarda.es'

        self.wrongUser = 'wrongUser'
        self.wrongPass = 'wrongPass'

        """
        Test database.
        """
        connection = connect(':memory:', detect_types = PARSE_DECLTYPES)
        cursor = connection.cursor()

        cursor.execute('''create table users
                            (user text,
                            password text,
                            email text)''')

        cursor.execute('''insert into users
                            (user, password, email)
                        values (?, ?, ?)''', 
                            (self.username, self.password, self.email))

        self.connection = connection

    def setUp(self):
        log.startLogging(sys.stdout)

        log.msg(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Flushing database")
        #management.execute_from_command_line(['manage.py', 'flush', '--noinput'])
        
        log.msg(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Populating database")
        #management.execute_from_command_line(['manage.py', 'createsuperuser',\
        # '--username', 'crespum', '--email', 'crespum@humsat.org', '--noinput'])
        self._setUp_databases()
        
        log.msg(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Running tests")
        return

    """
    Log in with valid credentials. The server should return True
    """
    def test_GoodCredentials(self):

        creds = credentials.UsernamePassword(self.username, self.password)
        checker = DjangoAuthChecker()
        d = checker.requestAvatarId(creds, self.connection)

        self.connection.close()

        # def checkRequestAvatarCb(result):
        #     self.assertEqual(result.username, 'xabi.crespo')

        # d.addCallback(checkRequestAvatarCb)
        # return d

    """
    Log in with wrong username. The server should raise UnauthorizedLogin
    with 'Incorrect username' message
    """
    def test_BadUsername(self):

        creds = credentials.UsernamePassword(self.wrongUser, self.password)
        checker = DjangoAuthChecker()
        d = checker.requestAvatarId(creds, self.connection)

        self.connection.close()

        # return self.assertRaisesRegexp(UnauthorizedLogin, 'Incorrect username',\
        # checker.requestAvatarId, creds)
    
    """
    Log in with wrong password. The server should raise UnauthorizedLogin
    with 'Incorrect password' message
    """
    def test_BadPassword(self):

        creds = credentials.UsernamePassword(self.username, self.wrongPass)
        checker = DjangoAuthChecker()
        d = checker.requestAvatarId(creds, self.connection)

        self.connection.close()

        # def checkError(result):
        #     self.assertEqual(result.message, 'Incorrect password')
        # return self.assertFailure(d, UnauthorizedLogin).addCallback(checkError) 

if __name__ == '__main__':

    unittest.main()       