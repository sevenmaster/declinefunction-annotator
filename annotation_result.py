from dataclasses import dataclass
from candidate_generation import Candidate


@dataclass
class InlineResult:
    candidate: Candidate
    annotated_source_path: str
    annotated_source: str
