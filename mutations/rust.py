"""Rust-specific mutations for edit benchmarks."""

import re

from common.mutation import Mutation, MutationMatch

class UnwrapToQuestionMark(Mutation):
    """Remove `.unwrap()` calls, forcing the model to add them back.

    Simulates accidentally replacing `?` with `.unwrap()` and then removing it,
    leaving a type error.
    """

    def __init__(self):
        super().__init__(
            name="unwrap-to-question-mark",
            category="single-line",
            description_template="An `.unwrap()` call was removed, which may cause a type error.",
            fix_hint="Add back the `.unwrap()` call to handle the Result/Option value.",
        )
        # self.languages = frozenset({"rust"})

    def find_candidates(self, lines: list[str], lang: str = "python") -> list[MutationMatch]:
        pattern = re.compile(r"\.unwrap\(\)")
        matches = []
        for i, line in enumerate(lines):
            stripped = line.rstrip()
            # Skip comment lines
            if stripped.lstrip().startswith("//"):
                continue
            if pattern.search(stripped):
                indent = len(line) - len(line.lstrip())
                mutated = pattern.sub("", stripped, count=1)
                matches.append(MutationMatch(i + 1, stripped, mutated, indent))
        return matches


class FlipMutability(Mutation):
    """Remove `mut` from `&mut` or `let mut` bindings.

    The model must add `mut` back to restore mutability.
    """

    def __init__(self):
        super().__init__(
            name="flip-mutability",
            category="single-line",
            description_template="A mutability qualifier was removed. `{mutated}` is missing `mut`.",
            fix_hint="Add back the `mut` keyword to restore mutability.",
        )
        # self.languages = frozenset({"rust"})

    def find_candidates(self, lines: list[str], lang: str = "python") -> list[MutationMatch]:
        # Order matters: try &mut first (more specific), then let mut
        ref_pattern = re.compile(r"&mut ")
        let_pattern = re.compile(r"\blet mut ")
        matches = []
        for i, line in enumerate(lines):
            stripped = line.rstrip()
            if stripped.lstrip().startswith("//"):
                continue
            indent = len(line) - len(line.lstrip())
            if ref_pattern.search(stripped):
                mutated = ref_pattern.sub("&", stripped, count=1)
                matches.append(MutationMatch(i + 1, stripped, mutated, indent))
            elif let_pattern.search(stripped):
                mutated = let_pattern.sub("let ", stripped, count=1)
                matches.append(MutationMatch(i + 1, stripped, mutated, indent))
        return matches


class RemovePub(Mutation):
    """Remove `pub` or `pub(crate)` visibility qualifier from declarations.

    The model must restore the visibility modifier.
    """

    def __init__(self):
        super().__init__(
            name="remove-pub",
            category="single-line",
            description_template="A visibility qualifier was removed. `{mutated}` should be public.",
            fix_hint="Add back the `pub` (or `pub(crate)`) visibility qualifier.",
        )
        # self.languages = frozenset({"rust"})

    # Matches pub(crate) or plain pub before these declaration keywords
    _PATTERN = re.compile(r"^(\s*)pub(\([^)]+\))?\s+(?=fn|struct|enum|trait|type|const|static|mod|impl|use)")

    def find_candidates(self, lines: list[str], lang: str = "python") -> list[MutationMatch]:
        matches = []
        for i, line in enumerate(lines):
            stripped = line.rstrip()
            if stripped.lstrip().startswith("//"):
                continue
            m = self._PATTERN.match(stripped)
            if m:
                indent = len(m.group(1))
                # Remove the pub / pub(crate) prefix
                mutated = self._PATTERN.sub(r"\1", stripped)
                matches.append(MutationMatch(i + 1, stripped, mutated, indent))
        return matches


class SwapMatchArms(Mutation):
    """Swap two adjacent match arms in a match block.

    Finds consecutive lines of the form `pattern => expr,` at the same
    indentation and swaps them.
    """

    def __init__(self):
        super().__init__(
            name="swap-match-arms",
            category="multi-line",
            description_template="Two match arms are in the wrong order.",
            fix_hint="Swap the two adjacent match arms back to their correct order.",
        )
        # self.languages = frozenset({"rust"})

    # A match arm: optional leading whitespace, then anything => anything, trailing comma
    _ARM_PATTERN = re.compile(r"^(\s+)(.+?)\s*=>\s*(.+),\s*$")

    def find_candidates(self, lines: list[str], lang: str = "python") -> list[MutationMatch]:
        matches = []
        i = 0
        while i < len(lines) - 1:
            line_a = lines[i].rstrip("\n")
            line_b = lines[i + 1].rstrip("\n")

            m_a = self._ARM_PATTERN.match(line_a)
            m_b = self._ARM_PATTERN.match(line_b)

            if m_a and m_b and m_a.group(1) == m_b.group(1):
                indent = len(m_a.group(1))
                original = line_a.rstrip() + "\n" + line_b.rstrip()
                mutated = line_b.rstrip() + "\n" + line_a.rstrip()
                # end_line = i+1 (0-indexed exclusive) = i+2 (per dual convention: end_line = j+1 where j=i+1)
                matches.append(
                    MutationMatch(
                        line_number=i + 1,
                        original=original,
                        mutated=mutated,
                        indent=indent,
                        end_line=i + 2,
                    )
                )
                i += 2  # skip both arms to avoid overlapping swaps
                continue
            i += 1
        return matches

# btree-to-hashmap
# swap-next-last (iterator)
# iter-skip-k (iter().skip(2)) (1 <= k <= 3)
# swap-min-max (more than iterator, and also min_by vs max_by)
# iter-append/remove-rev (iter().rev())
# len() to len() - 1
# first -> last (one way)
# swap all-any
# nth -> nth(i + 1)

MUTATIONS: list[Mutation] = [
    UnwrapToQuestionMark(),
    FlipMutability(),
    RemovePub(),
    SwapMatchArms(),
]
