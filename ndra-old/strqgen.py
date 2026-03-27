# strQgen.py

from querygenai import extract_query_info_llm, rewrite_query

def classify_intent(query: str) -> str:
    intent_keywords = {
        "eligibility_check": ["eligible", "eligibility", "can i", "still covered"],
        "claim_status": ["claim status", "track claim", "claim update"],
        "coverage_check": ["covered", "coverage", "what is included"],
        "renewal": ["renew", "extension", "renewal"],
        "premium_info": ["premium", "cost", "price", "installment"],
        "document_requirement": ["documents", "papers", "required for"],
    }

    query_lower = query.lower()
    for intent, keywords in intent_keywords.items():
        if any(kw in query_lower for kw in keywords):
            return intent
    return "general_inquiry"

def extract_structured_entities(query: str) -> dict:
    import re

    entities = {}

    if "accident" in query.lower():
        entities["incident"] = "accident"
    elif "surgery" in query.lower():
        entities["incident"] = "surgery"

    time_match = re.search(r"(last month|[0-9]+\s+(days?|months?|years?)\s+ago)", query.lower())
    if time_match:
        entities["incident_time"] = time_match.group(1)

    if "new policy" in query.lower():
        entities["policy_status"] = "new"
    elif "old policy" in query.lower() or "existing policy" in query.lower():
        entities["policy_status"] = "existing"

    return entities

def build_structured_query(info: dict, rewritten_query: str, raw_query: str) -> dict:
    return {
        "original_query": raw_query,
        "rewritten_query": rewritten_query,
        "intent": classify_intent(raw_query),
        "subject": info.get("subject"),
        "age": info.get("age"),
        "gender": info.get("gender"),
        "procedure": info.get("procedure"),
        "location": info.get("location"),
        "policy_duration": info.get("policy_duration"),
        "extracted_entities": extract_structured_entities(raw_query),
    }

def compute_completeness_score(structured_query: dict) -> float:
    fields = ["subject", "age", "gender", "procedure", "location", "policy_duration"]
    filled = sum(1 for field in fields if structured_query.get(field))
    return round(filled / len(fields), 2)
