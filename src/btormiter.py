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

from btoropt.program import *
from btoropt.parser import *
import os
import subprocess
import sys

def create_lec_assertion(out1: Instruction, out2: Instruction, base_lid: int) -> list[Instruction]:
    op1 = out1.operands[0]
    op2 = out2.operands[0]
    sort = Sort(base_lid, 1)
    neq = Neq(base_lid + 1, [sort, op1, op2])
    bad = Bad(base_lid + 2, neq)
    return [sort, neq, bad]

def merge(p1: list[Instruction], p2: list[Instruction]) -> list[Instruction]:
    # Start by extracting the inputs
    inputs: list[Instruction] = []
    for op in p1:
        if isinstance(op, Input):
            inputs.append(op)
    # Extract outputs (assume only 1 output per design at end of file)
    out1 = p1[len(p1) - 1]

    # Then reconstruct p2 without inputs and with an offset lid
    new_p2 = []
    cur_lid = len(p1) # don't count the output of p1
    for op in p2:
        if not isinstance(op, Input):
            op.move(cur_lid)
            cur_lid += 1
            new_p2.append(op)
        # Update input lids in operands
        for oper in op.operands:
            if isinstance(oper, Input):
                if oper.isin(inputs):
                    oper = next(inp for inp in inputs if inp.eq(oper))
    out2 = p2[len(new_p2) - 1]

    lec = create_lec_assertion(out1, out2, new_p2[len(new_p2) - 1].lid)

    # Remove outputs
    p1.pop()
    new_p2.pop()

    return p1 + new_p2 + lec # merge everything

# Given a firrtl design filename, creates a miter circuit from the two outputs of sfc and circt
def create_miter(fir_filename: str) -> list[Instruction]:

    if os.path.exists("tmp.btor2"):
        os.remove("tmp.btor2")

    # Run it through the SFC and store the output
    os.system(f"firrtl --compiler sverilog -E btor2 -i {fir_filename} -o tmp.btor2")
    sfc_p = ""
    with open("tmp.btor2", "r") as file:
        sfc_p = file.read()

    # Run the FIRRTL design through firtool
    circt_p = subprocess.run(f"firtool --btor2 {fir_filename}", stdout=subprocess.PIPE).stdout.decode('utf-8')

    # Parse both files
    p1 = parse(sfc_p)
    p2 = parse(circt_p)

    # Create the miter circt
    return merge(p1, p2)

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 btor-miter.py <fir_design.fir>")

    p = create_miter(sys.argv[1])
    print(serialize_p(p))

if __name__ == "__main__":
    main()
