import re 
import random
from common.mutation import MutationMatch


GENERAL_SYMBOL_PATTERN = r"[^\s\w]+"
GENERAL_IDENTIFIER_PATTERN = r"\w+"
GENERAL_IDENTIFIER_FUNCTION_PATTERN = r"\w+(\(\))?"

def swap_first(lines: list[str], swaps: list[tuple[str, str]]) -> list[MutationMatch]:
    matches = []
    for i, line in enumerate(lines):
        stripped = line.rstrip()
        for old, new in swaps:
            if old in stripped:
                indent = len(line) - len(line.lstrip())
                matches.append(MutationMatch(i + 1, stripped, stripped.replace(old, new, 1), indent))
                break
    return matches

def is_comment(stripped: str) -> bool:
    return stripped.lstrip().startswith(("#", "//"))


def simple_tokenize(s: str, spans: list[tuple[int, int]]) -> list[str]:
    # spans MUST be an ASC list of tuples [s, t)
    toks = []
    acc = ""
    span_i = 0
    for i, c in enumerate(s):
        if span_i >= len(spans):
            acc += s[i:]
            break
        (a, b) = spans[span_i]
        if i == a and acc != "":
            toks.append(acc)
            acc = ""
        acc += c
        if i == b - 1:
            span_i += 1
            toks.append(acc)
            acc = ""

    if acc != "":
        toks.append(acc)
    
    return toks

def swap_random(
    lines: list[str], 
    swaps: list[tuple[str, list[str]]],
    pattern: str,
    replacement_ratio = 0.5
) -> list[MutationMatch]:
    matches = []
    for i, line in enumerate(lines):
        s = line.rstrip()
        indent = len(line) - len(line.lstrip())
        replacement = {}
        olds = [ old for old, _news in swaps ]
        spans = [ m.span() for m in re.finditer(pattern, s) if m.group() in olds ]
        if spans == []:
            continue
        toks = simple_tokenize(s, spans)
        for old, news in swaps:
            if old not in s:
                continue
            targs = [ i for i, v in enumerate(toks) if v == old ]
            if targs == []:
                continue
            k = min(max(round(len(targs) * replacement_ratio), 1), len(targs))
            selected = random.sample(targs, k = k)

            for i in selected:
                replacement[i] = random.choice(news)
        toks = [ t if i not in replacement else replacement[i] for i, t in enumerate(toks) ]
        t = "".join(toks)
        matches.append(MutationMatch(i + 1, s, t, indent))
    return matches

