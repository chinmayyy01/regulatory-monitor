from datetime import date

from app.extract.obligations import (
    extract_facets,
    is_candidate,
    parse_valid_from,
    validate,
)

TEXT = "4. Every NBFC shall report the position to the Reserve Bank by the tenth day of the month."


def test_candidate_filter_finds_cue_words():
    assert is_candidate(TEXT)
    assert is_candidate("Entities must not share data.")
    assert not is_candidate("This chapter explains the background.")


def test_facets_match_entity_words():
    facets = extract_facets("All Scheduled Commercial Banks and NBFCs shall report.")
    assert "bank" in facets
    assert "nbfc" in facets


def test_valid_from_reads_effective_dates():
    assert parse_valid_from("These directions shall come into force on January 01, 2027.") == date(2027, 1, 1)
    assert parse_valid_from("with effect from 1st April 2025") == date(2025, 4, 1)
    assert parse_valid_from("no date mentioned here") is None


def test_validate_keeps_a_real_obligation():
    payload = {
        "obligations": [
            {
                "is_obligation": True,
                "modality": "shall",
                "actor": "NBFC",
                "action": "report the position to the Reserve Bank by the tenth day",
                "condition": "monthly",
            }
        ]
    }
    records = validate(payload, TEXT, date(2026, 1, 1))
    assert len(records) == 1
    assert records[0].modality == "shall"
    assert records[0].scope_entities == ["nbfc"]
    assert records[0].valid_from == date(2026, 1, 1)


def test_validate_rejects_commencement_and_regulator_actions():
    payload = {
        "obligations": [
            {"is_obligation": True, "modality": "shall", "actor": "entity", "action": "come into force on April 01, 2025", "condition": ""},
            {"is_obligation": True, "modality": "shall", "actor": "Reserve Bank", "action": "issue the amended directions", "condition": ""},
            {"is_obligation": True, "modality": "shall", "actor": "entity", "action": "apply", "condition": ""},
        ]
    }
    assert validate(payload, "x") == []


def test_validate_drops_duplicates_and_false_flags():
    payload = {
        "obligations": [
            {"is_obligation": False, "modality": "shall", "actor": "a", "action": "ignored because flag is false", "condition": ""},
            {"is_obligation": True, "modality": "shall", "actor": "bank", "action": "file the quarterly return", "condition": ""},
            {"is_obligation": True, "modality": "shall", "actor": "bank", "action": "File the quarterly return", "condition": ""},
        ]
    }
    records = validate(payload, TEXT)
    assert len(records) == 1
    assert records[0].ordinal == 0


def test_validate_rejects_bad_modality():
    payload = {"obligations": [{"is_obligation": True, "modality": "should", "actor": "bank", "action": "do something useful", "condition": ""}]}
    assert validate(payload, TEXT) == []
