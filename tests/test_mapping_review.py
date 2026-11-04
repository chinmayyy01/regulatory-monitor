from app.eval.mapping_review import select_mapping_ids


def test_mapping_review_selection_is_deterministic_and_includes_each_verdict():
    rows = []
    mapping_id = 1
    for verdict, count in (("satisfied", 4), ("partial", 16), ("missing", 25)):
        for _ in range(count):
            rows.append({"mapping_id": mapping_id, "judge": verdict})
            mapping_id += 1

    first = select_mapping_ids(rows, count=20, seed=7)
    second = select_mapping_ids(rows, count=20, seed=7)

    assert first == second
    assert len(first) == len(set(first)) == 20
    selected_verdicts = {row["mapping_id"]: row["judge"] for row in rows}
    assert {selected_verdicts[mapping_id] for mapping_id in first} == {
        "satisfied",
        "partial",
        "missing",
    }
