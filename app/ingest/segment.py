import re
from collections import Counter
from dataclasses import dataclass, field

from app.ingest.pdf import Line

NUMBERED_HEADING_RE = re.compile(r"^(\d{1,2}(?:\.\d{1,2}){0,3})[.)]?\s+(\S.{0,150})$")
MAX_HEADING_CHARS = 160
PARAGRAPH_GAP_FACTOR = 0.8


@dataclass
class Block:
    lines: list[Line] = field(default_factory=list)

    @property
    def text(self) -> str:
        return " ".join(line.text for line in self.lines)

    @property
    def size(self) -> float:
        return self.lines[0].size

    @property
    def bold_ratio(self) -> float:
        bold = sum(1 for line in self.lines if line.bold)
        return bold / len(self.lines)

    @property
    def page(self) -> int:
        return self.lines[0].page

    @property
    def bbox(self) -> list[float]:
        return [
            min(line.x0 for line in self.lines),
            min(line.top for line in self.lines),
            max(line.x1 for line in self.lines),
            max(line.bottom for line in self.lines),
        ]


@dataclass
class Clause:
    ordinal: int
    section_no: str | None
    heading_path: list[str]
    text: str
    page: int
    bbox: list[float] | None
    spans: list[dict]


def body_size(lines: list[Line]) -> float:
    weights: Counter = Counter()
    for line in lines:
        weights[line.size] += len(line.text)
    if not weights:
        return 10.0
    return weights.most_common(1)[0][0]


def group_blocks(lines: list[Line]) -> list[Block]:
    blocks: list[Block] = []
    current: list[Line] = []
    previous: Line | None = None
    for line in lines:
        if previous is None:
            current = [line]
        else:
            gap = line.top - previous.bottom
            continues = (
                line.page == previous.page
                and abs(line.size - previous.size) <= 0.6
                and line.bold == previous.bold
                and gap <= PARAGRAPH_GAP_FACTOR * previous.size
            )
            if continues:
                current.append(line)
            else:
                blocks.append(Block(current))
                current = [line]
        previous = line
    if current:
        blocks.append(Block(current))
    return blocks


def heading_level(block: Block, base_size: float) -> tuple[int | None, str | None]:
    text = block.text.strip()
    if not text or len(text) > MAX_HEADING_CHARS:
        return None, None
    match = NUMBERED_HEADING_RE.match(text)
    looks_heading = block.size >= base_size + 0.8 or block.bold_ratio >= 0.7
    ends_open = not text.endswith((".", ";"))
    if match and looks_heading and ends_open:
        number = match.group(1)
        return number.count(".") + 1, number
    if block.size >= base_size + 1.5 and block.bold_ratio >= 0.5 and ends_open:
        return 1, None
    return None, None


def page_spans(blocks: list[Block]) -> list[dict]:
    spans = []
    for block in blocks:
        by_page: dict[int, list[Line]] = {}
        for line in block.lines:
            by_page.setdefault(line.page, []).append(line)
        for page, page_lines in sorted(by_page.items()):
            spans.append(
                {
                    "page": page,
                    "bbox": [
                        min(line.x0 for line in page_lines),
                        min(line.top for line in page_lines),
                        max(line.x1 for line in page_lines),
                        max(line.bottom for line in page_lines),
                    ],
                }
            )
    return spans


def segment(lines: list[Line]) -> list[Clause]:
    if not lines:
        return []

    base_size = body_size(lines)
    clauses: list[Clause] = []
    stack: list[tuple[int, str]] = []
    section_no: str | None = None
    heading_path: list[str] = []
    heading_block: Block | None = None
    body_blocks: list[Block] = []

    def flush() -> None:
        if heading_block is None and not body_blocks:
            return
        head = heading_block.text if heading_block else ""
        body = "\n".join(block.text for block in body_blocks).strip()
        text = f"{head}\n{body}".strip()
        if not text:
            return
        spans_source = ([heading_block] if heading_block else []) + body_blocks
        clauses.append(
            Clause(
                ordinal=len(clauses),
                section_no=section_no,
                heading_path=list(heading_path),
                text=text,
                page=spans_source[0].page,
                bbox=spans_source[0].bbox,
                spans=page_spans(spans_source),
            )
        )

    for block in group_blocks(lines):
        level, number = heading_level(block, base_size)
        if level is None:
            body_blocks.append(block)
            continue
        flush()
        stack = [item for item in stack if item[0] < level]
        heading_path = [item[1] for item in stack]
        stack.append((level, block.text))
        section_no = number
        heading_block = block
        body_blocks = []

    flush()
    return clauses
