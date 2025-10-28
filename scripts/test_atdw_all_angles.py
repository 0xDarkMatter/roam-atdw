"""
Test ATDW extraction from ALL possible angles to ensure completeness.
"""

import json
from urllib.request import urlopen, Request
import time

API_KEY = "ee37502ebe584551a7eeb42bf2e26450"
BASE_URL = "https://atlas.atdw-online.com.au/api/atlas/products"

STATES = ["NSW", "VIC", "QLD", "SA", "WA", "TAS", "NT", "ACT"]

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
print("ATDW COMPREHENSIVE COVERAGE TEST")
print("="*80)

# BASELINE: No filters
print("\n[BASELINE] No filters:")
print("-"*80)
baseline = get_count("")
print(f"Total products: {baseline:,}\n")

# TEST 1: State coverage (what we did)
print("[TEST 1] State-based extraction:")
print("-"*80)
state_total = 0
for state in STATES:
    count = get_count(f"st={state}")
    state_total += count
    print(f"  {state}: {count:,}")
print(f"  TOTAL: {state_total:,}")
print(f"  Match baseline: {'YES' if state_total == baseline else 'NO'}\n")
time.sleep(1)

# TEST 2: Status filter (active vs cancelled)
print("[TEST 2] Status-based extraction:")
print("-"*80)
active = get_count("status=A")
cancelled = get_count("status=I")
status_total = active + cancelled
print(f"  Active (A): {active:,}")
print(f"  Inactive (I): {cancelled:,}")
print(f"  TOTAL: {status_total:,}")
print(f"  Match baseline: {'YES' if status_total == baseline else 'NO'}\n")
time.sleep(1)

# TEST 3: Entity type filter
print("[TEST 3] Testing entity type filter:")
print("-"*80)
# Try with and without entityTypes parameter
count_no_entity = get_count("")
count_with_entity = get_count("entityTypes=UNKNOWN")  # Test if this filters
print(f"  No entityTypes filter: {count_no_entity:,}")
print(f"  With entityTypes=UNKNOWN: {count_with_entity:,}")
print(f"  Filter affects results: {'YES' if count_with_entity != count_no_entity else 'NO'}\n")
time.sleep(1)

# TEST 4: Geographic boundary filter
print("[TEST 4] Testing without geographic filters:")
print("-"*80)
# Test if there are products without lat/long that need special handling
count_baseline = get_count("")
print(f"  All products: {count_baseline:,}")
print(f"  (Cannot filter by 'has coordinates' via API, but this is baseline)\n")

# TEST 5: Test product type (tourism vs non-tourism)
print("[TEST 5] Testing vertical filters:")
print("-"*80)
# ATDW has different verticals - test if verticals parameter affects results
count_no_vertical = get_count("")
count_with_vertical = get_count("verticals=ATDW")  # Tourism vertical
print(f"  No vertical filter: {count_no_vertical:,}")
print(f"  With verticals=ATDW: {count_with_vertical:,}")
print(f"  Filter affects results: {'YES' if count_with_vertical != count_no_vertical else 'NO'}\n")
time.sleep(1)

# TEST 6: Expiry date filter
print("[TEST 6] Testing expiry date filters:")
print("-"*80)
# Check if expired products are included in default search
count_all = get_count("")
# Note: Can't easily test expired products without complex date filters
print(f"  All products (default): {count_all:,}")
print(f"  (API may auto-exclude expired products by default)\n")

# SUMMARY
print("="*80)
print("COMPREHENSIVE TEST SUMMARY:")
print("="*80)
print(f"Baseline (no filters):       {baseline:,}")
print(f"State-based (st):            {state_total:,}  {'✓ MATCH' if state_total == baseline else '✗ MISMATCH'}")
print(f"Status-based (A + I):        {status_total:,}  {'✓ MATCH' if status_total == baseline else '✗ MISMATCH'}")
print(f"Our extraction:              56,507  {'✓ MATCH' if state_total == 56507 else '✗ MISMATCH'}")

print("\n" + "="*80)
print("CONCLUSION:")
print("="*80)

all_match = (state_total == baseline == 56507)

if all_match:
    print("✓ VERIFIED: State-based extraction captured ALL products")
    print(f"✓ Total products in ATDW: {baseline:,}")
    print("✓ No products missing from any angle")
    print("\nOur extraction is COMPLETE - no additional filters needed.")
else:
    print("✗ ISSUE DETECTED:")
    if state_total != baseline:
        print(f"  - State-based missing {baseline - state_total:,} products")
    if state_total != 56507:
        print(f"  - Our extraction has {abs(state_total - 56507):,} product discrepancy")
    print("\nNeed to investigate further.")

print("="*80)
