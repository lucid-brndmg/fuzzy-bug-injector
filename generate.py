import argparse
import json
import random
import re
import subprocess
import shlex
from pathlib import Path

from common.utils import load_module, load_path
from common.mutation import Mutation, MutationMatch, apply_mutations, default_mutation_sampler

# DEFAULT_MUTATION_MODULE = str(Path(os.path.dirname(os.path.realpath(__file__))) / "mutations" / "confuse.py")


def apply_candidates(
    id: str, src: str, lang: str,
    candidates: list[tuple[str, MutationMatch]],
    validator_script: str | None,
    min_mut = 1, max_mut = 5,
    variation_limit = 3,
    sampler = default_mutation_sampler
):
    lines_apply = src.splitlines(keepends=True)
    validator_cmd = shlex.split(validator_script) if validator_script is not None else []
    disjoint_subsets = sampler(candidates, min_mut, max_mut)
    out = []
    for i, var in enumerate(disjoint_subsets):
        print(f"iteration {i}")
        if len(out) >= variation_limit:
            print("variation limit reached")
            break
        mats = [m for (_n, m) in var]
        names = [n for (n, _m) in var]
        json_digest = [ {"name": n} | m.to_json_digest() for (n, m) in var ]
        applied = apply_mutations(lines_apply, mats)
        code = "".join(applied)
        var_id = f"{id}:{i}"
        if validator_script is not None:
            proc = subprocess.run([
                *validator_cmd, 
                "--code", code,
                "--language", lang, 
                "--id", var_id,
                "--mutations", ",".join(names)
            ])
            if proc.returncode != 0:
                continue

        out.append({
            "id": var_id,
            "code": code,
            "mutations": json_digest,
            "original": src
        })
    return out

def locate_candidates(
    id: str, src: str, lang: str,
    mutations: list[Mutation],
    validator_script: str | None
):
    lines_find = src.splitlines()
    lines_apply = src.splitlines(keepends=True)

    validator_cmd = shlex.split(validator_script) if validator_script is not None else []
    
    candidates: list[tuple[str, MutationMatch]] = []
    for mutation in mutations:
        matches = mutation.find_candidates(lines_find, lang=lang)
        for match in matches:
            if validator_script is not None:
                code = "".join(apply_mutations(lines_apply, [match]))
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
            candidates.append((mutation.name, match))
    return candidates
    # disjoint_subsets = sampler(candidates, min_mut, max_mut)
    # out = []
    # for i, var in enumerate(disjoint_subsets):
    #     print(f"iteration {i}")
    #     if len(out) >= variation_limit:
    #         print("variation limit reached")
    #         break
    #     mats = [m for (_n, m) in var]
    #     names = [n for (n, _m) in var]
    #     json_digest = [ {"name": n} | m.to_json_digest() for (n, m) in var ]
    #     applied = apply_mutations(lines_apply, mats)
    #     code = "".join(applied)
    #     var_id = f"{id}:{i}"
    #     if validator_script is not None:
    #         proc = subprocess.run([
    #             *validator_cmd, 
    #             "--code", code,
    #             "--language", lang, 
    #             "--id", var_id,
    #             "--mutations", ",".join(names)
    #         ])
    #         if proc.returncode != 0:
    #             continue

    #     out.append({
    #         "id": var_id,
    #         "code": code,
    #         "mutations": json_digest,
    #         "original": src
    #     })
    
    # return (candidates, out)


def main():
    print("Fuzzy Bug Injector (github.com/lucid-brndmg/fuzzy-bug-injector)")
    parser = argparse.ArgumentParser(description="Generate mutation candidates and variations to source code files")
    
    parser.add_argument("--dataset", required=True, help="A valid JSON dataset file")
    parser.add_argument("--out-candidates", default="", help="The output JSON file having mutation candidates")
    parser.add_argument("--out-variations", default="", help="The output JSON file having mutated variations")
    
    parser.add_argument("--min-matches", type=int, default=1, help="Minimum number of places to mutate")
    parser.add_argument("--max-matches", type=int, default=5, help="Maximum number of places to mutate")
    parser.add_argument("--max-variations", type=int, default=10, help="Maximum number of variations to generate for a source code")
    parser.add_argument("--validator", help="A validator script for checking validity of each variation")
    parser.add_argument("--seed", type=int, help="Random seed for reproducibility")
    parser.add_argument("--lang", type=str, default="", help="Specified language if omitted in dataset")
    
    parser.add_argument("--sampler-mod", type=str, default="", help="A sampler module (.py file)")
    parser.add_argument(
        "--mut",
        action="append",
        default=[],
        help="Mutation names to include (e.g. delete-statement)",
    )
    parser.add_argument(
        "--mut-mod",
        action="append",
        default=[],
        help="Mutation modules to load (directory or .py file)",
    )
    parser.add_argument(
        "--mut-list",
        help="A list file containing mutation names to include (split by spaces or lines)",
    )
    args = parser.parse_args()

    if args.out_candidates == "" and args.out_variations == "":
        print("warning: nothing to output")
    
    if args.seed is not None:
        random.seed(args.seed)
    
    mutation_inst = []
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

    mut_whitelist = args.mut
    if args.mut_list is not None and args.mut_list != "":
        file = Path(args.mut_list)
        content = []
        if file.name.endswith(".json"):
            content = json.loads(file.read_text())
        else:
            lines = file.read_text().splitlines()
            lines = [line for line in lines if re.match(r"^\w", line.strip())]
            content = re.split(r'\s+', " ".join(lines))
        mut_whitelist += [name for name in content if len(name) > 0]
    
    mutation_apply = [ m for m in mutation_inst if m.name in mut_whitelist ]
    print(f"prepared {len(mutation_apply)} mutations")
    for m in mutation_apply:
        print(f"\t- {m.name}")

    sampler = default_mutation_sampler
    if args.sampler_mod is not None and args.sampler_mod != "":
        sampler = load_module(args.sampler_mod).sampler

    dataset = json.loads(Path(args.dataset).read_text())
    print(f"total {len(dataset)} items loaded from dataset")
    out_variations = []
    out_candidates = []
    for i, entry in enumerate(dataset):
        str_entry = type(entry) is str
        code = entry if str_entry else entry["code"]
        id = str(i if str_entry or "id" not in entry else entry["id"])
        lang = args.lang if str_entry or "language" not in entry else entry["language"]
        candidates = locate_candidates(
            id, code, lang,
            mutation_apply,
            args.validator,
        )
        print(f"found {len(candidates)} candidates for id {id}")
        if args.out_variations != "":
            batch = apply_candidates(
                id, code, lang,
                candidates,
                args.validator,
                args.min_matches,
                args.max_matches,
                args.max_variations,
                sampler
            )
            if str_entry:
                out_variations += batch
            else:
                out_variations += [ entry | b for b in batch ]
        if args.out_candidates != "":
            candidates = [ {"name": name, "match": match.to_json_digest()} for name, match in candidates ]
            if str_entry:
                out_candidates.append({ "code": code, "id": id, "mutation_candidates": candidates })
            else:
                out_candidates.append({ "id": id } | entry | { "mutation_candidates": candidates })

    if args.out_variations != "":
        print(f"total {len(out_variations)} items")
        Path(args.out_variations).write_text(json.dumps(out_variations))
        print(f"variations written to {args.out_variations}")

    if args.out_candidates != "":
        total = sum([ len(c["mutation_candidates"]) for c in out_candidates ])
        print(f"total {total} candidates")
        Path(args.out_candidates).write_text(json.dumps(out_candidates))
        print(f"candidates written to {args.out_candidates}")
    
if __name__ == "__main__":
    main()