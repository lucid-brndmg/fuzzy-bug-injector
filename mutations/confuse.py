import re
import random
from common.mutation import Mutation, MutationMatch
from mutations.utils import GENERAL_IDENTIFIER_FUNCTION_PATTERN, GENERAL_IDENTIFIER_PATTERN, GENERAL_SYMBOL_PATTERN, is_comment, locate_parens, swap_random

class ConfuseBitwiseLogic(Mutation):
    SWAPS = [
        ("<<", [">>"]),
        (">>", ["<<"]),
        (">>=", ["<<="]),
        ("<<=", [">>="]),
        ("&", ["^", "|"]),
        ("^", ["|", "&"]),
        ("|", ["&", "^"]),
        ("&=", ["|=", "^="]),
        ("|=", ["&=", "^="]),
        ("^=", ["&=", "|="])
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

        return [ m for m in swap_random(lines, swaps, GENERAL_SYMBOL_PATTERN) if not is_comment(m.original) ]

class ConfuseLogical(Mutation):
    SWAPS = [
        ("&&", ["||"]),
        ("||", ["&&"]),
        ("==", ["!="]),
        ("!=", ["=="]),
        
        (">", [">="]),
        ("<", ["<="]),
        (">=", [">"]),
        ("<=", ["<"]),
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

# todo: line swap, pattern = ^\s*\**(\w+)\s*(=|\+=|-=|\*=|\/=)\s*(.*);\s*$ (previous / next lines not decl / parens / etc)
class ConfuseAssignment(Mutation):
    SWAPS = [
        ("+=", ["="]),
        ("-=", ["+="]),
        ("*=", ["+="]),
        ("/=", ["-="]),
        ("%=", ["/="]),
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


class ConfuseArithmetic(Mutation):
    def __init__(self):
        super().__init__(
            name="confuse-arithmetic",
            category="single-line",
            description_template="",
            fix_hint="Check the arithmetic operator.",
        )
    def find_candidates(self, lines: list[str], lang: str = "python") -> list[MutationMatch]:
        swaps = [
            ("-", ["+"]),
            ("*", ["+"]),
            ("/", ["-"]),
            ("%", ["/"]),
            ("**", ["*"])
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

# todo: cut condition branch
# todo: floats
# todo: confuse regex, \d, \w, etc
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
            found = list(re.finditer(r"(?:(or|and|&&|\|\||if|while)\s*)(\(*\w)", stripped))
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
        # todo: append a parens on functions
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
        ("continue", ["break"]),
        ("break", ["continue"]),

        ("j", ["i"]), # not for k
        ("y", ["x"]),
        ("z", ["x", "y"]),
        ("b", ["a"])
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

class ConfuseNumericLiterals(Mutation):
    SWAPS = [
        # small unsigned integers
        *[(str(i), [str(i + 1), str(i - 1)]) for i in range(2, 11)],
        # 4, 8, .., 65535
        *[(str(2 << i), [str((2 << i) - 1), str(2 << (i - 1)), str(2 << (i + 1))]) for i in range(2, 16)],
        # 127, 255, 65535
        *[(str((2 << i) - 1), [str(2 << i)]) for i in [6, 7, 15]],
        # angles
        *[(str(i * 60), [str((i + 3) * 60), str((i - 3) * 60)]) for i in [3, 6, 9, 12]],
    ]

    def __init__(self):
        super().__init__(
            name="confuse-numeric-literals",
            category="single-line",
            description_template="Swaps numeric literals",
            fix_hint="Swap back.",
        )

    def find_candidates(self, lines: list[str], lang: str = "python") -> list[MutationMatch]:
        return [ m for m in swap_random(lines, self.SWAPS, GENERAL_IDENTIFIER_PATTERN, 1.0) if not is_comment(m.original) ]

class ConfuseIndexVariable(Mutation):
    INDEX_PATTERNS = ["i", "j", "k", "index", "idx", "length", "len()"]
    def __init__(self):
        super().__init__(
            name="confuse-index-variable",
            category="single-line",
            description_template="Attempts to set a -1 to an index",
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




class RemoveParens(Mutation):
    def __init__(self):
        super().__init__(
            name="remove-parens",
            category="single-line",
            description_template="Remove parens.",
            fix_hint="Adds back.",
        )
    def find_candidates(self, lines: list[str], lang: str = "python") -> list[MutationMatch]:
        matches = []
        replacement_ratio = 0.4
        for i, line in enumerate(lines):
            if is_comment(line):
                continue

            stripped = line.rstrip()
            indent = len(line) - len(line.lstrip())
            toks = [t for t in stripped]
            parens = locate_parens(toks, ("(", ")"))
            if parens == []:
                continue
            
            k = min(max(round(len(parens) * replacement_ratio), 1), len(parens))
            
            parens = random.sample(parens, k = k)
            for (x, y) in parens:
                toks[x] = ""
                toks[y] = ""
            t = "".join(toks)
            matches.append(MutationMatch(i + 1, stripped, t, indent))
        
        return matches
        # return super().find_candidates(lines, lang)

class IntroParens(Mutation):
    OP_LEAD = ["-", "*", "/"]
    OP_FOLLOW = ["+", "-", "*", "/", "**", "%"]
    
    def __init__(self):
        super().__init__(
            name="intro-parens",
            category="single-line",
            description_template="Introduce parens.",
            fix_hint="Remove.",
        )
    def find_candidates(self, lines: list[str], lang: str = "python") -> list[MutationMatch]:
        matches = []
        ptn = r"\w+(\(.*\))?"
        for i, line in enumerate(lines):
            if is_comment(line):
                continue

            stripped = line.rstrip()
            indent = len(line) - len(line.lstrip())

            toks = []
            places = []
            j = 0
            while (j + 3) < len(toks):
                t = toks[j]
                if t in self.OP_LEAD and re.match(ptn, toks[j + 1]) and toks[j + 2] in self.OP_FOLLOW and re.match(ptn, toks[j + 3]):
                    places.append(j + 1)
                    j += 4
                else:
                    j += 1
            
            for j in places:
                t = [ 
                    ("(" + tok) if k == j else 
                    (tok + ")") if k == j + 2 else 
                    tok for k, tok in enumerate(toks) 
                ]
                matches.append(MutationMatch(i + 1, stripped, "".join(t), indent))
            
        return matches

MUTATIONS = [
    ConfuseBitwiseLogic(),
    ConfuseLogical(),
    ConfuseAssignment(),
    ConfuseIdentifiers(),
    ConfuseArithmetic(),
    ConfuseIndexVariable(),
    ConfuseNumericLiterals(),
    
    FlipPlusMinusOne(),
    NegateConditionBranch(),
    RemoveNegation(),
    RemoveElseIf(),
    RemoveParens(),
    IntroParens()
]