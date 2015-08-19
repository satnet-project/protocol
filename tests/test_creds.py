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
import unittest, mock, kiss

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlite3 import connect, PARSE_DECLTYPES
from datetime import date

from twisted.python import log
from twisted.cred import credentials
from twisted.cred.error import UnauthorizedLogin

from ampauth.testing import DjangoAuthChecker, UserModel


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

        column = ['username', 'first_name', 'last_name', 'email', 'password',\
         'groups', 'user_permissions', 'is_staff', 'is_active',\
          'is_superuser', 'last_login', 'date_joined']


        first_type = 'INTEGER'
        second_type = 'INTEGER'
        third_type = 'INTEGER'
        forth_type = 'INTEGER'
        forth_type = 'INTEGER'

        _type = 'INTEGER'
        _datetimetype = 'TEXT'


        # connection = connect(':memory:', detect_types = PARSE_DECLTYPES)
        connection = connect('test.db', detect_types = PARSE_DECLTYPES)


        connection.execute('CREATE TABLE {tn} ({nf} {ft}) '\
                            .format(tn='auth_user', nf=column[0], ft=_type))

        connection.execute("ALTER TABLE {tn} ADD COLUMN '{cn}' {ct}"\
                            .format(tn='auth_user', cn=column[1], ct=_type))

        connection.execute("ALTER TABLE {tn} ADD COLUMN '{cn}' {ct}"\
                            .format(tn='auth_user', cn=column[2], ct=_type))

        connection.execute("ALTER TABLE {tn} ADD COLUMN '{cn}' {ct}"\
                            .format(tn='auth_user', cn=column[3], ct=_type))

        connection.execute("ALTER TABLE {tn} ADD COLUMN '{cn}' {ct}"\
                            .format(tn='auth_user', cn=column[4], ct=_type))

        connection.execute("ALTER TABLE {tn} ADD COLUMN '{cn}' {ct}"\
                            .format(tn='auth_user', cn=column[5], ct=_type))

        connection.execute("ALTER TABLE {tn} ADD COLUMN '{cn}' {ct}"\
                            .format(tn='auth_user', cn=column[6], ct=_type))

        connection.execute("ALTER TABLE {tn} ADD COLUMN '{cn}' {ct}"\
                            .format(tn='auth_user', cn=column[7], ct=_type))

        connection.execute("ALTER TABLE {tn} ADD COLUMN '{cn}' {ct}"\
                            .format(tn='auth_user', cn=column[8], ct=_type))

        connection.execute("ALTER TABLE {tn} ADD COLUMN '{cn}' {ct}"\
                            .format(tn='auth_user', cn=column[9], ct=_type))

        connection.execute("ALTER TABLE {tn} ADD COLUMN '{cn}' {ct}"\
                            .format(tn='auth_user', cn=column[10], ct=_type))

        connection.execute("ALTER TABLE {tn} ADD COLUMN '{cn}' {ct}"\
                            .format(tn='auth_user', cn=column[11], ct=_datetimetype))


        contact = UserModel(user_name='xabi.crespo', password='pwd4django')

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
        d = checker.requestAvatarId(creds)

        self.connection.close()

        # def checkRequestAvatarCb(result):
        #     self.assertEqual(result.username, 'xabi.crespo')

        # d.addCallback(checkRequestAvatarCb)
        # return d

        os.rm('test.db')

    """
    Log in with wrong username. The server should raise UnauthorizedLogin
    with 'Incorrect username' message
    """
    # def test_BadUsername(self):

        # creds = credentials.UsernamePassword(self.wrongUser, self.password)
        # checker = DjangoAuthChecker()
        # d = checker.requestAvatarId(creds, self.connection)

        # self.connection.close()

        # return self.assertRaisesRegexp(UnauthorizedLogin, 'Incorrect username',\
        # checker.requestAvatarId, creds)
    
    """
    Log in with wrong password. The server should raise UnauthorizedLogin
    with 'Incorrect password' message
    """
    # def test_BadPassword(self):

        # creds = credentials.UsernamePassword(self.username, self.wrongPass)
        # checker = DjangoAuthChecker()
        # d = checker.requestAvatarId(creds, self.connection)

        # self.connection.close()

        # def checkError(result):
        #     self.assertEqual(result.message, 'Incorrect password')
        # return self.assertFailure(d, UnauthorizedLogin).addCallback(checkError) 

if __name__ == '__main__':

    unittest.main()       