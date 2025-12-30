import sys
import os

sys.path.append(os.path.abspath("."))

from agents.policy_agent import PolicyAgent

print("Loading Real NSRL Rules...")
agent = PolicyAgent(rules_dir="nsrl/rules")

print(f"Loaded {len(agent.rules)} rules successfully.")
if len(agent.rules) > 13:
    print("SUCCESS: Rule count increased after fix.")
else:
    print(f"Loaded count: {len(agent.rules)}")
