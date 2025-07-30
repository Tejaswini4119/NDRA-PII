import os
import re
import json
from typing import Dict
from dotenv import load_dotenv
from fastllm import fast_chat  # ✅ Make sure fastllm.py is created as discussed

# === Load environment ===
load_dotenv()

# === Prompt Template for Query Info Extraction ===
def build_extraction_prompt(query: str) -> str:
    return f"""
You are an intelligent insurance query parser.

Given this user query:
"{query}"

Extract a valid JSON object with these fields:
- age
- gender
- procedure
- location
- policy_duration
- subject
If a field is missing, set it as null.
Return only a JSON, no explanation.
"""

# === Parse JSON safely ===
def safe_json_parse(text: str) -> Dict:
    try:
        return json.loads(text)
    except Exception:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except Exception:
                return {"error": "Invalid JSON in output"}
        return {"error": "Failed to extract JSON"}

# === Use Fast LLM (Phi 3.5) to extract info ===
def extract_query_info_llm(query: str) -> Dict:
    prompt = build_extraction_prompt(query)
    response = fast_chat(prompt)
    return safe_json_parse(response)

# === Domain Detection ===
def detect_domain(info: Dict, query: str) -> str:
    subject_text = (info.get("subject") or "").lower()
    full_text = f"{query} {subject_text} {str(info)}".lower()

    domain_keywords = {
        "health": [
            "health", "hospital", "surgery", "treatment", "medical", "doctor", "illness",
            "pre-existing", "bypass", "angioplasty", "diabetes", "critical illness", "procedure"
        ],
        "motor": [
            "motor", "car", "bike", "vehicle", "accident", "third-party", "own damage",
            "garage", "repair", "engine", "theft", "four-wheeler", "two-wheeler"
        ],
        "travel": [
            "travel", "trip", "visa", "flight", "journey", "international", "abroad", "foreign",
            "luggage", "delay", "passport", "missed flight"
        ],
        "life": [
            "life insurance", "death", "term plan", "nominee", "sum assured", "life cover",
            "maturity", "premium waiver", "term policy"
        ],
        "property": [
            "property", "fire", "theft", "flood", "earthquake", "natural disaster", "building",
            "home", "house", "damage", "structure"
        ]
    }

    for domain, keywords in domain_keywords.items():
        if any(re.search(rf'\b{re.escape(kw)}\b', subject_text) for kw in keywords):
            return domain

    for domain, keywords in domain_keywords.items():
        if any(re.search(rf'\b{re.escape(kw)}\b', full_text) for kw in keywords):
            return domain

    return "general"

# === Domain-specific coverage hints ===
def get_coverage_hints(domain: str) -> str:
    hints = {
        'health': "Check hospitalization expenses, surgery costs, pre-existing condition clauses, and coverage exclusions.",
        'motor': "Check coverage for accidents, third-party liability, own damage, and add-ons like zero depreciation.",
        'travel': "Check coverage for trip cancellations, medical emergencies abroad, baggage loss, and visa support.",
        'life': "Check policy sum assured, nominee details, term duration, and death benefit clauses.",
        'property': "Check coverage for fire, theft, natural disasters, and exclusions related to unoccupied properties.",
        'general': "Check overall coverage, exclusions, premium amounts, and terms & conditions."
    }
    return hints.get(domain, hints["general"])

# === Rewrite query based on info ===
def rewrite_query(info: Dict, query: str) -> str:
    if "error" in info:
        return "Unable to process query."

    domain = detect_domain(info, query)
    coverage_points = get_coverage_hints(domain)

    subject = (info.get("subject") or "").lower()
    qlower = query.lower()

    vague_trigger = any(phrase in qlower for phrase in [
        "can he", "can she", "can i", "is it possible", "am i allowed",
        "what if", "eligible", "eligibility", "allowed", "qualify"
    ]) or "eligibility" in subject

    person = None
    if "dad" in qlower: person = "your father"
    elif "mom" in qlower: person = "your mother"
    elif "he" in qlower: person = "he"
    elif "she" in qlower: person = "she"
    elif "i" in qlower or "me" in qlower: person = "you"
    else: person = "the individual"

    phrases = []
    if info.get("age"): phrases.append(f"{info['age']} years old")
    if info.get("gender"): phrases.append(info["gender"])
    if info.get("location"): phrases.append(f"from {info['location']}")
    if info.get("procedure"): phrases.append(f"had {info['procedure']}")
    if info.get("policy_duration"): phrases.append(f"with a {info['policy_duration']} old policy")
    if info.get("subject") and not vague_trigger: phrases.append(info["subject"])

    joined_info = ", ".join(phrases) if phrases else query.strip().rstrip("?. ")

    eligibility_notes = {
        'health': "Eligibility may depend on age, pre-existing conditions, waiting periods, and current health status.",
        'motor': "Eligibility may depend on vehicle condition, registration location, and past claims history.",
        'life': "Eligibility may depend on age, medical history, smoker status, and financial background.",
        'travel': "Eligibility may depend on travel destination, age, trip purpose, and existing medical issues.",
        'property': "Eligibility may depend on property type, location risk (e.g., flood-prone), and previous claims.",
        'general': "Eligibility may vary depending on policy type, prior history, and specific terms and conditions."
    }

    if vague_trigger:
        if domain in ["motor", "property"]:
            if person == "you": person_phrase = "Can the vehicle be insured"
            elif person == "the individual": person_phrase = "Can the item be insured"
            else: person_phrase = f"Can {person}'s vehicle be insured"
        else:
            person_phrase = f"Can {person} be insured"

        return (
            f"{person_phrase}? Based on the context: {joined_info}. "
            f"{eligibility_notes.get(domain)} {coverage_points}"
        )

    return f"Insurance policy coverage for {joined_info}. {coverage_points}"