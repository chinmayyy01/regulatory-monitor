from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from urllib.parse import urljoin, urlparse

import requests

ALLOWED_HOSTS = ("rbi.org.in", "sebi.gov.in")
MAX_RESPONSE_BYTES = 20 * 1024 * 1024
MAX_REDIRECTS = 3
REQUEST_TIMEOUT_SECONDS = 15
CHUNK_SIZE = 65536
USER_AGENT = "RegIntelAI/0.1 (+https://github.com/chinmayyy01/regulatory-monitor)"


@dataclass
class Circular:
    id: str
    title: str
    source: str
    url: str
    published_date: datetime
    full_text: str
    raw_html: Optional[str] = None


def is_allowed_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return False
    host = (parsed.hostname or "").lower()
    return any(
        host == allowed or host.endswith("." + allowed)
        for allowed in ALLOWED_HOSTS
    )


def _read_capped(response: requests.Response, url: str) -> bytes:
    chunks = []
    total = 0
    for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
        total += len(chunk)
        if total > MAX_RESPONSE_BYTES:
            raise ValueError(f"response over {MAX_RESPONSE_BYTES} bytes: {url}")
        chunks.append(chunk)
    return b"".join(chunks)


def request_bytes(
    method: str,
    url: str,
    data: Optional[dict] = None,
    session: Optional[requests.Session] = None,
    headers: Optional[dict] = None,
    timeout: int = REQUEST_TIMEOUT_SECONDS,
) -> bytes:
    sender = session or requests
    request_headers = {"User-Agent": USER_AGENT}
    if headers:
        request_headers.update(headers)
    current = url
    for _ in range(MAX_REDIRECTS + 1):
        if not is_allowed_url(current):
            raise ValueError(f"blocked url: {current}")
        with sender.request(
            method,
            current,
            data=data,
            headers=request_headers,
            timeout=timeout,
            stream=True,
            allow_redirects=False,
        ) as response:
            if response.is_redirect:
                location = response.headers.get("Location", "")
                if not location:
                    raise ValueError(f"redirect without location: {current}")
                current = urljoin(current, location)
                continue
            response.raise_for_status()
            return _read_capped(response, current)
    raise ValueError(f"too many redirects: {url}")


def fetch_bytes(
    url: str,
    session: Optional[requests.Session] = None,
    headers: Optional[dict] = None,
    timeout: int = REQUEST_TIMEOUT_SECONDS,
) -> bytes:
    return request_bytes("GET", url, session=session, headers=headers, timeout=timeout)


def post_form(
    url: str,
    data: dict,
    session: Optional[requests.Session] = None,
    timeout: int = REQUEST_TIMEOUT_SECONDS,
) -> bytes:
    return request_bytes("POST", url, data=data, session=session, timeout=timeout)
