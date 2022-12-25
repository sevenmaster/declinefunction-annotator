import va_ranges
from os.path import join, abspath
import main
from candidate_generation import (
        StringVectorPushBackCandidateGeneration,
        LibraryCandidate
)


with open('../datasetQueryTest/ordered/sources.txt', 'r') as f:
    paths = f.read()

# remove comments
paths = filter(lambda x: not x.startswith('#'),
               paths.strip().split('\n'))
# point to dataset
paths = list(map(lambda x: abspath(join('../datasetQueryTest', x)), paths))[1:2]
candidate_generator = StringVectorPushBackCandidateGeneration()

for source_path in paths:
    print('==================')
    print('==================')
    print('source file', source_path)
    print('==================')
    print('==================')
    for candidate in candidate_generator.from_file(source_path):
        print('==================')
        print('calle', candidate.calle_name)
        print('in', candidate.caller_name)
        print('==================')
        candidate: LibraryCandidate
        binary_path = main.compile_with_symbols(source_path)
        caller_range = (candidate.caller_range.line_from,
                        candidate.caller_range.line_to)
        va_ranges.get_va_ranges(binary_path,
                                candidate.caller_name,
                                caller_range,
                                log=True)
        print('call at', candidate.call_line)
