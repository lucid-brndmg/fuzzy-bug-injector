"""Go-specific mutation definitions for edit benchmarks."""

import re

from common.mutation import Mutation, MutationMatch

class RemoveErrCheck(Mutation):
    """Remove an `if err != nil { ... }` error check block."""

    def __init__(self):
        super().__init__(
            name="remove-err-check",
            category="multi-line",
            description_template="An error check was removed. The code should handle the error.",
            fix_hint="Restore the missing `if err != nil` error check.",
        )
        # self.languages = frozenset({"go"})

    def find_candidates(self, lines: list[str], lang: str = "python") -> list[MutationMatch]:
        matches = []
        pattern = re.compile(r"^\s*if err != nil \{")
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.rstrip()
            if pattern.match(stripped):
                indent = len(line) - len(line.lstrip())
                block_lines = [stripped]
                j = i + 1
                while j < len(lines):
                    bl = lines[j].rstrip()
                    block_lines.append(bl)
                    bl_stripped = bl.lstrip()
                    bl_indent = len(bl) - len(bl_stripped)
                    if bl_stripped == "}" and bl_indent <= indent:
                        break
                    j += 1
                else:
                    # No closing brace found
                    i += 1
                    continue

                # block_lines: [if line, ...body lines..., }]
                body_lines = block_lines[1:-1]
                if 1 <= len(body_lines) <= 4:
                    matches.append(
                        MutationMatch(
                            line_number=i + 1,
                            original="\n".join(block_lines),
                            mutated="",
                            indent=indent,
                            end_line=j + 1,
                        )
                    )
            i += 1
        return matches


class SwapShortAssign(Mutation):
    """Swap `:=` with `=` to break short variable declaration."""

    def __init__(self):
        super().__init__(
            name="swap-short-assign",
            category="single-line",
            description_template="A short variable declaration was changed to assignment. `{mutated}` uses the wrong operator.",
            fix_hint="Change `=` back to `:=` for the short variable declaration.",
        )
        # self.languages = frozenset({"go"})

    def find_candidates(self, lines: list[str], lang: str = "python") -> list[MutationMatch]:
        matches = []
        for i, line in enumerate(lines):
            stripped = line.rstrip()
            if stripped.lstrip().startswith("//"):
                continue
            if " := " in stripped:
                indent = len(line) - len(line.lstrip())
                mutated = stripped.replace(" := ", " = ", 1)
                matches.append(MutationMatch(i + 1, stripped, mutated, indent))
        return matches


class FlipExport(Mutation):
    """Flip the export status of a function or type by changing first letter case."""

    def __init__(self):
        super().__init__(
            name="flip-export",
            category="single-line",
            description_template="An exported name was made unexported (or vice versa). `{mutated}` has the wrong visibility.",
            fix_hint="Fix the capitalization of the function/type name to restore the correct export status.",
        )
        # self.languages = frozenset({"go"})

    def find_candidates(self, lines: list[str], lang: str = "python") -> list[MutationMatch]:
        matches = []
        pattern = re.compile(r"^(\s*(?:func|type)\s+)([A-Za-z]\w*)")
        for i, line in enumerate(lines):
            stripped = line.rstrip()
            if stripped.lstrip().startswith("//"):
                continue
            m = pattern.match(stripped)
            if m:
                name = m.group(2)
                if name[0].isupper():
                    new_name = name[0].lower() + name[1:]
                else:
                    new_name = name[0].upper() + name[1:]
                mutated = stripped[: m.start(2)] + new_name + stripped[m.end(2) :]
                indent = len(line) - len(line.lstrip())
                matches.append(MutationMatch(i + 1, stripped, mutated, indent))
        return matches


class RemoveDefer(Mutation):
    """Remove the `defer` keyword from a defer statement."""

    def __init__(self):
        super().__init__(
            name="remove-defer",
            category="single-line",
            description_template="A `defer` keyword was removed. `{mutated}` should be deferred.",
            fix_hint="Add `defer` back before the function call.",
        )
        # self.languages = frozenset({"go"})

    def find_candidates(self, lines: list[str], lang: str = "python") -> list[MutationMatch]:
        matches = []
        pattern = re.compile(r"^(\s*)defer\s+(.+)")
        for i, line in enumerate(lines):
            stripped = line.rstrip()
            if stripped.lstrip().startswith("//"):
                continue
            m = pattern.match(stripped)
            if m:
                indent = len(m.group(1))
                mutated = m.group(1) + m.group(2)
                matches.append(MutationMatch(i + 1, stripped, mutated, indent))
        return matches


MUTATIONS: list[Mutation] = [
    RemoveErrCheck(),
    SwapShortAssign(),
    FlipExport(),
    RemoveDefer(),
]
