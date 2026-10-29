from datetime import datetime
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .base import Circular, fetch_bytes, is_allowed_url

SEBI_LISTING_URL = (
    "https://www.sebi.gov.in/"
    "sebiweb/home/HomeAction.do?doListing=yes&sid=1&ssid=7&smid=0"
)
MIN_TITLE_LENGTH = 10
MAX_TEXT_CHARS = 8000
DOC_TIMEOUT_SECONDS = 10


def extract_text(html: bytes) -> str:
    soup = BeautifulSoup(html, "lxml")
    container = (
        soup.find("div", class_="main-content")
        or soup.find("div", class_="inner_cont")
        or soup.find("body")
    )
    if container is None:
        return ""
    text = container.get_text(separator="\n", strip=True)
    return text[:MAX_TEXT_CHARS]


def fetch_sebi_circulars(limit: int = 10) -> list[Circular]:
    if limit <= 0:
        return []

    listing = BeautifulSoup(fetch_bytes(SEBI_LISTING_URL), "lxml")
    circulars = []
    for link in listing.find_all("a"):
        href = link.get("href")
        if not href:
            continue
        href_lower = href.lower()
        if (
            "circular" not in href_lower
            and "master" not in href_lower
            and ".pdf" not in href_lower
        ):
            continue
        title = link.get_text(strip=True)
        if len(title) < MIN_TITLE_LENGTH:
            continue

        url = urljoin(SEBI_LISTING_URL, href)
        if not is_allowed_url(url):
            print(f"[SEBI] Skipped url outside allowlist: {url}")
            continue

        try:
            full_text = extract_text(fetch_bytes(url, timeout=DOC_TIMEOUT_SECONDS))
        except Exception as error:
            print(f"[SEBI DOC ERROR] {url}: {error}")
            full_text = ""
        if not full_text:
            full_text = title

        circulars.append(
            Circular(
                id=url,
                title=title,
                source="SEBI",
                url=url,
                published_date=datetime.now(),
                full_text=full_text,
            )
        )
        if len(circulars) >= limit:
            break
    return circulars
