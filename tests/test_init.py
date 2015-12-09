# coding=utf-8
import unittest
from twisted.python import log


"""
   Copyright 2015 Samuel Góngora García

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


class TestClientToServer(unittest.TestCase):

    def setUp(self):
        log.msg("Init test")

    def tearDown(self):
        pass

    def test_AMPPresentCorrectFrame(self):
        log.msg(">>>>>>>>>>>>>>>>> Running AMPpresentCorrectFrame test")


if __name__ == '__main__':
    unittest.main()
