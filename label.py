from dataclasses import dataclass
from typing import List


@dataclass
class SourceLocation:
    file: str
    line: int
    column: int


@dataclass
class SourceRange:
    file: str
    line_from: int
    column_from: int
    line_to: int
    column_to: int

    @classmethod
    def from_locations(cls, start: SourceLocation, end: SourceLocation):
        assert(start.file == end.file)
        obj = cls()
        obj.file = start.file
        obj.line_from = start.line
        obj.column_from = start.line
        obj.line_to = end.line
        obj.column_to = end.line
        return obj

    def get_start_location(self) -> SourceLocation:
        return SourceLocation(self.file, self.line_from, self.column_from)


@dataclass
class Label:
    source: str


@dataclass
class FunctionInline(Label):
    function: str
    inlined_in: List[SourceLocation]


@dataclass
class TemplateInline(Label):
    """
    where the template was defined
    """
    def_at: SourceLocation
