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

from functools import reduce

# All supported btor2 instruction tags
tags = ["sort","input", "output", "bad", "constraint", "zero",
        "one", "ones", "constd", "consth", "const", "state",
        "init", "next", "slice", "ite", "implies", "iff",
        "add", "sub", "mul", "sdiv", "udiv", "smod", "sll",
        "srl", "sra", "and", "or", "xor", "concat", 
        # Unary operations
        "not", "inc", "dec", "neg", "redor", "redxor", "redand",
        "eq", "neq", "ugt", "sgt", "ugte", "sgte", "ult",
        "slt", "ulte", "slte", "uext", "sext"]

# All legal sort types
sort_tags = ["bitvector", "bitvec", "array"]

# All custom tags
custom_tags = ["inst", "set", "ref", "prec", "post"]
structure_tags = ["module", "contract"]

# Base class for an instruction
# @param lid: the line identifier of the instruction
# @param inst: the string litteral keyword for the instruction
# @param operands: the list of operands given to this instruction,
# these must also be instructions
# @param is_standard: whether or not the instruction is part of the btor2
#   True: instruction is part of the btor2 spec
#   False: instruction is a custom extension for btor-opt
class Instruction:
    def __init__(self, lid: int, inst: str, operands = [], is_standard=True):
        self.lid = lid
        self.inst = inst
        self.operands = operands
        self.is_standard = is_standard

    def move_up(self, amount: int):
        self.lid += amount

    def move_down(self, amount: int):
        self.lid -= amount

    def move(self, lid: int):
        self.lid = lid

    def eq(self, inst) -> bool:
        return self.operands == inst.operands and self.inst == inst.inst

    def isin(self, p) -> bool:
        for inst in p:
            if self.eq(inst):
                return True
        return False

    def serialize(self) -> str:
        assert all([isinstance(op, Instruction) or isinstance(op, int) for op in self.operands]), \
            "Operands must be instructions or integers, fails for operands: %d." % self.operands
        return str(self.lid) + " " + self.inst + " " + \
            ' '.join([(str(op.lid) if isinstance(op, Instruction) else str(op)) + " " \
                      for op in self.operands ])

def serialize_p(p: list[Instruction]) -> str:
    return reduce(lambda acc, s: acc + s.serialize() + "\n", p, "")

# Extracts an instruction from a given program
def get_inst(p: list[Instruction], lid: int) -> Instruction:
    ops = [op for op in p if op.lid == lid]
    if len(ops) > 0:
        return ops[0]
    return None

# Sort declaration instruction
# e.g. 1 sort bitvector 32
# @param type: {bitvector | bitvec | array}, the type of sort we are declaring
# @param width: the width of the declared sort
class Sort(Instruction):
    def __init__(self, lid: int, typ: str, width: int):
        super().__init__(lid, "sort", [])
        self.typ: str = typ
        self.width: int = width

    def eq(self, inst) -> bool:
        return super().eq(inst) and self.typ == inst.typ and self.width == inst.width

    def serialize(self) -> str:
        return super().serialize() + self.typ + " " + str(self.width)

# Input instruction: declares an input
# @param sort: the sort defining the type of this input
# @param name: the string name of the input
class Input(Instruction):
    def __init__(self, lid: int, sort: Sort, name: str):
        super().__init__(lid, "input", [sort])
        self.name = name
        self.sid = sort.lid

    def eq(self, inst) -> bool:
        return super().eq(inst) and self.name == inst.name

    def serialize(self) -> str:
        return super().serialize() + self.name


class Output(Instruction):
    def __init__(self, lid: int, out: Instruction):
        super().__init__(lid, "output", [out])

## Unary Instructions ##

class Bad(Instruction):
    def __init__(self, lid: int, cond: Instruction):
        super().__init__(lid, "bad", [cond])

class Constraint(Instruction):
    def __init__(self, lid: int, cond: Instruction):
        super().__init__(lid, "constraint", [cond])

class Zero(Instruction):
    def __init__(self, lid: int, sort: Sort):
        super().__init__(lid, "zero", [sort])
        self.sid = sort.lid

class One(Instruction):
    def __init__(self, lid: int, sort: Sort):
        super().__init__(lid, "one", [sort])
        self.sid = sort.lid

class Ones(Instruction):
    def __init__(self, lid: int, sort: Sort):
        super().__init__(lid, "ones", [sort])

class Not(Instruction):
    def __init__(self, lid: int, sort: Sort, cond: Instruction):
        super().__init__(lid, "not", [sort, cond])

class Inc(Instruction):
    def __init__(self, lid: int, sort: Sort, op1: Instruction):
        super().__init__(lid, "inc", [sort, op1])

class Dec(Instruction):
    def __init__(self, lid: int, sort: Sort, op1: Instruction):
        super().__init__(lid, "dec", [sort, op1])

class Neg(Instruction):
    def __init__(self, lid: int, sort: Sort, op1: Instruction):
        super().__init__(lid, "neg", [sort, op1])

class Redor(Instruction):
    def __init__(self, lid: int, sort: Sort, op1: Instruction):
        super().__init__(lid, "redor", [sort, op1])

class Redxor(Instruction):
    def __init__(self, lid: int, sort: Sort, op1: Instruction):
        super().__init__(lid, "redxor", [sort, op1])

class Redand(Instruction):
    def __init__(self, lid: int, sort: Sort, op1: Instruction):
        super().__init__(lid, "redand", [sort, op1])

## Constants: always of the form Instruction + sort + value ##

class Constd(Instruction):
    def __init__(self, lid: int, sort: Sort, value: int):
        super().__init__(lid, "constd", [sort])
        self.value: int = value
        self.sid = sort.lid

    def eq(self, inst) -> bool:
        return super().eq(inst) and self.value == inst.value

    def serialize(self) -> str:
        return super().serialize() + str(self.value)

class Consth(Instruction):
    def __init__(self, lid: int, sort: Sort, value: int):
        super().__init__(lid, "consth", [sort])
        self.value: int = value
        self.sid = sort.lid

    def eq(self, inst) -> bool:
        return super().eq(inst) and self.value == inst.value

    def serialize(self) -> str:
        return super().serialize() + str(self.value)

class Const(Instruction):
    def __init__(self, lid: int, sort: Sort, value: int):
        super().__init__(lid, "const", [sort])
        self.value: int = value
        self.sid = sort.lid

    def eq(self, inst) -> bool:
        return super().eq(inst) and self.value == inst.value

    def serialize(self) -> str:
        return super().serialize() + str(self.value)

## State related instructions ##
# States are declared using a sort and a name
class State(Instruction):
    def __init__(self, lid: int, sort: Sort, name: str):
        super().__init__(lid, "state", [sort])
        self.name: str = name
        self.sid = sort.lid

    def eq(self, inst) -> bool:
        return super().eq(inst) and self.name == inst.name

    def serialize(self) -> str:
        return super().serialize() + self.name

class Init(Instruction):
    def __init__(self, lid: int, sort: Sort, state: Instruction, constval: Instruction):
        super().__init__(lid, "init", [sort, state, constval])

class Next(Instruction):
    def __init__(self, lid: int, sort: Sort, state: Instruction, next: Instruction):
        super().__init__(lid, "next", [sort, state, next])
        self.stid = state.lid

class Slice(Instruction):
    def __init__(self, lid: int, sort: Sort, op: Instruction, highbit: int, lowbit: int):
        super().__init__(lid, "slice", [sort, op])
        self.highbit: int = highbit
        self.lowbit: int = lowbit
        self.width = (self.highbit-self.lowbit+1)

    def eq(self, inst) -> bool:
        return super().eq(inst) and self.highbit == inst.highbit and self.lowbit == inst.lowbit

    def serialize(self) -> str:
        return super().serialize() + str(self.width) + " " + str(self.lowbit)

class Ite(Instruction):
    def __init__(self, lid: int, sort: Sort, cond: Instruction, t: Instruction, f: Instruction):
        super().__init__(lid, "ite", [sort, cond, t, f])

class Implies(Instruction):
    def __init__(self, lid: int, sort: Sort, lhs: Instruction, rhs: Instruction):
        super().__init__(lid, "implies", [sort, lhs, rhs])

class Iff(Instruction):
    def __init__(self, lid: int, sort: Sort, lhs: Instruction, rhs: Instruction):
        super().__init__(lid, "iff", [sort, lhs, rhs])

## Binary operations ##
class Add(Instruction):
    def __init__(self, lid: int, sort: Sort, op1: Instruction, op2: Instruction):
        super().__init__(lid, "add", [sort, op1, op2])

class Sub(Instruction):
    def __init__(self, lid: int, sort: Sort, op1: Instruction, op2: Instruction):
        super().__init__(lid, "sub", [sort, op1, op2])

class Mul(Instruction):
    def __init__(self, lid: int, sort: Sort, op1: Instruction, op2: Instruction):
        super().__init__(lid, "mul", [sort, op1, op2])

class Sdiv(Instruction):
    def __init__(self, lid: int, sort: Sort, op1: Instruction, op2: Instruction):
        super().__init__(lid, "sdiv", [sort, op1, op2])

class Udiv(Instruction):
    def __init__(self, lid: int, sort: Sort, op1: Instruction, op2: Instruction):
        super().__init__(lid, "udiv", [sort, op1, op2])

class Smod(Instruction):
    def __init__(self, lid: int, sort: Sort, op1: Instruction, op2: Instruction):
        super().__init__(lid, "smod", [sort, op1, op2])

class Sll(Instruction):
    def __init__(self, lid: int, sort: Sort, op1: Instruction, op2: Instruction):
        super().__init__(lid, "sll", [sort, op1, op2])

class Srl(Instruction):
    def __init__(self, lid: int, sort: Sort, op1: Instruction, op2: Instruction):
        super().__init__(lid, "srl", [sort, op1, op2])

class Sra(Instruction):
    def __init__(self, lid: int, sort: Sort, op1: Instruction, op2: Instruction):
        super().__init__(lid, "sra", [sort, op1, op2])

class And(Instruction):
    def __init__(self, lid: int, sort: Sort, op1: Instruction, op2: Instruction):
        super().__init__(lid, "and", [sort, op1, op2])

class Or(Instruction):
    def __init__(self, lid: int, sort: Sort, op1: Instruction, op2: Instruction):
        super().__init__(lid, "or", [sort, op1, op2])

class Xor(Instruction):
    def __init__(self, lid: int, sort: Sort, op1: Instruction, op2: Instruction):
        super().__init__(lid, "xor", [sort, op1, op2])

class Concat(Instruction):
    def __init__(self, lid: int, sort: Sort, op1: Instruction, op2: Instruction):
        super().__init__(lid, "concat", [sort, op1, op2])

class Eq(Instruction):
    def __init__(self, lid: int, sort: Sort, op1: Instruction, op2: Instruction):
        super().__init__(lid, "eq", [sort, op1, op2])

class Neq(Instruction):
    def __init__(self, lid: int, sort: Sort, op1: Instruction, op2: Instruction):
        super().__init__(lid, "neq", [sort, op1, op2])

class Ugt(Instruction):
    def __init__(self, lid: int, sort: Sort, op1: Instruction, op2: Instruction):
        super().__init__(lid, "ugt", [sort, op1, op2])

class Sgt(Instruction):
    def __init__(self, lid: int, sort: Sort, op1: Instruction, op2: Instruction):
        super().__init__(lid, "sgt", [sort, op1, op2])

class Ugte(Instruction):
    def __init__(self, lid: int, sort: Sort, op1: Instruction, op2: Instruction):
        super().__init__(lid, "ugte", [sort, op1, op2])

class Sgte(Instruction):
    def __init__(self, lid: int, sort: Sort, op1: Instruction, op2: Instruction):
        super().__init__(lid, "sgte", [sort, op1, op2])

class Ult(Instruction):
    def __init__(self, lid: int, sort: Sort, op1: Instruction, op2: Instruction):
        super().__init__(lid, "ult", [sort, op1, op2])

class Slt(Instruction):
    def __init__(self, lid: int, sort: Sort, op1: Instruction, op2: Instruction):
        super().__init__(lid, "slt", [sort, op1, op2])

class Ulte(Instruction):
    def __init__(self, lid: int, sort: Sort, op1: Instruction, op2: Instruction):
        super().__init__(lid, "ulte", [sort, op1, op2])

class Slte(Instruction):
    def __init__(self, lid: int, sort: Sort, op1: Instruction, op2: Instruction):
        super().__init__(lid, "slte", [sort, op1, op2])

class Uext(Instruction):
    def __init__(self, lid: int, sort: Sort, op: Instruction, width: int, name: str):
        super().__init__(lid, "uext", [sort, op, width, name])
        self.width: int = width
        self.renaming = False
        if self.width == 0:
            self.renaming = True
            self.name = name
            self.aliasid = op.lid

class Sext(Instruction):
    def __init__(self, lid: int, sort: Sort, op: Instruction, width: int, name: str):
        super().__init__(lid, "sext", [sort, op, width, name])
        self.width: int = width


############ NON-STANDARD: Custom extensions for btor-opt ############

# Precondition instruction
# This becomes a "x not cond; bad x" when verifying an instance
#      becomes a "constraint cond" when verifying a module
class Prec(Instruction):
    def __init__(self, lid: int, cond: Instruction):
        super().__init__(lid, "prec", [cond], False)

# Postcondition instruction
# This becomes a "constraint cond" when verifying an instance
#      becomes a "x not cond; bad x" when verifying a module
class Post(Instruction):
    def __init__(self, lid: int, cond: Instruction):
        super().__init__(lid, "post", [cond], False)

# Instance Instruction
# Creates an instance of a named module
# @param name: the name of the module to instantiate
class Instance(Instruction):
    def __init__(self, lid: int, name: str):
        super().__init__(lid, "inst", [], False)
        self.name = name

# Reference to an instruction in a different named region
# Has a weird infix notation `<mod_name>:<lid>`
# Not really an instruction, more of a reference to an instruction
class Ref(Instruction):
    def __init__(self, lid: int, name: str, val: Instruction):
        super().__init__(lid, ":", [val], False)
        self.name = name
        self.val = val

# Set Instruction
# Similarly to an alias, this sets the inputs of an instance to a specific operation
# @param instance: the instance this is setting inputs for
# @param ref: a reference to the module's input we want to set, e.g. A:2
# @param alias: the instruction we want to set the input to
class Set(Instruction):
    def __init__(self, lid: int, instance: Instance, ref: Ref, alias: Instruction):
        super().__init__(lid, "set", [instance, ref, alias], False)


# Structural extensions
class ModuleLike():
    def __init__(self, name: str, body: list[Instruction]) -> None:
        self.name = name
        self.body = body

    def get_inst(self, i: int) -> Instruction:
        return self.body[i]

# Module instruction 
# Declares a named region of standard instructions
# Can be referred to by name and associated with a contract
class Module(ModuleLike):
    def __init__(self, name: str, body: list[Instruction]) -> None:
        super().__init__(name, body)
   
# Contract instruction 
# Declares a named region of custom instructions
# Only preconditions and postconditions are allowed
# Name must be an existing module name 
class Contract(ModuleLike):
    def __init__(self, name: str, body: list[Instruction]) -> None:
        super().__init__(name, body)
        self.preconditions = [i for i in body if isinstance(i, Prec)]
        self.postconditions = [i for i in body if isinstance(i, Post)]
        assert len(self.preconditions) > 0 or len(self.postconditions) > 0, \
            "Contracts must contain either a precondition or a post-condition!"
        

# Base class for a custom btor2 file (standard is simply a list of instructions)
class Program():
    def __init__(self, modules: list[Module], contracts: list[Contract]) -> None:
        self.modules = modules
        # Ignore all contracts that don't have an existing name
        self.contracts = contracts
        ## Sanity check: We should have as many modules as there are contracts
        assert len(modules) >= len(contracts), \
            "There should be at least as many modules as there are contracts!"
        ## Sanity check: Each module should have at most one contract
        for m in modules:
            cs = [c for c in contracts if c.name == m.name]
            assert len(cs) <= 1, f"Module {m.name} has more than one contract!"
        ## Sanity check: Each contract should name a module exactly once
        for c in contracts:
            ms = [m for m in modules if c.name == m.name]
            assert len(ms) == 1, f"Contract {c.name} references {str(len(ms))} modules instead of 1!"
    
    # Retrieves a module by its given name
    # @param name: the name of the module we want to retrive
    def get_module(self, name: str) -> Module:
        res = [x for x in self.modules if x.name == name]
        ## Check if the given name is defined
        assert len(res) > 0 , f"name: {name} is not defined!"
        return res[0]
    
    # Retrieves a contract by its given name
    # @param name: the name of the contract we want to retrive
    def get_contract(self, name: str) -> Contract:
        res = [x for x in self.contracts if x.name == name]
        ## Check if the given name is defined, otherwise return None
        if len(res) == 0:
            return None
        return res[0]
    
    # Retrieves the contract associated to a module if it exists
    # If it does not exist then simply return None
    def get_module_contract(self, module: Module) -> Contract:
        c = self.get_contract(module.name)
        ## Check that a contract was found
        return c

########################################################################
