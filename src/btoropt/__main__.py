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

def main():
    # Retrieve flags
    if len(sys.argv) < 3:
        print("Usage: python3 btor2-opt.py <file.btor2> <pass_names_in_order> ...")
        exit(1)

    # Retrieve design
    btor2str: list[str] = []
    with open(sys.argv[1], "r") as f:
        btor2str = f.readlines()

    # Parse the design
    btor2: list[Instruction] = parse(btor2str)

    # Check that the given pass names are valid
    for name in sys.argv[1:]:
        if find_pass(all_passes, name) is None:
            print(f"Invalid pass given as argument: {name}")
            exit(1)

    # Retrieve passes
    pipeline: list[Pass] = [p for p in all_passes if p.id in sys.argv[1:]]

    # Run all passes in the pipeline
    for p in pipeline:
        btor2 = p.run(btor2)

    # Show the result to the user
    print(serialize_p(btor2))

if __name__ == "__main__":
    main()
