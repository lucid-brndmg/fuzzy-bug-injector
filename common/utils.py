import importlib.util
from pathlib import Path
import sys
import string
import secrets

def power_set(items):
    N = len(items)
    # enumerate the 2 ** N possible combinations
    for i in range(2 ** N):
        combo = []
        for j in range(N):
            # test bit jth of integer i
            if (i >> j) % 2 == 1:
                combo.append(items[j])
        yield combo

def is_disjoint_intervals(a: tuple[int, int], b: tuple[int, int]) -> bool:
    (l1, l2) = a
    (l3, l4) = b
    return l3 > l2 or l4 < l1


def iter_disjoint_subsets(
    elements: list,
    is_disjoint,
    min_elements = 1,
    max_elements = None,
    iter_limit = None
):
    n = len(elements)
    conflicting_elements: list[set[int]] = [set([i]) for i in range(0, n)]
    for i, m1 in enumerate(elements):
        for j in range(i + 1, n):
            m2 = elements[j]
            if not is_disjoint(m1, m2):
                conflicting_elements[i].add(j)
                conflicting_elements[j].add(i)

    for k, subset in enumerate(power_set(range(n))):
        if iter_limit is not None and k > iter_limit:
            break
        m = len(subset)
        if m < min_elements or (max_elements is not None and m > max_elements):
            continue
        f = True
        for i in range(0, m):
            for j in range(i + 1, m):
                if (subset[j] in conflicting_elements[subset[i]]) or (subset[i] in conflicting_elements[subset[j]]):
                    f = False
                    break
            else:
                continue
            break
        if f:
            yield [ elements[i] for i in subset ]
        

def module_gensym(length=32, prefix="gensym_"):
    """
    generates a fairly unique symbol, used to make a module name,
    used as a helper function for load_module

    :return: generated symbol
    """
    alphabet = string.ascii_uppercase + string.ascii_lowercase + string.digits
    symbol = "".join([secrets.choice(alphabet) for i in range(length)])

    return prefix + symbol

# source: https://medium.com/@david.bonn.2010/dynamic-loading-of-python-code-2617c04e5f3f
def load_module(source, module_name=None):
    """
    reads file source and loads it as a module

    :param source: file to load
    :param module_name: name of module to register in sys.modules
    :return: loaded module
    """

    if module_name is None:
        module_name = module_gensym()

    spec = importlib.util.spec_from_file_location(module_name, source)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)

    return module

def load_path(path: Path):
    if path.is_dir():
        for file in path.iterdir():
            if file.name.endswith(".py"):
                try:
                    m = load_module(file)
                    yield m
                except:
                    pass
    else:
        try:
            m = load_module(path)
            yield m
        except:
            pass