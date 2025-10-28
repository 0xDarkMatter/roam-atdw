"""
Test ATDW field names - check if product_id/product_name have different names.
"""

import json
from urllib.request import urlopen, Request
from urllib.parse import urlencode

API_KEY = "ee37502ebe584551a7eeb42bf2e26450"
BASE_URL = "https://atlas.atdw-online.com.au/api/atlas/products"

def get_products(params_dict):
    """Get products with parameters."""
    query_params = {"key": API_KEY, "out": "json"}
    query_params.update(params_dict)

    query_string = urlencode(query_params)
    url = f"{BASE_URL}?{query_string}"

    req = Request(url)
    req.add_header('User-Agent', 'FATHOM-DataPlatform/1.0')

    with urlopen(req, timeout=30) as response:
        data = response.read()
        text = data.decode('utf-16')
        return json.loads(text)

print("="*80)
print("ATDW Field Name Investigation")
print("="*80)

# Get products WITHOUT fl parameter to see default fields
print("\n[TEST 1] Get products WITHOUT fl parameter (default fields):")
print("-"*80)
result = get_products({"st": "NSW", "size": "2"})

if result and 'products' in result:
    print(f"Total products: {result.get('numberOfResults', 0):,}")
    print(f"Sample size: {len(result['products'])}\n")

    for i, product in enumerate(result['products'], 1):
        print(f"Product {i} - All fields:")
        for key, value in product.items():
            # Show first 100 chars of value
            val_str = str(value)[:100]
            print(f"  {key}: {val_str}")
        print()

# Get products WITH fl parameter
print("\n[TEST 2] Get products WITH fl='productId,productName':")
print("-"*80)
result2 = get_products({
    "st": "NSW",
    "size": "2",
    "fl": "productId,productName,productCategoryId"
})

if result2 and 'products' in result2:
    for i, product in enumerate(result2['products'], 1):
        print(f"Product {i}:")
        for key, value in product.items():
            val_str = str(value)[:100]
            print(f"  {key}: {val_str}")
        print()

print("="*80)
print("CONCLUSION: Check actual field names used by API")
print("="*80)
