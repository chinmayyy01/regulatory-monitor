from app.ingest.html_doc import (
    paragraphs_to_clauses,
    rbi_paragraphs,
    rbi_pdf_url,
    sebi_pdf_url,
)

RBI_HTML = b"""
<html><body>
<div id="pnlDetails">
  <a href="https://rbidocs.rbi.org.in/rdocs/Notification/PDFs/A.PDF">PDF</a>
  <p>( 226 kb )</p>
  <p>Short</p>
  <p>1. These directions shall come into force on January 01, 2027 and apply to every entity.</p>
  <p>2. The entity shall maintain records of all transactions for a period of five years.</p>
</div>
</body></html>
"""

SEBI_HTML = b"""
<html><body>
<iframe src='../../../web/?file=https://www.sebi.gov.in/sebi_data/attachdocs/oct-2026/1793167964839.pdf' width='100%'></iframe>
</body></html>
"""


def test_rbi_paragraphs_skips_noise_and_short_blocks():
    paragraphs = rbi_paragraphs(RBI_HTML)
    assert len(paragraphs) == 2
    assert paragraphs[0].startswith("1. These directions")


def test_paragraphs_become_numbered_clauses():
    clauses = paragraphs_to_clauses(rbi_paragraphs(RBI_HTML))
    assert [clause.section_no for clause in clauses] == ["1", "2"]
    assert all(clause.bbox is None for clause in clauses)
    assert all(clause.page == 1 for clause in clauses)
    assert clauses[1].ordinal == 1


def test_rbi_pdf_url_is_kept_as_provenance():
    assert rbi_pdf_url(RBI_HTML) == "https://rbidocs.rbi.org.in/rdocs/Notification/PDFs/A.PDF"


def test_sebi_pdf_url_comes_from_the_iframe():
    assert (
        sebi_pdf_url(SEBI_HTML)
        == "https://www.sebi.gov.in/sebi_data/attachdocs/oct-2026/1793167964839.pdf"
    )


def test_missing_containers_return_nothing():
    assert rbi_paragraphs(b"<html></html>") == []
    assert sebi_pdf_url(b"<html></html>") is None
    assert rbi_pdf_url(b"<html></html>") is None
