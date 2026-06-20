from itertools import combinations
import re
import random
from common.mutation import Mutation, MutationMatch
from common.utils import is_disjoint_intervals
from mutations.utils import GENERAL_IDENTIFIER_FUNCTION_PATTERN, GENERAL_IDENTIFIER_PATTERN, GENERAL_SYMBOL_PATTERN, is_comment, locate_parens, simple_tokenize_by_multi, swap_random

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
        # ("+=", ["="]),
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
# todo: locate && ||, then search backwards
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

class ConfuseMathFunctions(Mutation):
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
    ]

    def __init__(self):
        super().__init__(
            name="confuse-math-functions",
            category="single-line",
            description_template="Swaps identifiers",
            fix_hint="Swap back.",
        )

    def find_candidates(self, lines: list[str], lang: str = "python") -> list[MutationMatch]:
        return [ m for m in swap_random(lines, self.SWAPS, GENERAL_IDENTIFIER_PATTERN) if not is_comment(m.original) ]

class ConfuseLanguageKeywords(Mutation):
    SWAPS = [
        ("true", ["false"]),
        ("false", ["true"]),
        ("True", ["False"]),
        ("False", ["True"]),
        ("continue", ["break"]),
        ("break", ["continue"]),
        ("and", ["or"]),
        ("or", ["and"]),
        ("xor", ["and", "or"]),
        
    ]

    def __init__(self):
        super().__init__(
            name="confuse-language-keywords",
            category="single-line",
            description_template="Swaps identifiers",
            fix_hint="Swap back.",
        )

    def find_candidates(self, lines: list[str], lang: str = "python") -> list[MutationMatch]:
        return [ m for m in swap_random(lines, self.SWAPS, GENERAL_IDENTIFIER_PATTERN) if not is_comment(m.original) ]

class ConfuseVariablePatterns(Mutation):
    SWAPS = [
        ("j", ["i"]),
        ("k", ["i", "j"]),
        ("m", ["n"]),
        ("y", ["x"]),
        ("z", ["x", "y"]),
        ("b", ["a"])
    ]

    def __init__(self):
        super().__init__(
            name="confuse-variable-patterns",
            category="single-line",
            description_template="Swaps identifiers",
            fix_hint="Swap back.",
        )
    
    def _match_duplicated_var(self, lines: list[str]):
        matches = []
        for i, line in enumerate(lines):
            stripped = line.rstrip()
            if is_comment(stripped):
                continue
            indent = len(line) - len(line.lstrip())
            found = re.finditer(r"([\w]*[a-zA-Z_])(\d+)", stripped)
            found = [ it for it in found if int(it.group(2)) <= 3 ]
            if found == []:
                continue
            for f in found:
                pref = f.group(1)
                k = int(f.group(2))
                s = stripped[: f.start()]
                t = stripped[f.end():]
                for j in range(k):
                    repl = pref if j == 0 else (pref + str(j))
                    matches.append(MutationMatch(i + 1, stripped, s + repl + t, indent))
        return matches

    def find_candidates(self, lines: list[str], lang: str = "python") -> list[MutationMatch]:
        return [ m for m in swap_random(lines, self.SWAPS, GENERAL_IDENTIFIER_PATTERN) if not is_comment(m.original) ] + self._match_duplicated_var(lines)

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
            parens = [ (x, y) for (x, y) in locate_parens(toks, ("(", ")")) if abs(y - x) > 1]
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
    OP_STOP = ["==", "!=", ">=", "<=", ">", "<", ";"]
    OP_LEAD = ["-", "*", "/", "%", "**", "!", "&&", "&", "|", "^", "<<", ">>"]
    OP_FOLLOW = {
        "arithmetic": (["+", "-", "*", "/", "%", "**"], ["&&", "||"]),
        "logic": (["&&", "||"], ["+", "-", "*", "/", "%", "**", "&", "|", "^", "<<", ">>"]),
        "bitwise": (["&", "|", "^", "<<", ">>"], ["&&", "||"])
    }
    
    # OP_FOLLOW = ["+", "-", "*", "/", "**", "%"]
    
    def __init__(self):
        super().__init__(
            name="intro-parens",
            category="single-line",
            description_template="Introduce parens.",
            fix_hint="Remove.",
        )
    def find_candidates(self, lines: list[str], lang: str = "python") -> list[MutationMatch]:
        matches = []
        ptn = r"(\(|\)|\*\*|&&|\|\||<<|>>|\+|-|\*|\/|%|\^|\!|\||&)"
        LP = "("
        RP = ")"
        op_follow_groups = {it : k for k in self.OP_FOLLOW for it in self.OP_FOLLOW[k][0]} | { "!": "logic" }
        for i, line in enumerate(lines):
            if is_comment(line):
                continue

            stripped = line.rstrip()
            indent = len(line) - len(line.lstrip())

            toks = simple_tokenize_by_multi([ptn, GENERAL_SYMBOL_PATTERN], stripped)
            places = []
            j = 0
            p = 0
            while j < len(toks):
                t = toks[j]
                if t == LP: p += 1
                if t == RP: p -= 1
                if j + 1 < len(toks) and t in self.OP_LEAD:
                    group = op_follow_groups[t]
                    (follow, excl) = self.OP_FOLLOW[group]
                    stop = self.OP_STOP + excl
                    k = j + 1
                    q = p
                    while k < len(toks):
                        u = toks[k]
                        if u == LP: q += 1
                        if u == RP: q -= 1
                        if u in stop: break
                        if k + 1 < len(toks) and u in follow and q == p:
                            l = k + 1
                            r = p
                            f = False
                            while l < len(toks):
                                v = toks[l]
                                if v == LP: r += 1
                                if v == RP: r -= 1
                                if v in stop: 
                                    f = True
                                    break
                                if r == q and v != LP and (v == RP or not re.match(ptn, v)):
                                    places.append((j + 1, l))
                                    # break
                                l += 1
                            if f:
                                break
                        k += 1
                j += 1
            
            for (l, r) in places:
                t = [ 
                    ("(" + tok) if k == l else 
                    (tok + ")") if k == r else 
                    tok for k, tok in enumerate(toks) 
                ]
                matches.append(MutationMatch(i + 1, stripped, "".join(t), indent))
            
        return matches

class SwapParens(Mutation):
    PARENS = [
        ("(", ")"),
        ("[", "]"),
        ("{", "}")
    ]
    def __init__(self):
        super().__init__(
            name="swap-parens",
            category="single-line",
            description_template="Swap parens.",
            fix_hint="Swap back.",
        )
    
    def find_candidates(self, lines: list[str], lang: str = "python") -> list[MutationMatch]:
        matches = []
        for i, line in enumerate(lines):
            if is_comment(line):
                continue
            stripped = line.rstrip()
            indent = len(line) - len(line.lstrip())
            toks = [t for t in stripped]
            parens = [locate_parens(toks, pair) for pair in self.PARENS]
            for located in parens:
                if len(located) < 2:
                    continue
                paren_pairs = [ (a, b) for a, b in combinations(located, 2) if is_disjoint_intervals(a, b) ]
                for (a, b) in paren_pairs:
                    (u, v) = a
                    (s, t) = b
                    toks_repl = list(toks)
                    # s1 [s2] s3 [s4] s5
                    s1 = toks_repl[0:u]
                    s2 = toks_repl[u:v + 1]
                    s3 = toks_repl[v + 1:s]
                    s4 = toks_repl[s:t + 1]
                    s5 = toks_repl[t + 1:]
                    replaced = "".join(s1 + s4 + s3 + s2 + s5)
                    matches.append(MutationMatch(i + 1, stripped, replaced, indent))
            
        return matches
        # return super().find_candidates(lines, lang)

MUTATIONS = [
    ConfuseBitwiseLogic(),
    ConfuseLogical(),
    ConfuseAssignment(),
    ConfuseMathFunctions(),
    ConfuseLanguageKeywords(),
    ConfuseVariablePatterns(),
    
    ConfuseArithmetic(),
    ConfuseIndexVariable(),
    ConfuseNumericLiterals(),
    
    FlipPlusMinusOne(),
    NegateConditionBranch(),
    RemoveNegation(),
    RemoveElseIf(),
    RemoveParens(),
    IntroParens(),
    SwapParens()
]