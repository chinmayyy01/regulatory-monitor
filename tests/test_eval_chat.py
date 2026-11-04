from datetime import date
from types import SimpleNamespace

from app.eval.chat import failures, retrieval_record, summarize, summarize_retrieval


def test_summary_reports_retrieval_and_answer_stages_separately():
    records = [
        {
            "question": "Missed by retrieval",
            "answerable": True,
            "insufficient": True,
            "gold_hit": False,
            "doc_hit": True,
            "cited_count": 0,
            "cited_gold": 0,
            "retrieval_gold_hit": False,
            "retrieval_doc_hit": True,
            "latency": 1.0,
        },
        {
            "question": "Retrieved but not cited",
            "answerable": True,
            "insufficient": False,
            "gold_hit": False,
            "doc_hit": True,
            "cited_count": 1,
            "cited_gold": 0,
            "retrieval_gold_hit": True,
            "retrieval_doc_hit": True,
            "latency": 2.0,
        },
        {
            "question": "Unanswerable",
            "answerable": False,
            "insufficient": True,
            "rejected": 0,
            "unsupported": 0,
            "latency": 1.5,
        },
    ]

    result = summarize(records)

    assert result["retrieval_diagnostic_rows"] == 2
    assert result["retrieval_gold_clause_recall"] == 0.5
    assert result["retrieval_same_document_rate"] == 1.0


def test_failures_distinguish_retrieval_misses_from_generation_misses():
    records = [
        {"question": "Missed", "answerable": True, "retrieval_gold_hit": False},
        {"question": "Not cited", "answerable": True, "retrieval_gold_hit": True, "gold_hit": False},
    ]

    assert [item["reason"] for item in failures(records)] == [
        "gold clause not retrieved",
        "gold retrieved but not cited",
    ]


def test_retrieval_record_stores_regulatory_sources_only():
    row = {
        "answerable": True,
        "gold_clause_id": 10,
        "gold_doc_id": 1,
    }
    sources = [
        SimpleNamespace(kind="regulation", clause_id=10, document_id=1),
        SimpleNamespace(kind="policy", clause_id=20, document_id=2),
    ]

    result = retrieval_record(row, sources, as_of=date(2026, 11, 3))

    assert result["retrieved_clause_ids"] == [10]
    assert result["retrieved_document_ids"] == [1]
    assert result["retrieval_gold_hit"]
    assert result["retrieval_doc_hit"]


def test_retrieval_summary_uses_only_rows_with_trace_data():
    rows = [
        {"question": "traced", "answerable": True},
        {"question": "untraced", "answerable": True},
    ]
    records = {"traced": {"retrieval_gold_hit": True, "retrieval_doc_hit": False}}

    result = summarize_retrieval(rows, records)

    assert result["retrieval_rows"] == 1
    assert result["answerable_questions"] == 2
    assert result["gold_clause_recall"] == 1.0
    assert result["same_document_rate"] == 0.0
