# btor2-opt
Very basic btor2 parser, circuit miter, and code optimizer.

## Install  
```
pip install btor2-opt
```

## Overview
This repo contains two main scripts:
  - `btor2-opt`: Takes a `.btor2` file and a list of pass names as argument and prints out the transformed result.
  - `btor2-miter`: Takes a `.fir` file as input and runs it through `firrtl` and `firtool` to obtain two `.btor2` designs which are then merged into a single miter circuit before being returned to the user. Note that this requires having `firrtl` and `firtool` in your path, specifically a [version of `firtool` that has the `--btor2` flag](https://github.com/llvm/circt/pull/6947).

The rest of the code can be found in the `src` folder, which contains a basic parser for `btor2` (not entirely complete, but supports anything `firtool --btor2` can produce), an internal representation of the language and a simple pass infrastructure, where you can add any of you custom passes.

## Adding a Pass
Simply create a new class (as its own file) in `src/passes` that inherits from `Pass`. Then in the constructor, make sure you give it a name. The pass's logic itself is written by overiding the `run(p: list[Instruction]) -> list[Instruction]` method. The pass must then be imported in `src/passes/passes.py` and instantiated in the `all_passes` list. Passes are grouped either in `transforms`, which contain all of the passes that transform the AST, and `validation`, which contains all of the passes used to gurantee the syntactic correctness of the output program.

Here is a simple example pass that renames all inputs to "inp_n".
```python
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

# Make sure to add an instance of the pass to the all_passes array
all_passes = [RenameInputs()]
```
This pass can then be called by running:
```sh
python3 btor2-opt.py ex.btor2 rename-inputs
```
