"""
Test if servicest parameter returns additional products.
"""

import json
from urllib.request import urlopen, Request

API_KEY = "ee37502ebe584551a7eeb42bf2e26450"
BASE_URL = "https://atlas.atdw-online.com.au/api/atlas/products"

STATES = ["NSW", "VIC", "QLD", "SA", "WA", "TAS", "NT", "ACT"]

def get_count(state, param_type):
    """Get product count for a state using different parameters."""
    if param_type == "st":
        url = f"{BASE_URL}?key={API_KEY}&st={state}&size=1&out=json"
    elif param_type == "servicest":
        url = f"{BASE_URL}?key={API_KEY}&servicest={state}&size=1&out=json"
    elif param_type == "both":
        url = f"{BASE_URL}?key={API_KEY}&st={state}&servicest={state}&size=1&out=json"

    req = Request(url)
    req.add_header('User-Agent', 'FATHOM-DataPlatform/1.0')

    with urlopen(req, timeout=30) as response:
        data = response.read()
        text = data.decode('utf-16')
        result = json.loads(text)
        return result.get('numberOfResults', 0)

print("="*80)
print("ATDW State Parameter Comparison")
print("="*80)
print("\nst = Product location state")
print("servicest = Service location state")
print("="*80)

print(f"\n{'State':<6} {'st only':<12} {'servicest only':<15} {'Difference'}")
print("-"*80)

total_st = 0
total_servicest = 0

for state in STATES:
    count_st = get_count(state, "st")
    count_servicest = get_count(state, "servicest")
    diff = count_servicest - count_st

    total_st += count_st
    total_servicest += count_servicest

    if diff != 0:
        print(f"{state:<6} {count_st:>10,}   {count_servicest:>12,}   {diff:>+10,} <- DIFFERENT")
    else:
        print(f"{state:<6} {count_st:>10,}   {count_servicest:>12,}   {diff:>10,}")

print("-"*80)
print(f"{'TOTAL':<6} {total_st:>10,}   {total_servicest:>12,}   {total_servicest - total_st:>+10,}")

print(f"\n{'='*80}")
print("Conclusion:")
if total_servicest > total_st:
    print(f"  ISSUE: servicest returns {total_servicest - total_st:,} MORE products!")
    print(f"  We extracted: {total_st:,}")
    print(f"  We should have: {total_servicest:,}")
    print("\n  ACTION NEEDED: Re-run extraction using servicest parameter")
elif total_st == total_servicest:
    print(f"  OK: Both parameters return same count ({total_st:,})")
    print("  No additional products to extract")
else:
    print(f"  Unexpected: st returns MORE than servicest")

print("="*80)
