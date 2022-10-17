from dataclasses import dataclass
from typing import List


@dataclass
class SourceLocation:
    file: str
    line: int
    column: str


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
