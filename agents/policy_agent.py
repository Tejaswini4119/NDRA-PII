import os
import yaml
import logging
from typing import List, Dict, Optional
from schemas.core_models import ClassifiedChunk, GovernedChunk, AgentDecision, DetectedPII
from schemas.rule_schema import NSRLRule

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
        print(f"[PolicyAgent] Loaded {loaded_count} rules from {self.rules_dir}")

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
                    # Unknown field
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
                    return False
        
        return True
