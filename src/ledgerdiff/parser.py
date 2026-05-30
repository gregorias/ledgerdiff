import re
from dataclasses import dataclass
from datetime import date, datetime
from typing import List, Union

import parsy  # type: ignore


@dataclass
class DatedChunk:
    date: date
    content: str


@dataclass
class UndatedChunk:
    content: str


Chunk = Union[DatedChunk, UndatedChunk]


@dataclass
class Journal:
    chunks: List[Chunk]


class ParseError(Exception):
    pass


def parse_date(date_str: str) -> date:
    if "-" in date_str:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    else:
        return datetime.strptime(date_str, "%Y/%m/%d").date()


emptyLine = parsy.string("\n")
nonEmptyLine = parsy.regex(r"[^\n]+(?:\n|$)")
commentLineP = parsy.regex(r";[^\n]*(?:\n|$)")

datedLineStr = parsy.regex(
    r"(?:[a-zA-Z]+[ \t]+)?\d{4}[-/]\d{1,2}[-/]\d{1,2}[^\n]*(?:\n|$)"
)


@parsy.generate
def datedLineWithStr():
    line = yield datedLineStr
    m = re.search(r"\d{4}[-/]\d{1,2}[-/]\d{1,2}", line)
    if m:
        day = parse_date(m.group(0))
        return (line, day)
    yield parsy.fail("Invalid date string")


@parsy.generate
def datedChunkStart():
    comments = yield commentLineP.many()
    line, day = yield datedLineWithStr
    return ("".join(comments), line, day)


indentedLineP = parsy.regex(r" [^\n]*(?:\n|$)")


@parsy.generate
def datedChunkP():
    comments_str, dated_line_str, day = yield datedChunkStart
    ils = yield indentedLineP.many()
    return DatedChunk(day, comments_str + dated_line_str + "".join(ils))


@parsy.generate
def undatedChunkLine():
    yield datedChunkStart.should_fail("not dated chunk")
    line = yield emptyLine | nonEmptyLine
    return line


undatedChunkP = undatedChunkLine.at_least(1).map(
    lambda lines: UndatedChunk("".join(lines))
)


chunkP = datedChunkP | undatedChunkP


@parsy.generate
def journalP():
    chunks = yield chunkP.many()
    yield parsy.eof
    return Journal(chunks)


def parse_journal(text: str) -> Journal:
    try:
        return journalP.parse(text)
    except parsy.ParseError as e:
        raise ParseError(str(e))
