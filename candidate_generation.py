import codeql
from abc import ABC, abstractmethod
from typing import List, Dict, Tuple, Generator
from dataclasses import dataclass
from label import SourceRange, SourceLocation
import os.path
import settings


@dataclass
class GeneralCandidate:
    """
    name(paramers,...) (all information needed for (de-)mangling.
    """
    calle_name: str


@dataclass
class DatasetCandidate(GeneralCandidate):
    caller_range: SourceRange

    def __hash__(self):
        return hash(self.calle_name + self.caller_range.file +
                    str(self.caller_range.line_from) +
                    str(self.caller_range.line_to))


@dataclass
class Candidate(GeneralCandidate):
    """
    where the function to be inlined is defined
    """
    calle_location: SourceLocation
    """
    return type of the calle (e.g., used for annotation with
    __attribute__((always_inline))
    """
    calle_return_type: str
    """
    Mapping from caller name(paramers,...) to the range of source code
    of their body
    """
    callers: Dict[str, Tuple[SourceRange, SourceLocation]]


@dataclass
class LibraryCandidate(GeneralCandidate):
    """
    Source location of the call
    """
    call_line: SourceLocation
    """
    Source range of the caller for va_ranges
    """
    caller_range: SourceRange
    """
    the calling function name as name(paramers,...)
    """
    caller_name: str


def _post_process(raw_results: List[List[str]]) -> List[list]:
    for res in raw_results:
        res.append(res[0].split(' ')[0])  # calle return type
        res[0] = _strip_return_type(res[0])  # calle_name
        # calle_location
        res[1] = to_source_range(res[1]).get_start_location()
        res[2] = _strip_return_type(res[2])  # caller_name
        res[3] = to_source_range(res[3])  # call location
        res[4] = to_source_range(res[4])  # caller_block
    return raw_results


def _strip_return_type(full_signature: str) -> str:
    return ' '.join(full_signature.split(' ')[1:])


def to_source_range(code_ql_location: str) -> SourceRange:
    location_range = code_ql_location[len('file://'):]
    split = location_range.split(':')
    source_range = SourceRange()
    source_range.line_from = int(split[-4])
    source_range.column_from = int(split[-3])
    source_range.line_to = int(split[-2])
    source_range.column_to = int(split[-1])
    source_range.file = ':'.join(split[:-4])
    return source_range


def _group(rows: List[list]) -> Dict:
    d = {}
    for row in rows:
        if row[0] not in d:
            d[row[0]] = []
        d[row[0]].append(row[1:])
    return d


class CandidateGeneration(ABC):
    def from_file(self, path: str) -> Generator[None, GeneralCandidate, None]:
        folder = os.path.dirname(path)
        compile_command = settings.cpp_compile + [path]
        db = codeql.Database.create('cpp',
                                    folder,
                                    command=compile_command)
        return self.from_db(db)

    def from_source(self, source: str)\
            -> Generator[None, GeneralCandidate, None]:
        db = codeql.Database.from_cpp(source)
        return self.from_db(db)

    @abstractmethod
    def from_db(self, db: codeql.Database)\
            -> Generator[None, GeneralCandidate, None]:
        pass


class TemplateCandidateGeneration(CandidateGeneration):
    def from_db(self, db: codeql.Database)\
            -> Generator[None, LibraryCandidate, None]:
        raw_results = db.query('''
import cpp
import semmle.code.cpp.Print

private predicate inLibrary(Element a) {
    a.getFile().toString().prefix("/usr/include/".length()) = "/usr/include/"
}

class InterestingFunction extends Function {
    InterestingFunction() {
        exists(ConstructorCall a | not inLibrary(a)
        and a.getTargetType().(Class).getAPublicMember().(Function) = this
        and inLibrary(a.getTarget()))
    }
}

from FunctionCall fc, InterestingFunction f
where
    fc.getTarget() = f and
    not inLibrary(fc)
select getIdentityString(f), fc.getLocation(),
fc.getEnclosingFunction().getBlock().getLocation(),
getIdentityString(fc.getEnclosingFunction())
        ''')
        for res in raw_results[1:]:
            caller_source_range = to_source_range(res[1]).get_start_location()
            yield LibraryCandidate(
                    calle_name=res[0],
                    call_line=caller_source_range,
                    caller_range=to_source_range(res[2]),
                    caller_name=_strip_return_type(res[3])
                    )


class StringVectorPushBackCandidateGeneration(CandidateGeneration):
    def from_db(self, db: codeql.Database)\
            -> Generator[None, LibraryCandidate, None]:
        raw_results = db.query('''
import cpp
import semmle.code.cpp.Print

private predicate inLibrary(Element a) {
    a.getFile().toString().prefix("/usr/include/".length()) = "/usr/include/"
}

from FunctionCall fc
where fc.getTarget().getName() = "push_back"
and not inLibrary(fc)
and fc.getTarget().isMember()
and fc.getTarget()
      .getDeclaringType()
      .getTemplateArgument(0)
      .toString()
      .prefix("basic_string".length()) = "basic_string"
select getIdentityString(fc.getTarget()), fc.getLocation(),
fc.getEnclosingFunction().getBlock().getLocation(),
getIdentityString(fc.getEnclosingFunction())
        ''')
        for res in raw_results[1:]:
            caller_source_range = to_source_range(res[1]).get_start_location()
            yield LibraryCandidate(
                    calle_name=res[0],
                    call_line=caller_source_range,
                    caller_range=to_source_range(res[2]),
                    caller_name=_strip_return_type(res[3])
                    )


class FunctionCandidateGeneration(CandidateGeneration):
    min_cc: int

    def __init__(self, min_cc: int):
        self.min_cc = min_cc

    def from_db(self, db: codeql.Database) -> Generator[None, Candidate, None]:
        raw_results = db.query(f'''
import cpp
import semmle.code.cpp.Print

private predicate inLibrary(Element a) {{
    a.getFile().toString().prefix("/usr/include/".length()) = "/usr/include/"
}}

from FunctionCall fc, Function f
where
    fc.getTarget() = f and
    f.hasDefinition() and
    not inLibrary(f) and
    not inLibrary(fc) and
    f.getMetrics().getCyclomaticComplexity() >= {self.min_cc}
select
    getIdentityString(f), f.getLocation(),
    getIdentityString(fc.getEnclosingFunction()), fc.getLocation(),
    fc.getEnclosingFunction().getBlock().getLocation()
        ''')
        # TODO choose more reasonable types to do better parsing
        post_processed = _post_process(raw_results[1:])
        groups = _group(post_processed)
        for key, value in groups.items():
            yield Candidate(calle_name=key,
                            calle_location=value[0][0],
                            calle_return_type=value[0][4],
                            callers={i[1]: (i[3], i[2]) for i in value})
