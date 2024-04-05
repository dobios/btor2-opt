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

from program import *
from program import Instruction

# Base clas for compiler pass
# @param id: the unique name of this pass
class Pass:
    def __init__(self, id: str):
        self.id = id

    def run(p: list[Instruction]) -> list[Instruction]:
        return p

# Example pass: Simply renames all inputs to inp_<pos>
class RenameInputs(Pass):
    def __init__(self):
        super().__init__("rename-inputs")

    # I chose to have this pass not modify p in place
    # you can also simply modify p and return it
    def run(p: list[Instruction]) -> list[Instruction]:
        i = 0
        res = []
        for inst in p:
            if isinstance(inst, Input):
                res.append(Input(inst.lid, inst.sort, f"inp_{i}"))
                i += 1
            else:
                res.append(inst)
        return res
    
# Makes sure that all states are initialized
class InitAllStates(Pass):
    def __init__(self):
        super().__init__("init-all-states")

    def run(p: list[Instruction]) -> list[Instruction]:
        res = []
        # start by extracting all states
        states: list[Instruction] = [s for s in p if isinstance(s, State)]

        # Create def-use pairs for states + initializations
        state_inits = [(s, 
            next((op for op in p if (s.isin(op.operands) and isinstance(op, Init))), None)
        ) for s in states]

        # Extract all uninitialized states
        uninit_states = [s for (s, initop) in state_inits if initop is None]

        # Insert new inits where needed
        res = []
        lid = 1 # Keep track of lid
        for inst in p:
            if isinstance(inst, State):
                # Check if the state was initialized
                if inst.isin(uninit_states):
                    inst.lid = lid
                    lid += 1
                    res.append(inst)
                    # Initialize all states to 0
                    zero = Constd(lid, inst.operands[0], 0)
                    lid += 1
                    res.append(zero)
                    res.append(Init(lid, inst.operands[0], inst, zero))
                    lid += 1
                else:
                    # Update lid
                    inst.lid = lid
                    lid += 1
                    res.append(inst)
            else:
                # Update lid
                inst.lid = lid
                lid += 1
                res.append(inst)
        return res



# List containing all passes
all_passes = [RenameInputs(), InitAllStates()]

# Retrieves a pass from the list given an id
def find_pass(p: list[Pass], id: str) -> Pass:
    return next((e for e in p if e.id == id), None)
