

from passes.transforms.initAllStates import *
from passes.transforms.renameInputs import *
from passes.validation.checkLidOrdering import *

# Retrieves a pass from the list given an id
def find_pass(p: list[Pass], id: str) -> Pass:
    return next((e for e in p if e.id == id), None)

# List containing all passes
all_passes = [RenameInputs(), InitAllStates(), CheckLidOrdering()]