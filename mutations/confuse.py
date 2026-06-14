import re
import random
from common.mutation import Mutation, MutationMatch
from mutations.utils import GENERAL_IDENTIFIER_FUNCTION_PATTERN, GENERAL_IDENTIFIER_PATTERN, GENERAL_SYMBOL_PATTERN, is_comment, swap_random

class ConfuseBitwiseLogic(Mutation):
    SWAPS = [
        ("<<", [">>"]),
        (">>", ["<<"]),
        (">>=", ["<<="]),
        ("<<=", [">>="]),
        ("&", ["^", "|"]),
        ("^", ["|", "&"]),
    ]

    def __init__(self):
        super().__init__(
            name="confuse-bitwise-logic",
            category="single-line",
            description_template="",
            fix_hint="",
        )
        

    def find_candidates(self, lines: list[str], lang: str = "python") -> list[MutationMatch]:
        swaps = list(self.SWAPS)
        if lang != "rust" and lang != "typescript":
            swaps.append(("|", ["&", "^"]))

        return [ m for m in swap_random(lines, swaps, GENERAL_SYMBOL_PATTERN) if not is_comment(m.original) ]

class ConfuseLogical(Mutation):
    SWAPS = [
        ("&&", ["||"]),
        ("||", ["&&"]),
        ("==", ["!="]),
        ("!=", ["=="]),
        (">", [">=", "!="]),
        ("<", ["<=", "!="]),
        (">=", [">", "=="]),
        ("<=", ["<", "=="]),
    ]

    def __init__(self):
        super().__init__(
            name="confuse-logical",
            category="single-line",
            description_template="",
            fix_hint="",
        )

    def find_candidates(self, lines: list[str], lang: str = "python") -> list[MutationMatch]:
        return [m for m in swap_random(lines, self.SWAPS, GENERAL_SYMBOL_PATTERN) if not is_comment(m.original)]

class ConfuseAssignment(Mutation):
    SWAPS = [
        ("+=", ["="]),
        ("-=", ["="]),
        ("*=", ["=", "+="]),
        ("/=", ["=", "-="])
    ]

    def __init__(self):
        super().__init__(
            name="confuse-assignment",
            category="single-line",
            description_template="",
            fix_hint="",
        )

    def find_candidates(self, lines: list[str], lang: str = "python") -> list[MutationMatch]:
        return [m for m in swap_random(lines, self.SWAPS, GENERAL_SYMBOL_PATTERN) if not is_comment(m.original)]


class ConfuseModDiv(Mutation):
    def __init__(self):
        super().__init__(
            name="confuse-mod-div",
            category="single-line",
            description_template="",
            fix_hint="Check the arithmetic operator (/, %).",
        )
    def find_candidates(self, lines: list[str], lang: str = "python") -> list[MutationMatch]:
        swaps = [
            ("/", ["%"]),
            ("%", ["/"])
        ]
        return [m for m in swap_random(lines, swaps, GENERAL_SYMBOL_PATTERN) if not is_comment(m.original)]


class FlipPlusMinusOne(Mutation):
    def __init__(self):
        super().__init__(
            name="flip-plus-minus-one",
            category="single-line",
            description_template="An off-by-one error: a numeric constant in `{mutated}` is wrong by 1.",
            fix_hint="Check numeric constants for off-by-one errors.",
        )

    def find_candidates(self, lines: list[str], lang: str = "python") -> list[MutationMatch]:
        matches = []
        for i, line in enumerate(lines):
            stripped = line.rstrip()
            if is_comment(stripped):
                continue
            indent = len(line) - len(line.lstrip())

            # +1, -1
            found = list(re.finditer(r"(?<![.\w])([\+-][\s*]1)(?![.\w])", stripped))
            if found == []:
                continue
            
            f = random.choice(found)
            pref = stripped[: f.start(1)]
            suff = stripped[f.end(1) :]
            (old, new) = ("+", "-") if f.group(1).startswith("+") else ("-", "+")
            candidates = [
                # remove the token
                MutationMatch(i + 1, stripped, pref + suff, indent),
                # flip the symbol
                MutationMatch(i + 1, stripped, pref + f.group(1).replace(old, new) + suff, indent)
            ]
            matches += candidates
        return matches

class NegateConditionBranch(Mutation):
    # && e => && !e
    def __init__(self):
        super().__init__(
            name="negate-condition-branch",
            category="single-line",
            description_template="Adds a negation before a condition branch",
            fix_hint="Remove the negation.",
        )
    
    def find_candidates(self, lines: list[str], lang: str = "python") -> list[MutationMatch]:
        neg = "not " if lang == "python" else "!"
        matches = []
        for i, line in enumerate(lines):
            stripped = line.rstrip()
            if is_comment(stripped):
                continue
            indent = len(line) - len(line.lstrip())

            # if e, && e, || e, if (...)
            found = list(re.finditer(r"(?:(or|and|&&|\|\||if)\s*)(\(*\w)", stripped))
            if found == []:
                continue
            
            f = random.choice(found)
            pref = stripped[: f.start(2)]
            suff = stripped[f.end(2) :]
            matches.append(MutationMatch(i + 1, stripped, pref + neg + f.group(2) + suff, indent))
        return matches

class RemoveNegation(Mutation):
    # && !e => && e
    def __init__(self):
        super().__init__(
            name="remove-negation",
            category="single-line",
            description_template="Removes a negation before a condition branch",
            fix_hint="Adds back the negation.",
        )
    
    def find_candidates(self, lines: list[str], lang: str = "python") -> list[MutationMatch]:
        # not for python
        neg = "not " if lang == "python" else "!"
        matches = []
        for i, line in enumerate(lines):
            stripped = line.rstrip()
            if is_comment(stripped):
                continue
            indent = len(line) - len(line.lstrip())

            # (!e), &&!e, ||!e, if !e
            found = list(re.finditer(rf"(?:\(*\s+)({neg})", stripped))
            if found == []:
                continue
            
            f = random.choice(found)
            pref = stripped[: f.start(1)]
            suff = stripped[f.end(1) :]
            matches.append(MutationMatch(i + 1, stripped, pref + suff, indent))
        return matches

class ConfuseIdentifiers(Mutation):
    SWAPS = [
        ("min", ["max"]), 
        ("max", ["min"]),
        ("floor", ["ceil", "round"]), 
        ("ceil", ["floor", "round"]), 
        ("round", ["floor", "ceil"]),
        ("sin", ["cos", "tan"]),
        ("cos", ["sin", "tan"]),
        ("tan", ["cos", "sin", "atan"]),
        ("atan", ["tan"]),
        ("log2", ["log10"]),
        ("log10", ["log2"]),
        ("true", ["false"]),
        ("false", ["true"]),
        ("True", ["False"]),
        ("False", ["True"]),
        # ("0", ["1"]), ("1", ["0"]), 
        ("2", ["1", "3"]),
        ("180", ["360"]), ("360", ["180"]),
        ("continue", ["break"]),
        ("break", ["continue"]),
    ]

    def __init__(self):
        super().__init__(
            name="confuse-identifiers",
            category="single-line",
            description_template="Swaps identifiers",
            fix_hint="Swap back.",
        )

    def find_candidates(self, lines: list[str], lang: str = "python") -> list[MutationMatch]:
        return [ m for m in swap_random(lines, self.SWAPS, GENERAL_IDENTIFIER_PATTERN) if not is_comment(m.original) ]

class ConfuseIndexVariable(Mutation):
    INDEX_PATTERNS = ["i", "j", "k", "index", "idx", "length", "len()"]
    def __init__(self):
        super().__init__(
            name="confuse-index-variable",
            category="single-line",
            description_template="Attempts to set a +1/-1 to an index",
            fix_hint="Swap back.",
        )

    def find_candidates(self, lines: list[str], lang: str = "python") -> list[MutationMatch]:
        swaps = [ (v, [f"{v} - 1"]) for v in self.INDEX_PATTERNS ]
        
        return [ m for m in swap_random(lines, swaps, GENERAL_IDENTIFIER_FUNCTION_PATTERN) if not is_comment(m.original) ]


class RemoveElseIf(Mutation):
    def __init__(self):
        super().__init__(
            name="remove-else-if",
            category="single-line",
            description_template="Removes the else before else if.",
            fix_hint="Adds back the else.",
        )
    def find_candidates(self, lines: list[str], lang: str = "python") -> list[MutationMatch]:
        ptn = r"else\s+if" if lang != "python" else r"elif"
        matches = []
        for i, line in enumerate(lines):
            stripped = line.rstrip()
            if is_comment(stripped):
                continue
            indent = len(line) - len(line.lstrip())
            found = list(re.finditer(ptn, stripped))
            if found == []:
                continue
            f = random.choice(found)
            pref = stripped[: f.start(0)]
            suff = stripped[f.end(0) :]
            matches.append(MutationMatch(i + 1, stripped, pref + "if" + suff, indent))
        return matches

MUTATIONS = [
    ConfuseBitwiseLogic(),
    ConfuseLogical(),
    ConfuseAssignment(),
    ConfuseIdentifiers(),
    ConfuseModDiv(),
    ConfuseIndexVariable(),
    
    FlipPlusMinusOne(),
    NegateConditionBranch(),
    RemoveNegation(),
    RemoveElseIf(),
    
]