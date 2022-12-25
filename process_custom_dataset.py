from typing import List, Dict
import compilation
import os
import lizard
from candidate_generation import DatasetCandidate
from label import SourceRange


def strip_arguments(demangled: str) -> str:
    """
    Strip arguments from a demangled function name
    """
    return demangled.split('(')[0]


dataset_location = '../datasetQueryTest/dataset/src/'

with open(os.path.join(dataset_location, 'all_funcs.txt'), 'r') as f:
    funcs = f.readlines()

source_files: Dict[str, List[str]] = {}

for func in funcs:
    # this is not how to do signature parsing but works here
    file_name, rest = func.split(':', 1)
    func_sig = ' '.join(rest.split(' ')[1:-1])
    if 'operator' in func_sig:
        continue
    while '>' in func_sig.split('(')[0]:
        func_sig = ' '.join(func_sig.split(' ')[1:])
    if file_name not in source_files:
        source_files[file_name] = []
    source_files[file_name].append(func_sig)
    if file_name not in source_files:
        source_files[file_name] = []
    source_files[file_name].append(func_sig)

for source_file in source_files:
    def still_exists(func_sig: str) -> bool:
        return strip_arguments(func_sig) in\
                functions, source_files[source_file]

    def to_candidate(func_sig: str) -> DatasetCandidate:
        func_info = functions[strip_arguments(func_sig)]
        sr = SourceRange(file=source_file,
                         line_from=func_info.start_line,
                         column_from=None,
                         line_to=func_info.end_line,
                         column_to=None)
        return DatasetCandidate(func_sig, sr)

    path = os.path.join(dataset_location, source_file)
    lizard_result = lizard.analyze_file(path)
    lizard_result: lizard.FileInformation
    functions: Dict[str, lizard.FunctionInfo] = {func.name: func for func in
                                                 lizard_result.function_list}
    filtered = list(map(to_candidate,
                        filter(still_exists, source_files[source_file])))
    source_files[source_file] = filtered

binary_files: Dict[str, List[str]] = {}
# compile all the source files
for file_name in source_files:
    file_name = os.path.join(dataset_location, file_name)
    # get the folder where file_name is located
    folder_name, _ = os.path.split(file_name)
    # create the folder bin if in folder_name it doesn't exist
    binary_dir = os.path.join(folder_name, 'bin/', file_name[:4])
    os.makedirs(binary_dir, exist_ok=True)
    # compile the source code
    binary_path = compilation.compile_all(file_name, binary_dir)
    if file_name not in binary_files:
        binary_files[file_name] = []
    binary_files[file_name].append(binary_path)

for source_file, binary_files in binary_files.items():
    for binary_file in binary_files:
        pass
