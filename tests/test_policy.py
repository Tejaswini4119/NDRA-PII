import unittest
import sys
import os
import shutil
import yaml

# Fix path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.policy_agent import PolicyAgent
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

if __name__ == '__main__':
    unittest.main()
