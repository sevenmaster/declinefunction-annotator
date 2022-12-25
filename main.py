import os
from typing import Generator
import subprocess
from annotation_result import InlineResult
import settings
from candidate_generation import Candidate,\
                                 SourceLocation,\
                                 TemplateCandidateGeneration,\
                                 FunctionCandidateGeneration,\
                                 LibraryCandidate
from va_ranges import get_va_ranges

annotation = '__attribute__((always_inline))'


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


def compile_with_symbols(source_file: str, binary_path=None) -> str:
    """
    compile to binary with g3 symbols according to settings.cpp_compile.
    The resulting binary will be placed next to the source_file, by default
    :param source_file: .cpp file to compile
    :param binary_path: where to place the binary
    """
    source_file = os.path.abspath(source_file)
    if binary_path is None:
        binary_path = source_file[:-4]
    command = settings.cpp_compile +\
        [source_file, '-o', binary_path]
    child = subprocess.call(command)
    assert child == 0
    return binary_path


if __name__ == '__main__':
    in_path = '/home/nine/CLionProjects/'\
              + 'inlinefunctionplayground/onlyInline/inlineFunction.cpp'
    path = os.path.abspath(in_path)

    # for s in produce_inline_variants_ql(in_path):
    #     s: InlineResult
    #     print('==================')
    #     print('==================')
    #     print('calle', s.candidate.calle_name)
    #     print('==================')
    #     print('==================')
    #     new_path = s.annotated_source_path
    #     binary_path = new_path[:-4]
    #     with open(new_path, 'w+') as f:
    #         f.write(s.annotated_source)
    #     binary_path = compile_with_symbols(new_path)
    #     print(s.candidate.callers)
    #     for caller_name, location in s.candidate.callers.items():
    #         print('------------------')
    #         print('caller', caller_name)
    #         print('------------------')
    #         caller_range = (location[0].line_from, location[0].line_to)
    #         get_va_ranges(binary_path, caller_name, caller_range)

    in_path = '/home/nine/CLionProjects/'\
              + 'inlinefunctionplayground/alltemplate/main.cpp'
    path = os.path.abspath(in_path)

    candidate_generator = TemplateCandidateGeneration()
    for candidate in candidate_generator.from_file(in_path):

        print('==================')
        print('==================')
        print('calle', candidate.calle_name)
        print('in', candidate.caller_name)
        print('==================')
        print('==================')
        candidate: LibraryCandidate
        binary_path = compile_with_symbols(path)
        caller_range = (candidate.caller_range.line_from,
                        candidate.caller_range.line_to)
        get_va_ranges(binary_path, candidate.caller_name, caller_range)
