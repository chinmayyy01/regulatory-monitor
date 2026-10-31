ENTITY_FACETS = {
    "bank": "bank",
    "commercial_bank": "bank",
    "nbfc": "nbfc",
    "payments_bank": "payments_bank",
    "small_finance_bank": "small_finance_bank",
    "cooperative_bank": "cooperative_bank",
    "aifi": "aifi",
    "housing_finance": "housing_finance",
    "payment_system_operator": "payment_system_operator",
    "mutual_fund": "mutual_fund",
    "stock_broker": "stock_broker",
    "depository": "depository",
    "investment_adviser": "investment_adviser",
    "research_analyst": "research_analyst",
    "debenture_trustee": "debenture_trustee",
    "aif": "aif",
}

IMPLEMENTATION_DOCS = {"hfc": "housing_finance", "ucb": "cooperative_bank"}


def tenant_facets(entity_type: str, products: list[str] | None = None) -> set[str]:
    facets = set()
    code = entity_type.strip().lower()
    if code in ENTITY_FACETS:
        facets.add(ENTITY_FACETS[code])
    for product in products or []:
        key = product.strip().lower()
        if key in ENTITY_FACETS:
            facets.add(ENTITY_FACETS[key])
        if key in IMPLEMENTATION_DOCS:
            facets.add(IMPLEMENTATION_DOCS[key])
    return facets


def applies(obligation_scope: list[str], facets: set[str]) -> bool:
    if not obligation_scope:
        return True
    return bool(set(obligation_scope) & facets)
