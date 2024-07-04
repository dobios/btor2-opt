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

def find_inst(p: list[Instruction], id: int) -> Instruction:
    inst = get_inst(p, id)
    assert inst is not None, f"Undeclared instruction used with id: {id}"
    return inst

def parse(inp: list[str]) -> list[Instruction]:
    # Split the string into instructions and read them 1 by 1
    p = []
    for line in inp:
        inst = line.split(" ")
        # BTOR comment
        if inst[0] == ";":
            continue
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

                # Construct instruction
                op = Sort(lid, inst[2], int(inst[3]))


            case "input":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 4,\
                    "input instruction must be of the form: <lid> input <sid> <name>. Found: " + line

                # Find the sort associated to this instruction
                sort = find_inst(p, int(inst[2]))
                assert isinstance(sort, Sort), f"Input sort must be a Sort. Found: " + line

                # Construct instruction
                op = Input(lid, sort, inst[3])

            case "output":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 3,\
                    "input instruction must be of the form: <lid> output <opid>. Found: " + line

                # Find the op associated to this instruction
                out = find_inst(p, int(inst[2]))

                # Construct instruction
                op = Output(lid, out)

            case "bad":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 3,\
                    "sort instruction must be of the form: <lid> bad <opid>. Found: " + line

                # Find the op associated to this instruction
                cond = find_inst(p, int(inst[2]))

                # Construct instruction
                op = Bad(lid, cond)

            case "constraint":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 3,\
                    "sort instruction must be of the form: <lid> constraint <opid>. Found: " + line

                # Find the op associated to this instruction
                cond = find_inst(p, int(inst[2]))

                # Construct instruction
                op = Constraint(lid, cond)

            case "zero":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 3,\
                    "sort instruction must be of the form: <lid> zero <sid>. Found: " + line

                # Find the sort associated to this instruction
                sort = find_inst(p, int(inst[2]))

                # Construct instruction
                op = Zero(lid, sort)

            case "one":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 3,\
                    "sort instruction must be of the form: <lid> one <sid>. Found: " + line

                # Find the sort associated to this instruction
                sort = find_inst(p, int(inst[2]))

                # Construct instruction
                op = One(lid, sort)

            case "ones":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 3,\
                    "sort instruction must be of the form: <lid> ones <sid>. Found: " + line

                # Find the sort associated to this instruction
                sort = find_inst(p, int(inst[2]))

                # Construct instruction
                op = Ones(lid, sort)

            case "constd":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 4,\
                    "sort instruction must be of the form: <lid> constd <sid> <value>. Found: " + line

                # Find the operands associated to this instruction
                sort = find_inst(p, int(inst[2]))
                value = int(inst[3])

                # Construct instruction
                op = Constd(lid, sort, value)

            case "consth":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 4,\
                    "sort instruction must be of the form: <lid> consth <sid> <value>. Found: " + line

                # Find the operands associated to this instruction
                sort = find_inst(p, int(inst[2]))
                value = int(inst[3])

                # Construct instruction
                op = Consth(lid, sort, value)

            case "const":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 4,\
                    "sort instruction must be of the form: <lid> const <sid> <value>. Found: " + line

                # Find the operands associated to this instruction
                sort = find_inst(p, int(inst[2]))
                # Default base is 2
                value = int(inst[3], 2)

                # Construct instruction
                op = Const(lid, sort, value)

            case "state":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 4,\
                    "state instruction must be of the form: <lid> state <sid> <name>. Found: " + line

                # Find the operands associated to this instruction
                sort = find_inst(p, int(inst[2]))
                assert isinstance(sort, Sort), f"State sort must be a Sort. Found: " + line
                name = inst[3].strip()

                # Construct instruction
                op = State(lid, sort, name)

            case "init":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 5,\
                    "sort instruction must be of the form: <lid> init <sid> <stateid> <valueid>. Found: " + line

                # Find the operands associated to this instruction
                sort = find_inst(p, int(inst[2]))
                state = find_inst(p, int(inst[3]))
                val = find_inst(p, int(inst[4]))

                # Construct instruction
                op = Init(lid, sort, state, val)

            case "next":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 5,\
                    "sort instruction must be of the form: <lid> next <sid> <stateid> <nextid>. Found: " + line

                # Find the operands associated to this instruction
                sort = find_inst(p, int(inst[2]))
                state = find_inst(p, int(inst[3]))
                next = find_inst(p, int(inst[4]))

                # Construct instruction
                op = Next(lid, sort, state, next)

            case "slice":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 6,\
                    "sort instruction must be of the form: <lid> slice <sid> <opid> <width> <lowbit>. Found: " + line

                # Find the operands associated to this instruction
                sort = find_inst(p, int(inst[2]))
                operand = find_inst(p, int(inst[3]))
                width = int(inst[4])
                lowbit = int(inst[5])

                # Construct instruction
                op = Slice(lid, sort, operand, width, lowbit)

            case "ite":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 6,\
                    "sort instruction must be of the form: <lid> ite <sid> <condid> <tid> <fid>. Found: " + line

                # Find the operands associated to this instruction
                sort = find_inst(p, int(inst[2]))
                cond = find_inst(p, int(inst[3]))
                t = find_inst(p, int(inst[4]))
                f = find_inst(p, int(inst[5]))

                # Construct instruction
                op = Ite(lid, sort, cond, t, f)

            case "implies":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 5,\
                    "sort instruction must be of the form: <lid> implies <sid> <lhsid> <rhsid>. Found: " + line

                # Find the operands associated to this instruction
                sort = find_inst(p, int(inst[2]))
                lhs = find_inst(p, int(inst[3]))
                rhs = find_inst(p, int(inst[4]))

                # Construct instruction
                op = Implies(lid, sort, lhs, rhs)

            case "iff":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 5,\
                    "sort instruction must be of the form: <lid> iff <sid> <lhsid> <rhsid>. Found: " + line

                # Find the operands associated to this instruction
                sort = find_inst(p, int(inst[2]))
                lhs = find_inst(p, int(inst[3]))
                rhs = find_inst(p, int(inst[4]))

                # Construct instruction
                op = Iff(lid, sort, lhs, rhs)

            case "add":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 5,\
                    "sort instruction must be of the form: <lid> add <sid> <op1> <op2>. Found: " + line

                # Find the operands associated to this instruction
                sort = find_inst(p, int(inst[2]))
                op1 = find_inst(p, int(inst[3]))
                op2 = find_inst(p, int(inst[4]))

                # Construct instruction
                op = Add(lid, sort, op1, op2)

            case "sub":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 5,\
                    "sort instruction must be of the form: <lid> sub <sid> <op1> <op2>. Found: " + line

                # Find the operands associated to this instruction
                sort = find_inst(p, int(inst[2]))
                op1 = find_inst(p, int(inst[3]))
                op2 = find_inst(p, int(inst[4]))

                # Construct instruction
                op = Sub(lid, sort, op1, op2)

            case "mul":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 5,\
                    "sort instruction must be of the form: <lid> mul <sid> <op1> <op2>. Found: " + line

                # Find the operands associated to this instruction
                sort = find_inst(p, int(inst[2]))
                op1 = find_inst(p, int(inst[3]))
                op2 = find_inst(p, int(inst[4]))

                # Construct instruction
                op = Mul(lid, sort, op1, op2)

            case "sdiv":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 5,\
                    "sort instruction must be of the form: <lid> sdiv <sid> <op1> <op2>. Found: " + line

                # Find the operands associated to this instruction
                sort = find_inst(p, int(inst[2]))
                op1 = find_inst(p, int(inst[3]))
                op2 = find_inst(p, int(inst[4]))

                # Construct instruction
                op = Sdiv(lid, sort, op1, op2)

            case "udiv":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 5,\
                    "sort instruction must be of the form: <lid> udiv <sid> <op1> <op2>. Found: " + line

                # Find the operands associated to this instruction
                sort = find_inst(p, int(inst[2]))
                op1 = find_inst(p, int(inst[3]))
                op2 = find_inst(p, int(inst[4]))

                # Construct instruction
                op = Udiv(lid, sort, op1, op2)

            case "smod":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 5,\
                    "sort instruction must be of the form: <lid> smod <sid> <op1> <op2>. Found: " + line

                # Find the operands associated to this instruction
                sort = find_inst(p, int(inst[2]))
                op1 = find_inst(p, int(inst[3]))
                op2 = find_inst(int(inst[4]))

                # Construct instruction
                op = Smod(lid, sort, op1, op2)

            case "sll":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 5,\
                    "sort instruction must be of the form: <lid> sll <sid> <op1> <op2>. Found: " + line

                # Find the operands associated to this instruction
                sort = find_inst(p, int(inst[2]))
                op1 = find_inst(p, int(inst[3]))
                op2 = find_inst(p, int(inst[4]))

                # Construct instruction
                op = Sll(lid, sort, op1, op2)

            case "srl":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 5,\
                    "sort instruction must be of the form: <lid> srl <sid> <op1> <op2>. Found: " + line

                # Find the operands associated to this instruction
                sort = find_inst(p, int(inst[2]))
                op1 = find_inst(p, int(inst[3]))
                op2 = find_inst(p, int(inst[4]))

                # Construct instruction
                op = Srl(lid, sort, op1, op2)

            case "sra":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 5,\
                    "sort instruction must be of the form: <lid> sra <sid> <op1> <op2>. Found: " + line

                # Find the operands associated to this instruction
                sort = find_inst(p, int(inst[2]))
                op1 = find_inst(p, int(inst[3]))
                op2 = find_inst(p, int(inst[4]))

                # Construct instruction
                op = Sra(lid, sort, op1, op2)

            case "and":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 5,\
                    "sort instruction must be of the form: <lid> and <sid> <op1> <op2>. Found: " + line

                # Find the operands associated to this instruction
                sort = find_inst(p, int(inst[2]))
                op1 = find_inst(p, int(inst[3]))
                op2 = find_inst(p, int(inst[4]))

                # Construct instruction
                op = And(lid, sort, op1, op2)

            case "or":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 5,\
                    "sort instruction must be of the form: <lid> or <sid> <op1> <op2>. Found: " + line

                # Find the operands associated to this instruction
                sort = find_inst(p, int(inst[2]))
                op1 = find_inst(p, int(inst[3]))
                op2 = find_inst(p, int(inst[4]))

                # Construct instruction
                op = Or(lid, sort, op1, op2)

            case "xor":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 5,\
                    "sort instruction must be of the form: <lid> xor <sid> <op1> <op2>. Found: " + line

                # Find the operands associated to this instruction
                sort = find_inst(p, int(inst[2]))
                op1 = find_inst(p, int(inst[3]))
                op2 = find_inst(p, int(inst[4]))

                # Construct instruction
                op = Xor(lid, sort, op1, op2)

            case "concat":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 5,\
                    "sort instruction must be of the form: <lid> concat <sid> <op1> <op2>. Found: " + line

                # Find the operands associated to this instruction
                sort = find_inst(p, int(inst[2]))
                op1 = find_inst(p, int(inst[3]))
                op2 = find_inst(p, int(inst[4]))

                # Construct instruction
                op = Concat(lid, sort, op1, op2)

            case "not":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 4,\
                    "sort instruction must be of the form: <lid> not <sid> <cond>. Found: " + line

                # Find the operands associated to this instruction
                sort = find_inst(p, int(inst[2]))
                cond = find_inst(p, int(inst[3]))

                # Construct instruction
                op = Not(lid, sort, cond)

            case "eq":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 5,\
                    "sort instruction must be of the form: <lid> eq <sid> <op1> <op2>. Found: " + line

                # Find the operands associated to this instruction
                sort = find_inst(p, int(inst[2]))
                op1 = find_inst(p, int(inst[3]))
                op2 = find_inst(p, int(inst[4]))

                # Construct instruction
                op = Eq(lid, sort, op1, op2)

            case "neq":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 5,\
                    "sort instruction must be of the form: <lid> neq <sid> <op1> <op2>. Found: " + line

                # Find the operands associated to this instruction
                sort = find_inst(p, int(inst[2]))
                op1 = find_inst(p, int(inst[3]))
                op2 = find_inst(p, int(inst[4]))

                # Construct instruction
                op = Neq(lid, sort, op1, op2)

            case "ugt":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 5,\
                    "sort instruction must be of the form: <lid> ugt <sid> <op1> <op2>. Found: " + line

                # Find the operands associated to this instruction
                sort = find_inst(p, int(inst[2]))
                op1 = find_inst(p, int(inst[3]))
                op2 = find_inst(p, int(inst[4]))

                # Construct instruction
                op = Ugt(lid, sort, op1, op2)

            case "sgt":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 5,\
                    "sort instruction must be of the form: <lid> sgt <sid> <op1> <op2>. Found: " + line

                # Find the operands associated to this instruction
                sort = find_inst(p, int(inst[2]))
                op1 = find_inst(p, int(inst[3]))
                op2 = find_inst(p, int(inst[4]))

                # Construct instruction
                op = Sgt(lid, sort, op1, op2)

            case "ugte":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 5,\
                    "sort instruction must be of the form: <lid> ugte <sid> <op1> <op2>. Found: " + line

                # Find the operands associated to this instruction
                sort = find_inst(p, int(inst[2]))
                op1 = find_inst(p, int(inst[3]))
                op2 = find_inst(p, int(inst[4]))

                # Construct instruction
                op = Ugte(lid, sort, op1, op2)

            case "sgte":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 5,\
                    "sort instruction must be of the form: <lid> sgte <sid> <op1> <op2>. Found: " + line

                # Find the operands associated to this instruction
                sort = find_inst(p, int(inst[2]))
                op1 = find_inst(p, int(inst[3]))
                op2 = find_inst(p, int(inst[4]))

                # Construct instruction
                op = Sgte(lid, sort, op1, op2)

            case "ult":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 5,\
                    "sort instruction must be of the form: <lid> ult <sid> <op1> <op2>. Found: " + line

                # Find the operands associated to this instruction
                sort = find_inst(p, int(inst[2]))
                op1 = find_inst(p, int(inst[3]))
                op2 = find_inst(p, int(inst[4]))

                # Construct instruction
                op = Ult(lid, sort, op1, op2)

            case "slt":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 5,\
                    "sort instruction must be of the form: <lid> slt <sid> <op1> <op2>. Found: " + line

                # Find the operands associated to this instruction
                sort = find_inst(p, int(inst[2]))
                op1 = find_inst(p, int(inst[3]))
                op2 = find_inst(p, int(inst[4]))

                # Construct instruction
                op = Slt(lid, sort, op1, op2)

            case "ulte":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 5,\
                    "sort instruction must be of the form: <lid> ulte <sid> <op1> <op2>. Found: " + line

                # Find the operands associated to this instruction
                sort = find_inst(p, int(inst[2]))
                op1 = find_inst(p, int(inst[3]))
                op2 = find_inst(p, int(inst[4]))

                # Construct instruction
                op = Ulte(lid, sort, op1, op2)

            case "slte":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 5,\
                    "sort instruction must be of the form: <lid> slte <sid> <op1> <op2>. Found: " + line

                # Find the operands associated to this instruction
                sort = find_inst(p, int(inst[2]))
                op1 = find_inst(p, int(inst[3]))
                op2 = find_inst(p, int(inst[4]))

                # Construct instruction
                op = Slte(lid, sort, op1, op2)

            case "uext":
                # Sanity check: verify that instruction is well formed
                assert len(inst) >= 6,\
                    "sort instruction must be of the form: <lid> uext <sid> <opid> <width> <name>. Found: " + line

                # Find the operands associated to this instruction
                sort = find_inst(p, int(inst[2]))
                operand = find_inst(p, int(inst[3]))
                width = int(inst[4])

                # Construct instruction
                op = Uext(lid, sort, operand, width, inst[5])

            case _:
                print(f"Unsupported operation type: {tag} in {line}")
                exit(1)

        if op is not None:
            p.append(op)
    return p
