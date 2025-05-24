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
from .parser import *
from tqdm import tqdm

# Old API for module parsing
def parse_file(file: list[str]) -> Program:
    parser = ModParser(file)
    return parser.parse_file()

# Special parser that handles custom instructions
class ModParser(Parser):
    def __init__(self, p_str):
        super().__init__(p_str)
        self.modules: list[Module] = []
        self.contracts: list[Contract] = []

    # Checks thaa a given module name has been defined
    def check_name(self, name: str) -> bool:
        return name in [m.name for m in self.modules]

    # Retrives a module by name from a list of parsed modules
    def get_module(self, name: str) -> Module:
        return [m for m in self.modules if m.name == name][0]

    # Extracts a body from an arbitrary code sequence
    # Returns the line idx at which the scanning ended
    def scan_body(self, i: int) -> tuple[list[str], int]:
        res = []
        l = self.p_str[i].split(" ")
        ## Check that the declaration line ends with an '{'
        assert str(l[len(l)-1].strip()) == '{', f"invalid body start: {l[len(l)-1]}"

        i += 1
        while self.p_str[i].strip() != "}":
            # Check that there are no nested structures
            lid = self.p_str[i].strip().split(" ")[0]
            assert lid.isnumeric(), f"All body lines must be instructions! Found: {lid}"
            res.append(self.p_str[i].strip())
            i += 1
        return (res, i)

    # Parses a ref instruction (only custom inst that is allowed in both modules and contracts)
    # @param inst: the pre-split ref instruction to be parsed
    # @param modules: the list of already parsed modules that can be referenced
    def parse_ref(self, inst: list[str]) -> Ref:
        ## Sanity check: Must be a ref instruction
        assert inst[1] == "ref", f"`parse_ref` can only handle ref instructions, not {inst[1]}!"
        ref_mod = inst[2]

        ## Sanity check: check that the name exists
        assert self.check_name(ref_mod), f"Named module {ref_mod} is undefined!"

        module = self.get_module(ref_mod)
        val = self.find_inst(module.body, int(inst[3]))
        return Ref(int(inst[0]), ref_mod, val)

    # Parse a module's pre-scanned body
    # @param body: the list of instructions contained within the body
    # @param modules: the list of already parsed modules that can be referenced
    def parse_module_body(self, body: list[str]) -> list[Instruction]:
        bodyParser = Parser(body)

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
                    assert self.check_name(instd_mod), f"Named module {instd_mod} is undefined!"
                    bodyParser.p.append(Instance(lid, instd_mod))

                case "ref":
                    bodyParser.p.append(self.parse_ref(inst))

                case "set":
                    instance = bodyParser.find_inst(int(inst[2]))
                    ref = bodyParser.find_inst(int(inst[3]))
                    assert ref.name == instance.name, "`set` can only set a reference to an instance input!"
                    alias = bodyParser.find_inst(int(inst[4]))
                    bodyParser.p.append(Set(lid, instance, ref, alias))

                # Handle standard instructions
                case _:
                    bodyParser.parse_inst(line)

        return bodyParser.p

    # Parse a contract's pre-scanned body
    # @param name: the name given to the module
    # @param body: the list of instructions contained within the body
    # @param modules: the list of already parsed modules that can be referenced
    def parse_contract_body(self, body: list[str]) -> list[Instruction]:
        bodyParser = Parser(body)
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
                    cond = bodyParser.find_inst(int(inst[2]))
                    bodyParser.p.append(Prec(lid, cond))

                case "post":
                    # Find the op associated to this instruction
                    cond = bodyParser.find_inst(int(inst[2]))
                    bodyParser.p.append(Post(lid, cond))

                case "ref":
                    bodyParser.p.append(self.parse_ref(inst))

                # Handle standard instructions
                case _:
                    bodyParser.parse_inst(line)

        return bodyParser.p

    # Parse an entire file that can contain contracts and modules
    def parse_file(self) -> Program:
        i = 0
        while i < len(self.p_str):
            symbols = self.p_str[i].strip().split(" ")
            # Check whether it's a module or a contract
            tag = symbols[0]
            match tag:
                case "module":
                    name = symbols[1]
                    # Scan and parse the body
                    (body, i) = self.scan_body(i)
                    b = self.parse_module_body(body)
                    # Create and store the module
                    self.modules.append(Module(name, b))

                case "contract":
                    name = symbols[1]
                    assert self.check_name(name), f"Contract name {name} is not defined!"
                    (body, i) = self.scan_body(i)
                    body = self.parse_contract_body(body)
                    # Create and store the module
                    self.contracts.append(Contract(name, body))

                case "}":
                    i+=1
                    continue

                case _:
                    print(f"Unsupported structure: {tag} is not module | contract")
                    exit(1)

        return Program(self.modules, self.contracts)
