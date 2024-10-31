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

# Abstract class for a compiler pass

from ..program import Instruction, Program, Module
import multiprocessing

# Base clas for compiler pass
# @param id: the unique name of this pass
class Pass:
    def __init__(self, id: str):
        self.id = id

    def run(self, p: list[Instruction]) -> list[Instruction]:
        return p
    
    # By default runs the standard pass in parallel on all modules
    def runOnProgram(self, p: Program) -> Program:
        pool = multiprocessing.Pool()
        f = lambda m : Module(m.name, self.run(m.body))
        p.modules = pool.map(f, p.modules)
        return p

