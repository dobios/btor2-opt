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

from ...passes.genericpass import Pass
from ...program import Instruction

# Rewrites all lids to be in instruction order
class CheckLidOrdering(Pass):
    def __init__(self):
        super().__init__("check-lid-ordering")

    def run(self, p: list[Instruction]) -> list[Instruction]:
        res = []

        for i in range(len(p)):
            inst = p[i]
            inst.lid = i
            res.append(inst)

        return res
