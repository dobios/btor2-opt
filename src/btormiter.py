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

    try:
        completed_process = subprocess.run(
        btormc_command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
        )
    except FileNotFoundError:
        return("\nError: btormc was not found.Install Boolector separately and ensure btormc is in your path.")
    
    
    btormc_run_output = completed_process.stdout.decode("utf-8").strip()

    if btormc_run_output.startswith("sat"):
        return "\nThese 2 btor2 programs are NOT Equivalent."
        #print(btormc_run_output)  # keep btormc's counterexample
    else:
        return "\nThese 2 btor2 programs are Equivalent."

def check_equivalence(btor_filename1: str, btor_filename2: str, output_filename: str | None = None):
    # generate the btor miter
    btor_miter_circuit = create_btor_miter(
        btor_filename1,btor_filename2) 

    # extract the btor2 filenames without the extensions
    btor_name1 = Path(btor_filename1).stem
    btor_name2 = Path(btor_filename2).stem

    # if the user gave -o, use that filename instead of the combined pathnames as the miter circuit filename
    if output_filename is not None:
        miter_filename = Path(output_filename)
    
    else:
        # otherwise generate unique miter filename
        miter_filename = Path("tests/miter") / f"{btor_name1}_{btor_name2}_miter.btor2"
        
    # save generated miter circuit output in a btor2 file
    with open(miter_filename, "w") as file:
        file.write(serialize_p(btor_miter_circuit)) 

    # runs the equivalence check using btormc on the miter circuit
    # btormc should print equivalency check results and counterexample
    result = run_btormc(str(miter_filename))

    return btor_name1, btor_name2, result

def main():

    # check for optional flags - no hardcoded argument order
    run_btormc_flag = "--btormc" in sys.argv
    output_filename = None

    if "-o" in sys.argv:
        output_index = sys.argv.index("-o")

        # check if an true output filename was given
        if output_index + 1 >= len(sys.argv):
            print("Error: -o requires output filename to follow it.")
            sys.exit(1)
        output_filename = sys.argv[output_index + 1]

    # obtain actual input files from argument list - hardcoded order of input files relative to position of other flags
    input_files = []
    skip_not_file = False
    
    for arg in sys.argv[1:]:
        if skip_not_file:
            skip_not_file = False
            continue
        if arg == "--btormc":
            skip_not_file = False
            continue
        if arg == "-o":
            skip_not_file = True
            continue

        input_files.append(arg)

    # firrtl functionality: btormiter design.fir
    if len(input_files) == 1:

        p = create_miter(input_files[0])

        print(serialize_p(p))

        return

    # btor2 functionality: btormiter file1.btor2 file2.btor2
    if  len(input_files) == 2:

        btor_file1 = input_files[0]
        btor_file2 = input_files[1]

        # If the user wants to use btormc, generate miter and run      
        # equivalence checking
        if run_btormc_flag:

            btor_name1, btor_name2, result = check_equivalence(
                btor_file1,
                btor_file2,
                output_filename
            )
            print(
                f"\nEquivalence check for "
                f"{btor_name1} and {btor_name2}:"
            )
            print(result)
            
            return

        # Otherwise only generate the miter and tool used for 
        # equivalency check is up to user preference
        p = create_btor_miter(
            btor_file1,
            btor_file2
        )
        # Save miter circuit if -o is given
        if output_filename is not None:
            with open(output_filename, "w") as file:
                file.write(
                    serialize_p(p)
                )
        # Otherwise just print the generated miter
        else:
            print(serialize_p(p))

        return

    # error out for any other number of input files as invalid
    print(
        "Error:\nUsage:\n"
        "  btormiter <fir_design.fir>\n"
        "  btormiter <file1.btor2> <file2.btor2>\n"
        "  btormiter <file1.btor2> <file2.btor2> "
        "[-o <output_file.btor2>] [--btormc]"
    )

    sys.exit(1)

if __name__ == "__main__":
    main()
