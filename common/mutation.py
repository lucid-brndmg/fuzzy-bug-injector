from dataclasses import dataclass, field

from common.utils import is_disjoint_intervals

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

    def json_digest(self):
        return {
            "line_number": self.line_number,
            "original": self.original,
            "mutated": self.mutated,
            "indent": self.indent,
            "end_line": self.end_line if self.end_line is not None else self.line_number,
            "extra_sites": self.extra_sites
        }

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