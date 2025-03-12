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

# Example pass: Simply renames all inputs to inp_<pos>

from ...passes.genericpass import Pass
from ...program import Instruction, Input

class RenameInputs(Pass):
    def __init__(self):
        super().__init__("rename-inputs")

    # I chose to have this pass not modify p in place
    # you can also simply modify p and return it
    def run(self, p: list[Instruction]) -> list[Instruction]:
        i = 0
        res = []
        for inst in p:
            if isinstance(inst, Input):
                res.append(Input(inst.lid, inst.sort, f"inp_{i}"))
                i += 1
            else:
                res.append(inst)
        return res
