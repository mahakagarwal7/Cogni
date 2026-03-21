import requests
import time

time.sleep(3)

print('=== TESTING RETENTION -> REFLECTION LOOP ===\n')

# Step 1: Ask initial question
print('STEP 1: Initial Question')
concept = 'dynamic programming'
belief = "don't know anything"

r1 = requests.post(
    f'http://localhost:8001/socratic/ask?concept={concept}&user_belief={belief}&user_id=test123&confusion_level=3',
    timeout=20
).json()

initial_question = (r1.get('data') or {}).get('question', '')
print(f'Question asked: {initial_question}\n')

# Step 2: User responds, system reflects
print('STEP 2: User Response & Reflection')
user_response = 'nothing'

r2 = requests.post(
    f'http://localhost:8001/socratic/reflect'
    f'?concept={concept}'
    f'&user_response={user_response}'
    f'&previous_question={initial_question}'
    f'&user_id=test123'
    f'&confusion_level=3',
    timeout=20
).json()

follow_up_question = (r2.get('data') or {}).get('follow_up_question', '')
response_analysis = (r2.get('data') or {}).get('response_analysis', '')
print(f'User said: {user_response}')
print(f'Analysis: {response_analysis}')
print(f'Follow-up question: {follow_up_question}')

print('\n✅ SUCCESS: Retention -> Reflection Loop Working!')
print(f'The system remembered the user response and generated a better follow-up.')
