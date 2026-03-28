import unittest
import sys
import os
import shutil
import tempfile
import yaml

# Fix path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.policy_agent import PolicyAgent
from agents.audit import AuditAgent
from schemas.core_models import ClassifiedChunk, DetectedPII
from schemas.rule_schema import NSRLRule

class TestPolicyAgent(unittest.TestCase):
    
    def setUp(self):
        # Create a temporary rules directory
        self.test_rules_dir = "tests/temp_rules"
        os.makedirs(self.test_rules_dir, exist_ok=True)
        
        # Create a dummy rule
        self.dummy_rule = [
            {
                "id": "TEST-RULE-001",
                "version": "1.0",
                "meta": {
                    "name": "Test Rule",
                    "description": "Test",
                    "priority": 100,
                    "tags": ["test"]
                },
                "conditions": [
                    {
                        "type": "PII_MATCH",
                        "field": "type",
                        "operator": "EQUALS",
                        "value": "TEST_ENTITY"
                    }
                ],
                "actions": {
                    "classification": "RESTRICTED",
                    "severity": "CRITICAL",
                    "score": 1.0,
                    "justification": "Test Trigger",
                    "tags": []
                }
            }
        ]
        
        with open(os.path.join(self.test_rules_dir, "test.yml"), "w") as f:
            yaml.dump(self.dummy_rule, f)
            
        self.agent = PolicyAgent(rules_dir=self.test_rules_dir)

    def tearDown(self):
        if os.path.exists(self.test_rules_dir):
            shutil.rmtree(self.test_rules_dir)

    def test_load_rules(self):
        self.assertTrue(len(self.agent.rules) >= 1)
        self.assertEqual(self.agent.rules[0].id, "TEST-RULE-001")

    def test_evaluate_match(self):
        # Create chunk with matching entity
        chunk = ClassifiedChunk(
            document_id="doc1",
            processed_text="secret",
            original_text="secret",
            page_number=1,
            token_span=(0,1),
            detected_entities=[
                DetectedPII(
                    entity_type="TEST_ENTITY",
                    text_value="secret",
                    start_index=0,
                    end_index=6,
                    score=0.9,
                    source="test"
                )
            ]
        )
        
        governed = self.agent.evaluate_chunk(chunk, trace_id="trace1")
        self.assertEqual(governed.decision.action, "Redact")
        self.assertEqual(governed.decision.risk_score, 1.0)
        self.assertIn("Rule TEST-RULE-001 fired", governed.decision.justification_trace[0])

    def test_evaluate_no_match(self):
        chunk = ClassifiedChunk(
            document_id="doc1",
            processed_text="nothing",
            original_text="nothing",
            page_number=1,
            token_span=(0,1),
            detected_entities=[
                DetectedPII(
                    entity_type="OTHER_ENTITY",
                    text_value="safe",
                    start_index=0,
                    end_index=4,
                    score=0.9,
                    source="test"
                )
            ]
        )
        
        governed = self.agent.evaluate_chunk(chunk, trace_id="trace1")
        # Should be allowed or low risk since no rule matched
        self.assertNotEqual(governed.decision.risk_score, 1.0)
        # Our logic defaults to 'Allow' if no CRITICAL/HIGH/MEDIUM rule matches, 
        # but assigns 0.1 if PII exists but no rule matches.
        self.assertEqual(governed.decision.risk_score, 0.1)


class TestPolicyAgentEvaluateDocument(unittest.TestCase):
    """Tests for the document-level CONTEXT_MATCH escalation evaluator."""

    def setUp(self):
        self.test_rules_dir = "tests/temp_ctx_rules"
        os.makedirs(self.test_rules_dir, exist_ok=True)

        # A CONTEXT_MATCH density rule: fires when pii_total_count > 3
        density_rule = [
            {
                "id": "TEST-CTX-DENSITY-001",
                "version": "1.0",
                "meta": {
                    "name": "Test Density",
                    "description": "High density test",
                    "priority": 200,
                    "tags": [],
                },
                "conditions": [
                    {
                        "type": "CONTEXT_MATCH",
                        "field": "pii_total_count",
                        "operator": "GREATER_THAN",
                        "value": 3,
                    }
                ],
                "actions": {
                    "classification": "RESTRICTED",
                    "severity": "CRITICAL",
                    "score": 1.0,
                    "justification": "Too many PII items.",
                    "tags": [],
                },
            }
        ]
        # A CONTEXT_MATCH toxic-combo rule: fires when has_gov_id AND has_financial_data
        toxic_rule = [
            {
                "id": "TEST-CTX-TOXIC-001",
                "version": "1.0",
                "meta": {
                    "name": "Test Toxic",
                    "description": "ID + Finance",
                    "priority": 150,
                    "tags": [],
                },
                "conditions": [
                    {
                        "type": "CONTEXT_MATCH",
                        "field": "has_gov_id",
                        "operator": "EQUALS",
                        "value": True,
                    },
                    {
                        "type": "CONTEXT_MATCH",
                        "field": "has_financial_data",
                        "operator": "EQUALS",
                        "value": True,
                    },
                ],
                "actions": {
                    "classification": "RESTRICTED",
                    "severity": "CRITICAL",
                    "score": 0.95,
                    "justification": "Identity + Finance combo.",
                    "tags": [],
                },
            }
        ]

        with open(os.path.join(self.test_rules_dir, "ctx_density.yml"), "w") as f:
            yaml.dump(density_rule, f)
        with open(os.path.join(self.test_rules_dir, "ctx_toxic.yml"), "w") as f:
            yaml.dump(toxic_rule, f)

        self.agent = PolicyAgent(rules_dir=self.test_rules_dir)

    def tearDown(self):
        if os.path.exists(self.test_rules_dir):
            shutil.rmtree(self.test_rules_dir)

    def _make_chunk(self, entity_types):
        """Helper: build a ClassifiedChunk with entities of the given types."""
        entities = [
            DetectedPII(
                entity_type=et,
                text_value="x",
                start_index=0,
                end_index=1,
                score=0.9,
                source="test",
            )
            for et in entity_types
        ]
        return ClassifiedChunk(
            document_id="doc1",
            processed_text="x",
            original_text="x",
            page_number=1,
            token_span=(0, 1),
            detected_entities=entities,
        )

    def test_density_rule_fires_when_above_threshold(self):
        # 4 PII entities > threshold of 3 → density rule fires
        chunks = [self._make_chunk(["EMAIL_ADDRESS"] * 4)]
        result = self.agent.evaluate_document(chunks, trace_id="t1")
        self.assertTrue(result["escalated"])
        self.assertIn("TEST-CTX-DENSITY-001", result["rules_fired"])
        self.assertEqual(result["risk_score"], 1.0)
        self.assertEqual(result["severity"], "CRITICAL")

    def test_density_rule_silent_when_below_threshold(self):
        # 2 PII entities ≤ threshold of 3 → no rule fires
        chunks = [self._make_chunk(["EMAIL_ADDRESS", "PHONE_NUMBER"])]
        result = self.agent.evaluate_document(chunks, trace_id="t2")
        self.assertFalse(result["escalated"])
        self.assertEqual(result["rules_fired"], [])
        self.assertEqual(result["risk_score"], 0.0)

    def test_toxic_combo_fires_when_gov_id_and_finance_present(self):
        # US_SSN (gov ID) + CREDIT_CARD (financial) → toxic combo fires
        chunks = [self._make_chunk(["US_SSN", "CREDIT_CARD"])]
        result = self.agent.evaluate_document(chunks, trace_id="t3")
        self.assertTrue(result["escalated"])
        self.assertIn("TEST-CTX-TOXIC-001", result["rules_fired"])

    def test_toxic_combo_silent_with_only_gov_id(self):
        # Only gov ID — no financial data → toxic combo should NOT fire
        chunks = [self._make_chunk(["US_SSN"])]
        result = self.agent.evaluate_document(chunks, trace_id="t4")
        self.assertFalse(result["escalated"])

    def test_no_escalation_for_empty_document(self):
        result = self.agent.evaluate_document([], trace_id="t5")
        self.assertFalse(result["escalated"])
        self.assertEqual(result["risk_score"], 0.0)

    def test_context_snapshot_included(self):
        chunks = [self._make_chunk(["US_SSN"])]
        result = self.agent.evaluate_document(chunks, trace_id="t6")
        self.assertIn("context_snapshot", result)
        snap = result["context_snapshot"]
        self.assertEqual(snap["pii_total_count"], 1)
        self.assertTrue(snap["has_gov_id"])
        self.assertFalse(snap["has_financial_data"])


class TestAuditVerifyChain(unittest.TestCase):
    """Tests for AuditAgent.verify_chain()."""

    def test_fresh_log_is_valid(self):
        with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as f:
            log_path = f.name
        try:
            agent = AuditAgent(log_file=log_path)
            result = agent.verify_chain()
            self.assertTrue(result["valid"])
            self.assertEqual(result["entries_verified"], 0)
        finally:
            os.remove(log_path)

    def test_valid_chain_after_entries(self):
        with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as f:
            log_path = f.name
        try:
            agent = AuditAgent(log_file=log_path)
            for i in range(5):
                agent.process({"action": f"event_{i}"})
            result = agent.verify_chain()
            self.assertTrue(result["valid"])
            self.assertEqual(result["entries_verified"], 5)
            self.assertIsNone(result["first_broken_at"])
        finally:
            os.remove(log_path)

    def test_tampered_entry_detected(self):
        with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as f:
            log_path = f.name
        try:
            agent = AuditAgent(log_file=log_path)
            agent.process({"action": "event_0"})
            agent.process({"action": "event_1"})

            # Tamper: read all lines, corrupt second entry's payload
            import json as json_lib
            with open(log_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            entry2 = json_lib.loads(lines[1])
            entry2["payload"]["event"]["action"] = "TAMPERED"
            lines[1] = json_lib.dumps(entry2) + "\n"

            with open(log_path, "w", encoding="utf-8") as f:
                f.writelines(lines)

            result = agent.verify_chain()
            self.assertFalse(result["valid"])
            self.assertEqual(result["first_broken_at"], 2)
        finally:
            os.remove(log_path)

    def test_missing_log_is_valid(self):
        agent = AuditAgent(log_file="/tmp/nonexistent_ndra_audit_xyz.log")
        result = agent.verify_chain()
        self.assertTrue(result["valid"])
        self.assertEqual(result["entries_verified"], 0)


if __name__ == '__main__':
    unittest.main()
