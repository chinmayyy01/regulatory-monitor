from io import BytesIO

import pytest
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from app.ingest.pdf import extract_lines, page_count
from app.ingest.segment import segment


def build_pdf() -> bytes:
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(72, height - 90, "1. Introduction")
    pdf.setFont("Helvetica", 10)
    pdf.drawString(72, height - 110, "This direction applies to every regulated entity.")

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(72, height - 150, "1.1 Applicability")
    pdf.setFont("Helvetica", 10)
    pdf.drawString(72, height - 170, "It applies to non banking financial companies.")

    pdf.showPage()
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(72, height - 90, "2. Reporting")
    pdf.setFont("Helvetica", 10)
    pdf.drawString(72, height - 110, "Reports must be filed within seven days.")
    pdf.save()
    return buffer.getvalue()


@pytest.fixture(scope="module")
def pdf_bytes() -> bytes:
    return build_pdf()


def test_page_count(pdf_bytes):
    assert page_count(pdf_bytes) == 2


def test_extract_lines_has_geometry(pdf_bytes):
    lines = extract_lines(pdf_bytes)
    assert lines
    assert lines[0].page == 1
    assert lines[0].x0 > 0 and lines[0].x1 > lines[0].x0
    assert lines[0].top < lines[0].bottom
    assert any(line.page == 2 for line in lines)
    assert any(line.bold for line in lines)


def test_segment_builds_sections_and_spans(pdf_bytes):
    clauses = segment(extract_lines(pdf_bytes))
    sections = [clause.section_no for clause in clauses]
    assert "1" in sections
    assert "1.1" in sections
    assert "2" in sections

    nested = next(clause for clause in clauses if clause.section_no == "1.1")
    assert nested.heading_path == ["1. Introduction"]
    assert nested.spans[0]["page"] == 1
    assert len(nested.spans[0]["bbox"]) == 4

    reporting = next(clause for clause in clauses if clause.section_no == "2")
    assert reporting.page == 2
    assert "seven days" in reporting.text


def test_empty_pdf_has_no_clauses():
    assert segment([]) == []
