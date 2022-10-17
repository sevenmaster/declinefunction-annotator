import codeql
from abc import ABC, abstractmethod
from typing import List, Tuple
from dataclasses import dataclass


@dataclass
class Candidate:
    caller_names: List[str]
    caller_ranges: List[Tuple[int, int]]


class CandidateGeneration(ABC):
    @abstractmethod
    def from_source(self, source: str) -> List[Candidate]:
        pass


class FunctionCandidateGeneration(CandidateGeneration):
    min_cc: int

    def __init__(self, min_cc: int):
        self.min_cc = min_cc

    def __get_raw_results(self, source):
        db = codeql.Database.from_cpp(source)
        results = db.query(f'''import cpp
from FunctionCall fc, Function f
where
    fc.getTarget() = f and
    f.hasDefinition() and
    f.getMetrics().getCyclomaticComplexity() >= {self.min_cc}
select f.getFullSignature(), f.getBlock().getLocation(), fc.getLocation()
        ''')
        return results

    def from_source(self, source: str) -> List[Candidate]:
        raw_results = self.__get_raw_results(source)
        groups = group(raw_results[1:])
        for 
        return groups


def group(rows: List[list]):
    d = {}
    for row in rows:
        if row[0] not in d:
            d[row[0]] = []
        d[row[0]].append(row[1:])
    return d
