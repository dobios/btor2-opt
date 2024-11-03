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

# Desugar modularity
# This requires replacing all module instances with their contracts
# Contracts are replaced by following the hoare triple pattern:
# - Module: Assume preconditions, check module, assert postconditions
# - Instance: Assert preconditions on set inputs, assume postconditions

from ..genericpass import Pass
from ...program import *

class ApplyContracts(Pass):
    def __init__(self):
        super().__init__("apply-contracts")

    # Replace an instance with either the inlined module or its applied contract
    # @param m: The module that contains the instance
    # @param i: The instance we want to replace
    # @param p: The entire program (used to identify modules and contracts by name)
    # @return the list of instructions that should take the instance's place
    def replaceInst(self, m: Module, i: Instance, p: Program) -> list[Instruction]:
        return None
    
    # Apply a contract to a module. This requires assuming preconditions on the module's inputs
    # Then asserting the postconditions at the end of the module
    # @param m: The module that will be wrapped
    # @param c: The contract associated to the module
    # @return a new module that has had its contract applied
    def wrapModuleWithContract(self, m: Module, c: Contract) -> Module:
        return None 

    def runOnProgram(self, p: Program) -> Program:
        # Iterate over all modules
        for i in range(0, len(p.modules)):
            m = p.modules[i]
            # The new module body
            res_m_body = []

            # Replace all instances in the module with a contract
            for inst in m.body:
                if isinstance(inst, Instance):
                    inst_ = self.replaceInst(m, inst, p)
                    res_m_body.append(inst_)
                else:
                    res_m_body.append(inst)
            m.body = res_m_body
                
            # Once all of the instances are replaced, wrap the module in its contract
            c = p.get_module_contract(m)
            if c is None:
                p.modules[i] = Module(m.name, res_m_body)
            else:
                p.modules[i] = self.wrapModuleWithContract(m, c)

        # After this no contracts should be left
        return Program(p.modules, [])

