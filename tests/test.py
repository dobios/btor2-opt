
##########################################################################
# BTOR2 parser, code optimizer, and circuit miter
# Copyright (C) 2024  Amelia Dobis
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
##########################################################################

import unittest

from src.btoropt.parser import *

def parsewrapper (filepath):
    btor2str: list[str] = []
    with open(filepath, "r") as f:
        btor2str = f.readlines()
    return btor2str

class BTORTest(unittest.TestCase):
    """Check whether BTOR interface is working properly"""

    def test_btor1(self):
        prgm = parse(parsewrapper("tests/btor/reg_en.btor"))

        self.assertEqual(prgm[0].inst, "sort")
        self.assertEqual(prgm[1].inst, "input")
        self.assertEqual(len(prgm), 22)

        print("test passed")


if __name__ == '__main__':
    unittest.main()
