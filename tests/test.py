##########################################################################
# BTOR2 parser, code optimizer, and circuit miter
# Copyright (C) 2024-2025  Amelia Dobis
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
from src.btoropt.modparser import *

def parsewrapper (filepath):
    btor2str: list[str] = []
    with open(filepath, "r") as f:
        btor2str = f.readlines()
    return btor2str

def reduce_p_str(p_str: list[str]) -> str:
    return reduce(lambda acc, s: acc + s + "\n", p_str, "")

class BTORTestParser(unittest.TestCase):
    """Check whether BTOR interface is working properly"""
     
    # Checks that a btor2 file produced by yosys can be parsed
    def test_standard(self):
        prgm = parse(parsewrapper("tests/btor/reg_en.btor"))

        self.assertEqual(prgm[0].inst, "sort")
        self.assertEqual(prgm[1].inst, "input")
        self.assertEqual(len(prgm), 22)

        print("test passed")

    # Checks that a single btor2 instruction can be parsed
    def test_basic(self):
        p = parse(["1 sort bitvector 1"])
        self.assertEqual(p[0].inst, "sort")
        self.assertEqual(len(p), 1)

        print("test basic passed")

    # Checks that a simple btor2 model can be parsed
    def test_simple(self):
        p = parse([ \
            "1 sort bitvector 1", \
            "2 input 1 a", \
            "3 const 1 1", \
            "4 or 1 2 3", \
            "5 eq 1 2 3", \
            "6 not 1 5", \
            "7 bad 6" \
        ])
        self.assertEqual(p[0].inst, "sort")
        self.assertEqual(len(p), 7)

        print("test simple passed")

    # Checks that both par and simple parse the same
    def test_deferred_serial(self):
        s = [ \
            "1 sort bitvector 1", \
            "2 input 1 a", \
            "3 const 1 1", \
            "4 or 1 2 3", \
            "5 eq 1 2 3", \
            "6 not 1 5", \
            "7 bad 6" \
        ]
        par_p = parse(s, deferred=True)

        self.assertEqual(serialize_p(par_p), reduce_p_str(s))

        print("test serilaization passed")

    # Checks that both par and simple parse the same
    def test_diff(self):
        s = [ \
            "1 sort bitvector 1", \
            "2 input 1 a", \
            "3 const 1 1", \
            "4 or 1 2 3", \
            "5 eq 1 2 3", \
            "6 not 1 5", \
            "7 bad 6" \
        ]
        seq_p = parse(s)
        par_p = parse(s, deferred=True)
        
        self.assertEqual(len(seq_p), len(par_p))   
        for i in range(len(seq_p)):
            self.assertEqual(seq_p[i], par_p[i])

        print("differential test passed")


    # def test_modular(self):
    #         p: Program = parse_file(parsewrapper("tests/btor/modular.btor"))
    #         self.assertIsNotNone(p)

    #         self.assertEqual(len(p.modules), 2)
    #         self.assertEqual(len(p.contracts), 1)
    #         ma = p.get_module("A")
    #         ca = p.get_contract("A")
    #         self.assertIsNotNone(ca)
    #         c = p.get_module_contract(ma)
    #         self.assertIsNotNone(c)
    #         self.assertEqual(c, ca)
    #         self.assertEqual(c.name, "A")

if __name__ == '__main__':
    unittest.main()
