import unittest
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.redaction_agent import RedactionAgent
from schemas.core_models import GovernedChunk, AgentDecision, DetectedPII

class TestRedactionAgent(unittest.TestCase):
    
    def setUp(self):
        self.agent = RedactionAgent()

    def create_chunk(self, text, action="Redact", entities=[]):
        decision = AgentDecision(
            trace_id="test",
            chunk_id="chk1",
            agent_name="Policy",
            action=action,
            risk_score=1.0 if action=="Redact" else 0.0,
            justification_trace=[]
        )
        return GovernedChunk(
            document_id="doc1",
            processed_text=text,
            original_text=text,
            page_number=1,
            token_span=(0,10),
            detected_entities=entities,
            redacted_text="", # To be filled
            decision=decision
        )

    def test_no_redaction_needed(self):
        chunk = self.create_chunk("Hello World", action="Allow")
        result = self.agent.redact(chunk)
        self.assertEqual(result.redacted_text, "Hello World")

    def test_single_redaction(self):
        # "My name is John." -> "John" at 11-15
        text = "My name is John."
        entities = [
            DetectedPII(
                entity_type="PERSON", text_value="John", start_index=11, end_index=15, score=0.9, source="test"
            )
        ]
        chunk = self.create_chunk(text, entities=entities)
        result = self.agent.redact(chunk)
        self.assertEqual(result.redacted_text, "My name is [PERSON].")

    def test_multiple_redactions(self):
        # "John lives in London."
        # John: 0-4
        # London: 14-20
        text = "John lives in London."
        entities = [
            DetectedPII(entity_type="PERSON", text_value="John", start_index=0, end_index=4, score=0.9, source="t"),
            DetectedPII(entity_type="LOCATION", text_value="London", start_index=14, end_index=20, score=0.9, source="t")
        ]
        # Mix order to test sorting
        chunk = self.create_chunk(text, entities=list(reversed(entities)))
        result = self.agent.redact(chunk)
        self.assertEqual(result.redacted_text, "[PERSON] lives in [LOCATION].")
        
    def test_replacement_length_diff(self):
        # "A" (1 char) -> is replaced by "[INITIAL]" (9 chars)
        text = "My name is A."
        entities = [DetectedPII(entity_type="INITIAL", text_value="A", start_index=11, end_index=12, score=0.9, source="t")]
        chunk = self.create_chunk(text, entities=entities)
        result = self.agent.redact(chunk)
        self.assertEqual(result.redacted_text, "My name is [INITIAL].")

if __name__ == '__main__':
    unittest.main()
