import argparse
import json
import os
import random
import re
import subprocess
from pathlib import Path
from typing import Any, Generator

from common.utils import load_module, load_path, iter_disjoint_subsets
from common.mutation import Mutation, MutationMatch, apply_mutations

DEFAULT_MUTATION_MODULE = str(Path(os.path.dirname(os.path.realpath(__file__))) / "mutations" / "common.py")

def check_disjoint(a, b):
    (_name1, mat1) = a
    (_name2, mat2) = b
    return mat1.is_disjoint(mat2)

def default_sampler(
    candidates: list[tuple[str, MutationMatch]],
    min_mut: int,
    max_mut: int,
) -> Generator[list[tuple[str, MutationMatch]], Any, None]:
    random.shuffle(candidates)
    return iter_disjoint_subsets(candidates, check_disjoint, min_mut, max_mut, 2**32)

def generate_multi(
    id: str, src: str, lang: str,
    mutations: list[Mutation],
    validator_script: str | None,
    min_mut = 1, max_mut = 5,
    variation_limit = 3,
    sampler = default_sampler
):
    lines_find = src.splitlines()
    lines_apply = src.splitlines(keepends=True)
    
    candidates: list[tuple[str, MutationMatch]] = []
    for mutation in mutations:
        matches = mutation.find_candidates(lines_find, lang=lang)
        for match in matches:
            if validator_script is not None:
                code = "".join(apply_mutations(lines_apply, [match]))
                proc = subprocess.run([
                    validator_script, 
                    "--language", lang, 
                    "--pre-validate",
                    "--mutations", mutation.name,
                    "--code", code
                ])
                if proc.returncode != 0:
                    continue
            candidates.append((mutation.name, match))

    print(f"found {len(candidates)} candidates for id {id}")
    disjoint_subsets = sampler(candidates, min_mut, max_mut)
    out = []
    for i, var in enumerate(disjoint_subsets):
        if len(out) >= variation_limit:
            print("variation limit reached")
            break
        mats = [m for (_n, m) in var]
        names = [n for (n, _m) in var]
        json_digest = [ {"name": n} | m.json_digest() for (n, m) in var ]
        applied = apply_mutations(lines_apply, mats)
        code = "".join(applied)
        var_id = f"{id}:{i}"
        if validator_script is not None:
            proc = subprocess.run([
                validator_script, 
                "--language", lang, 
                "--id", var_id,
                "--mutations", ",".join(names),
                "--code", code
            ])
            if proc.returncode != 0:
                continue

        out.append({
            "id": var_id,
            "code": code,
            "mutations": json_digest
        })
    
    return out


def main():
    print("Fuzzy Bug Injector (github.com/lucid-brndmg/fuzzy-bug-injector)")
    parser = argparse.ArgumentParser(description="Apply mutations to source code files")
    
    parser.add_argument("--dataset", required=True, help="A valid JSON dataset file")
    parser.add_argument("--output", default="out.json", help="The output dataset file")
    parser.add_argument("--min-matches", type=int, default=1, help="Minimum number of places to mutate")
    parser.add_argument("--max-matches", type=int, default=5, help="Maximum number of places to mutate")
    parser.add_argument("--max-variations", type=int, default=10, help="Maximum number of variations to generate for a source code")
    parser.add_argument("--validator", help="A validator script for checking validity of each variation")
    parser.add_argument("--seed", type=int, help="Random seed for reproducibility")
    parser.add_argument("--lang", type=str, default="", help="Specified language if omitted in dataset")
    
    parser.add_argument("--sampler-module", type=str, default="", help="A sampler module (.py file)")
    parser.add_argument(
        "--mutation-modules",
        nargs="*",
        default=[DEFAULT_MUTATION_MODULE],
        help="Mutation modules to load (directory or .py file)",
    )
    parser.add_argument(
        "--mutations",
        nargs="*",
        default=[],
        help="Mutation names to include (e.g. delete-statement)",
    )
    parser.add_argument(
        "--mutation-list",
        help="A list file containing mutation names to include (split by spaces or lines)",
    )
    args = parser.parse_args()
    if args.seed is not None:
        random.seed(args.seed)

    mutation_inst = []
    for path in args.mutation_modules:
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

    mut_whitelist = args.mutations
    if args.mutation_list is not None and args.mutation_list != "":
        file = Path(args.mutation_list)
        content = []
        if file.name.endswith(".json"):
            content = json.loads(file.read_text())
        else:
            content = re.split(r'\s+', file.read_text())
        mut_whitelist += [name for name in content if len(name) > 0]
    
    mutation_apply = [ m for m in mutation_inst if m.name in mut_whitelist ]
    print(f"prepared {len(mutation_apply)} mutations")
    for m in mutation_apply:
        print(f"\t- {m.name}")

    sampler = default_sampler
    if args.sampler_module is not None and args.sampler_module != "":
        sampler = load_module(args.sampler_module).sampler

    dataset = json.loads(Path(args.dataset).read_text())
    print(f"total {len(dataset)} items loaded from dataset")
    out = []
    for i, entry in enumerate(dataset):
        str_entry = type(entry) is str
        code = entry if str_entry else entry["code"]
        id = str(i if str_entry or "id" not in entry else entry["id"])
        lang = "" if str_entry or "language" not in entry else entry["language"]
        batch = generate_multi(
            id, code, lang,
            mutation_apply,
            args.validator,
            args.min_matches,
            args.max_matches,
            args.max_variations,
            sampler
        )
        if str_entry:
            out += batch
        else:
            out += [ entry | b for b in batch ]
    print(f"total {len(out)} items")
    Path(args.output).write_text(json.dumps(out))
    print(f"written to {args.output}")
    
if __name__ == "__main__":
    main()