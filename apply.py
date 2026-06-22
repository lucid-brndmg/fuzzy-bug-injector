import argparse
import json
from pathlib import Path
import random

from common.mutation import default_mutation_sampler, json_digest_to_mutation_match
from common.utils import load_module
from generate import apply_candidates

def main():
    print("Fuzzy Bug Injector (github.com/lucid-brndmg/fuzzy-bug-injector)")
    parser = argparse.ArgumentParser(description="Generate mutation variations to source code files")

    parser.add_argument("--dataset", required=True, help="A valid JSON dataset file")
    parser.add_argument("--out-variations", default="out_variations.json", help="The output JSON file having mutated variations")
    parser.add_argument("--validator", help="A validator script for checking validity of each variation")
    parser.add_argument("--seed", type=int, help="Random seed for reproducibility")
    parser.add_argument("--sampler-mod", type=str, default="", help="A sampler module (.py file)")
    parser.add_argument("--min-matches", type=int, default=1, help="Minimum number of places to mutate")
    parser.add_argument("--max-matches", type=int, default=5, help="Maximum number of places to mutate")
    parser.add_argument("--max-variations", type=int, default=10, help="Maximum number of variations to generate for a source code")
    parser.add_argument("--lang", type=str, default="", help="Specified language if omitted in dataset")
    

    args = parser.parse_args()
    if args.seed is not None:
        random.seed(args.seed)
    
    sampler = default_mutation_sampler
    if args.sampler_mod is not None and args.sampler_mod != "":
        sampler = load_module(args.sampler_mod).sampler

    dataset = json.loads(Path(args.dataset).read_text())
    print(f"total {len(dataset)} items loaded from dataset")

    out_variations = []
    for entry in dataset:
        code = entry["code"]
        id = entry["id"]
        lang = args.lang if "language" not in entry else entry["language"]
        candidates = [ (d["name"], json_digest_to_mutation_match(d["match"])) for d in entry["mutation_candidates"]]
        batch = apply_candidates(
            id, code, lang,
            candidates,
            args.validator,
            args.min_matches,
            args.max_matches,
            args.max_variations,
            sampler
        )
        del entry["mutation_candidates"]
        out_variations += [ entry | b for b in batch ]

    if args.out_variations != "":
        print(f"total {len(out_variations)} items")
        Path(args.out_variations).write_text(json.dumps(out_variations))
        print(f"variations written to {args.out_variations}")
        

if __name__ == "__main__":
    main()