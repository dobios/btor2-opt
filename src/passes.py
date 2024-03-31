from program import *


# Base clas for compiler pass
# @param id: the unique name of this pass
class Pass:
    def __init__(self, id: str):
        self.id = id

    def run(p: list[Instruction]) -> list[Instruction]:
        return p

# Example pass: Simply renames all inputs to inp_<pos>
class RenameInputs(Pass):
    def __init__(self):
        super().__init__("rename-inputs")

    # I chose to have this pass not modify p in place
    # you can also simply modify p and return it
    def run(p: list[Instruction]) -> list[Instruction]:
        i = 0
        res = []
        for inst in p:
            if isinstance(inst, Input):
                res.append(Input(inst.lid, inst.sort, f"inp_{i}"))
                i += 1
            else:
                res.append(inst)
        return res

# List containing all passes
all_passes = [RenameInputs()]

# Retrieves a pass from the list given an id
def find_pass(p: list[Pass], id: str) -> Pass:
    return next((e for e in p if e.id == id), None)
