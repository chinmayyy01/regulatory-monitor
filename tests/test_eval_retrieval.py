from app.eval.retrieval import summarize


def test_retrieval_summary_separates_exact_clause_from_document_hits():
    rows = [
        {"question": "exact", "answerable": True, "gold_clause_id": 10, "gold_doc_id": 1},
        {"question": "document", "answerable": True, "gold_clause_id": 20, "gold_doc_id": 2},
        {"question": "unanswerable", "answerable": False, "gold_clause_id": None, "gold_doc_id": None},
    ]
    candidates = {
        "exact": [(10, 1), (11, 1)],
        "document": [(21, 2)],
    }

    result = summarize(rows, candidates)

    assert result["answerable"] == 2
    assert result["exact_clause_recall"] == 0.5
    assert result["same_document_rate"] == 1.0
    assert result["no_candidates"] == 0


def test_retrieval_summary_counts_questions_without_candidates():
    rows = [
        {"question": "none", "answerable": True, "gold_clause_id": 10, "gold_doc_id": 1}
    ]

    result = summarize(rows, {})

    assert result["exact_clause_recall"] == 0.0
    assert result["same_document_rate"] == 0.0
    assert result["no_candidates"] == 1
