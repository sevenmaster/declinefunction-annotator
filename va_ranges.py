import itertools
import re
import subprocess
from typing import List, Tuple


def _caller_source_file(output: List[str]) -> str:
    defining_file = next(line for line in output if line.startswith('; '))
    return _dwarf_annotation_to_source_file(defining_file)


def _dwarf_annotation_to_source_file(annotation_line: str) -> str:
    return ':'.join(annotation_line[2:].split(':')[:-1])


def get_va_ranges(binary_path: str,
                  caller: str,
                  caller_range: Tuple[int, int]) -> List[Tuple[int, int]]:
    if caller == 'main()':
        caller = 'main'
    start = caller_range[0]
    end = caller_range[1] + 1

    # get objdump lines for disassembly of caller with draw line mapping
    objdump_command = ['llvm-objdump',
                       '-M', 'intel',
                       '--demangle',
                       f'--disassemble-symbols={caller}',
                       '-l', binary_path]
    output = subprocess.check_output(objdump_command)
    output = output.decode('utf-8')
    output = output.split('\n')

    output = itertools.dropwhile(  # keep only disassembly, no headers
            lambda x: re.match(r'; .+.[cpp|h]:[0-9]+', x) is None,
            output
            )
    output = filter(lambda x: x != '', output)  # remove blank lines
    output = list(map(str.lstrip, output))  # remove indentation
    caller_source_file = _caller_source_file(output)
    line_insturction_mapping: List[Tuple[int, str, List[str]]] = []
    instructions_for_line: List[str] = []
    last_line_num = 0
    last_from_file = ''
    for line in output:
        if line.startswith('; '):
            if instructions_for_line != []:  # store previous line if exists
                line_insturction_mapping.append(
                        (last_line_num, last_from_file, instructions_for_line))
            last_from_file = _dwarf_annotation_to_source_file(line)
            last_line_num = int(line.split(':')[-1])
            instructions_for_line = []
        else:
            instructions_for_line.append(line)
    INLINE_COLOR = '\033[91m'
    DEFAULT_COLOR = '\033[0m'
    for line_num, from_file, instructions in line_insturction_mapping:
        if line_num > end or line_num < start\
                or from_file != caller_source_file:
            print(INLINE_COLOR + from_file, line_num)
            for i in instructions:
                print(INLINE_COLOR + f'I{line_num}\t', i)
        else:
            print(DEFAULT_COLOR + from_file, line_num)
            for i in instructions:
                print(DEFAULT_COLOR + f'O{line_num}\t', i)
    print(DEFAULT_COLOR)
    return None
