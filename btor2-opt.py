from src.program import *
from src.passes import *
from src.parser import *
import sys

if __name__ == "__main__":
    # Retrieve flags
    if len(sys.argv) < 3:
        print("Usage: python3 btor2-opt.py <file.btor2> <pass_names_in_order> ...")
        exit(1)

    # Retrieve design
    btor2str: list[str] = []
    with open(sys.argv[1], "r") as f:
        btor2str = f.readlines()
    
    # Parse the design
    btor2: list[Instruction] = parse(btor2str)

    # Check that the given pass names are valid
    for name in sys.argv[1:]:
        if find_pass(all_passes, name) is None:
            print(f"Invalid pass given as argument: {name}")
            exit(1)

    # Retrieve passes
    pipeline: list[Pass] = [p for p in all_passes if p.id in sys.argv[1:]]

    # Run all passes in the pipeline
    for p in pipeline:
        btor2 = p.run(btor2)

    # Show the result to the user
    print(serialize_p(btor2))
