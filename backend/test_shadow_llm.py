#!/usr/bin/env python
"""Test the LLM shadow prediction"""

from app.services.llm_service import llm_service

prompt = """INSTRUCTION: Output ONLY the following format. No thinking, no explanation, no preamble.

Current topic: rotational motion

OUTPUT FORMAT (fill in the blanks):
Next Topic: [1-3 word topic name]
Reason: [1 sentence]

Examples:
Next Topic: Torque and Angular Momentum
Reason: Understanding how forces cause rotation is essential after rotational motion.

Next Topic: Chemical Bonding
Reason: After understanding atomic structure, chemical bonding explains how atoms combine.

Now output for input: rotational motion"""

print("Testing IMPROVED LLM shadow prediction response:")
print("=" * 60)
response = llm_service.generate(prompt, max_tokens=80, temperature=0.3)

print("\nRAW RESPONSE:")
print(repr(response))

print("\nFORMATTED:")
response = response.replace("<think>", "").replace("</think>", "")
lines = response.strip().split('\n')
for line in lines:
    if line.strip():
        print(f"  {line}")

print("\nPARSED:")
next_topic = "Advanced Concepts"
reason = "deepening your understanding"

for line in lines:
    line = line.strip()
    if "Next Topic:" in line:
        next_topic = line.split("Next Topic:")[-1].strip()
        print(f"  Found Next Topic: {next_topic}")
    elif "Reason:" in line:
        reason = line.split("Reason:")[-1].strip()
        print(f"  Found Reason: {reason}")

print(f"\nFINAL RESULT:")
print(f"  Next Topic: {next_topic}")
print(f"  Reason: {reason}")

