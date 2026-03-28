"""Adapters that bridge v1 agents into the v2 orchestration contracts."""

from agents.classifier import ClassifierAgent
from agents.extractor import ExtractorAgent
from agents.fusion_agent import FusionAgent
from agents.policy_agent import PolicyAgent
from agents.redaction_agent import RedactionAgent


class LegacyExtractorAdapter(ExtractorAgent):
    pass


class LegacyClassifierAdapter(ClassifierAgent):
    pass


class LegacyFusionAdapter(FusionAgent):
    pass


class LegacyPolicyAdapter(PolicyAgent):
    pass


class LegacyRedactionAdapter(RedactionAgent):
    pass
