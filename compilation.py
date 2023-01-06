"""
compile to binary with g3 symbols according to settings.cpp_compile.
The resulting binary will be placed next to the source_file, by default
"""
import subprocess
import os
from typing import List

optimization_levels = ['-O0', '-O1', '-O2', '-O3']
compilers = ['clang++', 'g++']


def _get_binary_name(source_file: str, compiler: str, optimization_level) ->\
        str:
    _, fn = os.path.split(source_file)
    return fn[:-4] + '_' + compiler + '_' + optimization_level[1:]


def compile_with_symbols(source_file: str, binary_dir, compiler: str,
                         optimization_level: str) -> str:
    """
    compile to binary with g3 symbols if not already compiled
    :param source_file: .cpp file to compile
    :param binary_dir: where to place the binary
    :param compiler: compiler to use
    :param optimization_level: optimization level to use
    """
    binary_file = os.path.join(binary_dir, 'bin/')
    binary_file = os.path.join(binary_file,
                               _get_binary_name(source_file,
                                                compiler,
                                                optimization_level))
    # absolute paths just to be sure
    source_file = os.path.abspath(source_file)
    binary_file = os.path.abspath(binary_file)
    # get last modification time of source file
    source_mod_time = os.path.getmtime(source_file)
    # if binary exists and is newer than source file, return it
    if os.path.exists(binary_file) and\
            os.path.getmtime(binary_file) > source_mod_time:
        return binary_file
    command = [compiler,
               optimization_level,
               '-g3',
               source_file,
               '-o', binary_file]
    child = subprocess.call(command)
    assert child == 0
    return binary_file


def compile_all(source_file: str, binary_dir: str) -> List[str]:
    results = []
    os.makedirs(binary_dir, exist_ok=True)
    for compiler in compilers:
        for optimization_level in optimization_levels:
            binary_file = compile_with_symbols(source_file,
                                               binary_dir,
                                               compiler,
                                               optimization_level)
            results.append(binary_file)
    return results
