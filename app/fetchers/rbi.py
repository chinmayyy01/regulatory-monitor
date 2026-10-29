from datetime import datetime
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .base import Circular, fetch_bytes, is_allowed_url

RBI_LISTING_URL = "https://www.rbi.org.in/scripts/NotificationUser.aspx"
MIN_TITLE_LENGTH = 10
MAX_TEXT_CHARS = 8000
DOC_TIMEOUT_SECONDS = 10


def extract_text(html: bytes) -> str:
    soup = BeautifulSoup(html, "lxml")
    container = (
        soup.find("div", class_="content")
        or soup.find("div", id="content")
        or soup.find("table")
    )
    if container is None:
        return ""
    text = container.get_text(separator=" ", strip=True)
    return " ".join(text.split())[:MAX_TEXT_CHARS]


def fetch_rbi_circulars(limit: int = 10) -> list[Circular]:
    if limit <= 0:
        return []

    listing = BeautifulSoup(fetch_bytes(RBI_LISTING_URL), "lxml")
    table = listing.find("table")
    if table is None:
        print("[RBI] No table found")
        return []

    circulars = []
    for row in table.find_all("tr"):
        link = row.find("a")
        if link is None:
            continue
        href = link.get("href")
        title = link.get_text(strip=True)
        if not href or "NotificationUser.aspx" not in href:
            continue
        if len(title) < MIN_TITLE_LENGTH:
            continue

        url = urljoin(RBI_LISTING_URL, href)
        if not is_allowed_url(url):
            print(f"[RBI] Skipped url outside allowlist: {url}")
            continue

        try:
            full_text = extract_text(fetch_bytes(url, timeout=DOC_TIMEOUT_SECONDS))
        except Exception as error:
            print(f"[RBI DOC ERROR] {url}: {error}")
            full_text = ""
        if not full_text:
            full_text = title

        circulars.append(
            Circular(
                id=url,
                title=title,
                source="RBI",
                url=url,
                published_date=datetime.now(),
                full_text=full_text,
            )
        )
        if len(circulars) >= limit:
            break
    return circulars
