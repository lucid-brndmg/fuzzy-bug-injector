import re 
import random
from common.mutation import MutationMatch


GENERAL_SYMBOL_PATTERN = r"[^\s\w]+"
GENERAL_IDENTIFIER_PATTERN = r"\w+"
GENERAL_IDENTIFIER_FUNCTION_PATTERN = r"\w+(\(\))?"
GENERAL_VAR_DECL_ASSIGN_PATTERN = r"^\s*(let\s+|let\s+mut\s+|var\s+|const\s+)?[\w][\w.]*(?:\[.*?\])?\s*[+\-\*\/%&|^@\:]?=(?!=)\s*(.+)$"

def line_split_assign(line: str) -> tuple[str, str]:
    f = re.match(GENERAL_VAR_DECL_ASSIGN_PATTERN, line)
    if f is None:
        return ("", line)
    i = f.start(2)
    return (line[:i], line[i:])

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

def simple_tokenize_by(ptn: str, s: str) -> list[str]:
    spans = [ m.span() for m in re.finditer(ptn, s) ]
    if spans == []:
        return []
    toks = simple_tokenize(s, spans)
    return toks

def swap_random(
    lines: list[str], 
    swaps: list[tuple[str, list[str]]],
    pattern: str,
    replacement_ratio = 0.5,
    # line_split = line_split_assign
) -> list[MutationMatch]:
    matches = []
    for line_idx, line in enumerate(lines):
        s = line.rstrip()
        (l, r) = line_split_assign(s)
        indent = len(line) - len(line.lstrip())
        replacement = {}
        olds = [ old for old, _news in swaps ]
        spans = [ m.span() for m in re.finditer(pattern, r) if m.group() in olds ]
        if spans == []:
            continue
        toks = simple_tokenize(r, spans)
        for old, news in swaps:
            if old not in r:
                continue
            selected = [ i for i, v in enumerate(toks) if v == old ]
            # if selected == []:
            #     continue
            # k = min(max(round(len(selected) * replacement_ratio), 1), len(selected))
            # selected = random.sample(selected, k = k)
            for i in selected:
                replacement[i] = random.choice(news)

        k = min(max(round(len(replacement) * replacement_ratio), 1), len(replacement))
        keys = random.sample(sorted(replacement), k = k)
        
        toks = [ t if i not in keys else replacement[i] for i, t in enumerate(toks) ]
        t = l + "".join(toks)
        matches.append(MutationMatch(line_idx + 1, s, t, indent))
    return matches

def locate_parens(line, parens: tuple[str, str]):
    (lp, rp) = parens
    stack = []
    results = []
    for j, c in enumerate(line):
        if c == lp:
            stack.append(j)
        if c == rp:
            if stack == []:
                continue
            i = stack.pop()
            results.append((i, j))
    return results