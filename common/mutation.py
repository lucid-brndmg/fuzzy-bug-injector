from dataclasses import dataclass, field
import random
from typing import Any, Generator

from common.utils import is_disjoint_intervals, iter_disjoint_subsets

@dataclass
class MutationMatch:
    line_number: int | None  # 1-indexed, primary line
    original: str  # original content (may be multi-line, joined by \n)
    mutated: str  # mutated content (empty string = delete)
    indent: int  # leading spaces of primary line

    # For multi-line mutations
    end_line: int | None = None  # inclusive end line (None = single line)

    # For multi-site mutations: additional (line, original, mutated) tuples
    extra_sites: list[tuple[int, str, str, int | None]] = field(default_factory=list)
    
    def intervals(self) -> list[tuple[int, int]]:
        main_lines = [(self.line_number, self.end_line if self.end_line is not None else self.line_number)] if self.line_number is not None else []
        return [(line, line + len(new.split("\n")) - 1) for (line, _1, new, _2) in self.extra_sites] + main_lines
    
    def is_disjoint(self, other) -> bool:
        i1 = self.intervals()
        i2 = other.intervals()
        for x in i1:
            for y in i2:
                if not is_disjoint_intervals(x, y):
                    return False
        return True

    def to_json_digest(self):
        return {
            "line_number": self.line_number,
            "original": self.original,
            "mutated": self.mutated,
            "indent": self.indent,
            "end_line": self.end_line if self.end_line is not None else self.line_number,
            "extra_sites": self.extra_sites
        }

def json_digest_to_mutation_match(digest: dict) -> MutationMatch:
    return MutationMatch(digest["line_number"], digest["original"], digest["mutated"], digest["indent"], digest["end_line"], digest["extra_sites"])

def apply_mutations(lines: list[str], muts: list[MutationMatch]) -> list[str]:
    # muts must be disjoint
    result = list(lines)
    digests = []
    for mut in muts:
        if mut.line_number is not None:
            # otherwise, this is multi-site mutation
            digests.append((
                mut.line_number,
                mut.end_line if mut.end_line is not None else mut.line_number,
                mut.mutated,
                len(mut.mutated.split("\n")),
                mut.indent
            ))
        for (line, _original, mutated, indent) in mut.extra_sites:
            digests.append((
                line,
                line,
                mutated,
                len(mutated.split("\n")),
                indent if indent is not None else mut.indent
            ))
    digests = sorted(digests, key = lambda it : it[0], reverse=False)
    offset = 0
    for (start, end, new, new_lines, ind) in digests:
        idx = start - 1 + offset
        ind = len(result[idx]) - len(result[idx].lstrip()) if idx < len(result) else 0
        result[idx] = " " * ind + new.lstrip() + "\n"
        offset += new_lines - (end - start + 1)

    return result

@dataclass
class Mutation:
    name: str
    category: str
    description_template: str
    fix_hint: str
    # languages: frozenset[str] = ALL_LANGUAGES

    def find_candidates(self, lines: list[str], lang: str = "python") -> list[MutationMatch]:
        raise NotImplementedError

    def describe(self, match: MutationMatch) -> str:
        return self.description_template.format(original=match.original.strip(), mutated=match.mutated.strip())


def default_mutation_sampler(
    candidates: list[tuple[str, MutationMatch]],
    min_mut: int,
    max_mut: int,
) -> Generator[list[tuple[str, MutationMatch]], Any, None]:
    def check_disjoint(a, b):
        (_name1, mat1) = a
        (_name2, mat2) = b
        return mat1.is_disjoint(mat2)
    random.shuffle(candidates)
    ps = iter_disjoint_subsets(candidates, check_disjoint, min_mut, max_mut, 2**32)
    # 2**24 would be a reasonable range
    if len(candidates) <= 24:
        subsets = list(ps)
        random.shuffle(subsets)
        yield from subsets
    else:
        yield from ps