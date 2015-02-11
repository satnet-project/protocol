from twisted.trial import unittest
from twisted.cred import credentials
from ampauth.credentials import DjangoAuthChecker
from twisted.cred.error import UnauthorizedLogin


class CredentialsChecker(unittest.TestCase):

    """
    Testing the server credentials handling
    """
    """
    Log in with valid credentianls. The server should return True
    """

        def test_GoodCredentials(self):
            creds = credentials.UsernamePassword('xabi.crespo', 'pwd4django')
            checker = DjangoAuthChecker()
            d = checker.requestAvatarId(creds)

            def checkRequestAvatarCb(result):
                self.assertEqual(result.username, 'xabi.crespo')
            d.addCallback(checkRequestAvatarCb)
            return d
    """
    Log in with wrong username. The server should raise UnauthorizedLogin
    with 'Incorrect username' message
    """

        def test_BadUsername(self):
            creds = credentials.UsernamePassword('wrongUser', 'pwd4django')
            checker = DjangoAuthChecker()
            try:
                d = checker.requestAvatarId(creds)
            except UnauthorizedLogin, e:
                return self.assertEqual(e.message, 'Incorrect username')
    """
    Log in with wrong password. The server should raise UnauthorizedLogin
    with 'Incorrect password' message
    """

        def test_BadPassword(self):
            creds = credentials.UsernamePassword('xabi.crespo', 'wrongPass')
            checker = DjangoAuthChecker()
            d = checker.requestAvatarId(creds)

            def checkError(result):
                self.assertEqual(result.message, 'Incorrect password')
            return self.assertFailure(d, UnauthorizedLogin).addCallback(checkError)
