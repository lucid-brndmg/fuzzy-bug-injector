"""TypeScript/JavaScript-specific mutations for edit benchmarks.

These mutations target TypeScript-specific patterns that don't exist in other languages.
Each is tagged with languages=frozenset({"typescript"}).
"""

import re

from common.mutation import Mutation, MutationMatch


class RemoveOptionalChain(Mutation):
    """Remove `?.` optional chaining operators, replacing with `.`.

    The model must add back `?.` to safely access potentially null/undefined values.
    """

    _PATTERN = re.compile(r"\?\.")

    def __init__(self):
        super().__init__(
            name="remove-optional-chain",
            category="single-line",
            description_template="An optional chaining operator was removed. `{mutated}` may throw on null/undefined.",
            fix_hint="Add back the `?.` optional chaining operator.",
        )
        # self.languages = frozenset({"typescript"})

    def find_candidates(self, lines: list[str], lang: str = "python") -> list[MutationMatch]:
        matches = []
        for i, line in enumerate(lines):
            stripped = line.rstrip()
            if stripped.lstrip().startswith(("//", "#")):
                continue
            if self._PATTERN.search(stripped):
                indent = len(line) - len(line.lstrip())
                mutated = self._PATTERN.sub(".", stripped, count=1)
                matches.append(MutationMatch(i + 1, stripped, mutated, indent))
        return matches


class SwapNullishCoalescing(Mutation):
    """Swap `??` with `||` (different falsy semantics).

    `??` only falls back on null/undefined; `||` falls back on any falsy value.
    The model must restore `??` to preserve correct null-check semantics.
    """

    def __init__(self):
        super().__init__(
            name="swap-nullish-coalescing",
            category="single-line",
            description_template="A nullish coalescing operator was changed to logical OR. `{mutated}` uses the wrong fallback operator.",
            fix_hint="Change `||` back to `??` for correct nullish fallback.",
        )
        # self.languages = frozenset({"typescript"})

    def find_candidates(self, lines: list[str], lang: str = "python") -> list[MutationMatch]:
        matches = []
        for i, line in enumerate(lines):
            stripped = line.rstrip()
            if stripped.lstrip().startswith(("//", "#")):
                continue
            if " ?? " in stripped:
                indent = len(line) - len(line.lstrip())
                mutated = stripped.replace(" ?? ", " || ", 1)
                matches.append(MutationMatch(i + 1, stripped, mutated, indent))
        return matches


class RemoveReadonly(Mutation):
    """Remove `readonly` modifier from property declarations.

    The model must add back `readonly` to restore immutability semantics.
    """

    # Matches `readonly ` as a modifier — after optional indent and/or access keywords
    _PATTERN = re.compile(r"^(\s*(?:(?:public|private|protected|static|abstract|override)\s+)*)readonly ")

    def __init__(self):
        super().__init__(
            name="remove-readonly",
            category="single-line",
            description_template="A `readonly` modifier was removed. `{mutated}` should be immutable.",
            fix_hint="Add back the `readonly` modifier.",
        )
        # self.languages = frozenset({"typescript"})

    def find_candidates(self, lines: list[str], lang: str = "python") -> list[MutationMatch]:
        matches = []
        for i, line in enumerate(lines):
            stripped = line.rstrip()
            if stripped.lstrip().startswith(("//", "#")):
                continue
            m = self._PATTERN.match(stripped)
            if m:
                indent = len(m.group(1))
                mutated = self._PATTERN.sub(r"\1", stripped)
                matches.append(MutationMatch(i + 1, stripped, mutated, indent))
        return matches


class SwapStrictEquality(Mutation):
    """Replace strict equality (`===`/`!==`) with loose equality (`==`/`!=`).

    Strict equality checks type AND value; loose equality coerces types.
    The model must restore `===`/`!==` to preserve correct strict-check semantics.
    """

    def __init__(self):
        super().__init__(
            name="swap-strict-equality",
            category="single-line",
            description_template="A strict equality check was changed to loose. `{mutated}` uses `==` instead of `===`.",
            fix_hint="Change `==` back to `===` (or `!=` back to `!==`) for strict equality.",
        )
        # self.languages = frozenset({"typescript"})

    def find_candidates(self, lines: list[str], lang: str = "python") -> list[MutationMatch]:
        matches = []
        for i, line in enumerate(lines):
            stripped = line.rstrip()
            if stripped.lstrip().startswith(("//", "#")):
                continue
            indent = len(line) - len(line.lstrip())
            # Check !== before === to avoid double-matching a line with both
            if " !== " in stripped:
                mutated = stripped.replace(" !== ", " != ", 1)
                matches.append(MutationMatch(i + 1, stripped, mutated, indent))
            elif " === " in stripped:
                mutated = stripped.replace(" === ", " == ", 1)
                matches.append(MutationMatch(i + 1, stripped, mutated, indent))
        return matches


MUTATIONS: list[Mutation] = [
    RemoveOptionalChain(),
    SwapNullishCoalescing(),
    RemoveReadonly(),
    SwapStrictEquality(),
]
