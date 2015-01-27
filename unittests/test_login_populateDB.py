import os, sys, logging
print sys.path
sys.path.append(os.path.dirname(os.getcwd())+"/WebServices")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "website.settings")

from services.common import testing as db_tools


def _initDjangoDB():
    """
    This method populates the database with some information to be used
    only for this test suite.
    """
    #self.__verbose_testing = False
    username_1 = 'xabi'
    password_1 = 'pwdxabi'
    email_1 = 'xabi@aguarda.es'

    username_2 = 'marti'
    password_2 = 'pwdmarti'
    email_2 = 'marti@montederramo.es'

    db_tools.create_user_profile(
        username=username_1, password=password_1, email=email_1)
    db_tools.create_user_profile(
        username=username_2, password=password_2, email=email_2)

if __name__ == '__main__':
    _initDjangoDB()