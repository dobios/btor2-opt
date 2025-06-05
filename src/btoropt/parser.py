##########################################################################
# BTOR2 parser, code optimizer, and circuit miter
# Copyright (C) 2024-2025  Amelia Dobis
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
from tqdm import tqdm
import multiprocessing

pool = multiprocessing.Pool()

# Trying to maintain original parser API
def parse(p_str: list[str], deferred=False) -> list[Instruction]:
    parse = Parser(p_str)
    if deferred:
        parse.parseDeferred()
    else: 
        parse.parseSeq()
    return parse.p 

# Parses a given btor2 program
class Parser:
    # @param{p_str: list[str]}: list of lines to parse
    def __init__(self, p_str: list[str]):
        self.p : list[Instruction] = []
        self.p_str : list[str] = p_str
        self.context : dict[int, Instruction] = {}
        self.done = False # Whether or not the parser is done parsing

    # Resets the parser to be used again
    def clear(self, p_str: list[str] = []):
        self.p = []
        self.p_str = p_str
        self.context = {}
        self.done = False

    # Retrieves an instruction with the given ID from the given standard program
    # This is a safe wrapper around `get_inst` and enforces that the given
    # ID must be correct.
    def find_inst(self, id: int) -> Instruction:
        inst = get_inst(self.p, id)
        if inst is None:
            print(self.p)
            assert False, f"Undeclared instruction used with id: {id}"
        return inst
    
    # Defers the resolution of all operand IDs
    def defer(self, ids: list[str]) -> list[Instruction]:
        return list(map(lambda id: Instruction(int(id)), ids))

    # Parses a single instruction
    # @param line: the current instruction that needs to be parsed
    # @param p: the current parsed state of the program
    def parse_inst(self, line: str, deferred=True) -> Instruction:
        inst = line.split(" ")
        # BTOR comment
        if inst[0] == ";":
            return None
        lid = int(inst[0])
        tag = inst[1]

        # Check if tag is valid
        assert tag in tags, f"Unsupported operation type: {tag} in {line}"

        # Create the instruction associated to the tag
        op = None

        match tag:
            case "sort":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 4,\
                    "sort instruction must be of the form: <lid> sort \{bitvector|array\} <width>. Found: " + line
                assert inst[2] in sort_tags,\
                    f"sort must be of type bitvector or array! Found: {inst[2]}"

                # Construct instruction, defer if required
                op = Sort(lid, inst[2], int(inst[3]))

            case "input":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 3,\
                    "input instruction must be of the form: <lid> input <sid> [<name>]. Found: " + line

                # Find the sort associated to this instruction
                sort = self.defer(inst[2])[0] if deferred else \
                        self.find_inst(int(inst[2]))
                # assert isinstance(sort, Sort), f"Input sort must be a Sort. Found: " + line

                if len(inst) >= 4:
                    name = inst[3].strip()
                else:
                    name = f"input_{inst[0]}"
                # Construct instruction
                op = Input(lid, sort, name)

            case "output":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 3,\
                    "output instruction must be of the form: <lid> output <opid> [name]. Found: " + line

                # Set a temporary instruction to be resolved later
                out = self.defer(inst[2])[0] if deferred else \
                        self.find_inst(int(inst[2]))

                if len(inst) >= 4:
                    name = inst[3].strip()
                else:
                    name = f"output_{inst[0]}"

                # Construct instruction
                op = Output(lid, out, name)

            case "bad":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 3,\
                    "sort instruction must be of the form: <lid> bad <opid>. Found: " + line

                # Find the op associated to this instruction
                cond = self.defer(inst[2])[0] if deferred else \
                        self.find_inst(int(inst[2]))

                # Construct instruction
                op = Bad(lid, cond)

            case "constraint":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 3,\
                    "sort instruction must be of the form: <lid> constraint <opid>. Found: " + line

                # Find the op associated to this instruction
                cond = self.defer(inst[2])[0] if deferred else \
                        self.find_inst(int(inst[2]))

                # Construct instruction
                op = Constraint(lid, cond)

            case "zero":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 3,\
                    "sort instruction must be of the form: <lid> zero <sid>. Found: " + line

                # Find the sort associated to this instruction
                sort = self.defer(inst[2])[0] if deferred else \
                        self.find_inst(int(inst[2]))

                # Construct instruction
                op = Zero(lid, sort)

            case "one":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 3,\
                    "sort instruction must be of the form: <lid> one <sid>. Found: " + line

                # Find the sort associated to this instruction
                sort = self.defer(inst[2])[0] if deferred else \
                        self.find_inst(int(inst[2]))

                # Construct instruction
                op = One(lid, sort)

            case "ones":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 3,\
                    "sort instruction must be of the form: <lid> ones <sid>. Found: " + line

                # Find the sort associated to this instruction
                sort = self.defer(inst[2])[0] if deferred else \
                        self.find_inst(int(inst[2]))

                # Construct instruction
                op = Ones(lid, sort)

            case "constd":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 4,\
                    "sort instruction must be of the form: <lid> constd <sid> <value>. Found: " + line

                # Find the operands associated to this instruction
                sort = self.defer(inst[2])[0] if deferred else \
                        self.find_inst(int(inst[2]))
                value = int(inst[3])

                # Construct instruction
                op = Constd(lid, sort, value)

            case "consth":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 4,\
                    "sort instruction must be of the form: <lid> consth <sid> <value>. Found: " + line

                # Find the operands associated to this instruction
                sort = self.defer(inst[2])[0] if deferred else \
                        self.find_inst(int(inst[2]))
                value = int(inst[3])

                # Construct instruction
                op = Consth(lid, sort, value)

            case "const":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 4,\
                    "sort instruction must be of the form: <lid> const <sid> <value>. Found: " + line

                # Find the operands associated to this instruction
                sort = self.defer(inst[2])[0] if deferred else \
                        self.find_inst(int(inst[2]))
                # Default base is 2
                value = int(inst[3], 2)

                # Construct instruction
                op = Const(lid, sort, value)

            case "state":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 3,\
                    "state instruction must be of the form: <lid> state <sid> [<name>]. Found: " + line

                # Find the operands associated to this instruction
                sort = self.defer(inst[2])[0] if deferred else \
                        self.find_inst(int(inst[2]))
                # assert isinstance(sort, Sort), f"State sort must be a Sort. Found: " + line
                if len(inst) >= 4:
                    name = inst[3].strip()
                else:
                    name = f"state_{inst[0]}"

                # Construct instruction
                op = State(lid, sort, name)

            case "init":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 5,\
                    "sort instruction must be of the form: <lid> init <sid> <stateid> <valueid>. Found: " + line

                # Find the operands associated to this instruction or defer
                (sort, state, val) = \
                    tuple(self.defer(inst[2:5])) if deferred else \
                    tuple(map(lambda i: self.find_inst(int(i)), inst[2:5]))

                # Construct instruction
                op = Init(lid, sort, state, val)

            case "next":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 5,\
                    "sort instruction must be of the form: <lid> next <sid> <stateid> <nextid>. Found: " + line

               # Find the operands associated to this instruction or defer
                (sort, state, next) = \
                    tuple(self.defer(inst[2:5])) if deferred else \
                    tuple(map(lambda i: self.find_inst(int(i)), inst[2:5]))

                # Construct instruction
                op = Next(lid, sort, state, next)

            case "slice":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 6,\
                    "slice instruction must be of the form: <lid> slice <sid> <opid> <highbit> <lowbit>. Found: " + line

                # Find the operands associated to this instruction or defer
                (sort, operand) = \
                    tuple(self.defer(inst[2:4])) if deferred else \
                    tuple(map(lambda i: self.find_inst(int(i)), inst[2:4]))
                
                highbit = int(inst[4])
                lowbit = int(inst[5])

                # Construct instruction
                op = Slice(lid, sort, operand, highbit, lowbit)

            case "ite":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 6,\
                    "sort instruction must be of the form: <lid> ite <sid> <condid> <tid> <fid>. Found: " + line

                # Find the operands associated to this instruction or defer
                (sort, cond, t, f) = \
                    tuple(self.defer(inst[2:6])) if deferred else \
                    tuple(map(lambda i: self.find_inst(int(i)), inst[2:6]))

                # Construct instruction
                op = Ite(lid, sort, cond, t, f)

            case "implies":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 5,\
                    "sort instruction must be of the form: <lid> implies <sid> <lhsid> <rhsid>. Found: " + line

                # Find the operands associated to this instruction or defer
                (sort, lhs, rhs) = \
                    tuple(self.defer(inst[2:5])) if deferred else \
                    tuple(map(lambda i: self.find_inst(int(i)), inst[2:5]))

                # Construct instruction
                op = Implies(lid, sort, lhs, rhs)

            case "iff":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 5,\
                    "sort instruction must be of the form: <lid> iff <sid> <lhsid> <rhsid>. Found: " + line

                # Find the operands associated to this instruction or defer
                (sort, lhs, rhs) = \
                    tuple(self.defer(inst[2:5])) if deferred else \
                    tuple(map(lambda i: self.find_inst(int(i)), inst[2:5]))

                # Construct instruction
                op = Iff(lid, sort, lhs, rhs)

            case "add":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 5,\
                    "sort instruction must be of the form: <lid> add <sid> <op1> <op2>. Found: " + line

                # Find the operands associated to this instruction or defer
                (sort, op1, op2) = \
                    tuple(self.defer(inst[2:5])) if deferred else \
                    tuple(map(lambda i: self.find_inst(int(i)), inst[2:5]))

                # Construct instruction
                op = Add(lid, sort, op1, op2)

            case "sub":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 5,\
                    "sort instruction must be of the form: <lid> sub <sid> <op1> <op2>. Found: " + line

                # Find the operands associated to this instruction or defer
                (sort, op1, op2) = \
                    tuple(self.defer(inst[2:5])) if deferred else \
                    tuple(map(lambda i: self.find_inst(int(i)), inst[2:5]))

                # Construct instruction
                op = Sub(lid, sort, op1, op2)

            case "mul":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 5,\
                    "sort instruction must be of the form: <lid> mul <sid> <op1> <op2>. Found: " + line

                # Find the operands associated to this instruction or defer
                (sort, op1, op2) = \
                    tuple(self.defer(inst[2:5])) if deferred else \
                    tuple(map(lambda i: self.find_inst(int(i)), inst[2:5]))

                # Construct instruction
                op = Mul(lid, sort, op1, op2)

            case "sdiv":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 5,\
                    "sort instruction must be of the form: <lid> sdiv <sid> <op1> <op2>. Found: " + line

                # Find the operands associated to this instruction or defer
                (sort, op1, op2) = \
                    tuple(self.defer(inst[2:5])) if deferred else \
                    tuple(map(lambda i: self.find_inst(int(i)), inst[2:5]))

                # Construct instruction
                op = Sdiv(lid, sort, op1, op2)

            case "udiv":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 5,\
                    "sort instruction must be of the form: <lid> udiv <sid> <op1> <op2>. Found: " + line

                # Find the operands associated to this instruction or defer
                (sort, op1, op2) = \
                    tuple(self.defer(inst[2:5])) if deferred else \
                    tuple(map(lambda i: self.find_inst(int(i)), inst[2:5]))

                # Construct instruction
                op = Udiv(lid, sort, op1, op2)

            case "smod":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 5,\
                    "sort instruction must be of the form: <lid> smod <sid> <op1> <op2>. Found: " + line

                # Find the operands associated to this instruction or defer
                (sort, op1, op2) = \
                    tuple(self.defer(inst[2:5])) if deferred else \
                    tuple(map(lambda i: self.find_inst(int(i)), inst[2:5]))

                # Construct instruction
                op = Smod(lid, sort, op1, op2)

            case "srem":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 5,\
                    "sort instruction must be of the form: <lid> srem <sid> <op1> <op2>. Found: " + line

                # Find the operands associated to this instruction or defer
                (sort, op1, op2) = \
                    tuple(self.defer(inst[2:5])) if deferred else \
                    tuple(map(lambda i: self.find_inst(int(i)), inst[2:5]))

                # Construct instruction
                op = Srem(lid, sort, op1, op2)

            case "urem":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 5,\
                    "sort instruction must be of the form: <lid> urem <sid> <op1> <op2>. Found: " + line

                # Find the operands associated to this instruction or defer
                (sort, op1, op2) = \
                    tuple(self.defer(inst[2:5])) if deferred else \
                    tuple(map(lambda i: self.find_inst(int(i)), inst[2:5]))

                # Construct instruction
                op = Urem(lid, sort, op1, op2)


            case "sll":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 5,\
                    "sort instruction must be of the form: <lid> sll <sid> <op1> <op2>. Found: " + line

                # Find the operands associated to this instruction or defer
                (sort, op1, op2) = \
                    tuple(self.defer(inst[2:5])) if deferred else \
                    tuple(map(lambda i: self.find_inst(int(i)), inst[2:5]))

                # Construct instruction
                op = Sll(lid, sort, op1, op2)

            case "srl":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 5,\
                    "sort instruction must be of the form: <lid> srl <sid> <op1> <op2>. Found: " + line

                # Find the operands associated to this instruction or defer
                (sort, op1, op2) = \
                    tuple(self.defer(inst[2:5])) if deferred else \
                    tuple(map(lambda i: self.find_inst(int(i)), inst[2:5]))

                # Construct instruction
                op = Srl(lid, sort, op1, op2)

            case "sra":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 5,\
                    "sort instruction must be of the form: <lid> sra <sid> <op1> <op2>. Found: " + line

                # Find the operands associated to this instruction or defer
                (sort, op1, op2) = \
                    tuple(self.defer(inst[2:5])) if deferred else \
                    tuple(map(lambda i: self.find_inst(int(i)), inst[2:5]))

                # Construct instruction
                op = Sra(lid, sort, op1, op2)

            case "and":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 5,\
                    "sort instruction must be of the form: <lid> and <sid> <op1> <op2>. Found: " + line

                # Find the operands associated to this instruction or defer
                (sort, op1, op2) = \
                    tuple(self.defer(inst[2:5])) if deferred else \
                    tuple(map(lambda i: self.find_inst(int(i)), inst[2:5]))

                # Construct instruction
                op = And(lid, sort, op1, op2)

            case "or":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 5,\
                    "sort instruction must be of the form: <lid> or <sid> <op1> <op2>. Found: " + line

                # Find the operands associated to this instruction or defer
                (sort, op1, op2) = \
                    tuple(self.defer(inst[2:5])) if deferred else \
                    tuple(map(lambda i: self.find_inst(int(i)), inst[2:5]))

                # Construct instruction
                op = Or(lid, sort, op1, op2)

            case "xor":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 5,\
                    "sort instruction must be of the form: <lid> xor <sid> <op1> <op2>. Found: " + line

                # Find the operands associated to this instruction or defer
                (sort, op1, op2) = \
                    tuple(self.defer(inst[2:5])) if deferred else \
                    tuple(map(lambda i: self.find_inst(int(i)), inst[2:5]))

                # Construct instruction
                op = Xor(lid, sort, op1, op2)

            case "concat":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 5,\
                    "sort instruction must be of the form: <lid> concat <sid> <op1> <op2>. Found: " + line

                # Find the operands associated to this instruction or defer
                (sort, op1, op2) = \
                    tuple(self.defer(inst[2:5])) if deferred else \
                    tuple(map(lambda i: self.find_inst(int(i)), inst[2:5]))

                # Construct instruction
                op = Concat(lid, sort, op1, op2)

            case "not":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 4,\
                    "not instruction must be of the form: <lid> not <sid> <cond>. Found: " + line

                # Find the operands associated to this instruction or defer
                (sort, cond) = \
                    tuple(self.defer(inst[2:4])) if deferred else \
                    tuple(map(lambda i: self.find_inst(int(i)), inst[2:4]))

                # Construct instruction
                op = Not(lid, sort, cond)

            case "inc":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 4,\
                    "inc instruction must be of the form: <lid> inc <sid> <stateid>. Found: " + line

                # Find the operands associated to this instruction or defer
                (sort, state) = \
                    tuple(self.defer(inst[2:4])) if deferred else \
                    tuple(map(lambda i: self.find_inst(int(i)), inst[2:4]))

                # Construct instruction
                op = Inc(lid, sort, state)

            case "dec":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 4,\
                    "dec instruction must be of the form: <lid> dec <sid> <stateid>. Found: " + line

                # Find the operands associated to this instruction or defer
                (sort, state) = \
                    tuple(self.defer(inst[2:4])) if deferred else \
                    tuple(map(lambda i: self.find_inst(int(i)), inst[2:4]))

                # Construct instruction
                op = Dec(lid, sort, state)

            case "neg":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 4,\
                    "neg instruction must be of the form: <lid> neg <sid> <cond>. Found: " + line

                # Find the operands associated to this instruction or defer
                (sort, cond) = \
                    tuple(self.defer(inst[2:4])) if deferred else \
                    tuple(map(lambda i: self.find_inst(int(i)), inst[2:4]))

                # Construct instruction
                op = Neg(lid, sort, cond)

            case "redor":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 4,\
                    "redor instruction must be of the form: <lid> redor <srtid> <sid>. Found: " + line

                # Find the operands associated to this instruction or defer
                (sort, cond) = \
                    tuple(self.defer(inst[2:4])) if deferred else \
                    tuple(map(lambda i: self.find_inst(int(i)), inst[2:4]))

                # Construct instruction
                op = Redor(lid, sort, cond)

            case "redand":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 4,\
                    "redand instruction must be of the form: <lid> redand <srtid> <sid>. Found: " + line
                # Find the operands associated to this instruction or defer
                (sort, cond) = \
                    tuple(self.defer(inst[2:4])) if deferred else \
                    tuple(map(lambda i: self.find_inst(int(i)), inst[2:4]))
                
                # Construct instruction
                op = Redand(lid, sort, cond)
            case "redxor":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 4,\
                    "redxor instruction must be of the form: <lid> redxor <srtid> <sid>. Found: " + line
                # Find the operands associated to this instruction or defer
                (sort, cond) = \
                    tuple(self.defer(inst[2:4])) if deferred else \
                    tuple(map(lambda i: self.find_inst(int(i)), inst[2:4]))
                
                # Construct instruction
                op = Redxor(lid, sort, cond)

            case "eq":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 5,\
                    "sort instruction must be of the form: <lid> eq <sid> <op1> <op2>. Found: " + line

                # Find the operands associated to this instruction or defer
                (sort, op1, op2) = \
                    tuple(self.defer(inst[2:5])) if deferred else \
                    tuple(map(lambda i: self.find_inst(int(i)), inst[2:5]))

                # Construct instruction
                op = Eq(lid, sort, op1, op2)

            case "neq":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 5,\
                    "sort instruction must be of the form: <lid> neq <sid> <op1> <op2>. Found: " + line

                # Find the operands associated to this instruction or defer
                (sort, op1, op2) = \
                    tuple(self.defer(inst[2:5])) if deferred else \
                    tuple(map(lambda i: self.find_inst(int(i)), inst[2:5]))

                # Construct instruction
                op = Neq(lid, sort, op1, op2)

            case "ugt":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 5,\
                    "sort instruction must be of the form: <lid> ugt <sid> <op1> <op2>. Found: " + line

                # Find the operands associated to this instruction or defer
                (sort, op1, op2) = \
                    tuple(self.defer(inst[2:5])) if deferred else \
                    tuple(map(lambda i: self.find_inst(int(i)), inst[2:5]))

                # Construct instruction
                op = Ugt(lid, sort, op1, op2)

            case "sgt":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 5,\
                    "sort instruction must be of the form: <lid> sgt <sid> <op1> <op2>. Found: " + line

                # Find the operands associated to this instruction or defer
                (sort, op1, op2) = \
                    tuple(self.defer(inst[2:5])) if deferred else \
                    tuple(map(lambda i: self.find_inst(int(i)), inst[2:5]))

                # Construct instruction
                op = Sgt(lid, sort, op1, op2)

            case "ugte":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 5,\
                    "sort instruction must be of the form: <lid> ugte <sid> <op1> <op2>. Found: " + line

                # Find the operands associated to this instruction or defer
                (sort, op1, op2) = \
                    tuple(self.defer(inst[2:5])) if deferred else \
                    tuple(map(lambda i: self.find_inst(int(i)), inst[2:5]))

                # Construct instruction
                op = Ugte(lid, sort, op1, op2)

            case "sgte":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 5,\
                    "sort instruction must be of the form: <lid> sgte <sid> <op1> <op2>. Found: " + line

                # Find the operands associated to this instruction or defer
                (sort, op1, op2) = \
                    tuple(self.defer(inst[2:5])) if deferred else \
                    tuple(map(lambda i: self.find_inst(int(i)), inst[2:5]))

                # Construct instruction
                op = Sgte(lid, sort, op1, op2)

            case "ult":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 5,\
                    "sort instruction must be of the form: <lid> ult <sid> <op1> <op2>. Found: " + line

                # Find the operands associated to this instruction or defer
                (sort, op1, op2) = \
                    tuple(self.defer(inst[2:5])) if deferred else \
                    tuple(map(lambda i: self.find_inst(int(i)), inst[2:5]))

                # Construct instruction
                op = Ult(lid, sort, op1, op2)

            case "slt":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 5,\
                    "sort instruction must be of the form: <lid> slt <sid> <op1> <op2>. Found: " + line

                # Find the operands associated to this instruction or defer
                (sort, op1, op2) = \
                    tuple(self.defer(inst[2:5])) if deferred else \
                    tuple(map(lambda i: self.find_inst(int(i)), inst[2:5]))

                # Construct instruction
                op = Slt(lid, sort, op1, op2)

            case "ulte":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 5,\
                    "sort instruction must be of the form: <lid> ulte <sid> <op1> <op2>. Found: " + line

                # Find the operands associated to this instruction or defer
                (sort, op1, op2) = \
                    tuple(self.defer(inst[2:5])) if deferred else \
                    tuple(map(lambda i: self.find_inst(int(i)), inst[2:5]))

                # Construct instruction
                op = Ulte(lid, sort, op1, op2)

            case "slte":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 5,\
                    "sort instruction must be of the form: <lid> slte <sid> <op1> <op2>. Found: " + line

                # Find the operands associated to this instruction or defer
                (sort, op1, op2) = \
                    tuple(self.defer(inst[2:5])) if deferred else \
                    tuple(map(lambda i: self.find_inst(int(i)), inst[2:5]))

                # Construct instruction
                op = Slte(lid, sort, op1, op2)

            case "uext":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 5,\
                    "uext instruction must be of the form: <lid> uext <sid> <opid> <width> [<name>]. Found: " + line

                # Find the operands associated to this instruction or defer
                (sort, operand) = \
                    tuple(self.defer(inst[2:4])) if deferred else \
                    tuple(map(lambda i: self.find_inst(int(i)), inst[2:4]))
                
                width = int(inst[4])

                if len(inst) >= 6:
                    name = inst[5].strip()
                else:
                    name = f"uext_{inst[0]}"

                # Construct instruction
                op = Uext(lid, sort, operand, width, name)

            case "sext":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 5,\
                    "sext instruction must be of the form: <lid> sext <sid> <opid> <width> [<name>]. Found: " + line

                # Find the operands associated to this instruction or defer
                (sort, operand) = \
                    tuple(self.defer(inst[2:4])) if deferred else \
                    tuple(map(lambda i: self.find_inst(int(i)), inst[2:4]))
                
                width = int(inst[4])

                if len(inst) >= 6:
                    name = inst[5].strip()
                else:
                    name = f"sext_{inst[0]}"

                # Construct instruction
                op = Sext(lid, sort, operand, width, name)

            case _:
                print(f"Unsupported operation type: {tag} in {line}")
                exit(1)
        return op
    

    # Resolves the IDs of all of the operands
    def resolveIds(self, inst: Instruction) -> Instruction:
        inst.operands = list(map(lambda op: self.context.get(op.lid), inst.operands)) 
        return inst

    # Parses the entire program using deferred operand resolution
    def parseDeferred(self) -> None:
        assert not self.done, "Parser must be cleared before being reused!"

        self.p = list(map(self.parse_inst, self.p_str))

        # Create the context from the parsed program
        self.context = dict(map(lambda inst: (inst.lid, inst), self.p))

        # Resolve all of the IDs in parallel
        self.p = list(map(self.resolveIds, self.p))

        # Parser is done parsing
        self.done = True


    # Parse a standard btor2 file, does not handle custom instructions
    def parseSeq(self) -> None:
        assert not self.done, "Parser must be cleared before being reused!"

        # Split the string into instructions and read them 1 by 1
        for line in tqdm(self.p_str, desc="Parsing BTOR2"):
            # Parse instructions in an eager manner
            op = self.parse_inst(line, deferred=False)
            if op is not None:
                self.p.append(op)

        # Parser is done parsing
        self.done = True

