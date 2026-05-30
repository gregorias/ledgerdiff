import difflib
from dataclasses import dataclass
from datetime import date
from typing import List, Union

from .ed import (
    Both,
    Diff,
    First,
    Second,
    ed_hunks_to_ed_diff,
    generate_vim_compatible_diff,
)
from .parser import Chunk, DatedChunk, UndatedChunk, parse_journal


@dataclass
class UndatedSectionChunk:
    content: str


@dataclass
class DatedSectionChunk:
    content: str


SectionChunk = Union[UndatedSectionChunk, DatedSectionChunk]


@dataclass
class UndatedSection:
    content: str


@dataclass
class DatedSection:
    date: date
    chunks: List[SectionChunk]


Section = Union[UndatedSection, DatedSection]


def group_chunks_into_sections(chunks: List[Chunk]) -> List[Section]:
    grouped_undated = []
    if chunks:
        grouped_undated.append(chunks[0])
        for c in chunks[1:]:
            if isinstance(grouped_undated[-1], UndatedChunk) and isinstance(
                c, UndatedChunk
            ):
                grouped_undated[-1] = UndatedChunk(
                    grouped_undated[-1].content + c.content
                )
            else:
                grouped_undated.append(c)

    sections: List[Section] = []
    i = 0
    while i < len(grouped_undated):
        c = grouped_undated[i]
        if isinstance(c, UndatedChunk):
            sections.append(UndatedSection(c.content))
            i += 1
        elif isinstance(c, DatedChunk):
            d = c.date
            sc: List[SectionChunk] = []
            while i < len(grouped_undated):
                curr = grouped_undated[i]
                if isinstance(curr, DatedChunk) and curr.date == d:
                    sc.append(DatedSectionChunk(curr.content))
                    i += 1
                elif isinstance(curr, UndatedChunk):
                    if (
                        i + 1 < len(grouped_undated)
                        and isinstance(grouped_undated[i + 1], DatedChunk)
                        and grouped_undated[i + 1].date == d  # type: ignore
                    ):
                        sc.append(UndatedSectionChunk(curr.content))
                        sc.append(DatedSectionChunk(grouped_undated[i + 1].content))
                        i += 2
                    else:
                        break
                else:
                    break
            sections.append(DatedSection(d, sc))
    return sections


def serialize_two_sections_into_one_diff(
    ls: List[Section], rs: List[Section]
) -> List[Diff]:
    res: List[Diff] = []
    i, j = 0, 0
    while i < len(ls) and j < len(rs):
        left_sec, right_sec = ls[i], rs[j]
        if isinstance(left_sec, UndatedSection):
            res.append(First(left_sec))
            i += 1
        elif isinstance(right_sec, UndatedSection):
            res.append(Second(right_sec))
            j += 1
        else:
            if left_sec.date == right_sec.date:
                res.append(Both(left_sec, right_sec))
                i += 1
                j += 1
            elif left_sec.date < right_sec.date:
                res.append(First(left_sec))
                i += 1
            else:
                res.append(Second(right_sec))
                j += 1
    for x in ls[i:]:
        res.append(First(x))
    for x in rs[j:]:
        res.append(Second(x))
    return res


def is_sp_ordered(p) -> bool:
    if isinstance(p, UndatedSection) or isinstance(p, UndatedSectionChunk):
        return False
    elif isinstance(p, tuple):  # For the test case (status, text)
        return p[0] == "Meat"
    return True


def get_sp_content(p):
    if isinstance(p, UndatedSection):
        return p.content
    elif isinstance(p, DatedSection):
        return p
    elif isinstance(p, UndatedSectionChunk):
        return p.content
    elif isinstance(p, DatedSectionChunk):
        return p.content
    elif isinstance(p, tuple):
        return p[1]
    raise ValueError(p)


def flip_diff(d: Diff) -> Diff:
    if isinstance(d, First):
        return Second(d.content)
    if isinstance(d, Second):
        return First(d.content)
    if isinstance(d, Both):
        return Both(d.right, d.left)
    raise ValueError(d)


def match_filler_ranges(diffs: List[Diff]) -> List[Diff]:
    if not diffs:
        return []

    p0 = diffs[0]
    ps0 = diffs[1:]

    match p0:
        case Both(l, r):
            return [Both(get_sp_content(l), get_sp_content(r))] + match_filler_ranges(
                ps0
            )

        case Second():
            flipped_diffs: List[Diff] = [flip_diff(d) for d in diffs]
            result = match_filler_ranges(flipped_diffs)
            return [flip_diff(d) for d in result]

        case First(f0):
            if is_sp_ordered(f0):
                return [First(get_sp_content(f0))] + match_filler_ranges(ps0)

            # f0 is filler
            match ps0:
                case []:
                    return [First(get_sp_content(f0))]

                case [Both(l, r), *rest]:
                    return [
                        First(get_sp_content(f0)),
                        Both(get_sp_content(l), get_sp_content(r)),
                    ] + match_filler_ranges(
                        rest
                    )  # type: ignore

                case [Second(s1), *rest]:
                    if is_sp_ordered(s1):
                        return [Second(get_sp_content(s1))] + match_filler_ranges(
                            [p0] + rest
                        )

                    # s1 is filler
                    match rest:
                        case [First(f2), First(), *_]:
                            return [
                                First(get_sp_content(f0)),
                                First(get_sp_content(f2)),
                            ] + match_filler_ranges([ps0[0]] + rest[1:])
                        case [Second(s2), Second(), *_]:
                            return [
                                Second(get_sp_content(s1)),
                                Second(get_sp_content(s2)),
                            ] + match_filler_ranges([p0] + rest[1:])
                        case _:
                            return [
                                Both(get_sp_content(f0), get_sp_content(s1))
                            ] + match_filler_ranges(rest)

                case [First(f1), *rest]:
                    match rest:
                        case [] | [First(), *_] | [Both(), *_]:
                            return [First(get_sp_content(f0))] + match_filler_ranges(
                                ps0
                            )
                        case [Second(s2), *rest2]:
                            if is_sp_ordered(s2):
                                return [
                                    First(get_sp_content(f0))
                                ] + match_filler_ranges(ps0)

                            # s2 is filler
                            match rest2:
                                case [First(), *_]:
                                    return [
                                        First(get_sp_content(f0)),
                                        First(get_sp_content(f1)),
                                    ] + match_filler_ranges(rest)
                                case _:
                                    return [
                                        Both(get_sp_content(f0), get_sp_content(s2))
                                    ] + match_filler_ranges([ps0[0]] + rest2)
    return []


def similar_ledger_line(left_line: str, right_line: str) -> bool:
    def process(s: str) -> str:
        s = s.replace(" ", "")
        s = s.lstrip("!*")
        return s

    return process(left_line) == process(right_line)


def get_diff_by(ls: list, rs: list, is_equal) -> List[Diff]:
    class Wrapper:
        def __init__(self, val):
            self.val = val

        def __eq__(self, other):
            if not isinstance(other, Wrapper):
                return False
            return is_equal(self.val, other.val)

        def __hash__(self):
            return 1

    sm = difflib.SequenceMatcher(
        None, [Wrapper(x) for x in ls], [Wrapper(x) for x in rs]
    )
    result: List[Diff] = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "replace":
            for x in ls[i1:i2]:
                result.append(First(x))
            for y in rs[j1:j2]:
                result.append(Second(y))
        elif tag == "delete":
            for x in ls[i1:i2]:
                result.append(First(x))
        elif tag == "insert":
            for y in rs[j1:j2]:
                result.append(Second(y))
        elif tag == "equal":
            for x, y in zip(ls[i1:i2], rs[j1:j2]):
                result.append(Both(x, y))
    return result


def diff_paired_sections(ls: List[SectionChunk], rs: List[SectionChunk]) -> List[Diff]:
    def similar_chunk(left_chunk, right_chunk):
        if isinstance(left_chunk, UndatedSectionChunk) or isinstance(
            right_chunk, UndatedSectionChunk
        ):
            return False

        l_lines = left_chunk.content.splitlines()  # type: ignore
        r_lines = right_chunk.content.splitlines()  # type: ignore

        diffs = get_diff_by(l_lines, r_lines, similar_ledger_line)
        for d in diffs:
            if isinstance(d, Both):
                return True
        return False

    return get_diff_by(ls, rs, similar_chunk)


def section_to_section_chunks(section: Section) -> List[SectionChunk]:
    if isinstance(section, UndatedSection):
        return [UndatedSectionChunk(section.content)]
    elif isinstance(section, DatedSection):
        return section.chunks
    return []


def match_internal_chunks(diffs: List[Diff]) -> List[Diff]:
    result: List[Diff] = []
    for d in diffs:
        if isinstance(d, First):
            result.extend(First(x) for x in section_to_section_chunks(d.content))
        elif isinstance(d, Second):
            result.extend(Second(x) for x in section_to_section_chunks(d.content))
        elif isinstance(d, Both):
            result.extend(
                diff_paired_sections(
                    section_to_section_chunks(d.left),
                    section_to_section_chunks(d.right),
                )
            )
    return result


def smartly_diff_text(diffs: List[Diff]) -> List[Diff]:
    result: List[Diff] = []
    for d in diffs:
        if isinstance(d, First):
            lines = d.content.splitlines()  # type: ignore
            result.extend(First(line) for line in lines)
        elif isinstance(d, Second):
            lines = d.content.splitlines()  # type: ignore
            result.extend(Second(line) for line in lines)
        elif isinstance(d, Both):
            l_lines = d.left.splitlines()  # type: ignore
            r_lines = d.right.splitlines()  # type: ignore
            result.extend(get_diff_by(l_lines, r_lines, similar_ledger_line))
    return result


def diff_ledger_text(orig: str, dest: str) -> str:
    orig_j = parse_journal(orig)
    dest_j = parse_journal(dest)

    sections_orig = group_chunks_into_sections(orig_j.chunks)
    sections_dest = group_chunks_into_sections(dest_j.chunks)

    sections_matched = serialize_two_sections_into_one_diff(
        sections_orig, sections_dest
    )
    matched_chunks = match_internal_chunks(sections_matched)
    matched_chunks_with_filler = match_filler_ranges(matched_chunks)

    diffs_of_lines = smartly_diff_text(matched_chunks_with_filler)

    hunks = generate_vim_compatible_diff(diffs_of_lines)
    return ed_hunks_to_ed_diff(hunks)
