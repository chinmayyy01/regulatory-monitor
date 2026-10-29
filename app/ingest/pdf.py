import io
import re
import statistics
from dataclasses import dataclass

import pdfplumber

PAGE_NUMBER_RE = re.compile(r"^\d{1,4}$")
MIN_LINE_CHARS = 2


@dataclass(frozen=True)
class Line:
    page: int
    text: str
    x0: float
    top: float
    x1: float
    bottom: float
    size: float
    bold: bool


def parse_pdf(pdf_bytes: bytes) -> tuple[list[Line], int]:
    lines = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        total_pages = len(pdf.pages)
        for page_number, page in enumerate(pdf.pages, start=1):
            for raw in page.extract_text_lines():
                text = " ".join(raw["text"].split())
                if len(text) < MIN_LINE_CHARS:
                    continue
                if PAGE_NUMBER_RE.match(text):
                    continue
                sizes = [char["size"] for char in raw["chars"] if char["size"]]
                fonts = [char["fontname"] for char in raw["chars"]]
                if not sizes:
                    continue
                lines.append(
                    Line(
                        page=page_number,
                        text=text,
                        x0=raw["x0"],
                        top=raw["top"],
                        x1=raw["x1"],
                        bottom=raw["bottom"],
                        size=round(statistics.median(sizes), 2),
                        bold=any("bold" in font.lower() for font in fonts),
                    )
                )
    return lines, total_pages


def extract_lines(pdf_bytes: bytes) -> list[Line]:
    return parse_pdf(pdf_bytes)[0]


def page_count(pdf_bytes: bytes) -> int:
    return parse_pdf(pdf_bytes)[1]
