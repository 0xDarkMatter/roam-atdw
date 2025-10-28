#!/usr/bin/env python3
"""Test ATDW API pagination to understand response structure."""

import requests
import json

API_KEY = 'ee37502ebe584551a7eeb42bf2e26450'
BASE_URL = 'https://atlas.atdw-online.com.au/api/atlas/products'

# Test NSW - should have more than 5000 products
params = {
    'key': API_KEY,
    'st': 'NSW',
    'out': 'json',
    'size': 10,  # Small size for testing
    'pge': 1
}

print("Testing ATDW API response structure...")
print("="*80)

response = requests.get(BASE_URL, params=params)
data = response.json()

print(f"\nResponse keys: {list(data.keys())}")
print(f"\nMetadata fields:")
for key, value in data.items():
    if key != 'products':
        print(f"  {key}: {value}")

print(f"\nNumber of products in response: {len(data.get('products', []))}")
print(f"\nTotal count field: {data.get('numberOfResults', 'NOT FOUND')}")
print(f"\nTotal pages needed (at size 5000): {data.get('numberOfResults', 0) / 5000:.1f}")
