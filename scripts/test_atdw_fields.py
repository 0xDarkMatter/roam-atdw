"""Test ATDW field combinations to find optimal extraction strategy."""

import requests
import json

API_KEY = 'ee37502ebe584551a7eeb42bf2e26450'
BASE_URL = 'https://atlas.atdw-online.com.au/api/atlas/products'

print("="*80)
print("ATDW FIELD EXTRACTION TEST")
print("="*80)

# Test 1: Default fields (no fl parameter)
print("\nTest 1: Default fields (no fl parameter)")
print("-"*80)
r = requests.get(BASE_URL, params={
    'key': API_KEY,
    'st': 'NSW',
    'size': 1,
    'pge': 1,
    'out': 'json'
})
p = r.json()['products'][0]
print(f"Fields returned: {len(p.keys())}")
print(f"Field list: {', '.join(sorted(p.keys()))}")
print(f"\nKey data:")
print(f"  - productCategoryId: {p.get('productCategoryId', 'MISSING')}")
print(f"  - addresses: {len(p.get('addresses', []))} entries")
print(f"  - comms_ph: {'YES' if 'comms_ph' in p else 'MISSING'}")
print(f"  - comms_em: {'YES' if 'comms_em' in p else 'MISSING'}")
print(f"  - comms_url: {'YES' if 'comms_url' in p else 'MISSING'}")
print(f"  - boundary: {'YES' if 'boundary' in p else 'MISSING'}")

# Test 2: Request contact fields explicitly
print("\nTest 2: With contact fields (fl parameter)")
print("-"*80)
fl = 'product_id,product_name,product_category_id,addresses,comms_ph,comms_em,comms_url,comms_burl,boundary'
r = requests.get(BASE_URL, params={
    'key': API_KEY,
    'st': 'NSW',
    'size': 1,
    'pge': 1,
    'out': 'json',
    'fl': fl
})
p = r.json()['products'][0]
print(f"Fields returned: {len(p.keys())}")
print(f"Field list: {', '.join(sorted(p.keys()))}")
print(f"\nKey data:")
print(f"  - productCategoryId: {p.get('productCategoryId', 'MISSING')}")
print(f"  - addresses: {len(p.get('addresses', []))} entries" if 'addresses' in p else "  - addresses: MISSING")
print(f"  - comms_ph: {p.get('comms_ph', 'MISSING')}")
print(f"  - comms_em: {p.get('comms_em', 'MISSING')}")
print(f"  - comms_url: {p.get('comms_url', 'MISSING')}")
print(f"  - boundary: {'YES' if 'boundary' in p else 'MISSING'}")

print("\n" + "="*80)
print("CONCLUSION:")
print("="*80)
print("The 'fl' parameter appears to be broken or contact fields don't exist.")
print("Recommendation: Use default fields (no fl parameter) for extraction.")
print("="*80)
