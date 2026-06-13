import re
from common.mutation import Mutation, MutationMatch

class IndentBlock(Mutation):
    """Shift indentation of a block by one level (4 spaces).

    The model must fix the indentation of a code block that's been
    indented too far — a common paste/refactor error.
    """

    def __init__(self):
        super().__init__(
            name="indent-block",
            category="multi-line",
            description_template="A block of code has incorrect indentation.",
            fix_hint="A code block has been indented by one extra level. Fix the indentation.",
            # languages=frozenset({"python"}),
        )

    def find_candidates(self, lines: list[str], lang: str = "python") -> list[MutationMatch]:
        matches = []
        i = 0
        while i < len(lines) - 4:
            line = lines[i].rstrip()
            content = line.lstrip()

            if content and content.endswith(":") and any(content.startswith(kw) for kw in ("if ", "for ", "while ", "with ", "try:")):
                indent = len(lines[i]) - len(lines[i].lstrip())
                block_indent = indent + 4

                block_start = i + 1
                block_end = block_start
                while block_end < len(lines) and block_end < block_start + 8:
                    bl = lines[block_end]
                    if bl.strip() == "":
                        block_end += 1
                        continue
                    bl_indent = len(bl) - len(bl.lstrip())
                    if bl_indent >= block_indent:
                        block_end += 1
                    else:
                        break

                block_len = block_end - block_start
                if 3 <= block_len <= 6:
                    original_block = [lines[j].rstrip() for j in range(block_start, block_end)]
                    mutated_block = ["    " + lines[j].rstrip() for j in range(block_start, block_end)]
                    matches.append(
                        MutationMatch(
                            line_number=block_start + 1,
                            original="\n".join(original_block),
                            mutated="\n".join(mutated_block),
                            indent=block_indent,
                            end_line=block_end,
                        )
                    )
            i += 1
        return matches



class UnwrapBlock(Mutation):
    """Remove an if-guard or try/except wrapper but keep the body.

    The mutation removes the wrapper and de-indents the body. The model
    must re-add the wrapper and re-indent.
    """

    def __init__(self):
        super().__init__(
            name="unwrap-block",
            category="multi-line",
            description_template="A conditional guard or error handler has been removed. The code runs unconditionally when it shouldn't.",
            fix_hint="A guard clause (if/try) was removed. The body code needs to be re-wrapped.",
            # languages=frozenset({"python"}),
        )

    def find_candidates(self, lines: list[str], lang: str = "python") -> list[MutationMatch]:
        matches = []
        for i, line in enumerate(lines):
            content = line.rstrip().lstrip()
            if not content.endswith(":"):
                continue
            if not (content.startswith("if ") or content.startswith("try:")):
                continue
            indent = len(line) - len(line.lstrip())
            block_indent = indent + 4

            block_start = i + 1
            block_end = block_start
            while block_end < len(lines):
                bl = lines[block_end]
                if bl.strip() == "":
                    block_end += 1
                    continue
                bl_indent = len(bl) - len(bl.lstrip())
                if bl_indent >= block_indent:
                    block_end += 1
                else:
                    break

            block_len = block_end - block_start
            if 2 <= block_len <= 5:
                original_lines = [lines[j].rstrip() for j in range(i, block_end)]
                mutated_lines = []
                for j in range(block_start, block_end):
                    bl = lines[j]
                    if bl.strip() == "":
                        mutated_lines.append("")
                    elif bl.startswith(" " * block_indent):
                        mutated_lines.append(" " * indent + bl[block_indent:].rstrip())
                    else:
                        mutated_lines.append(bl.rstrip())

                matches.append(
                    MutationMatch(
                        line_number=i + 1,
                        original="\n".join(original_lines),
                        mutated="\n".join(mutated_lines),
                        indent=indent,
                        end_line=block_end,
                    )
                )
        return matches



class SwapIfElse(Mutation):
    """Swap the if-body and else-body of an if/else statement.

    The condition stays the same but the branches are reversed. Tests the
    model's ability to recognise swapped logic in a multi-line context.
    """

    def __init__(self):
        super().__init__(
            name="swap-if-else",
            category="multi-line",
            description_template="The if and else branches are swapped.",
            fix_hint="The if-body and else-body have been swapped. Swap them back.",
        )

    def _collect_body(self, lines: list[str], start: int, block_indent: int) -> int:
        """Return exclusive end index of the block starting at lines[start]."""
        j = start
        while j < len(lines):
            bl = lines[j]
            if bl.strip() == "":
                j += 1
                continue
            if len(bl) - len(bl.lstrip()) >= block_indent:
                j += 1
            else:
                break
        return j

    def find_candidates(self, lines: list[str], lang: str = "python") -> list[MutationMatch]:
        matches = []
        i = 0
        while i < len(lines):
            line = lines[i]
            content = line.rstrip().lstrip()

            # Must be an if statement (not elif, not a comment)
            if not (content.startswith("if ") and content.endswith(":")):
                i += 1
                continue

            if_indent = len(line) - len(line.lstrip())

            # Detect block indent from the first non-blank body line
            block_indent = if_indent + 4
            for probe in range(i + 1, min(i + 6, len(lines))):
                if lines[probe].strip():
                    block_indent = len(lines[probe]) - len(lines[probe].lstrip())
                    break

            if block_indent <= if_indent:
                i += 1
                continue

            # Collect if-body
            if_body_start = i + 1
            if_body_end = self._collect_body(lines, if_body_start, block_indent)

            if_body_nonblank = [lines[k] for k in range(if_body_start, if_body_end) if lines[k].strip()]
            if not (1 <= len(if_body_nonblank) <= 5):
                i += 1
                continue

            # Find else: (at the same indent level as the if)
            else_idx = if_body_end
            # _collect_body already stops at the else: line (lower indent), but
            # if_body_end could sit on it or on a trailing blank – advance past blanks.
            while else_idx < len(lines) and not lines[else_idx].strip():
                else_idx += 1

            if else_idx >= len(lines):
                i += 1
                continue

            else_content = lines[else_idx].rstrip().lstrip()
            else_indent = len(lines[else_idx]) - len(lines[else_idx].lstrip())

            if else_content != "else:" or else_indent != if_indent:
                i += 1
                continue

            # Collect else-body
            else_body_start = else_idx + 1
            else_body_end = self._collect_body(lines, else_body_start, block_indent)

            else_body_nonblank = [lines[k] for k in range(else_body_start, else_body_end) if lines[k].strip()]
            if not (1 <= len(else_body_nonblank) <= 5):
                i += 1
                continue

            # Reject if either body contains nested if/else
            def has_nested(body_lines: list[str]) -> bool:
                for bl in body_lines:
                    c = bl.lstrip()
                    if c.startswith(("if ", "else:", "elif ")):
                        return True
                return False

            if has_nested(if_body_nonblank) or has_nested(else_body_nonblank):
                i += 1
                continue

            # Build original (full range) and mutated (bodies swapped) texts
            original_parts = [lines[j].rstrip() for j in range(i, else_body_end)]

            if_line_text = lines[i].rstrip()
            else_kw_text = lines[else_idx].rstrip()
            if_body_text = [lines[j].rstrip() for j in range(if_body_start, if_body_end)]
            else_body_text = [lines[j].rstrip() for j in range(else_body_start, else_body_end)]

            mutated_parts = [if_line_text] + else_body_text + [else_kw_text] + if_body_text

            matches.append(
                MutationMatch(
                    line_number=i + 1,
                    original="\n".join(original_parts),
                    mutated="\n".join(mutated_parts),
                    indent=if_indent,
                    end_line=else_body_end,
                )
            )

            i = else_body_end
        return matches


class SwapMethods(Mutation):
    """Swap two adjacent function/method definitions.

    Tests the ability to move multi-line blocks precisely.
    """

    def __init__(self):
        super().__init__(
            name="swap-methods",
            category="multi-line-multi-site",
            description_template="Two adjacent methods have been swapped and are in the wrong order.",
            fix_hint="Two adjacent function/method definitions need to be swapped back to their correct order.",
            # languages=frozenset({"python"}),
        )

    def find_candidates(self, lines: list[str], lang: str = "python") -> list[MutationMatch]:
        matches = []
        func_ranges: list[tuple[int, int, str]] = []
        def_pattern = re.compile(r"^(\s*)def\s+(\w+)\s*\(")

        for i, line in enumerate(lines):
            m = def_pattern.match(line)
            if m:
                func_ranges.append((i, 0, m.group(2)))

        for idx in range(len(func_ranges)):
            start = func_ranges[idx][0]
            end = func_ranges[idx + 1][0] if idx + 1 < len(func_ranges) else len(lines)
            func_ranges[idx] = (start, end, func_ranges[idx][2])

        for idx in range(len(func_ranges) - 1):
            a_start, a_end, a_name = func_ranges[idx]
            b_start, b_end, b_name = func_ranges[idx + 1]

            if b_start != a_end:
                continue

            a_indent = len(lines[a_start]) - len(lines[a_start].lstrip())
            b_indent = len(lines[b_start]) - len(lines[b_start].lstrip())
            if a_indent != b_indent:
                continue

            a_len = a_end - a_start
            b_len = b_end - b_start
            if a_len < 3 or b_len < 3 or a_len > 30 or b_len > 30:
                continue

            a_block = [lines[j].rstrip() for j in range(a_start, a_end)]
            b_block = [lines[j].rstrip() for j in range(b_start, b_end)]

            matches.append(
                MutationMatch(
                    line_number=a_start + 1,
                    original="\n".join(a_block + b_block),
                    mutated="\n".join(b_block + a_block),
                    indent=a_indent,
                    end_line=b_end,
                )
            )

        return matches

    def describe(self, match: MutationMatch) -> str:
        return (
            "Two adjacent function definitions have been swapped and are now in the wrong order. "
            "The code may still run but the logical ordering is incorrect. Swap them back."
        )


MUTATIONS: list[Mutation] = [
    IndentBlock(),
    UnwrapBlock(),
    SwapIfElse(),
    SwapMethods()
]