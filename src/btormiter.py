##########################################################################
# BTOR2 parser, code optimizer, and circuit miter
# Copyright (C) 2024-2026  Amelia Dobis, Nidhi Lawange
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
import sys

def create_lec_assertion(out1: Instruction, out2: Instruction, base_lid: int) -> list[Instruction]:
    op1 = out1.operands[0]
    op2 = out2.operands[0]
    # second argument of Sort should be a string for the sort type
    sort = Sort(base_lid, "bitvec", 1)
    # second argument of Neq should not be a list
    neq = Neq(base_lid + 1, sort, op1, op2) 
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
    
    out2 = new_p2[-1]
    lec = create_lec_assertion(out1, out2, new_p2[-1].lid)

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
    
    
# Given 2 btor2 filenames, creates a miter circuit from the two outputs 
def create_btor_miter(btor_filename1: str, btor_filename2: str) -> list[Instruction]:
    with open(btor_filename1, "r") as file1:
        file1_text = file1.read()

    with open(btor_filename2, "r") as file2:
        file2_text = file2.read()

    p1 = parse(file1_text.splitlines())
    p2 = parse(file2_text.splitlines())

    return merge(p1, p2)


def main():

    # obtain actual input files from argument list - hardcoded order of input files relative to position of other flags
    in_files = []
    if "-o" in sys.argv:
        output_index = sys.argv.index("-o")

        if output_index + 1 >= len(sys.argv):
            print("Error: -o requires an output filename.")
            sys.exit(1)

    out_file = next(
    (
        sys.argv[i + 1]
        for i in range(len(sys.argv) - 1)
        if sys.argv[i] == "-o"
    ), None)

    in_files = [
    file
    for file in sys.argv[1:]
    if file != "-o" and file != out_file
    ]

    # firrtl functionality: btormiter design.fir
    if len(in_files) == 1 and in_files[0].endswith(".fir"):

        p = create_miter(in_files[0])

        print(serialize_p(p))

        return

    # btor2 functionality: btormiter file1.btor2 file2.btor2
    if  (len(in_files) == 2 and in_files[0].endswith(".btor2")
    and in_files[1].endswith(".btor2")):

        btor_file1 = in_files[0]
        btor_file2 = in_files[1]   

        # Otherwise only generate the miter and tool used for 
        # equivalency check is up to user preference
        p = create_btor_miter(
            btor_file1,
            btor_file2
        )
        # Save miter circuit if -o is given
        if out_file is not None:
            with open(out_file, "w") as file:
                file.write(serialize_p(p))
        # Otherwise just print the generated miter
        else:
            print(serialize_p(p))

        return

    # error out for any other number of input files as invalid
    print(
    "Usage:\n"
    "  btormiter <fir_design.fir>\n"
    "  btormiter <file1.btor2> <file2.btor2> "
    "[-o <output_file.btor2>]"
    )   

    sys.exit(1)

if __name__ == "__main__":
    main()
