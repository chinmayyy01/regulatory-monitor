from dataclasses import dataclass

from app.chat.answer import parse
from app.chat.retrieve import reciprocal_rank_fusion, tsquery_from


@dataclass
class FakeSource:
    kind: str
    clause_id: int
    label: str
    text: str


SOURCES = [
    FakeSource("regulation", 10, "regulation · KYC Directions · s.4", "The entity shall carry out customer due diligence before opening an account."),
    FakeSource("policy", 20, "policy · KYC Policy · s.1", "We verify the identity of every customer before opening an account."),
]


def test_tsquery_drops_stopwords_and_keeps_terms():
    query = tsquery_from("What should we do about customer due diligence?")
    assert "customer" in query
    assert "diligence" in query
    assert "what" not in query
    assert " | " in query


def test_rrf_prefers_documents_found_by_both_lists():
    dense = [(1, "a"), (2, "b"), (3, "c")]
    lexical = [(2, "b"), (4, "d")]
    merged = reciprocal_rank_fusion([dense, lexical], limit=4)
    assert merged[0][0] == 2


def test_rrf_respects_limit():
    merged = reciprocal_rank_fusion([[(index, "x") for index in range(10)]], limit=3)
    assert len(merged) == 3


def test_claim_with_verbatim_quote_is_kept():
    payload = {
        "insufficient": False,
        "claims": [
            {
                "text": "We verify identity before opening an account.",
                "citations": [{"source": 1, "quote": "We verify the identity of every customer before opening an account."}],
            }
        ],
    }
    answer = parse(payload, SOURCES)
    assert not answer.insufficient
    assert len(answer.claims) == 1
    assert answer.claims[0].citations[0].kind == "policy"
    assert answer.claims[0].citations[0].span["start"] >= 0


def test_claim_with_fabricated_quote_is_dropped():
    payload = {
        "insufficient": False,
        "claims": [
            {
                "text": "Customers must be verified within 24 hours.",
                "citations": [{"source": 1, "quote": "customers must be verified within 24 hours"}],
            }
        ],
    }
    answer = parse(payload, SOURCES)
    assert answer.insufficient
    assert answer.rejected == 1


def test_claim_without_citations_is_rejected():
    payload = {"insufficient": False, "claims": [{"text": "Something true.", "citations": []}]}
    answer = parse(payload, SOURCES)
    assert answer.insufficient
    assert answer.rejected == 1


def test_partial_citation_failure_drops_the_claim():
    payload = {
        "insufficient": False,
        "claims": [
            {
                "text": "The entity must do due diligence.",
                "citations": [
                    {"source": 0, "quote": "carry out customer due diligence"},
                    {"source": 1, "quote": "a quote that does not exist"},
                ],
            }
        ],
    }
    answer = parse(payload, SOURCES)
    assert not answer.insufficient
    assert len(answer.claims[0].citations) == 1


def test_explicit_insufficient_is_honoured():
    assert parse({"insufficient": True, "claims": []}, SOURCES).insufficient
    assert parse({"insufficient": True, "claims": [{"text": "x", "citations": []}]}, SOURCES).insufficient


def test_garbage_payload_abstains():
    assert parse(None, SOURCES).insufficient
    assert parse({"claims": "nope"}, SOURCES).insufficient
