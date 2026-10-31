from app.mapping.applicability import applies, tenant_facets
from app.mapping.judge import validate

OBLIGATION = "carry out customer due diligence before opening an account"
POLICY = "We verify identity before opening any account."


def test_tenant_facets_from_entity_type():
    assert tenant_facets("nbfc") == {"nbfc"}
    assert tenant_facets("commercial_bank") == {"bank"}
    assert tenant_facets("unknown_type") == set()


def test_tenant_facets_from_products():
    assert "housing_finance" in tenant_facets("nbfc", ["hfc"])


def test_applicability():
    facets = {"nbfc"}
    assert applies(["nbfc", "bank"], facets)
    assert not applies(["mutual_fund"], facets)


def test_unscoped_obligation_applies_everywhere():
    assert applies([], {"nbfc"})


def test_judge_accepts_verbatim_quotes():
    payload = {
        "clause_index": 0,
        "verdict": "satisfied",
        "confidence": 0.9,
        "evidence_regulation": "carry out customer due diligence",
        "evidence_policy": "verify identity before opening any account",
        "reason": "policy requires identity verification before account opening",
    }
    result = validate(payload, OBLIGATION, [POLICY])
    assert result is not None
    assert result.verdict == "satisfied"
    assert result.clause_index == 0


def test_judge_rejects_paraphrased_policy_quote():
    payload = {
        "clause_index": 0,
        "verdict": "satisfied",
        "confidence": 0.9,
        "evidence_regulation": "carry out customer due diligence",
        "evidence_policy": "we always check who our customers are",
        "reason": "paraphrase should not pass",
    }
    assert validate(payload, OBLIGATION, [POLICY]) is None


def test_judge_rejects_quote_not_in_obligation():
    payload = {
        "clause_index": 0,
        "verdict": "satisfied",
        "confidence": 0.9,
        "evidence_regulation": "maintain records for five years",
        "evidence_policy": "verify identity before opening any account",
        "reason": "wrong regulation quote",
    }
    assert validate(payload, OBLIGATION, [POLICY]) is None


def test_judge_rejects_out_of_range_index():
    payload = {"clause_index": 7, "verdict": "partial", "confidence": 0.5,
               "evidence_regulation": "carry out customer due diligence",
               "evidence_policy": "verify identity", "reason": "x"}
    assert validate(payload, OBLIGATION, [POLICY]) is None


def test_missing_needs_no_quotes():
    payload = {"clause_index": -1, "verdict": "missing", "confidence": 0.8,
               "evidence_regulation": "", "evidence_policy": "", "reason": "no clause covers this"}
    result = validate(payload, OBLIGATION, [POLICY])
    assert result is not None
    assert result.verdict == "missing"


def test_unknown_verdict_rejected():
    payload = {"clause_index": 0, "verdict": "compliant", "confidence": 0.9,
               "evidence_regulation": "x", "evidence_policy": "y", "reason": "z"}
    assert validate(payload, OBLIGATION, [POLICY]) is None
