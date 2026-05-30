from dataclasses import dataclass
from typing import Any, List, Union


@dataclass
class First:
    content: Any


@dataclass
class Second:
    content: Any


@dataclass
class Both:
    left: Any
    right: Any


Diff = Union[First, Second, Both]


@dataclass
class EdHunk:
    orig_pos: int
    dest_pos: int
    hunk_type: str
    os_lines: List[str]
    ds_lines: List[str]


def print_segment_spec(orig_pos: int, line_count: int) -> str:
    if line_count == 0:
        return str(orig_pos)
    elif line_count == 1:
        return str(orig_pos + 1)
    else:
        return f"{orig_pos + 1},{orig_pos + line_count}"


def print_hunk_head(hunk: EdHunk) -> str:
    os_len = len(hunk.os_lines)
    ds_len = len(hunk.ds_lines)
    if hunk.hunk_type == "append":
        return f"{print_segment_spec(hunk.orig_pos, 0)}a{print_segment_spec(hunk.dest_pos, ds_len)}"
    elif hunk.hunk_type == "delete":
        return f"{print_segment_spec(hunk.orig_pos, os_len)}d{print_segment_spec(hunk.dest_pos, 0)}"
    elif hunk.hunk_type == "change":
        return f"{print_segment_spec(hunk.orig_pos, os_len)}c{print_segment_spec(hunk.dest_pos, ds_len)}"
    raise ValueError(hunk.hunk_type)


def print_hunk_body(hunk: EdHunk) -> str:
    def format_lines(prefix: str, lines: List[str]) -> str:
        # We assume `lines` don't have trailing newlines. If they do, strip them.
        return "\n".join(f"{prefix}{line.rstrip('\n')}" for line in lines)

    if hunk.hunk_type == "append":
        return format_lines("> ", hunk.ds_lines)
    elif hunk.hunk_type == "delete":
        return format_lines("< ", hunk.os_lines)
    elif hunk.hunk_type == "change":
        return f"{format_lines('< ', hunk.os_lines)}\n---\n{format_lines('> ', hunk.ds_lines)}"
    raise ValueError(hunk.hunk_type)


def diffs_to_ed_hunks(diffs: List[Diff]) -> List[EdHunk]:
    hunks = []
    orig_pos = 0
    dest_pos = 0

    fs: List[Any] = []
    ss: List[Any] = []
    orig_pos_start = orig_pos
    dest_pos_start = dest_pos

    def add_hunk():
        if not fs and not ss:
            return
        hunk_type = "change"
        if not fs:
            hunk_type = "append"
        elif not ss:
            hunk_type = "delete"

        hunks.append(
            EdHunk(
                orig_pos=orig_pos_start,
                dest_pos=dest_pos_start,
                hunk_type=hunk_type,
                os_lines=list(fs),
                ds_lines=list(ss),
            )
        )

    for d in diffs:
        if isinstance(d, Both):
            if fs or ss:
                add_hunk()
                fs.clear()
                ss.clear()
            orig_pos += 1
            dest_pos += 1
            orig_pos_start = orig_pos
            dest_pos_start = dest_pos
        elif isinstance(d, First):
            fs.append(d.content)
            orig_pos += 1
        elif isinstance(d, Second):
            ss.append(d.content)
            dest_pos += 1

    if fs or ss:
        add_hunk()

    return hunks


def ed_hunk_to_ed_diff(eh: EdHunk) -> str:
    return f"{print_hunk_head(eh)}\n{print_hunk_body(eh)}"


def ed_hunks_to_ed_diff(ehs: List[EdHunk]) -> str:
    return "\n".join(ed_hunk_to_ed_diff(eh) for eh in ehs)


def generate_vim_compatible_diff(diffs: List[Diff]) -> List[EdHunk]:
    return diffs_to_ed_hunks(diffs)
