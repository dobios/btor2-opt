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

from .program import *
from .passes.allpasses import *
from .parser import *
import sys

options = ["modular"]

def main():
    # Retrieve flags
    if len(sys.argv) < 3:
        print("Usage: btoropt [optional](--modular) <file.btor2> <pass_names_in_order> ...")
        exit(1)

    # Check options
    base = 1
    modular = False
    
    # NOTE: This if should be a while if you want to introduce more than one option
    if "--" in sys.argv[base].strip():
        option = sys.argv[base].strip().strip("--")
        if option not in options:
            print(f"Invalid option given: {option}")
            exit(1)
        modular = True
        base += 1
        

    # Retrieve design
    btor2str: list[str] = []
    with open(sys.argv[base], "r") as f:
        btor2str = f.readlines()

    # Parse the design
    btor2 = None
    if modular:
        btor2 = parse_file(btor2str)
    else:
        btor2 = parse(btor2str)
    
    assert btor2 is not None

    # Fetch the pass names
    pass_base = base + 1
    pass_names = sys.argv[pass_base:]

    # Check that the given pass names are valid
    for name in pass_names:
        if find_pass(all_passes, name) is None:
            print(f"Invalid pass given as argument: {name}")
            exit(1)

    # Retrieve passes
    pipeline: list[Pass] = [p for p in all_passes if p.id in pass_names]

    # Run all passes in the pipeline
    for p in pipeline:
        if modular: 
            btor2 = p.runOnProgram(btor2)
        else:
            btor2 = p.run(btor2)

    # Show the result to the user
    if(modular):
        print(serialize_p(btor2))
    else:
        print("Success")

if __name__ == "__main__":
    main()
