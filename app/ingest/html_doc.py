import re

from bs4 import BeautifulSoup

from app.ingest.segment import Clause

SECTION_PREFIX = re.compile(r"^(\d{1,2}(?:\.\d{1,2}){0,3})[.)]?\s+")
MIN_PARAGRAPH_CHARS = 25
NOISE_PARAGRAPHS = {"index to rbi circulars", "index to rbi circulars | official website of reserve bank of india"}


def clean(text: str) -> str:
    return " ".join(text.split())


def rbi_paragraphs(html: bytes) -> list[str]:
    soup = BeautifulSoup(html, "lxml")
    box = soup.find("div", id="pnlDetails")
    if box is None:
        return []
    paragraphs = []
    for element in box.find_all("p"):
        text = clean(element.get_text(" ", strip=True))
        if len(text) < MIN_PARAGRAPH_CHARS:
            continue
        if text.lower() in NOISE_PARAGRAPHS:
            continue
        if text.lower().endswith("kb )") or text.lower().endswith("kb)"):
            continue
        paragraphs.append(text)
    return paragraphs


def sebi_pdf_url(html: bytes) -> str | None:
    soup = BeautifulSoup(html, "lxml")
    for frame in soup.find_all("iframe"):
        source = frame.get("src") or ""
        if "file=" not in source:
            continue
        candidate = source.split("file=", 1)[1].strip()
        if candidate.lower().endswith(".pdf"):
            return candidate
    return None


def sebi_title(html: bytes) -> str | None:
    soup = BeautifulSoup(html, "lxml")
    if soup.title is None:
        return None
    title = clean(soup.title.get_text(" ", strip=True))
    return title.replace("SEBI |", "").strip() or None


def paragraphs_to_clauses(paragraphs: list[str]) -> list[Clause]:
    clauses = []
    for text in paragraphs:
        match = SECTION_PREFIX.match(text)
        clauses.append(
            Clause(
                ordinal=len(clauses),
                section_no=match.group(1) if match else None,
                heading_path=[],
                text=text,
                page=1,
                bbox=None,
                spans=[],
            )
        )
    return clauses


def rbi_pdf_url(html: bytes) -> str | None:
    soup = BeautifulSoup(html, "lxml")
    box = soup.find("div", id="pnlDetails")
    if box is None:
        return None
    for link in box.find_all("a", href=True):
        if link["href"].lower().endswith(".pdf"):
            return link["href"]
    return None
