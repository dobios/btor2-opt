##########################################################################
# BTOR2 parser, code optimizer, and circuit miter
# Copyright (C) 2026  Amelia Dobis, Nidhi Lawange
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
from pathlib import Path

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

def run_btormc(miter_filename: str):
    btormc_command = ["btormc", miter_filename]

    completed_process = subprocess.run(
    btormc_command,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
    )

    btormc_run_output = completed_process.stdout.decode("utf-8").strip()

    if btormc_run_output.startswith("sat"):
        return "\nThese 2 btor2 programs are NOT Equivalent."
        #print(btormc_run_output)  # keep btormc's counterexample
    else:
        return "\nThese 2 btor2 programs are Equivalent."

def check_equivalence(btor_filename1: str, btor_filename2: str):
    # 2 arguments for the create_miter() function
    btor_miter_circuit = create_btor_miter(btor_filename1,btor_filename2) 

    # extract the btor2 filenames without the extensions
    btor_name1 = Path(btor_filename1).stem
    btor_name2 = Path(btor_filename2).stem

    # if the user gave -o, use that filename instead of the combined pathnames as the miter circuit filename
    if output_filename is not None:
        miter_filename = Path(output_filename)
    
    else:
        # then combine those extracted filenames to obtain a unique miter circuit btor2 filename - so each unique pair of btor equivalency checks can be saved
        miter_filename = Path("tests/miter") / f"{btor_name1}_{btor_name2}_miter.btor2"
        
    # now, adding in the automation workflow which should generate the miter circuit, save that output to a miter circuit btor2 file, run btormc on that btor miter circuit file, and produce the equivalent/non-equivalent printed results automatically to the user, all using btor_automated.py functions
    with open(miter_filename, "w") as file:
        file.write(serialize_p(btor_miter_circuit)) # saves the miter circuit output in a btor2 file

    # runs the equivalence check using btormc on the miter circuit
    # btormc should print equivalency check results and counterexample
    result = run_btormc(str(miter_filename))

    return btor_name1, btor_name2, result

def main():
    # requires only the firrtl functionality
    # btormiter design.fir
    if len(sys.argv) == 2:
        p = create_miter(sys.argv[1])
        print(serialize_p(p))
        return
    
    # Requires only one pair of BTOR2 files
    # btormiter file1.btor2 file2.btor2 -o out.btor2 [len = 5]
    if len(sys.argv) == 5 and sys.argv[3] == "-o":

        btor_file1 = sys.argv[1]
        btor_file2 = sys.argv[2]
        output_filename = sys.argv[4]

        p = create_btor_miter(
            btor_file1,
            btor_file2
        )

        with open(output_filename, "w") as file:
            file.write(serialize_p(p))

        return
    
    # btor2 pair mode:
    # btormiter file1.btor2 file2.btor2 OR
    # btormiter file1.btor2 file2.btor2
    #           file3.btor2 file4.btor2...

    # Must have at least one pair and an even number of BTOR2 files
    if len(sys.argv) >= 3 and (len(sys.argv) - 1) % 2 == 0:

        # Move through command-line arguments two at a time, inherently making every two btor2 files as one equivalence-check pair - skip every 2 when iterating bc last 2 files taken into account per iteration
        for i in range(1, len(sys.argv), 2):

            btor_file1 = sys.argv[i]
            btor_file2 = sys.argv[i + 1]

            p = create_btor_miter(
                btor_file1,
                btor_file2
            )

            print(
                f"\nMiter for {btor_file1} "
                f"and {btor_file2}:"
            )

            print(serialize_p(p))

        return

    # in case control is not taken to any of the above branches, an invalid command has been sent:
    print(
        "Error:\nUsage:\n"
        "  btormiter <fir_design.fir>\n"
        "  btormiter <file1.btor2> <file2.btor2> "
        "[<file3.btor2> <file4.btor2> ...]\n"
        "  btormiter <file1.btor2> <file2.btor2> "
        "-o <output_file.btor2>"
    )

    sys.exit(1)

if __name__ == "__main__":
    main()
