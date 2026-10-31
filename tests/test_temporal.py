from app.change.feed import diff, render, verdict_map
from app.search.span import find_span
from app.temporal.relations import extract, title_similarity


def test_find_span_maps_offsets_through_normalisation():
    text = "We conduct Due  Diligence on every provider."
    span = find_span(text, "conduct due diligence on every provider")
    assert span is not None
    assert text[span["start"] : span["end"]].lower().startswith("conduct due")


def test_find_span_returns_none_when_absent():
    assert find_span("abc", "xyz") is None
    assert find_span("", "abc") is None
    assert find_span("abc", "") is None


def test_extract_amendment_with_clause_reference():
    found = extract("In Chapter II, Paragraph 14 shall be amended by addition of the following.")
    assert len(found) == 1
    assert found[0].kind == "amends"
    assert found[0].clause_ref == "14"


def test_extract_supersession_captures_the_sentence():
    found = extract("These Directions shall supersede the Reserve Bank of India (KYC) Directions, 2016.")
    assert found and found[0].kind == "supersedes"
    assert "KYC" in found[0].target_text


def test_extract_repeal():
    found = extract("The earlier instructions stand repealed with effect from April 01, 2026.")
    assert any(item.kind == "repeals" for item in found)


def test_title_similarity_ignores_noise_words():
    score = title_similarity(
        "Reserve Bank of India (KYC) Directions, 2016",
        "Master Direction - Reserve Bank of India (KYC) Directions, 2016",
    )
    assert score > 0.6


def test_verdict_map_keeps_the_best_verdict_per_obligation():
    rows = [(1, "missing"), (1, "partial"), (2, "satisfied")]
    assert verdict_map(rows) == {1: "partial", 2: "satisfied"}


def test_diff_classifies_transitions():
    old = {1: "satisfied", 2: "partial", 3: "missing"}
    new = {1: "partial", 2: "partial", 4: "missing"}
    changes = {item["obligation_id"]: item for item in diff(old, new)}
    assert changes[1]["direction"] == "worsened"
    assert changes[3]["direction"] == "dropped"
    assert changes[4]["direction"] == "new"
    assert 2 not in changes


def test_render_says_nothing_changed():
    text = render("acme", "a", "b", [], {})
    assert "No verdicts changed" in text


def test_render_lists_changes():
    changes = [{"obligation_id": 1, "before": "satisfied", "after": "missing", "direction": "worsened"}]
    text = render("acme", "a", "b", changes, {1: "maintain records"})
    assert "worsened" in text
    assert "maintain records" in text
