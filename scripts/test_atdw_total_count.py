"""
Test script to check total ATDW product counts with and without field filters.
"""

import json
from urllib.request import urlopen, Request

API_KEY = "ee37502ebe584551a7eeb42bf2e26450"
BASE_URL = "https://atlas.atdw-online.com.au/api/atlas/products"

STATES = ["NSW", "VIC", "QLD", "SA", "WA", "TAS", "NT", "ACT"]

FIELDS = [
    "product_id", "product_number", "product_name", "product_category_id",
    "product_description", "product_image", "addresses", "boundary",
    "comms_ph", "comms_em", "comms_url", "comms_burl", "status",
    "product_update_date", "atdw_expiry_date", "owning_organisation_name",
    "rate_from", "rate_to", "star_rating", "number_of_rooms"
]

def get_count(state, with_fields=False):
    """Get product count for a state."""
    url = f"{BASE_URL}?key={API_KEY}&st={state}&size=1&pge=1&out=json"

    if with_fields:
        fl = ",".join(FIELDS)
        url += f"&fl={fl}"

    req = Request(url)
    req.add_header('User-Agent', 'FATHOM-DataPlatform/1.0')

    with urlopen(req, timeout=30) as response:
        data = response.read()
        text = data.decode('utf-16')
        result = json.loads(text)
        return result.get('numberOfResults', 0)

print("="*80)
print("ATDW Product Count Comparison")
print("="*80)
print(f"\n{'State':<6} {'Without FL':<15} {'With FL':<15} {'Difference'}")
print("-"*80)

total_without = 0
total_with = 0

for state in STATES:
    count_without = get_count(state, with_fields=False)
    count_with = get_count(state, with_fields=True)
    diff = count_without - count_with

    total_without += count_without
    total_with += count_with

    print(f"{state:<6} {count_without:>12,}   {count_with:>12,}   {diff:>+10,}")

print("-"*80)
print(f"{'TOTAL':<6} {total_without:>12,}   {total_with:>12,}   {total_without - total_with:>+10,}")

print(f"\n{'='*80}")
print(f"Conclusion:")
if total_without == total_with:
    print("  ✓ Field list (fl) parameter does NOT filter results")
    print(f"  ✓ Total products in ATDW: {total_without:,}")
else:
    print(f"  ✗ Field list (fl) parameter IS filtering out {total_without - total_with:,} products")
    print(f"  → Need to extract without fl parameter to get all {total_without:,} products")
print("="*80)
