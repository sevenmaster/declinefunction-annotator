from typing import List, Tuple
import os


class AnnotationResult:
    annotated_source: str
    annotated_function: str
    all_candidates: List[str]
    cyclomatic_complexity: int
    original_path: str
    # source code range the function that calls the inlined function
    lines_of_calling_function: Tuple[int, int]

    def __init__(self,
                 annotated_source: str,
                 annotated_function: str,
                 all_candidates: List[str],
                 cyclomatic_complexity: int,
                 original_path: str,
                 lines_of_calling_function: Tuple[int, int]):
        self.annotated_source = annotated_source
        self.annotated_function = annotated_function
        self.all_candidates = all_candidates
        self.cyclomatic_complexity = cyclomatic_complexity
        self.original_path = original_path
        self.lines_of_calling_function = lines_of_calling_function

    def new_filename(self) -> str:
        unescaped = self.original_path + '::' + self.annotated_function
        _, extension = os.path.splitext(self.original_path)
        escaped = ''.join(c if c not in '/.' else '_' for c in unescaped)
        return escaped + extension

    def commented_source(self):
        prefix = f'''// annotated function: {self.annotated_function}
// cyclomatic complexity: {self.cyclomatic_complexity}
// all candidates: {self.all_candidates}
// original file: {self.original_path}
// main_range: {self.lines_of_calling_function}
'''
        return prefix + self.annotated_source
