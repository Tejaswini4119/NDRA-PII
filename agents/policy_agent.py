import os
import yaml
import logging
from typing import Any, Dict, List, Optional
from schemas.core_models import ClassifiedChunk, GovernedChunk, AgentDecision, DetectedPII
from schemas.rule_schema import NSRLRule

# ---------------------------------------------------------------------------
# Document-context entity type classification sets
#
# These sets map Presidio / custom entity type names to the boolean context
# fields used by CONTEXT_MATCH escalation rules in the NSRL rule files:
#
#   _GOV_ID_ENTITY_TYPES  → ``has_gov_id``
#   _HEALTHCARE_ENTITY_TYPES → ``has_healthcare_data``
#   _FINANCIAL_ENTITY_TYPES  → ``has_financial_data``
#
# When a document contains any entity whose type appears in one of these
# sets, the corresponding boolean is set to True in the document context
# dict passed to :meth:`PolicyAgent._check_context_conditions`.  This
# enables rules like ESC-TOXIC-ID-FIN-001 (identity + finance) and
# ESC-TOXIC-ID-HEALTH-001 (identity + healthcare) to fire correctly.
# ---------------------------------------------------------------------------
_GOV_ID_ENTITY_TYPES: frozenset = frozenset({
    "US_SSN", "UK_NINO", "IN_AADHAAR", "IN_PAN",
    "DE_PASSPORT", "FR_PASSPORT", "ES_PASSPORT", "IT_PASSPORT",
})
_HEALTHCARE_ENTITY_TYPES: frozenset = frozenset({
    "ICD10_CODE", "MEDICAL_LICENSE", "US_HEALTHCARE_NPI",
    "NHS_NUMBER", "HEALTHCARE_NUMBER",
})
_FINANCIAL_ENTITY_TYPES: frozenset = frozenset({
    "CREDIT_CARD", "IBAN_CODE", "SWIFT_CODE",
    "CRYPTO_BTC_WALLET", "US_BANK_NUMBER",
})

# Configure Logging
logger = logging.getLogger(__name__)

class PolicyAgent:
    """
    Agents responsible for loading NSRL rules and enforcing policies on ClassifiedChunks.
    Phase 5: Governance.
    """
    
    def __init__(self, rules_dir: str = "nsrl/rules"):
        self.rules_dir = rules_dir
        self.rules: List[NSRLRule] = []
        self._load_rules()

    def _load_rules(self):
        """Loads all YAML rule files from the rules directory."""
        if not os.path.exists(self.rules_dir):
            logger.warning(f"Rules directory not found: {self.rules_dir}")
            return

        loaded_count = 0
        for root, _, files in os.walk(self.rules_dir):
            for file in files:
                if file.endswith(".yml") or file.endswith(".yaml"):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, "r") as f:
                            content = yaml.safe_load(f)
                            if isinstance(content, list):
                                for item in content:
                                    rule = NSRLRule(**item)
                                    self.rules.append(rule)
                                    loaded_count += 1
                    except Exception as e:
                        logger.error(f"Failed to load rule file {file_path}: {e}")
        
        # Sort rules by priority (descending)
        self.rules.sort(key=lambda x: x.meta.priority, reverse=True)
        logger.info(f"[PolicyAgent] Loaded {loaded_count} rules from {self.rules_dir}")

    def evaluate_chunk(self, chunk: ClassifiedChunk, trace_id: str = "unknown") -> GovernedChunk:
        """
        Evaluates a classified chunk against loaded rules.
        Determines the highest risk score and appropriate action.
        """
        max_risk_score = 0.0
        final_action = "Allow"
        justifications = []
        
        # Default decision if no rules fire
        if not chunk.detected_entities:
             decision = AgentDecision(
                trace_id=trace_id,
                chunk_id=chunk.chunk_id,
                agent_name="PolicyAgent",
                action="Allow",
                risk_score=0.0,
                justification_trace=["No PII detected."]
            )
             return GovernedChunk(
                 **chunk.dict(),
                 redacted_text=chunk.processed_text, # No redaction needed
                 decision=decision
             )

        # Iterate over entities and check rules
        # We need to find the most severe rule that applies to *any* entity in the chunk.
        
        for entity in chunk.detected_entities:
            for rule in self.rules:
                if self._check_conditions(entity, rule):
                    # Rule Fired
                    justifications.append(f"Rule {rule.id} fired on '{entity.entity_type}': {rule.actions.justification}")
                    
                    if rule.actions.score > max_risk_score:
                        max_risk_score = rule.actions.score
                        
                    # Determine Action based on Severity/Score
                    # Map NSRL Actions to System Actions
                    # Currently NSRL has 'classification' and 'severity'.
                    
                    if rule.actions.severity in ["CRITICAL", "HIGH"]:
                        # Escalate to Redact/Block
                        final_action = "Redact" 
                    elif rule.actions.severity == "MEDIUM" and final_action != "Redact":
                         final_action = "Redact" # Or maybe Review? Let's stick to Redact for PII.

                    # Since we sort by priority, maybe we want to keep checking? 
                    # Yes, to find max score.
        
        if not justifications:
             justifications.append("No specific NSRL rules matched active PII, but PII was present.")
             # Fallback: if PII is present but no specific rule, what to do?
             # Default to Warning or Low Risk? 
             # For now, let's assume if Presidio found it, it's at least 'Low' risk.
             if max_risk_score == 0:
                 max_risk_score = 0.1
        
        decision = AgentDecision(
            trace_id=trace_id,
            chunk_id=chunk.chunk_id,
            agent_name="PolicyAgent",
            action=final_action,
            risk_score=max_risk_score,
            justification_trace=justifications
        )

        return GovernedChunk(
            **chunk.dict(),
            redacted_text=chunk.processed_text, # Placeholder for Phase 6
            decision=decision
        )

    def _check_conditions(self, entity: DetectedPII, rule: NSRLRule) -> bool:
        """
        Checks if a detected entity matches the rule conditions.
        ALL conditions must match (AND logic).

        Only PII_MATCH conditions can be evaluated here because this method
        operates at the entity level.  CONTEXT_MATCH conditions require
        document-level context (e.g. total PII count, jurisdiction) that is
        not available per-entity.  Such conditions are intentionally skipped
        (treated as non-matching) so that escalation / jurisdiction rules do
        NOT silently fire on every entity — they must be evaluated separately
        at the document level before calling this method.
        """
        for cond in rule.conditions:
            if cond.type == "PII_MATCH":
                # Retrieve the value to check from the entity
                val_to_check = None
                if cond.field == "type":
                    val_to_check = entity.entity_type
                elif cond.field == "confidence":
                    val_to_check = entity.score
                elif cond.field == "value":
                    val_to_check = entity.text_value
                else:
                    # Unknown field — condition cannot be satisfied
                    return False

                # Check operator
                if cond.operator == "EQUALS":
                    if val_to_check != cond.value:
                        return False
                elif cond.operator == "GREATER_THAN":
                    if not (isinstance(val_to_check, (int, float)) and val_to_check > cond.value):
                        return False
                elif cond.operator == "LESS_THAN_OR_EQUALS":
                    if not (isinstance(val_to_check, (int, float)) and val_to_check <= cond.value):
                        return False
                elif cond.operator == "IN_LIST":
                    if val_to_check not in cond.value:
                        return False
                else:
                    # Unknown operator — condition cannot be satisfied
                    return False

            elif cond.type == "CONTEXT_MATCH":
                # CONTEXT_MATCH requires document-level evaluation (not per-entity).
                # Return False so this rule does not fire at the entity level.
                # Document-level escalation rules should be evaluated separately.
                return False

            else:
                # Unknown condition type — treat as non-matching to be safe
                return False

        return True

    # ------------------------------------------------------------------
    # Document-level escalation evaluation (CONTEXT_MATCH rules)
    # ------------------------------------------------------------------

    def _build_document_context(
        self,
        chunks: List[ClassifiedChunk],
        jurisdiction: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Derives document-level context fields from all classified chunks.

        The returned dict is passed to :meth:`_check_context_conditions` so
        that CONTEXT_MATCH rules can be evaluated against real document data.
        """
        all_entity_types: set = set()
        total_pii = 0
        for chunk in chunks:
            for entity in chunk.detected_entities:
                all_entity_types.add(entity.entity_type)
                total_pii += 1

        return {
            "pii_total_count": total_pii,
            "has_gov_id": bool(all_entity_types & _GOV_ID_ENTITY_TYPES),
            "has_healthcare_data": bool(all_entity_types & _HEALTHCARE_ENTITY_TYPES),
            "has_financial_data": bool(all_entity_types & _FINANCIAL_ENTITY_TYPES),
            "jurisdiction": jurisdiction,
        }

    def _check_context_conditions(
        self,
        doc_context: Dict[str, Any],
        rule: NSRLRule,
    ) -> bool:
        """Evaluates all conditions in *rule* against the document-level context.

        Returns False immediately if any condition is not CONTEXT_MATCH —
        those rules belong to the per-entity evaluation path in
        :meth:`_check_conditions`.  This enforces strict separation between
        the two evaluation tiers.
        """
        for cond in rule.conditions:
            if cond.type != "CONTEXT_MATCH":
                # Mixed or PII_MATCH rules are handled in evaluate_chunk — skip here.
                return False

            val = doc_context.get(cond.field)

            if cond.operator == "EQUALS":
                if val != cond.value:
                    return False
            elif cond.operator == "GREATER_THAN":
                if not (isinstance(val, (int, float)) and val > cond.value):
                    return False
            elif cond.operator == "LESS_THAN_OR_EQUALS":
                if not (isinstance(val, (int, float)) and val <= cond.value):
                    return False
            elif cond.operator == "IN_LIST":
                if val not in cond.value:
                    return False
            else:
                # Unknown operator — condition cannot be satisfied
                return False

        return True

    def evaluate_document(
        self,
        chunks: List[ClassifiedChunk],
        trace_id: str = "unknown",
        jurisdiction: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Evaluate document-level CONTEXT_MATCH escalation rules.

        This is the **second evaluation phase**, complementing the per-chunk
        :meth:`evaluate_chunk` method.  It must be called after all chunks
        have been classified so that accurate document-wide statistics (total
        PII count, presence of gov-ID/health/financial entity types) are
        available.

        Only rules whose **every** condition is of type ``CONTEXT_MATCH`` are
        evaluated here; rules that mix PII_MATCH with CONTEXT_MATCH are not
        yet supported and are skipped with a warning.

        Args:
            chunks: All classified chunks from the document (post Fusion).
            trace_id: Trace identifier for auditability.
            jurisdiction: Optional jurisdiction code (e.g. ``"EU"`` to trigger
                GDPR rules).  Pass ``None`` (default) when unknown.

        Returns:
            A dict with the following keys:

            * ``escalated`` (bool) — True if any escalation rule fired.
            * ``risk_score`` (float) — Highest score among fired rules.
            * ``severity`` (str) — Highest severity among fired rules.
            * ``rules_fired`` (list[str]) — IDs of rules that matched.
            * ``justifications`` (list[str]) — Human-readable explanations.
            * ``context_snapshot`` (dict) — The document context that was
              evaluated, useful for debugging and audit purposes.
        """
        doc_context = self._build_document_context(chunks, jurisdiction=jurisdiction)

        _severity_order = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1, "NONE": 0}
        max_risk_score = 0.0
        severity = "NONE"
        rules_fired: List[str] = []
        justifications: List[str] = []

        for rule in self.rules:
            if not rule.conditions:
                continue

            # Skip rules that mix condition types — they require a combined evaluator
            # not yet implemented.  Log a warning so operators know.
            if not all(c.type == "CONTEXT_MATCH" for c in rule.conditions):
                continue

            if self._check_context_conditions(doc_context, rule):
                rules_fired.append(rule.id)
                justifications.append(
                    f"Rule {rule.id} fired: "
                    f"{rule.actions.justification or rule.meta.description}"
                )
                if rule.actions.score > max_risk_score:
                    max_risk_score = rule.actions.score
                if _severity_order.get(rule.actions.severity, 0) > _severity_order.get(severity, 0):
                    severity = rule.actions.severity

        logger.info(
            "[PolicyAgent] Document evaluation complete: trace=%s escalated=%s "
            "rules_fired=%d risk=%.2f",
            trace_id, bool(rules_fired), len(rules_fired), max_risk_score,
        )

        return {
            "escalated": bool(rules_fired),
            "risk_score": max_risk_score,
            "severity": severity,
            "rules_fired": rules_fired,
            "justifications": justifications,
            "context_snapshot": doc_context,
        }
