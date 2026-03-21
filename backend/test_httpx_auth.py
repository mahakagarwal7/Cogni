#!/usr/bin/env python3
"""Test direct httpx call with proper Bearer token authentication."""
import os
import httpx
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('HINDSIGHT_API_KEY')
base_url = os.getenv('HINDSIGHT_BASE_URL', 'https://api.hindsight.vectorize.io')
bank_id = os.getenv('HINDSIGHT_USER_BANK_PREFIX') or os.getenv('HINDSIGHT_BANK_ID', 'student_demo_001')

print(f'API Key: {api_key[:20]}...')
print(f'Base URL: {base_url}')
print(f'Bank ID: {bank_id}')

# Test with proper headers
headers = {
    'Authorization': f'Bearer {api_key}',
    'Content-Type': 'application/json'
}

# Try different endpoint URLs  
endpoints = [
    f'{base_url}/recall',
    f'{base_url}/api/recall',
    f'{base_url}/memories/recall',
    f'{base_url}/v1/memories/recall',
]

payload = {
    'bank_id': bank_id,
    'query': 'test query',
    'max_tokens': 100
}

print(f'\nTesting endpoints with Bearer token:')
print('='*60)

for endpoint in endpoints:
    try:
        print(f'\n{endpoint}', end='... ')
        response = httpx.post(endpoint, headers=headers, json=payload, timeout=5)
        print(f'Status {response.status_code}')
        if response.status_code != 200:
            try:
                print(f'  Error: {response.json()}')
            except:
                print(f'  Body: {response.text[:200]}')
        else:
            print(f'  Success! Got response.')
    except Exception as e:
        print(f'Error: {str(e)[:100]}')
