from typing import List, Dict, Union
import compilation
import os
import lizard
from candidate_generation import DatasetCandidate
from label import SourceRange
from va_ranges import get_va_ranges
from tqdm import tqdm
# from multiprocessing import Pool, cpu_count
import json
import time


def strip_arguments(demangled: str) -> str:
    """
    Strip arguments from a demangled function name
    """
    return demangled.split('(')[0]


dataset_location = '../datasetQueryTest/dataset/src/'

with open(os.path.join(dataset_location, 'all_funcs.txt'), 'r') as f:
    funcs = f.readlines()

source_files: Dict[str, List[Union[str, DatasetCandidate]]] = {}

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

processing_times = []
for source_file in source_files:
    start = time.time()

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
    end = time.time()
    processing_times.append(end - start)

print(f'Average processing time: {sum(processing_times) / len(processing_times)}')

binary_files: Dict[str, List[str]] = {}


def compile_here(file_name: str) -> List[str]:
    file_path = os.path.join(dataset_location, file_name)
    # get the folder where file_name is located
    folder_name, _ = os.path.split(file_path)
    # compile the source code
    binary_path = compilation.compile_all(file_path, folder_name)
    return binary_path


for file_name in tqdm(source_files.keys()):
    binary_files[file_name] = compile_here(file_name)


for source_file, binary_files in tqdm(binary_files.items()):
    for binary_file in binary_files:
        output = {}
        label_file = binary_file + '.json'
        # if label file is newer than binary file, skip
        if os.path.exists(label_file) and\
                os.path.getmtime(label_file) > os.path.getmtime(binary_file):
            continue
        for candidate in source_files[source_file]:
            f = candidate.caller_range.line_from
            t = candidate.caller_range.line_to
            va_ranges = get_va_ranges(binary_path=binary_file,
                                      caller=candidate.calle_name,
                                      caller_range=(f, t),
                                      log=False)
            output[candidate.calle_name] = va_ranges
        with open(label_file, 'w') as f:
            f.write(json.dumps(output))
