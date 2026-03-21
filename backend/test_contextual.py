import requests
import time

time.sleep(1)

print("=== TEST 1: SAME ENDPOINT, DIFFERENT TOPICS ===\n")

topics = ["recursion", "arrays", "sorting"]
for topic in topics:
    resp = requests.get(
        f'http://localhost:8001/study/archaeology?topic={topic}&user_id=test&confusion_level=3',
        timeout=10
    ).json()
    recommendation = (resp.get('data') or {}).get('result', {}).get('recommendation', '')
    print(f"Topic: {topic}")
    print(f"Recommendation (first 150 chars): {recommendation[:150]}")
    print()

print("\n=== TEST 2: SOCRATIC WITH DIFFERENT INPUTS ===\n")

beliefs = [
    "recursion always uses more memory",
    "arrays are always faster than linked lists",
    "sorting is always O(n)"
]

for belief in beliefs:
    concept = belief.split()[0]
    resp = requests.post(
        f'http://localhost:8001/socratic/ask?concept={concept}&user_belief={belief}&user_id=test',
        timeout=10
    ).json()
    question = (resp.get('data') or {}).get('question', '')
    print(f"Input belief: {belief}")
    print(f"Question (first 150 chars): {question[:150]}")
    print()

print("\n=== TEST 3: SHADOW WITH DIFFERENT TOPICS ===\n")

topics_shadow = ["recursion", "arrays"]
for topic in topics_shadow:
    resp = requests.get(
        f'http://localhost:8001/insights/shadow?topic={topic}&days=7&user_id=test',
        timeout=10
    ).json()
    insight = (resp.get('data') or {}).get('insights', '')
    print(f"Topic: {topic}")
    print(f"Insight (first 150 chars): {str(insight)[:150]}")
    print()
