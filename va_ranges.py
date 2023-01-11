import itertools
import re
import subprocess
from typing import List, Tuple, Set
import mangle


def _caller_source_file(output: List[str]) -> str:
    defining_file = next(line for line in output if line.startswith('; '))
    return _dwarf_annotation_to_source_file(defining_file)


def _dwarf_annotation_to_source_file(annotation_line: str) -> str:
    return ':'.join(annotation_line[2:].split(':')[:-1])


def _line_to_va(line: str) -> int:
    va = line.split(':')[0].strip()
    return int(va, 16)


def _get_disassembly(binary_path: str, caller: str) -> List[str]:
    # get objdump lines for disassembly of caller with draw line mapping
    objdump_command = ['llvm-objdump',
                       '-M', 'intel',
                       # '--demangle',
                       f'--disassemble-symbols={caller}',
                       '-l', binary_path]
    output = subprocess.check_output(objdump_command)
    output = output.decode('utf-8')
    return output.split('\n')


def _parse(output: List[str]) -> List[Tuple[int, str, List[str]]]:
    output = itertools.dropwhile(  # keep only disassembly, no headers
            lambda x: re.match(r'; .+.[cpp|h]:[0-9]+', x) is None,
            output
            )
    output = filter(lambda x: x != '', output)  # remove blank lines
    output = map(str.lstrip, output)  # remove indentation
    # filter out lines that start with #
    output = filter(lambda x: not x.startswith('#'), output)
    output = list(output)
    caller_source_file = _caller_source_file(output)
    line_to_instructions: List[Tuple[int, str, List[str]]] = []
    instructions_for_line: List[str] = []
    last_line_num = 0
    last_from_file = ''
    for line in output:
        if line.startswith('; '):
            if instructions_for_line != []:  # store previous line if exists
                line_to_instructions.append(
                        (last_line_num, last_from_file, instructions_for_line))
            last_from_file = _dwarf_annotation_to_source_file(line)
            last_line_num = int(line.split(':')[-1])
            instructions_for_line = []
        else:
            instructions_for_line.append(line)
    return line_to_instructions, caller_source_file


def get_va_ranges(binary_path: str,
                  caller: str,
                  caller_range: Tuple[int, int],
                  log=True) -> List[int]:
    if caller == 'main()':
        caller = 'main'
    else:
        caller = mangle.mangle(binary_path, caller)
    start = caller_range[0]
    end = caller_range[1] + 1
    disasm = _get_disassembly(binary_path, caller)
    ignore = any('prevent_opt' in instr for instr in disasm)
    line_to_instructions, caller_source_file = _parse(disasm)
    INLINE_COLOR = '\033[91m'
    DEFAULT_COLOR = '\033[0m'
    res: Set[int] = set()
    for line_num, from_file, instructions in line_to_instructions:
        if (line_num > end and False or line_num < start and False)\
                or from_file != caller_source_file:
            if log:
                print(INLINE_COLOR + from_file, line_num)
            for instr in instructions:
                if log:
                    print(INLINE_COLOR + f'I{line_num}\t', instr)
                if not ignore:
                    res.add(_line_to_va(instr))
        else:
            if log:
                print(DEFAULT_COLOR + from_file, line_num)
                for instr in instructions:
                    print(DEFAULT_COLOR + f'O{line_num}\t', instr)
        ignore = any('prevent_opt' in instr for instr in instructions)
    if log:
        print(DEFAULT_COLOR)
    return sorted(res)
