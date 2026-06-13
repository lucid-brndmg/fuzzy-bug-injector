"""Mutation definitions for edit benchmarks.

Organized by the kind of edit the model must perform, not just the
kind of bug introduced. The edit difficulty matrix:

                    single-line          multi-line
  single-site   | swap operators     | indent-block, unwrap-block
  multi-site    | rename-partial     | swap-methods
"""

import re
from common.mutation import Mutation, MutationMatch


# ── Single-site, single-line mutations ────────────────────────────────


class SwapComparison(Mutation):
    SWAPS = [
        ("<= ", ">= "), 
        (">= ", "<= "), 
        ("< ", "> "), 
        ("> ", "< ")
    ]

    def __init__(self):
        super().__init__(
            name="swap-comparison",
            category="single-line",
            description_template="A comparison operator has been swapped. `{mutated}` uses the wrong comparison direction.",
            fix_hint="Check the comparison operator direction.",
        )

    def find_candidates(self, lines: list[str], lang: str = "python") -> list[MutationMatch]:
        matches = []
        for i, line in enumerate(lines):
            stripped = line.rstrip()
            if stripped.lstrip().startswith(("#", "//")):
                continue
            # Skip Rust generics/lifetimes: <'a, T>, <T: Clone>
            if re.search(r"<['\w]", stripped) and "=>" not in stripped:
                continue
            for old, new in self.SWAPS:
                if old in stripped and "=>" not in stripped and "->" not in stripped:
                    indent = len(line) - len(line.lstrip())
                    matches.append(MutationMatch(i + 1, stripped, stripped.replace(old, new, 1), indent))
                    break
        return matches

class ConfuseComparison(Mutation):
    SWAPS = [
        ("<= ", "< "), 
        (">= ", "> "), 
        ("< ", "<= "), 
        ("> ", ">= ")
    ]
    def __init__(self):
        super().__init__(
            name="confuse-comparison",
            category="single-line",
            description_template="A comparison operator has been swapped. `{mutated}` uses the wrong comparison direction.",
            fix_hint="Check the comparison operator direction.",
        )
    def find_candidates(self, lines: list[str], lang: str = "python") -> list[MutationMatch]:
        matches = []
        for i, line in enumerate(lines):
            stripped = line.rstrip()
            if stripped.lstrip().startswith(("#", "//")):
                continue
            # Skip Rust generics/lifetimes: <'a, T>, <T: Clone>
            if re.search(r"<['\w]", stripped) and "=>" not in stripped:
                continue
            for old, new in self.SWAPS:
                if old in stripped and "=>" not in stripped and "->" not in stripped:
                    indent = len(line) - len(line.lstrip())
                    matches.append(MutationMatch(i + 1, stripped, stripped.replace(old, new, 1), indent))
                    break
        return matches

class SwapEquality(Mutation):
    def __init__(self):
        super().__init__(
            name="swap-equality",
            category="single-line",
            description_template="An equality check has been inverted. `{mutated}` uses the wrong equality operator.",
            fix_hint="Check whether == or != is correct.",
        )

    def find_candidates(self, lines: list[str], lang: str = "python") -> list[MutationMatch]:
        matches = []
        for i, line in enumerate(lines):
            stripped = line.rstrip()
            if stripped.lstrip().startswith(("#", "//")):
                continue
            indent = len(line) - len(line.lstrip())
            # Check strict equality first (TypeScript/JS) to avoid partial match
            if " !== " in stripped:
                matches.append(MutationMatch(i + 1, stripped, stripped.replace(" !== ", " === ", 1), indent))
            elif " === " in stripped:
                matches.append(MutationMatch(i + 1, stripped, stripped.replace(" === ", " !== ", 1), indent))
            elif " != " in stripped:
                matches.append(MutationMatch(i + 1, stripped, stripped.replace(" != ", " == ", 1), indent))
            elif " == " in stripped:
                matches.append(MutationMatch(i + 1, stripped, stripped.replace(" == ", " != ", 1), indent))
        return matches


class FlipBoolean(Mutation):
    def __init__(self):
        super().__init__(
            name="flip-boolean",
            category="single-line",
            description_template="A boolean literal has been flipped. `{mutated}` has the wrong truth value.",
            fix_hint="Check boolean literals for correctness.",
        )

    def find_candidates(self, lines: list[str], lang: str = "python") -> list[MutationMatch]:
        matches = []
        for i, line in enumerate(lines):
            stripped = line.rstrip()
            if stripped.lstrip().startswith(("#", "//")):
                continue
            indent = len(line) - len(line.lstrip())
            if "True" in stripped:
                matches.append(MutationMatch(i + 1, stripped, stripped.replace("True", "False", 1), indent))
            elif "False" in stripped:
                matches.append(MutationMatch(i + 1, stripped, stripped.replace("False", "True", 1), indent))
            elif re.search(r"\btrue\b", stripped):
                matches.append(MutationMatch(i + 1, stripped, re.sub(r"\btrue\b", "false", stripped, count=1), indent))
            elif re.search(r"\bfalse\b", stripped):
                matches.append(MutationMatch(i + 1, stripped, re.sub(r"\bfalse\b", "true", stripped, count=1), indent))
        return matches


class SwapLogical(Mutation):
    def __init__(self):
        super().__init__(
            name="swap-logical",
            category="single-line",
            description_template="A logical operator has been swapped. `{mutated}` uses the wrong logical connective.",
            fix_hint="Check whether and/or (&&/||) is correct.",
        )

    def find_candidates(self, lines: list[str], lang: str = "python") -> list[MutationMatch]:
        matches = []
        for i, line in enumerate(lines):
            stripped = line.rstrip()
            if stripped.lstrip().startswith(("#", "//")):
                continue
            indent = len(line) - len(line.lstrip())
            if " and " in stripped:
                matches.append(MutationMatch(i + 1, stripped, stripped.replace(" and ", " or ", 1), indent))
            elif " or " in stripped:
                matches.append(MutationMatch(i + 1, stripped, stripped.replace(" or ", " and ", 1), indent))
            elif " && " in stripped:
                matches.append(MutationMatch(i + 1, stripped, stripped.replace(" && ", " || ", 1), indent))
            elif " || " in stripped:
                matches.append(MutationMatch(i + 1, stripped, stripped.replace(" || ", " && ", 1), indent))
        return matches


class RemoveNegation(Mutation):
    _NOT_PATTERN = re.compile(r"\bnot\s+")

    def __init__(self):
        super().__init__(
            name="remove-negation",
            category="single-line",
            description_template="A logical negation was accidentally removed. `{mutated}` is missing a `not`.",
            fix_hint="A `not` operator was removed from a boolean expression.",
        )

    def find_candidates(self, lines: list[str], lang: str = "python") -> list[MutationMatch]:
        matches = []
        for i, line in enumerate(lines):
            stripped = line.rstrip()
            if stripped.lstrip().startswith(("#", "//")):
                continue
            indent = len(line) - len(line.lstrip())
            for m in self._NOT_PATTERN.finditer(stripped):
                before = stripped[: m.start()]
                after_not = stripped[m.end() :]
                # Skip 'is not'
                if before.endswith("is "):
                    continue
                # Skip 'not in'
                if re.match(r"in\b", after_not):
                    continue
                mutated = before + after_not
                matches.append(MutationMatch(i + 1, stripped, mutated, indent))
                break
        return matches


class OffByOne(Mutation):
    def __init__(self):
        super().__init__(
            name="off-by-one",
            category="single-line",
            description_template="An off-by-one error: a numeric constant in `{mutated}` is wrong by 1.",
            fix_hint="Check numeric constants for off-by-one errors.",
        )

    def find_candidates(self, lines: list[str], lang: str = "python") -> list[MutationMatch]:
        matches = []
        for i, line in enumerate(lines):
            stripped = line.rstrip()
            if stripped.lstrip().startswith(("#", "//")):
                continue
            indent = len(line) - len(line.lstrip())
            for m in re.finditer(r"(?<![.\w])(\d+)(?![.\w])", stripped):
                val = int(m.group(1))
                if 2 <= val <= 100:
                    mutated = stripped[: m.start(1)] + str(val + 1) + stripped[m.end(1) :]
                    matches.append(MutationMatch(i + 1, stripped, mutated, indent))
                    break
        return matches


class SwapArithmetic(Mutation):
    SWAPS = [(" + ", " - "), (" - ", " + "), (" * ", " / "), (" / ", " * ")]

    def __init__(self):
        super().__init__(
            name="swap-arithmetic",
            category="single-line",
            description_template="An arithmetic operator has been swapped. `{mutated}` uses the wrong operator.",
            fix_hint="Check the arithmetic operator (+, -, *, /).",
        )

    def find_candidates(self, lines: list[str], lang: str = "python") -> list[MutationMatch]:
        matches = []
        for i, line in enumerate(lines):
            stripped = line.rstrip()
            content = stripped.lstrip()
            # Skip comment lines and import lines
            if content.startswith(("#", "//", "import ", "from ")):
                continue
            indent = len(line) - len(line.lstrip())
            for old, new in self.SWAPS:
                if old not in stripped:
                    continue
                idx = stripped.find(old)
                # Avoid ** (power): char adjacent to * must not be another *
                if old == " * ":
                    before_idx = idx - 1
                    after_idx = idx + len(old)
                    if (before_idx >= 0 and stripped[before_idx] == "*") or (after_idx < len(stripped) and stripped[after_idx] == "*"):
                        continue
                # Avoid // (floor div): char adjacent to / must not be another /
                if old == " / ":
                    before_idx = idx - 1
                    after_idx = idx + len(old)
                    if (before_idx >= 0 and stripped[before_idx] == "/") or (after_idx < len(stripped) and stripped[after_idx] == "/"):
                        continue
                # Avoid augmented assignments: +=, -=, *=, /=
                after_op_idx = idx + len(old.rstrip())
                if after_op_idx < len(stripped) and stripped[after_op_idx] == "=":
                    continue
                matches.append(MutationMatch(i + 1, stripped, stripped.replace(old, new, 1), indent))
                break
        return matches


class SwapArgs(Mutation):
    def __init__(self):
        super().__init__(
            name="swap-args",
            category="single-line",
            description_template="Function arguments have been swapped in `{mutated}`.",
            fix_hint="Check the argument order in function calls.",
        )

    def find_candidates(self, lines: list[str], lang: str = "python") -> list[MutationMatch]:
        matches = []
        pattern = re.compile(r"(\w+)\((\w+),\s*(\w+)\)")
        for i, line in enumerate(lines):
            stripped = line.rstrip()
            if stripped.lstrip().startswith(("#", "//")):
                continue
            indent = len(line) - len(line.lstrip())
            m = pattern.search(stripped)
            if m and m.group(2) != m.group(3):
                mutated = stripped[: m.start(2)] + m.group(3) + ", " + m.group(2) + stripped[m.end(3) :]
                matches.append(MutationMatch(i + 1, stripped, mutated, indent))
        return matches


class SwapAugmentedAssign(Mutation):
    SWAPS = [(" += ", " -= "), (" -= ", " += "), (" *= ", " /= "), (" /= ", " *= ")]

    def __init__(self):
        super().__init__(
            name="swap-augmented-assign",
            category="single-line",
            description_template="An augmented assignment operator has been swapped. `{mutated}` uses the wrong operator.",
            fix_hint="Check the augmented assignment operator (+=, -=, *=, /=).",
        )

    def find_candidates(self, lines: list[str], lang: str = "python") -> list[MutationMatch]:
        matches = []
        for i, line in enumerate(lines):
            stripped = line.rstrip()
            if stripped.lstrip().startswith(("#", "//")):
                continue
            for old, new in self.SWAPS:
                if old in stripped:
                    indent = len(line) - len(line.lstrip())
                    matches.append(MutationMatch(i + 1, stripped, stripped.replace(old, new, 1), indent))
                    break
        return matches


class UnicodeHyphen(Mutation):
    """Replace an ASCII hyphen-minus with a visually identical unicode en-dash inside a string literal.

    This is a high-difficulty sneaky mutation: the characters look identical in most fonts.
    The model must detect a character-level difference (U+002D vs U+2013).
    """

    _DQ = re.compile(r'"[^"]*-[^"]*"')
    _SQ = re.compile(r"'[^']*-[^']*'")

    def __init__(self):
        super().__init__(
            name="unicode-hyphen",
            category="single-line",
            description_template="A string literal contains a lookalike unicode dash instead of an ASCII hyphen.",
            fix_hint="A unicode en-dash (U+2013) was substituted for an ASCII hyphen-minus (U+002D) in a string.",
        )

    def find_candidates(self, lines: list[str], lang: str = "python") -> list[MutationMatch]:
        matches = []
        for i, line in enumerate(lines):
            stripped = line.rstrip()
            if stripped.lstrip().startswith(("#", "//")):
                continue
            indent = len(line) - len(line.lstrip())
            for pattern in (self._DQ, self._SQ):
                m = pattern.search(stripped)
                if not m:
                    continue
                # Skip f-strings: the hyphen inside {expr} is arithmetic, not a string char
                if m.start() > 0 and stripped[m.start() - 1].lower() == "f":
                    continue
                full_match = m.group(0)
                opening_quote = full_match[0]
                content = full_match[1:-1]
                new_content = content.replace("-", "\u2013", 1)
                new_full = opening_quote + new_content + opening_quote
                mutated = stripped[: m.start()] + new_full + stripped[m.end() :]
                matches.append(MutationMatch(i + 1, stripped, mutated, indent))
                break  # one match per line
        return matches


class DeleteStatement(Mutation):
    """Delete a single deletable statement line.

    Target statement types: variable/attribute assignments, augmented assignments,
    expression-call statements, and return statements. Excludes structural
    keywords (def, class, if, for, etc.) and lines that are the sole statement
    in their containing block (which would produce a SyntaxError).
    """

    _SKIP_RE = re.compile(
        r"^(?:def |async def |class |"
        r"if |elif |else:|else |"
        r"for |async for |while |"
        r"with |async with |"
        r"try:|except|finally:|finally |"
        r"import |from |@|#)"
    )
    # Assignment: simple (x = ...) or augmented (x += ...) or attribute/subscript (self.x = ...)
    _ASSIGNMENT_RE = re.compile(r"^[\w][\w.]*(?:\[.*?\])?\s*[+\-*/%&|^@]?=(?!=)\s*.+")
    # Return statement
    _RETURN_RE = re.compile(r"^return\b")
    # Standalone expression call: identifier or dotted name followed by (
    _EXPR_CALL_RE = re.compile(r"^[\w][\w.]*\s*\(")

    def __init__(self):
        super().__init__(
            name="delete-statement",
            category="single-line",
            description_template="A critical statement was deleted from the code.",
            fix_hint="A statement is missing. Find where it should be and restore it.",
        )

    def find_candidates(self, lines: list[str], lang: str = "python") -> list[MutationMatch]:
        matches = []
        for i, line in enumerate(lines):
            content = line.lstrip()

            # Skip empty and whitespace-only lines
            if not content.strip():
                continue

            # Skip non-deletable structural keywords, decorators, comments
            if self._SKIP_RE.match(content):
                continue

            stripped = line.rstrip()
            indent = len(line) - len(line.lstrip())

            # Must match one of the target statement patterns
            if not (self._ASSIGNMENT_RE.match(content) or self._RETURN_RE.match(content) or self._EXPR_CALL_RE.match(content)):
                continue

            # Skip if this is the only statement in its containing block (would cause SyntaxError)
            if self._is_only_in_block(lines, i, indent):
                continue

            matches.append(MutationMatch(i + 1, stripped, "", indent))

        return matches

    def _is_only_in_block(self, lines: list[str], idx: int, indent: int) -> bool:
        """Return True if this line is the only statement in its enclosing block."""
        if indent == 0:
            return False  # Module-level: never structurally required

        # Walk backwards to find the enclosing block header (a line ending with ':' at lower indent)
        for j in range(idx - 1, -1, -1):
            bl = lines[j]
            if not bl.strip():
                continue
            bl_indent = len(bl) - len(bl.lstrip())
            if bl_indent < indent:
                if not bl.rstrip().endswith(":"):
                    return False  # Enclosing context doesn't introduce a block
                # Count non-empty, non-comment sibling statements at same indent inside this block
                count = 0
                for k in range(j + 1, len(lines)):
                    sibling = lines[k]
                    if not sibling.strip():
                        continue
                    sib_indent = len(sibling) - len(sibling.lstrip())
                    if sib_indent < indent:
                        break
                    if sib_indent == indent and not sibling.lstrip().startswith("#"):
                        count += 1
                return count == 1

        return False

    def describe(self, match: MutationMatch) -> str:
        return f"A statement has been deleted near line {match.line_number}. The line `{match.original.strip()}` is missing."


class DuplicateLineFlip(Mutation):
    """Flip a boolean or comparison operator on one copy of a duplicate line.

    Invariants:
    - The mutated occurrence is never the FIRST occurrence (index ≥ 1 in the list).
    - The mutation changes exactly one token on exactly one line.
    - If no flippable token is found, the line is skipped.
    """

    def __init__(self):
        super().__init__(
            name="duplicate-line-flip",
            category="single-line",
            description_template="A duplicated line contains a subtle operator/literal change.",
            fix_hint="One copy of a repeated line has had an operator or literal flipped. Find and fix the inconsistency.",
        )

    @staticmethod
    def _try_flip(line: str) -> str | None:
        """Return mutated line with one token flipped, or None if no flippable token found."""
        # Boolean literals (word boundaries)
        if re.search(r"\bTrue\b", line):
            return re.sub(r"\bTrue\b", "False", line, count=1)
        if re.search(r"\bFalse\b", line):
            return re.sub(r"\bFalse\b", "True", line, count=1)
        if re.search(r"\btrue\b", line):
            return re.sub(r"\btrue\b", "false", line, count=1)
        if re.search(r"\bfalse\b", line):
            return re.sub(r"\bfalse\b", "true", line, count=1)
        # Comparison operators — longer tokens first to avoid partial matches
        if " <= " in line:
            return line.replace(" <= ", " < ", 1)
        if " >= " in line:
            return line.replace(" >= ", " > ", 1)
        if " < " in line:
            return line.replace(" < ", " <= ", 1)
        if " > " in line:
            return line.replace(" > ", " >= ", 1)
        if " == " in line:
            return line.replace(" == ", " != ", 1)
        if " != " in line:
            return line.replace(" != ", " == ", 1)
        # Logical operators
        if " and " in line:
            return line.replace(" and ", " or ", 1)
        if " or " in line:
            return line.replace(" or ", " and ", 1)
        return None

    def find_candidates(self, lines: list[str], lang: str = "python") -> list[MutationMatch]:
        # Build stripped content → list of 1-indexed line numbers
        line_map: dict[str, list[int]] = {}
        for i, line in enumerate(lines):
            content = line.strip()
            if not content or content.startswith(("#", "//", '"""', "'''")):
                continue
            line_map.setdefault(content, []).append(i + 1)

        matches = []
        for content, line_nums in line_map.items():
            if len(line_nums) < 2:
                continue

            mutated_content = self._try_flip(content)
            if mutated_content is None or mutated_content == content:
                continue

            # Pick a middle or later occurrence — never the first
            pick_idx = max(1, len(line_nums) // 2)
            target_line_num = line_nums[pick_idx]

            actual_line = lines[target_line_num - 1].rstrip()
            indent = len(actual_line) - len(actual_line.lstrip())

            matches.append(
                MutationMatch(
                    line_number=target_line_num,
                    original=actual_line,
                    mutated=" " * indent + mutated_content,
                    indent=indent,
                )
            )

        return matches

# ── Single-site, multi-line mutations ─────────────────────────────────




class SwapAdjacentLines(Mutation):
    """Swap two adjacent single-line statements.

    Tests whether the model can detect order-dependent logic: e.g.
    a = compute_x() / b = compute_y() vs b = compute_y() / a = compute_x().
    """

    # Prefixes that mark structural/block statements (not eligible to swap)
    _STRUCTURAL = (
        "if ", "elif ", "else:", "for ", "while ", "with ",
        "try:", "except", "finally:", "class ", "def ", "async ", "@",
    )

    def __init__(self):
        super().__init__(
            name="swap-adjacent-lines",
            category="multi-line",
            description_template="Two adjacent statements are in the wrong order.",
            fix_hint="Two adjacent lines need to be swapped back to their correct order.",
        )

    def _is_simple_statement(self, line: str) -> bool:
        content = line.strip()
        if not content or any(content.startswith(y) for y in ["#", "//", "}", "]", ")"]):
            return False
        for prefix in self._STRUCTURAL:
            if content.startswith(prefix):
                return False
        # Block headers end with ':'
        if content.endswith(":"):
            return False
        return True

    def _are_independent_assignments(self, line_a: str, line_b: str) -> bool:
        """Return True when both lines assign to different vars with no cross-reference.

        Such pairs are less interesting because swapping doesn't change semantics.
        """
        pat = re.compile(r"^\s*([a-zA-Z_]\w*)\s*=(?!=)")
        ma = pat.match(line_a)
        mb = pat.match(line_b)
        if not (ma and mb):
            return False
        var_a, var_b = ma.group(1), mb.group(1)
        if var_a == var_b:
            return False
        rhs_a = line_a[ma.end():]
        rhs_b = line_b[mb.end():]
        # If either RHS references the other's target, they're NOT independent
        if re.search(rf"\b{re.escape(var_a)}\b", rhs_b):
            return False
        if re.search(rf"\b{re.escape(var_b)}\b", rhs_a):
            return False
        return True

    def find_candidates(self, lines: list[str], lang: str = "python") -> list[MutationMatch]:
        matches = []
        n = len(lines)

        for i in range(n - 1):
            line_a = lines[i]
            if not self._is_simple_statement(line_a):
                continue
            indent_a = len(line_a) - len(line_a.lstrip())

            # Find next non-empty line (at most 1 blank line gap)
            j = i + 1
            blank_count = 0
            while j < n and lines[j].strip() == "":
                blank_count += 1
                j += 1
            if blank_count > 1 or j >= n:
                continue

            line_b = lines[j]
            if not self._is_simple_statement(line_b):
                continue
            indent_b = len(line_b) - len(line_b.lstrip())
            if indent_a != indent_b:
                continue
            if line_a.rstrip() == line_b.rstrip():
                continue

            # Skip trivially independent assignments — not order-sensitive
            if self._are_independent_assignments(line_a, line_b):
                continue

            a_content = line_a.rstrip()
            b_content = line_b.rstrip()

            if blank_count == 0:
                original = a_content + "\n" + b_content
                mutated = b_content + "\n" + a_content
            else:
                blank = lines[j - 1].rstrip()  # the single blank line (usually "")
                original = a_content + "\n" + blank + "\n" + b_content
                mutated = b_content + "\n" + blank + "\n" + a_content

            # end_line uses the 1-indexed-inclusive / 0-indexed-exclusive convention
            end_line = j + 1

            matches.append(
                MutationMatch(
                    line_number=i + 1,
                    original=original,
                    mutated=mutated,
                    indent=indent_a,
                    end_line=end_line,
                )
            )

        return matches


# ── Multi-site, single-line mutations ─────────────────────────────────


class RenamePartial(Mutation):
    """Rename a variable in some occurrences but not all.

    Simulates an incomplete rename refactor. This is where exact string
    matching struggles because multiple valid lines contain the name.
    """

    KEYWORDS_BY_LANG: dict[str, frozenset[str]] = {
        "python": frozenset(
            {
                "self",
                "None",
                "True",
                "False",
                "return",
                "import",
                "from",
                "class",
                "def",
                "if",
                "else",
                "elif",
                "for",
                "while",
                "try",
                "except",
                "finally",
                "with",
                "as",
                "in",
                "is",
                "not",
                "and",
                "or",
                "pass",
                "break",
                "continue",
                "raise",
                "yield",
                "lambda",
                "async",
                "await",
                "assert",
                "del",
                "global",
                "nonlocal",
                "print",
                "len",
                "str",
                "int",
                "float",
                "list",
                "dict",
                "set",
                "tuple",
                "type",
                "range",
                "enumerate",
                "zip",
                "map",
                "filter",
                "any",
                "all",
                "isinstance",
                "hasattr",
                "getattr",
                "setattr",
                "super",
                "property",
            }
        ),
        "rust": frozenset(
            {
                "self",
                "Self",
                "fn",
                "let",
                "mut",
                "pub",
                "use",
                "impl",
                "struct",
                "enum",
                "match",
                "mod",
                "crate",
                "super",
                "trait",
                "where",
                "async",
                "await",
                "move",
                "ref",
                "dyn",
                "type",
                "const",
                "static",
                "return",
                "if",
                "else",
                "for",
                "while",
                "loop",
                "break",
                "continue",
                "true",
                "false",
                "Some",
                "None",
                "Ok",
                "Err",
                "Box",
                "Vec",
                "Option",
                "Result",
                "String",
                "str",
                "println",
                "eprintln",
                "format",
                "unwrap",
                "expect",
                "clone",
                "iter",
                "into",
                "from",
                "new",
                "default",
            }
        ),
        "go": frozenset(
            {
                "func",
                "var",
                "const",
                "type",
                "struct",
                "interface",
                "map",
                "chan",
                "go",
                "defer",
                "select",
                "case",
                "switch",
                "range",
                "fallthrough",
                "package",
                "import",
                "return",
                "break",
                "continue",
                "goto",
                "nil",
                "true",
                "false",
                "error",
                "string",
                "int",
                "bool",
                "float64",
                "byte",
                "rune",
                "make",
                "len",
                "cap",
                "append",
                "copy",
                "delete",
                "close",
                "new",
                "panic",
                "recover",
                "print",
                "println",
                "fmt",
                "err",
            }
        ),
        "typescript": frozenset(
            {
                "const",
                "let",
                "var",
                "function",
                "class",
                "interface",
                "type",
                "enum",
                "return",
                "import",
                "export",
                "from",
                "if",
                "else",
                "for",
                "while",
                "do",
                "switch",
                "case",
                "break",
                "continue",
                "try",
                "catch",
                "finally",
                "throw",
                "new",
                "delete",
                "typeof",
                "instanceof",
                "void",
                "null",
                "undefined",
                "true",
                "false",
                "this",
                "super",
                "async",
                "await",
                "yield",
                "console",
                "Promise",
                "Array",
                "Object",
                "Map",
                "Set",
                "string",
                "number",
                "boolean",
                "any",
                "never",
                "unknown",
            }
        ),
    }
    # Combined set as fallback
    KEYWORDS = frozenset().union(*KEYWORDS_BY_LANG.values())

    def __init__(self):
        super().__init__(
            name="rename-partial",
            category="multi-site",
            description_template="A variable was renamed inconsistently.",
            fix_hint="Find the inconsistent variable name and make all occurrences consistent.",
        )

    def find_candidates(self, lines: list[str], lang: str = "python") -> list[MutationMatch]:
        matches = []
        keywords = self.KEYWORDS_BY_LANG.get(lang, self.KEYWORDS)
        ident_lines: dict[str, list[int]] = {}
        ident_pattern = re.compile(r"\b([a-z_][a-z0-9_]{2,20})\b")
        for i, line in enumerate(lines):
            content = line.rstrip()
            if content.lstrip().startswith(("#", "//", '"""', "'''")):
                continue
            for m in ident_pattern.finditer(content):
                name = m.group(1)
                if name in keywords:
                    continue
                ident_lines.setdefault(name, []).append(i)

        for name, line_nums in ident_lines.items():
            unique_lines = sorted(set(line_nums))
            if len(unique_lines) < 3 or len(unique_lines) > 12:
                continue

            new_name = f"{name}_v2" if not name.startswith("_") else name[1:]
            if new_name == name:
                continue

            half = max(1, len(unique_lines) // 2)
            mutated_lines = unique_lines[:half]

            primary = mutated_lines[0]
            indent = len(lines[primary]) - len(lines[primary].lstrip())
            extra = []
            for ln in mutated_lines[1:]:
                orig = lines[ln].rstrip()
                mut = re.sub(rf"\b{re.escape(name)}\b", new_name, orig, count=1)
                extra.append((ln + 1, orig, mut))

            matches.append(
                MutationMatch(
                    line_number=primary + 1,
                    original=name,
                    mutated=new_name,
                    indent=indent,
                    extra_sites=extra,
                )
            )

        return matches

    def describe(self, match: MutationMatch) -> str:
        n = 1 + len(match.extra_sites)
        return (
            f"A variable was partially renamed: `{match.original}` was changed to "
            f"`{match.mutated}` in {n} of its occurrences, but the remaining "
            f"occurrences still use the old name. All occurrences should use `{match.original}`."
        )


class InconsistentLiteral(Mutation):
    """Change one occurrence of a repeated string literal.

    When a constant appears N times, changing one creates a subtle
    inconsistency the model must locate.
    """

    def __init__(self):
        super().__init__(
            name="inconsistent-literal",
            category="multi-site",
            description_template="A constant value is inconsistent across its occurrences.",
            fix_hint="A literal value was changed in one place but not others. Find the inconsistency.",
        )

    def find_candidates(self, lines: list[str], lang: str = "python") -> list[MutationMatch]:
        matches = []
        string_pattern = re.compile(r'"([^"]{3,30})"')
        literal_lines: dict[str, list[int]] = {}
        for i, line in enumerate(lines):
            if line.lstrip().startswith(("#", "//")):
                continue
            for m in string_pattern.finditer(line):
                literal_lines.setdefault(m.group(1), []).append(i)

        for val, line_nums in literal_lines.items():
            unique = sorted(set(line_nums))
            if len(unique) < 3:
                continue

            target_idx = unique[len(unique) // 2]
            original_line = lines[target_idx].rstrip()
            indent = len(lines[target_idx]) - len(lines[target_idx].lstrip())
            mutated_val = val + "_old" if len(val) < 25 else val[:-3] + "xxx"
            mutated_line = original_line.replace(f'"{val}"', f'"{mutated_val}"', 1)

            matches.append(MutationMatch(target_idx + 1, original_line, mutated_line, indent))

        return matches

    def describe(self, match: MutationMatch) -> str:
        return (
            f"A string literal has been changed in one place but not others, "
            f"creating an inconsistency. The line `{match.mutated.strip()}` "
            f"has a value that doesn't match the same constant used elsewhere in the file."
        )


# ── Multi-site, multi-line mutations ──────────────────────────────────

MUTATIONS: list[Mutation] = [
    # Single-site, single-line (universal)
    SwapComparison(),
    ConfuseComparison(),
    SwapEquality(),
    FlipBoolean(),
    SwapLogical(),
    RemoveNegation(),
    OffByOne(),
    SwapArithmetic(),
    SwapArgs(),
    SwapAugmentedAssign(),
    UnicodeHyphen(),
    DeleteStatement(),
    DuplicateLineFlip(),
    
    # Single-site, multi-line (Python-only)
    SwapAdjacentLines(),
    # Multi-site (universal)
    RenamePartial(),
    InconsistentLiteral(),
]

# todo: swap-bitwise: <<, >>, &, |, ^
# string-literal-cases: lower / upper, including char
# swap-mod-div
# swap ..= and .. (rust)
# swap-fn-names: sin, cos, tan, atan, ...
# swap-some-literals: 180, 360, etc