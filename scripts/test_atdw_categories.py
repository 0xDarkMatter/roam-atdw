"""
Test if category-based extraction would return different products than state-based.
"""

import json
from urllib.request import urlopen, Request

API_KEY = "ee37502ebe584551a7eeb42bf2e26450"
BASE_URL = "https://atlas.atdw-online.com.au/api/atlas/products"

# Major ATDW categories
CATEGORIES = [
    "ACCOMM",      # Accommodation
    "ATTRACTION",  # Attractions
    "DESTINFO",    # Destination Information
    "EVENT",       # Events
    "FOOD",        # Food & Beverage
    "HIRE",        # Hire & Transport
    "JOURNEYS",    # Journeys
    "TOUR",        # Tours
    "TRANSPORT",   # Transport
    "RETAIL",      # Retail & Services
]

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
print("ATDW Category Coverage Test")
print("="*80)

# Test 1: No filters (baseline)
print("\n1. No filters (baseline):")
print("-"*80)
no_filter = get_count("")
print(f"   Total: {no_filter:,}")

# Test 2: State-based (what we extracted)
print("\n2. State-based extraction (what we did):")
print("-"*80)
state_sum = 56507
print(f"   Total: {state_sum:,}")

# Test 3: Category-based counts
print("\n3. Category-based counts:")
print("-"*80)
print(f"{'Category':<15} {'Count':>10}")
print("-"*80)

category_total = 0
for cat in CATEGORIES:
    count = get_count(f"cats={cat}")
    category_total += count
    print(f"{cat:<15} {count:>10,}")

print("-"*80)
print(f"{'TOTAL':<15} {category_total:>10,}")

# Test 4: Check for products WITHOUT categories
print("\n4. Products by category assignment:")
print("-"*80)
print(f"   Total products: {no_filter:,}")
print(f"   Sum of categories: {category_total:,}")
print(f"   Difference: {no_filter - category_total:+,}")

# Test 5: Check if state-based missed any
print("\n5. Coverage comparison:")
print("-"*80)
print(f"   No filter: {no_filter:,}")
print(f"   State-based: {state_sum:,}")
print(f"   Missing from state-based: {no_filter - state_sum:+,}")

print(f"\n{'='*80}")
print("CONCLUSION:")
if category_total > state_sum:
    print(f"  WARNING: Category-based returns {category_total - state_sum:,} MORE products!")
    print("  Some products may not have a state but DO have a category")
    print("  ACTION: Need to re-extract using category filters")
elif state_sum == category_total == no_filter:
    print(f"  OK: All three approaches return same count ({state_sum:,})")
    print("  State-based extraction captured everything")
else:
    print(f"  Mixed results - need to investigate further")
    print(f"  No filter: {no_filter:,}")
    print(f"  State-based: {state_sum:,}")
    print(f"  Category sum: {category_total:,}")

print("="*80)
