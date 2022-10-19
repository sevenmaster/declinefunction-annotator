import lizard
from lizard import FunctionInfo
import os
from typing import List, Generator, Tuple, Dict
import subprocess
import itertools
import re
from annotation_result import AnnotationResult, InlineResult
from candidate_generation import FunctionCandidateGeneration
import settings
from candidate_generation import Candidate, SourceLocation

annotation = '__attribute__((always_inline))'


# TODO detect where function is called
def produce_inline_variants(path: str) \
        -> Generator[None, AnnotationResult, None]:
    MIN_CC = 4
    with open(path, 'r') as f:
        sourcecode = f.read()
    analysis = lizard.analyze_file.analyze_source_code(os.path.basename(path),
                                                       sourcecode)
    to_inline: List[FunctionInfo] = \
        filter(lambda x: x.cyclomatic_complexity >= MIN_CC
               and x.name != 'main',
               analysis.function_list)

    source_lines = sourcecode.split('\n')
    main: FunctionInfo = list(filter(lambda x: x.name == 'main',
                                     analysis.function_list))[0]
    function_range = (main.start_line, main.end_line)
    for function in to_inline:
        line = function.start_line
        # annotated = source_lines[:line - 1] \
        #     + [annotation] \
        #     + source_lines[line - 1:]
        # annotated = '\n'.join(annotated)
        func_def = source_lines[line - 1].split(' ')
        source_lines[line - 1] = ' '.join(func_def[:2] +
                                          [annotation] +
                                          func_def[2:])
        annotated = '\n'.join(source_lines)

        inline_candidate_names = list(map(lambda x: x.long_name, to_inline))
        annotation_result = AnnotationResult(
                annotated_source=annotated,
                annotated_function=function.long_name,
                all_candidates=inline_candidate_names,
                cyclomatic_complexity=function.cyclomatic_complexity,
                original_path=path,
                lines_of_calling_function=function_range
                )
        yield annotation_result


def prepare_result_path(path: str, inlined_function: str) -> str:
    full_folder_path, filename = os.path.split(path)
    escaped = ''.join(c if c not in '/.' else '_' for c in inlined_function)
    _, folder_name = os.path.split(full_folder_path)
    # insert function name before .cpp
    result_filename = filename[:-4] + '::' + escaped + '.cpp'
    result_folder = os.path.join('results', folder_name)
    result_path = os.path.join(result_folder, result_filename)
    os.makedirs(result_folder, exist_ok=True)
    return result_path


def source_annotation(path: str, calle_location: SourceLocation,
                      calle_return_type: str) -> str:
    with open(path, 'r') as f:
        sourcecode = f.read()
    source_lines = sourcecode.split('\n')
    idx = calle_location.line - 1
    replacement = calle_return_type + ' ' + annotation
    source_lines[idx] = source_lines[idx].replace(calle_return_type,
                                                  replacement,
                                                  1)
    return '\n'.join(source_lines)


def produce_inline_variants_ql(path: str)\
        -> Generator[None, InlineResult, None]:
    MIN_CC = 0
    candidate_generator = FunctionCandidateGeneration(MIN_CC)
    to_inline = candidate_generator.from_file(path)
    for candidate in to_inline:
        candidate: Candidate
        result_path = prepare_result_path(path, candidate.calle_name)
        result_source_code = source_annotation(path,
                                               candidate.calle_location,
                                               candidate.calle_return_type)
        yield InlineResult(candidate, result_path, result_source_code)


def compile_with_symbols(annotated_source_path: str) -> str:
    annotated_source_path = os.path.abspath(annotated_source_path)
    binary_path = annotated_source_path[:-4]
    command = settings.unoptimized_compile +\
        [annotated_source_path, '-o', binary_path]
    child = subprocess.call(command)
    assert child == 0
    return binary_path


def get_va_ranges(binary_path: str,
                  caller: str,
                  caller_range: Tuple[int, int]) -> List[Tuple[int, int]]:
    if caller == 'main()':
        caller = 'main'
    start = caller_range[0] + 1
    end = caller_range[1] + 1
    objdump_command = ['llvm-objdump',
                       '-M', 'intel',
                       '--demangle',
                       f'--disassemble-symbols={caller}',
                       '-l', binary_path]
    output = subprocess.check_output(objdump_command)
    output = output.decode('utf-8').split('\n')
    output = itertools.dropwhile(
            lambda x: re.match(r'; .+.cpp:[0-9]+', x) is None,
            output
            )
    output = filter(lambda x: x != '', output)
    output = map(str.lstrip, output)
    line_insturction_mapping: Dict[int, List[str]] = {}
    instructions_for_line: List[str] = []
    for line in output:
        if line.startswith('; '):
            line_num = int(line.split('.cpp:')[1])
            if instructions_for_line != []:
                line_insturction_mapping[line_num] = instructions_for_line
            instructions_for_line = []
        else:
            instructions_for_line.append(line)
    INLINE_COLOR = '\033[91m'
    DEFAULT_COLOR = '\033[0m'
    for line_num, instructions in line_insturction_mapping.items():
        if line_num > end or line_num < start:
            for i in instructions:
                print(INLINE_COLOR + f'I{line_num}\t', i)
        else:
            for i in instructions:
                print(DEFAULT_COLOR + f'O{line_num}\t', i)
    return None


in_path = '/home/nine/CLionProjects/'\
          + 'inlinefunctionplayground/onlyInline/inlineFunction.cpp'
path = os.path.abspath(in_path)
# produce_inline_variants_ql(path)

# for s in produce_inline_variants(in_path):
#     new_path = './results/' + s.new_filename()
#     with open(new_path, 'w+') as f:
#         f.write(s.annotated_source)
#     binary_path = compile_with_symbols(new_path)
#     get_va_ranges(binary_path, 'main', s.lines_of_calling_function)


for s in produce_inline_variants_ql(in_path):
    s: InlineResult
    print('==================')
    print('==================')
    print('calle', s.candidate.calle_name)
    print('==================')
    print('==================')
    new_path = s.annotated_source_path
    binary_path = new_path[:-4]
    with open(new_path, 'w+') as f:
        f.write(s.annotated_source)
    binary_path = compile_with_symbols(new_path)
    print(s.candidate.callers)
    for caller_name, location in s.candidate.callers.items():
        print('------------------')
        print('caller', caller_name)
        print('------------------')
        caller_range = (location[0].line_from, location[0].line_to)
        get_va_ranges(binary_path, caller_name, caller_range)
