import unittest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.fusion_agent import FusionAgent
from schemas.core_models import DetectedPII

class TestFusionAgent(unittest.TestCase):
    
    def setUp(self):
        self.agent = FusionAgent()

    def create_entity(self, text, start, end, score=0.9, type="PERSON"):
        return DetectedPII(
            entity_type=type,
            text_value=text,
            start_index=start,
            end_index=end,
            score=score,
            source="test"
        )

    def test_exact_duplicate(self):
        e1 = self.create_entity("John", 0, 4)
        e2 = self.create_entity("John", 0, 4)
        result = self.agent.deduplicate_entities([e1, e2])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].text_value, "John")

    def test_containment(self):
        # "John Doe" contains "John"
        e1 = self.create_entity("John Doe", 0, 8)
        e2 = self.create_entity("John", 0, 4)
        result = self.agent.deduplicate_entities([e1, e2])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].text_value, "John Doe")

    def test_partial_overlap_prefer_longer(self):
        # "New York" (0-8) vs "York City" (4-13)
        # "New York" len 8, "York City" len 9. Should keep York City?
        e1 = self.create_entity("New York", 0, 8)
        e2 = self.create_entity("York City", 4, 13)
        
        result = self.agent.deduplicate_entities([e1, e2])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].text_value, "York City")

    def test_no_overlap(self):
        e1 = self.create_entity("John", 0, 4)
        e2 = self.create_entity("Doe", 10, 13)
        result = self.agent.deduplicate_entities([e1, e2])
        self.assertEqual(len(result), 2)

    def test_same_len_prefer_score(self):
        e1 = self.create_entity("John", 0, 4, score=0.5)
        e2 = self.create_entity("Lohn", 0, 4, score=0.9) # Typo but higher score
        result = self.agent.deduplicate_entities([e1, e2])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].text_value, "Lohn")

if __name__ == '__main__':
    unittest.main()
