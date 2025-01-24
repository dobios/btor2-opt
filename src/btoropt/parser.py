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
from tqdm import tqdm

# Retrieves an instruction with the given ID from the given standard program
# This is a safe wrapper around `get_inst` and enforces that the given
# ID must be correct.
def find_inst(p: list[Instruction], id: int) -> Instruction:
    inst = get_inst(p, id)
    assert inst is not None, f"Undeclared instruction used with id: {id}"
    return inst

# Checks thaa a given module name has been defined
def check_name(name: str, modules: list[Module]) -> bool:
    return name in [m.name for m in modules]

# Retrives a module by name from a list of parsed modules
def get_module(name: str, modules: list[Module]) -> Module:
    return [m for m in modules if m.name == name][0]

# Extracts a body from an arbitrary code sequence
# Returns the line idx at which the scanning ended
def scan_body(inp: list[str], i: int) -> tuple[list[str], int]:
    res = []
    l = inp[i].split(" ")
    ## Check that the declaration line ends with an '{'
    assert str(l[len(l)-1].strip()) == '{', f"invalid body start: {l[len(l)-1]}"

    i += 1
    while inp[i].strip() != "}":
        # Check that there are no nested structures
        lid = inp[i].strip().split(" ")[0]
        assert lid.isnumeric(), f"All body lines must be instructions! Found: {lid}"
        res.append(inp[i].strip())
        i += 1
    return (res, i)

# Parses a ref instruction (only custom inst that is allowed in both modules and contracts)
# @param inst: the pre-split ref instruction to be parsed
# @param modules: the list of already parsed modules that can be referenced
def parse_ref(inst: list[str], modules: list[Module]) -> Ref:
    ## Sanity check: Must be a ref instruction
    assert inst[1] == "ref", f"`parse_ref` can only handle ref instructions, not {inst[1]}!"
    ref_mod = inst[2]

    ## Sanity check: check that the name exists
    assert check_name(ref_mod, modules), f"Named module {ref_mod} is undefined!"

    module = get_module(ref_mod, modules)
    val = find_inst(module.body, int(inst[3]))
    return Ref(int(inst[0]), ref_mod, val)

# Parse a module's pre-scanned body
# @param body: the list of instructions contained within the body
# @param modules: the list of already parsed modules that can be referenced
def parse_module_body(body: list[str], modules: list[Module]) -> list[Instruction]:
    p = []
    for line in body:
        inst = line.split(" ")
        if inst[0] == ";": # handle comments
            continue
        lid = int(inst[0])
        tag = inst[1]
        match tag:
            # Handle special instructions
            case "inst":
                instd_mod = inst[2]
                ## Sanity check: check that the name exists
                assert check_name(instd_mod, modules), f"Named module {instd_mod} is undefined!"
                p.append(Instance(lid, instd_mod))

            case "ref":
                p.append(parse_ref(inst, modules))

            case "set":
                instance = find_inst(p, int(inst[2]))
                ref = find_inst(p, int(inst[3]))
                assert ref.name == instance.name, "`set` can only set a reference to an instance input!"
                alias = find_inst(p, int(inst[4]))
                p.append(Set(lid, instance, ref, alias))

            # Handle standard instructions
            case _:
                op = parse_inst(line, p)
                if op is not None:
                    p.append(op)

    return p

# Parse a contract's pre-scanned body
# @param name: the name given to the module
# @param body: the list of instructions contained within the body
# @param modules: the list of already parsed modules that can be referenced
def parse_contract_body(body: list[str], modules: list[Module]) -> list[Instruction]:
    p = []
    for line in body:
        inst = line.split(" ")
        if inst[0] == ";": # handle comments
            continue
        lid = int(inst[0])
        tag = inst[1]
        match tag:
            # Handle special instructions
            case "prec":
                # Find the op associated to this instruction
                cond = find_inst(p, int(inst[2]))
                p.append(Prec(lid, cond))

            case "post":
                # Find the op associated to this instruction
                cond = find_inst(p, int(inst[2]))
                p.append(Post(lid, cond))

            case "ref":
                p.append(parse_ref(inst, modules))

            # Handle standard instructions
            case _:
                op = parse_inst(line, p)
                if op is not None:
                    p.append(op)

    return p

# Parses a single instruction
# @param line: the current instruction that needs to be parsed
# @param p: the current parsed state of the program
def parse_inst(line: str, p: list[Instruction]) -> Instruction:
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

            # Construct instruction
            op = Sort(lid, inst[2], int(inst[3]))


        case "input":
            # Sanity check: verify that instruction is well formed
            assert len(inst) >= 3,\
                "input instruction must be of the form: <lid> input <sid> [<name>]. Found: " + line

            # Find the sort associated to this instruction
            sort = find_inst(p, int(inst[2]))
            assert isinstance(sort, Sort), f"Input sort must be a Sort. Found: " + line

            if len(inst) >= 4:
                name = inst[3].strip()
            else:
                name = f"input_{inst[0]}"
            # Construct instruction
            op = Input(lid, sort, name)

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
            assert len(inst) >= 3,\
                "state instruction must be of the form: <lid> state <sid> [<name>]. Found: " + line

            # Find the operands associated to this instruction
            sort = find_inst(p, int(inst[2]))
            assert isinstance(sort, Sort), f"State sort must be a Sort. Found: " + line
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
                "slice instruction must be of the form: <lid> slice <sid> <opid> <highbit> <lowbit>. Found: " + line

            # Find the operands associated to this instruction
            sort = find_inst(p, int(inst[2]))
            operand = find_inst(p, int(inst[3]))
            highbit = int(inst[4])
            lowbit = int(inst[5])

            # Construct instruction
            op = Slice(lid, sort, operand, highbit, lowbit)

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
            op2 = find_inst(p, int(inst[4]))

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
                "not instruction must be of the form: <lid> not <sid> <cond>. Found: " + line

            # Find the operands associated to this instruction
            sort = find_inst(p, int(inst[2]))
            cond = find_inst(p, int(inst[3]))

            # Construct instruction
            op = Not(lid, sort, cond)

        case "inc":
            # Sanity check: verify that instruction is well formed
            assert len(inst) >= 4,\
                "inc instruction must be of the form: <lid> inc <sid> <stateid>. Found: " + line

            # Find the operands associated to this instruction
            sort = find_inst(p, int(inst[2]))
            state = find_inst(p, int(inst[3]))

            # Construct instruction
            op = Inc(lid, sort, state)

        case "dec":
            # Sanity check: verify that instruction is well formed
            assert len(inst) >= 4,\
                "dec instruction must be of the form: <lid> dec <sid> <stateid>. Found: " + line

            # Find the operands associated to this instruction
            sort = find_inst(p, int(inst[2]))
            state = find_inst(p, int(inst[3]))

            # Construct instruction
            op = Dec(lid, sort, state)

        case "neg":
            # Sanity check: verify that instruction is well formed
            assert len(inst) >= 4,\
                "neg instruction must be of the form: <lid> neg <sid> <cond>. Found: " + line

            # Find the operands associated to this instruction
            sort = find_inst(p, int(inst[2]))
            cond = find_inst(p, int(inst[3]))

            # Construct instruction
            op = Neg(lid, sort, cond)

        case "redor":
            # Sanity check: verify that instruction is well formed
            assert len(inst) >= 4,\
                "redor instruction must be of the form: <lid> redor <srtid> <sid>. Found: " + line

            # Find the operands associated to this instruction
            sort = find_inst(p, int(inst[2]))
            cond = find_inst(p, int(inst[3]))

            # Construct instruction
            op = Redor(lid, sort, cond)

        case "redand":
            # Sanity check: verify that instruction is well formed
            assert len(inst) >= 4,\
                "redand instruction must be of the form: <lid> redand <srtid> <sid>. Found: " + line
            # Find the operands associated to this instruction
            sort = find_inst(p, int(inst[2]))
            cond = find_inst(p, int(inst[3]))
            # Construct instruction
            op = Redand(lid, sort, cond)
        case "redxor":
            # Sanity check: verify that instruction is well formed
            assert len(inst) >= 4,\
                "redxor instruction must be of the form: <lid> redxor <srtid> <sid>. Found: " + line
            # Find the operands associated to this instruction
            sort = find_inst(p, int(inst[2]))
            cond = find_inst(p, int(inst[3]))
            # Construct instruction
            op = Redxor(lid, sort, cond)

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
            assert len(inst) >= 5,\
                "uext instruction must be of the form: <lid> uext <sid> <opid> <width> [<name>]. Found: " + line

            # Find the operands associated to this instruction
            sort = find_inst(p, int(inst[2]))
            operand = find_inst(p, int(inst[3]))
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

            # Find the operands associated to this instruction
            sort = find_inst(p, int(inst[2]))
            operand = find_inst(p, int(inst[3]))
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

# Parse an entire file that can contain contracts and modules
def parse_file(inp: list[str]) -> Program:
    m: list[Module] = []
    c: list[Contract] = []
    i = 0
    while i < len(inp):
        symbols = inp[i].strip().split(" ")
        # Check whether it's a module or a contract
        tag = symbols[0]
        match tag:
            case "module":
                name = symbols[1]
                # Scan and parse the body
                (body, i) = scan_body(inp, i)
                b = parse_module_body(body, m)
                # Create and store the module
                m.append(Module(name, b))

            case "contract":
                name = symbols[1]
                assert check_name(name, m), f"Contract name {name} is not defined!"
                (body, i) = scan_body(inp, i)
                body = parse_contract_body(body, m)
                # Create and store the module
                c.append(Contract(name, body))

            case "}":
                i+=1
                continue

            case _:
                print(f"Unsupported structure: {tag} is not module | contract")
                exit(1)

    return Program(m, c)

# Parse a standard btor2 file, does not handle custom instructions
def parse(inp: list[str]) -> list[Instruction]:
    # Split the string into instructions and read them 1 by 1
    p = []
    for line in tqdm(inp, desc="Parsing BTOR2"):
        op = parse_inst(line, p)
        if op is not None:
            p.append(op)
    return p
