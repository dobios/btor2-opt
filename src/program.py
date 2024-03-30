from functools import reduce

# All supported btor2 instruction tags
tags = ["sort","input", "output", "bad", "constraint", "zero",
        "one", "ones", "constd", "consth", "const", "state",
        "init", "next", "slice", "ite", "implies", "iff", 
        "add", "sub", "mul", "sdiv", "udiv", "smod", "sll", 
        "srl", "sra", "and", "or", "xor", "concat", "not",
        "eq", "neq", "ugt", "sgt", "ugte", "sgte", "ult",
        "slt", "ulte", "slte"]

# All legal sort types
sort_tags = ["bitvector", "array"]

# Base class for an instruction
# @param lid: the line identifier of the instruction
# @param inst: the string litteral keyword for the instruction
# @param operands: the list of operands given to this instruction,
# these must also be instructions
class Instruction:
    def __init__(self, lid: int, inst: str, operands = []):
        self.lid = lid
        self.inst = inst
        self.operands = operands
        
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
        return str(self.lid) + " " + self.inst + " " + [str(op.lid) + " " for op in self.operands]
    
def serialize_p(p: list[Instruction]) -> str:
    return reduce(lambda acc, s: acc + s.serialize() + "\n", p, "")

def get_inst(p: list[Instruction], lid: int) -> Instruction:
    for op in p:
        if op.lid == lid:
            return op
    return None

# Sort declaration instruction
# e.g. 1 sort bitvector 32
# @param type: {bitvector | array}, the type of sort we are declaring
# @param width: the width of the declared sort
class Sort(Instruction):
    def __init__(self, lid: int, type: str, width: int):
        super().__init__(lid, "sort", [])
        self.type: str = type
        self.width: int = width

    def eq(self, inst) -> bool:
        return super().eq(inst) and self.type == inst.type and self.width == inst.width
    
    def serialize(self) -> str:
        return super().serialize() + type + " " + str(self.width)

# Input instruction: declares an input
# @param sort: the sort defining the type of this input
# @param name: the string name of the input
class Input(Instruction):
    def __init__(self, lid: int, sort: Instruction, name: str):
        super().__init__(lid, "input", [sort])
        self.name = name
    
    def eq(self, inst) -> bool:
        return super().eq(inst) and self.name == inst.name
    
    def serialize(self) -> str:
        return super().serialize() + self.name
    
## Unary Instructions ##
    
class Output(Instruction):
    def __init__(self, lid: int, out: Instruction):
        super().__init__(lid, "output", [out])

class Bad(Instruction):
    def __init__(self, lid: int, cond: Instruction):
        super().__init__(lid, "bad", [cond])

class Constraint(Instruction):
    def __init__(self, lid: int, cond: Instruction):
        super().__init__(lid, "constraint", [cond])

class Zero(Instruction):
    def __init__(self, lid: int, sort: Instruction):
        super().__init__(lid, "zero", [sort])

class One(Instruction):
    def __init__(self, lid: int, sort: Instruction):
        super().__init__(lid, "one", [sort])

class Ones(Instruction):
    def __init__(self, lid: int, sort: Instruction):
        super().__init__(lid, "ones", [sort])

class Not(Instruction):
    def __init__(self, lid: int, sort: Instruction, cond: Instruction):
        super().__init__(lid, "not", [sort, cond])

## Constants: always of the form Instruction + sort + value ##
    
class Constd(Instruction):
    def __init__(self, lid: int, sort: Instruction, value: int):
        super().__init__(lid, "constd", [sort])
        self.value: int = value

    def eq(self, inst) -> bool:
        return super().eq(inst) and self.value == inst.value
    
    def serialize(self) -> str:
        return super().serialize() + str(self.value)
    
class Consth(Instruction):
    def __init__(self, lid: int, sort: Instruction, value: int):
        super().__init__(lid, "consth", [sort])
        self.value: int = value

    def eq(self, inst) -> bool:
        return super().eq(inst) and self.value == inst.value
    
    def serialize(self) -> str:
        return super().serialize() + str(self.value)
    
class Const(Instruction):
    def __init__(self, lid: int, sort: Instruction, value: int):
        super().__init__(lid, "const", [sort])
        self.value: int = value

    def eq(self, inst) -> bool:
        return super().eq(inst) and self.value == inst.value
    
    def serialize(self) -> str:
        return super().serialize() + str(self.value)
    
## State related instructions ##
# States are declared using a sort and a name
class State(Instruction):
    def __init__(self, lid: int, sort: Instruction, name: str):
        super().__init__(lid, "state", [sort])
        self.name: str = name

    def eq(self, inst) -> bool:
        return super().eq(inst) and self.name == inst.name
    
    def serialize(self) -> str:
        return super().serialize() + self.name
    
class Init(Instruction):
    def __init__(self, lid: int, sort: Instruction, state: Instruction, constval: Instruction):
        super().__init__(lid, "init", [sort, state, constval])

class Next(Instruction):
    def __init__(self, lid: int, sort: Instruction, state: Instruction, next: Instruction):
        super().__init__(lid, "next", [sort, state, next])

class Slice(Instruction):
    def __init__(self, lid: int, sort: Instruction, op: Instruction, width: int, lowbit: int):
        super().__init__(lid, "slice", [sort, op])
        self.width: int = width
        self.lowbit: int = lowbit

    def eq(self, inst) -> bool:
        return super().eq(inst) and self.width == inst.width and self.lowbit == inst.lowbit
    
    def serialize(self) -> str:
        return super().serialize() + str(self.width) + " " + str(self.lowbit)
    
class Ite(Instruction):
    def __init__(self, lid: int, sort: Instruction, cond: Instruction, t: Instruction, f: Instruction):
        super().__init__(lid, "ite", [sort, cond, t, f])

class Implies(Instruction):
    def __init__(self, lid: int, sort: Instruction, lhs: Instruction, rhs: Instruction):
        super().__init__(lid, "implies", [sort, lhs, rhs])

class Iff(Instruction):
    def __init__(self, lid: int, sort: Instruction, lhs: Instruction, rhs: Instruction):
        super().__init__(lid, "iff", [sort, lhs, rhs])

## Binary operations ##
class Add(Instruction):
    def __init__(self, lid: int, sort: Instruction, op1: Instruction, op2: Instruction):
        super().__init__(lid, "add", [sort, op1, op2])

class Sub(Instruction):
    def __init__(self, lid: int, sort: Instruction, op1: Instruction, op2: Instruction):
        super().__init__(lid, "sub", [sort, op1, op2])

class Mul(Instruction):
    def __init__(self, lid: int, sort: Instruction, op1: Instruction, op2: Instruction):
        super().__init__(lid, "mul", [sort, op1, op2])

class Sdiv(Instruction):
    def __init__(self, lid: int, sort: Instruction, op1: Instruction, op2: Instruction):
        super().__init__(lid, "sdiv", [sort, op1, op2])

class Udiv(Instruction):
    def __init__(self, lid: int, sort: Instruction, op1: Instruction, op2: Instruction):
        super().__init__(lid, "udiv", [sort, op1, op2])

class Smod(Instruction):
    def __init__(self, lid: int, sort: Instruction, op1: Instruction, op2: Instruction):
        super().__init__(lid, "smod", [sort, op1, op2])

class Sll(Instruction):
    def __init__(self, lid: int, sort: Instruction, op1: Instruction, op2: Instruction):
        super().__init__(lid, "sll", [sort, op1, op2])

class Srl(Instruction):
    def __init__(self, lid: int, sort: Instruction, op1: Instruction, op2: Instruction):
        super().__init__(lid, "srl", [sort, op1, op2])

class Sra(Instruction):
    def __init__(self, lid: int, sort: Instruction, op1: Instruction, op2: Instruction):
        super().__init__(lid, "sra", [sort, op1, op2])

class And(Instruction):
    def __init__(self, lid: int, sort: Instruction, op1: Instruction, op2: Instruction):
        super().__init__(lid, "and", [sort, op1, op2])

class Or(Instruction):
    def __init__(self, lid: int, sort: Instruction, op1: Instruction, op2: Instruction):
        super().__init__(lid, "or", [sort, op1, op2])

class Xor(Instruction):
    def __init__(self, lid: int, sort: Instruction, op1: Instruction, op2: Instruction):
        super().__init__(lid, "xor", [sort, op1, op2])

class Concat(Instruction):
    def __init__(self, lid: int, sort: Instruction, op1: Instruction, op2: Instruction):
        super().__init__(lid, "concat", [sort, op1, op2])

class Eq(Instruction):
    def __init__(self, lid: int, sort: Instruction, op1: Instruction, op2: Instruction):
        super().__init__(lid, "eq", [sort, op1, op2])

class Neq(Instruction):
    def __init__(self, lid: int, sort: Instruction, op1: Instruction, op2: Instruction):
        super().__init__(lid, "neq", [sort, op1, op2])   

class Ugt(Instruction):
    def __init__(self, lid: int, sort: Instruction, op1: Instruction, op2: Instruction):
        super().__init__(lid, "ugt", [sort, op1, op2])

class Sgt(Instruction):
    def __init__(self, lid: int, sort: Instruction, op1: Instruction, op2: Instruction):
        super().__init__(lid, "sgt", [sort, op1, op2])
    
class Ugte(Instruction):
    def __init__(self, lid: int, sort: Instruction, op1: Instruction, op2: Instruction):
        super().__init__(lid, "ugte", [sort, op1, op2])

class Sgte(Instruction):
    def __init__(self, lid: int, sort: Instruction, op1: Instruction, op2: Instruction):
        super().__init__(lid, "sgte", [sort, op1, op2])

class Ult(Instruction):
    def __init__(self, lid: int, sort: Instruction, op1: Instruction, op2: Instruction):
        super().__init__(lid, "ult", [sort, op1, op2])

class Slt(Instruction):
    def __init__(self, lid: int, sort: Instruction, op1: Instruction, op2: Instruction):
        super().__init__(lid, "slt", [sort, op1, op2])

class Ulte(Instruction):
    def __init__(self, lid: int, sort: Instruction, op1: Instruction, op2: Instruction):
        super().__init__(lid, "ulte", [sort, op1, op2])

class Slte(Instruction):
    def __init__(self, lid: int, sort: Instruction, op1: Instruction, op2: Instruction):
        super().__init__(lid, "slte", [sort, op1, op2])
