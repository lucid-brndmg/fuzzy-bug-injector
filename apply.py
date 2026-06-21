import os
import argparse
from pathlib import Path
import random
import shlex
import subprocess
import difflib

from common.mutation import MutationMatch, apply_mutations
from common.utils import load_path

DEFAULT_MUTATION_MODULE = str(Path(os.path.dirname(os.path.realpath(__file__))) / "mutations" / "confuse.py")

def display_mut(src: str, mutated: str, mode: str):
    if mode == "code":
        print(mutated)
    else:
        src_lines = [ f"|{i + 1} {line}" for i, line in enumerate(src.splitlines(keepends=True))]
        mut_lines = [ f"|{i + 1} {line}" for i, line in enumerate(mutated.splitlines(keepends=True))]
        df = difflib.ndiff(src_lines, mut_lines)
        if mode == "diff":
            print(*df, sep="")
        if mode == "diff_only":
            print(*[d for d in df if not d.startswith(" ")], sep="")
    print("")

def main():
    parser = argparse.ArgumentParser(description="Fuzzy Bug Injector: apply mutations to source code")
    parser.add_argument("--seed", type=int, help="Random seed for reproducibility")
    parser.add_argument("--lang", type=str, default="", help="Specified language if omitted in dataset")
    parser.add_argument("--validator", help="A validator script for checking validity of each variation")
    parser.add_argument(
        "--mut-mod",
        default=[],
        action="append",
        help="Mutation modules to load (directory or .py file)",
    )
    parser.add_argument(
        "--mut",
        action="append",
        default=[],
        help="Mutation names to include (e.g. delete-statement)",
    )
    parser.add_argument(
        "--display",
        default="diff_only",
        help="Display mode (code, diff, diff_only)"
    )
    parser.add_argument("source", help="A source code file")
    args = parser.parse_args()
    if args.seed is not None:
        random.seed(args.seed)
    mutation_inst = []
    loaded = []
    for path in args.mut_mod:
        loaded = []
        for mod in load_path(Path(path)):
            try:
                if len(mod.MUTATIONS) > 0:
                    loaded += mod.MUTATIONS
                    print(f"loaded {len(mod.MUTATIONS)} mutations")
            except Exception as inst:
                print(f"failed to load mutation module: {inst}")
                pass
        print(f"loaded {len(loaded)} mutations from {str(path)}")
        mutation_inst += loaded
    print(f"loaded {len(loaded)} mutations from {str(args.mut_mod)}")

    mut_whitelist = args.mut
    mutation_apply = [ m for m in mutation_inst if m.name in mut_whitelist ]
    print(f"prepared {len(mutation_apply)} mutations")
    for m in mutation_apply:
        print(f"\t- {m.name}")
    validator_script = args.validator
    src_path = Path(args.source)
    src = src_path.read_text()
    lines_find = src.splitlines()
    lines_apply = src.splitlines(keepends=True)
    validator_cmd = shlex.split(validator_script) if validator_script is not None else []
    lang: str = args.lang or ""
    candidates: list[tuple[str, MutationMatch, str]] = []
    id = src_path.name
    for mutation in mutation_apply:
        matches = mutation.find_candidates(lines_find, lang=lang)
        for match in matches:
            code = "".join(apply_mutations(lines_apply, [match]))
            if validator_script is not None:
                proc = subprocess.run([
                    *validator_cmd, 
                    "--code", code,
                    "--language", lang, 
                    "--pre-validate",
                    "--id", id,
                    "--mutations", mutation.name
                ])
                if proc.returncode != 0:
                    continue
            candidates.append((mutation.name, match, code))

    print(f"found {len(candidates)} candidates for id {id}")
    for i, (name, match, code) in enumerate(candidates):
        print(f"candidate #{i}: {name}")
        display_mut(src, code, args.display)
        

if __name__ == "__main__":
    main()