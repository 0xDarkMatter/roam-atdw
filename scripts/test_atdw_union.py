"""
Test if we need to use st OR servicest (union) to get all products.
"""

import json
from urllib.request import urlopen, Request

API_KEY = "ee37502ebe584551a7eeb42bf2e26450"
BASE_URL = "https://atlas.atdw-online.com.au/api/atlas/products"

def get_count(params_str):
    """Get product count with custom parameters."""
    url = f"{BASE_URL}?key={API_KEY}&size=1&out=json&{params_str}"

    req = Request(url)
    req.add_header('User-Agent', 'FATHOM-DataPlatform/1.0')

    with urlopen(req, timeout=30) as response:
        data = response.read()
        text = data.decode('utf-16')
        result = json.loads(text)
        return result.get('numberOfResults', 0)

print("="*80)
print("ATDW Product Coverage Test")
print("="*80)

# Test different approaches
print("\n1. No state filter (all of Australia):")
print("-"*80)
no_filter = get_count("")
print(f"   Total: {no_filter:,}")

print("\n2. Using st parameter only (what we extracted):")
print("-"*80)
print(f"   NSW st: {get_count('st=NSW'):,}")
print("   (Sum of all 8 states with st: 56,507)")

print("\n3. Using servicest parameter only:")
print("-"*80)
print(f"   NSW servicest: {get_count('servicest=NSW'):,}")
print("   (Sum of all 8 states with servicest: 469)")

print("\n4. Test if there are products WITHOUT a state:")
print("-"*80)
# The difference between no filter and st should tell us if products lack states
states_sum = 56507
products_without_state = no_filter - states_sum
print(f"   All products: {no_filter:,}")
print(f"   Products with st: {states_sum:,}")
print(f"   Products WITHOUT st: {products_without_state:,}")

print(f"\n{'='*80}")
print("CONCLUSION:")
print(f"  Total products in ATDW: {no_filter:,}")
print(f"  Products we extracted: 56,507")

if no_filter > 56507:
    print(f"\n  MISSING: {no_filter - 56507:,} products!")
    print("  These products likely don't have a state (st) assigned")
    print("  ACTION: Need to extract products WITHOUT state filter")
else:
    print("\n  OK: We got all products!")

print("="*80)
