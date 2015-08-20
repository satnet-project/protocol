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

from ampauth.testing import DjangoAuthChecker


class CredentialsChecker(unittest.TestCase):

    """
    Testing the server credentials handling
    """

    def _setUp_databases(self):

        self.username = 'xabi.crespo'
        self.password = 'pwd4django'
        self.email = 'xabi@aguarda.es'

        """
        Test database.
        """

        column = ['id', 'username', 'first_name', 'last_name', 'email',\
         'password', 'groups', 'user_permissions', 'is_staff', 'is_active',\
          'is_superuser', 'last_login', 'date_joined']

        _type = 'INTEGER'
        _typetext = 'INTEGER'
        _datetimetype = 'TEXT'

        connection = connect('test.db', detect_types = PARSE_DECLTYPES)

        connection.execute('CREATE TABLE {tn} ({nf} {ft}) '\
                            .format(tn='auth_user', nf=column[0], ft=_type))

        connection.execute("ALTER TABLE {tn} ADD COLUMN '{cn}' {ct}"\
                            .format(tn='auth_user', cn=column[1], ct=_typetext))

        connection.execute("ALTER TABLE {tn} ADD COLUMN '{cn}' {ct}"\
                            .format(tn='auth_user', cn=column[2], ct=_typetext))

        connection.execute("ALTER TABLE {tn} ADD COLUMN '{cn}' {ct}"\
                            .format(tn='auth_user', cn=column[3], ct=_typetext))

        connection.execute("ALTER TABLE {tn} ADD COLUMN '{cn}' {ct}"\
                            .format(tn='auth_user', cn=column[4], ct=_typetext))

        connection.execute("ALTER TABLE {tn} ADD COLUMN '{cn}' {ct}"\
                            .format(tn='auth_user', cn=column[5], ct=_typetext))

        connection.execute("ALTER TABLE {tn} ADD COLUMN '{cn}' {ct}"\
                            .format(tn='auth_user', cn=column[6], ct=_typetext))

        connection.execute("ALTER TABLE {tn} ADD COLUMN '{cn}' {ct}"\
                            .format(tn='auth_user', cn=column[7], ct=_typetext))

        connection.execute("ALTER TABLE {tn} ADD COLUMN '{cn}' {ct}"\
                            .format(tn='auth_user', cn=column[8], ct=_typetext))

        connection.execute("ALTER TABLE {tn} ADD COLUMN '{cn}' {ct}"\
                            .format(tn='auth_user', cn=column[9], ct=_typetext))

        connection.execute("ALTER TABLE {tn} ADD COLUMN '{cn}' {ct}"\
                            .format(tn='auth_user', cn=column[10], ct=_typetext))

        connection.execute("ALTER TABLE {tn} ADD COLUMN '{cn}' {ct}"\
                            .format(tn='auth_user', cn=column[11], ct=_typetext))

        connection.execute("ALTER TABLE {tn} ADD COLUMN '{cn}' {ct}"\
                            .format(tn='auth_user', cn=column[12], ct=_datetimetype))

        self.connection = connection

    def setUp(self):
        log.startLogging(sys.stdout)

        log.msg(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Setting database")
        self._setUp_databases()

        return

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

        creds = credentials.UsernamePassword(self.username, self.password)
        checker = DjangoAuthChecker()
        d = checker.requestAvatarId(creds, mockUserGoodCredentials, 'test.db')

        def checkRequestAvatarCb(result):
            self.assertEqual(result.username, self.username)

        d.addCallback(checkRequestAvatarCb)
        return d

        log.msg(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> GoodCrendentials test ok!")


    """
    Log in with wrong username. The server should raise UnauthorizedLogin
    with 'Incorrect username' message
    """
    def test_BadUsername(self):

        log.msg(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Running BadUsername test")

        """
        Mock object.
        """
        mockUserBadUsername = mock.Mock()
        mockUserBadUsername.username = 'wrongUser'
        mockUserBadUsername.password = 'pwd4django'

        creds = credentials.UsernamePassword(self.username, self.password)
        checker = DjangoAuthChecker()

        return self.assertRaisesRegexp(UnauthorizedLogin, 'Incorrect username',\
        checker.requestAvatarId, creds, mockUserBadUsername, 'test.db')

        log.msg(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> BadUsername test ok!")

    """
    Log in with wrong password. The server should raise UnauthorizedLogin
    with 'Incorrect password' message
    """
    # def test_BadPassword(self):

    #     """
    #     Mock object.
    #     """
    #     mockUserBadPassword = mock.Mock()
    #     mockUserBadPassword.username = 'xabi.crespo'
    #     mockUserBadPassword.password = 'wrongPass'

    #     creds = credentials.UsernamePassword(self.username, self.password)
    #     checker = DjangoAuthChecker()
    #     d = checker.requestAvatarId(creds, mockUserBadPassword)

    #     self.connection.close()

    #     def checkError(result):
    #         self.assertEqual(result.message, 'Incorrect password')
    #     return self.assertFailure(d, UnauthorizedLogin).addCallback(checkError)

    def tearDown(self):

        try:
            self.connection.close()
            os.remove('test.db')
            log.msg(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Deleting database")
        except:
            pass 


if __name__ == '__main__':

    unittest.main()       