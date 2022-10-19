from typing import List, Tuple
import os
from dataclasses import dataclass
from candidate_generation import Candidate


@dataclass
class AnnotationResult:
    annotated_source: str
    annotated_function: str
    all_candidates: List[str]
    cyclomatic_complexity: int
    original_path: str
    """
    source code range the function that calls the inlined function
    """
    lines_of_calling_function: Tuple[int, int]

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


@dataclass
class InlineResult:
    candidate: Candidate
    annotated_source_path: str
    annotated_source: str
