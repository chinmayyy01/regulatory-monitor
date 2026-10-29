from dataclasses import dataclass
from datetime import date, datetime
from typing import Iterator
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from app.fetchers.base import request_bytes

ARCHIVE_URL = "https://www.rbi.org.in/scripts/NotificationUser.aspx"
SUBMIT_FIELD = "UsrFontCntr$btn"
DATE_FORMATS = ("%b %d, %Y", "%B %d, %Y")


@dataclass(frozen=True)
class Announcement:
    title: str
    date_issued: date | None
    detail_url: str
    pdf_url: str | None


def parse_date(value: str) -> date | None:
    cleaned = " ".join(value.split())
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(cleaned, fmt).date()
        except ValueError:
            continue
    return None


def parse_announcements(html: bytes) -> list[Announcement]:
    soup = BeautifulSoup(html, "lxml")
    announcements = []
    current_date: date | None = None
    for row in soup.select("table.tablebg tr"):
        header = row.find("td", class_="tableheader")
        if header is not None:
            current_date = parse_date(header.get_text(" ", strip=True))
            continue
        link = row.find("a", class_="link2")
        if link is None:
            continue
        href = link.get("href") or ""
        pdf_url = None
        for candidate in row.find_all("a"):
            candidate_href = candidate.get("href") or ""
            if candidate_href.lower().endswith(".pdf"):
                pdf_url = urljoin(ARCHIVE_URL, candidate_href)
        announcements.append(
            Announcement(
                title=link.get_text(" ", strip=True),
                date_issued=current_date,
                detail_url=urljoin(ARCHIVE_URL, href),
                pdf_url=pdf_url,
            )
        )
    return announcements


def hidden_fields(html: bytes) -> dict:
    soup = BeautifulSoup(html, "lxml")
    return {
        element["name"]: element.get("value", "")
        for element in soup.select("input[type=hidden]")
        if element.get("name")
    }


def fetch_month(session, year: int, month: int) -> list[Announcement]:
    listing = request_bytes("GET", ARCHIVE_URL, session=session)
    form = hidden_fields(listing)
    form.update(
        {
            "hdnYear": str(year),
            "hdnMonth": f"{month:02d}",
            SUBMIT_FIELD: "",
        }
    )
    response = request_bytes("POST", ARCHIVE_URL, data=form, session=session)
    return parse_announcements(response)


def iter_months(start: tuple[int, int], end: tuple[int, int]) -> Iterator[tuple[int, int]]:
    year, month = start
    while (year, month) <= end:
        yield year, month
        month += 1
        if month > 12:
            year += 1
            month = 1
