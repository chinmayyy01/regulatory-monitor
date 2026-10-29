from datetime import datetime

import pytest

from app.fetchers.base import Circular, fetch_bytes, is_allowed_url


def test_allows_regulator_hosts():
    assert is_allowed_url("https://www.rbi.org.in/scripts/NotificationUser.aspx")
    assert is_allowed_url("https://rbidocs.rbi.org.in/rdocs/notification/PDFs/x.pdf")
    assert is_allowed_url("https://www.sebi.gov.in/sebi_data/attachdocs/x.pdf")


def test_blocks_other_hosts():
    assert not is_allowed_url("https://example.com/circular")
    assert not is_allowed_url("https://rbi.org.in.evil.com/circular")
    assert not is_allowed_url("http://127.0.0.1:8000/admin")
    assert not is_allowed_url("https://192.168.1.1/")


def test_blocks_non_http_schemes():
    assert not is_allowed_url("file:///etc/passwd")
    assert not is_allowed_url("javascript:alert(1)")
    assert not is_allowed_url("")


def test_fetch_bytes_refuses_unknown_hosts():
    with pytest.raises(ValueError):
        fetch_bytes("https://example.com/")


def test_circular_raw_html_is_optional():
    circular = Circular(
        id="https://www.rbi.org.in/x",
        title="Some circular",
        source="RBI",
        url="https://www.rbi.org.in/x",
        published_date=datetime(2026, 1, 1),
        full_text="body",
    )
    assert circular.raw_html is None
