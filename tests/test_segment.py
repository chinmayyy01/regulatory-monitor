from app.ingest.pdf import Line
from app.ingest.segment import body_size, segment


def line(text, page=1, top=0.0, size=10.0, bold=False):
    return Line(
        page=page,
        text=text,
        x0=40.0,
        top=top,
        x1=500.0,
        bottom=top + size,
        size=size,
        bold=bold,
    )


def test_body_size_uses_character_weight():
    lines = [line("body " * 50, size=10.0), line("Heading", size=16.0)]
    assert body_size(lines) == 10.0


def test_numbered_heading_starts_a_clause():
    lines = [
        line("1. Introduction", top=40.0, size=14.0, bold=True),
        line("This direction applies to every entity.", top=60.0),
    ]
    clauses = segment(lines)
    assert len(clauses) == 1
    assert clauses[0].section_no == "1"
    assert clauses[0].heading_path == []
    assert clauses[0].text.startswith("1. Introduction")
    assert "every entity" in clauses[0].text
    assert clauses[0].page == 1
    assert clauses[0].spans[0]["page"] == 1


def test_sibling_headings_do_not_nest():
    lines = [
        line("1. Scope", top=40.0, size=14.0, bold=True),
        line("Applies to banks.", top=60.0),
        line("2. Definitions", top=120.0, size=14.0, bold=True),
        line("In this direction, bank means.", top=140.0),
    ]
    clauses = segment(lines)
    assert [clause.section_no for clause in clauses] == ["1", "2"]
    assert clauses[1].heading_path == []


def test_sub_headings_nest_under_parent():
    lines = [
        line("1. Scope", top=40.0, size=14.0, bold=True),
        line("General scope text.", top=60.0),
        line("1.1 Applicability", top=100.0, size=12.0, bold=True),
        line("Applies to NBFCs.", top=120.0),
    ]
    clauses = segment(lines)
    nested = [clause for clause in clauses if clause.section_no == "1.1"]
    assert len(nested) == 1
    assert nested[0].heading_path == ["1. Scope"]


def test_numbered_body_sentence_is_not_a_heading():
    lines = [
        line("1. Scope", top=40.0, size=14.0, bold=True),
        line("1. The entity shall maintain records for five years.", top=60.0),
    ]
    clauses = segment(lines)
    assert len(clauses) == 1
    assert clauses[0].section_no == "1"
    assert "maintain records" in clauses[0].text


def test_document_without_headings_is_one_clause():
    lines = [line("Plain paragraph one.", top=40.0), line("Plain paragraph two.", top=60.0)]
    clauses = segment(lines)
    assert len(clauses) == 1
    assert clauses[0].section_no is None
    assert clauses[0].heading_path == []


def test_empty_input():
    assert segment([]) == []
