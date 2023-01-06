import os
from typing import List
import re
# This is a pretty hacky and inefficient way, but it works for the dataset


def _strip_args(symbol: str) -> str:
    return re.sub(r'<.*>', '', symbol)


def _parse(objdump_output: str) -> List[str]:
    return list(map(lambda x: x.split('<', 1)[1][:-2],
                    sorted(objdump_output.strip().split('\n'))))


def _common_prefix(a: str, b: str) -> int:
    for i in range(min(len(a), len(b))):
        if a[i] != b[i]:
            return i
    return min(len(a), len(b))


def _match(a: str, li: List[str]) -> int:
    ls = list(map(lambda x: _common_prefix(a, x), li))
    return ls.index(max(ls))


def mangle(binary_path: str, caller: str):
    caller = ', '.join(map(lambda x: x.split(' ')[0],
                           _strip_args(caller.replace('const ', ''))
                                      .split(', '))) + ')'
    demangled_cmd = ['llvm-objdump',
                     '-d',
                     '--demangle',
                     binary_path,
                     '|', 'grep', '">:$"']
    demangled_output = _parse(os.popen(' '.join(demangled_cmd))
                                .read().replace('std::', '')
                                       .replace('__cxx11::', ''))
    demangled_output = list(map(_strip_args, demangled_output))
    mangled_cmd = ['llvm-objdump',
                   '-d',
                   binary_path,
                   '|', 'grep', '">:$"']
    mangled_ouput = _parse(os.popen(' '.join(mangled_cmd))
                             .read())
    return mangled_ouput[_match(caller, demangled_output)]
