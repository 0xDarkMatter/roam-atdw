"""
Test script to check total ATDW products with and without state filter.
"""

import json
from urllib.request import urlopen, Request

API_KEY = "ee37502ebe584551a7eeb42bf2e26450"
BASE_URL = "https://atlas.atdw-online.com.au/api/atlas/products"

def get_total_count(with_state_filter=False):
    """Get total product count."""
    url = f"{BASE_URL}?key={API_KEY}&size=1&pge=1&out=json"

    if with_state_filter:
        # Test with NSW as example
        url += "&st=NSW"

    req = Request(url)
    req.add_header('User-Agent', 'FATHOM-DataPlatform/1.0')

    with urlopen(req, timeout=30) as response:
        data = response.read()
        text = data.decode('utf-16')
        result = json.loads(text)
        return result.get('numberOfResults', 0)

print("="*80)
print("ATDW National Product Count Test")
print("="*80)

# Test 1: All of Australia (no state filter)
print("\nTest 1: Search all of Australia (no st parameter)")
print("-"*80)
national_count = get_total_count(with_state_filter=False)
print(f"Total products: {national_count:,}")

# Test 2: Sum of all states
print("\nTest 2: Sum of all states (using st parameter)")
print("-"*80)
state_sum = 56507  # From previous extraction
print(f"Total products: {state_sum:,}")

# Comparison
print(f"\n{'='*80}")
print("COMPARISON:")
print(f"  National search (no st filter): {national_count:,}")
print(f"  Sum of all states (with st filter): {state_sum:,}")
print(f"  Difference: {national_count - state_sum:+,}")

if national_count > state_sum:
    print(f"\n  ISSUE FOUND: {national_count - state_sum:,} products missing when filtering by state!")
    print("  → Some products don't have a state assigned")
    print("  → Need to run national extraction WITHOUT st parameter")
elif national_count == state_sum:
    print("\n  OK: All products accounted for")
    print(f"  → ATDW contains {national_count:,} products total")
else:
    print("\n  UNEXPECTED: National count is LESS than state sum")

print("="*80)
