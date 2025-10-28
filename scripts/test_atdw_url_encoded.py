"""
Test ATDW API with proper URL encoding and investigate actual working parameters.
"""

import json
from urllib.request import urlopen, Request
from urllib.parse import urlencode, quote
import time

API_KEY = "ee37502ebe584551a7eeb42bf2e26450"
BASE_URL = "https://atlas.atdw-online.com.au/api/atlas/products"

def get_products(params_dict, description="", return_sample=False):
    """Get products with URL-encoded parameters."""
    # Build query string with proper encoding
    query_params = {"key": API_KEY, "size": 5 if return_sample else 1, "out": "json"}
    query_params.update(params_dict)

    query_string = urlencode(query_params)
    url = f"{BASE_URL}?{query_string}"

    req = Request(url)
    req.add_header('User-Agent', 'FATHOM-DataPlatform/1.0')

    try:
        with urlopen(req, timeout=30) as response:
            data = response.read()
            text = data.decode('utf-16')
            result = json.loads(text)
            count = result.get('numberOfResults', 0)
            print(f"  {description:<45} {count:>10,}")

            if return_sample:
                return result
            return count
    except Exception as e:
        print(f"  {description:<45} ERROR: {str(e)[:50]}")
        return None

print("="*80)
print("ATDW API: URL-Encoded Parameter Testing")
print("="*80)

# Baseline
print("\n[BASELINE]")
print("-"*80)
baseline = get_products({}, "No filters")
time.sleep(1)

# TEST 1: Location with URL encoding
print("\n[TEST 1] Location Searches (URL encoded):")
print("-"*80)
get_products({"city": "Yarra Ranges"}, "city=Yarra Ranges")
time.sleep(1)
get_products({"dest": "Yarra Ranges"}, "dest=Yarra Ranges")
time.sleep(1)
get_products({"area": "Yarra Ranges"}, "area=Yarra Ranges")
time.sleep(1)
get_products({"locality": "Yarra Ranges"}, "locality=Yarra Ranges")
time.sleep(1)

# TEST 2: Sample product to check status field values
print("\n[TEST 2] Sample Products to Check Status Values:")
print("-"*80)
print("Fetching 5 sample products to inspect status field...")
sample = get_products({"st": "NSW"}, "NSW sample products", return_sample=True)

if sample and 'products' in sample:
    print("\nStatus values found in sample:")
    statuses = set()
    for product in sample['products'][:5]:
        status = product.get('status', 'N/A')
        statuses.add(status)
        print(f"  - Product {product.get('product_id')}: status = '{status}'")

    print(f"\nUnique status values: {statuses}")

    # Now test with actual status value
    if statuses:
        print("\n[TEST 3] Testing with actual status values:")
        print("-"*80)
        for status_val in statuses:
            time.sleep(1)
            get_products({"st": "NSW", "status": status_val}, f"NSW with status='{status_val}'")

# TEST 4: Check if there's a separate inactive/expired parameter
print("\n[TEST 4] Testing Other Status-Related Parameters:")
print("-"*80)
get_products({"st": "NSW", "active": "true"}, "NSW - active=true")
time.sleep(1)
get_products({"st": "NSW", "active": "false"}, "NSW - active=false")
time.sleep(1)
get_products({"st": "NSW", "expired": "false"}, "NSW - expired=false")
time.sleep(1)
get_products({"st": "NSW", "expired": "true"}, "NSW - expired=true")
time.sleep(1)

# TEST 5: Fetch sample to see all available fields
print("\n[TEST 5] Check what fields are returned:")
print("-"*80)
sample_nsw = get_products({"st": "NSW", "size": "1"}, "NSW - 1 product sample", return_sample=True)
if sample_nsw and 'products' in sample_nsw and sample_nsw['products']:
    product = sample_nsw['products'][0]
    print(f"\nSample product fields:")
    print(f"  product_id: {product.get('product_id')}")
    print(f"  product_name: {product.get('product_name')}")
    print(f"  status: {product.get('status')}")
    print(f"  atdw_expiry_date: {product.get('atdw_expiry_date')}")
    print(f"  product_update_date: {product.get('product_update_date')}")

print("\n" + "="*80)
print("SUMMARY:")
print("="*80)
print("Based on testing:")
print("1. Check if location parameters work with URL encoding")
print("2. Identify actual status field values (A, I, or something else)")
print("3. Determine if API returns only active products by default")
print("4. Check if we need special parameter to get inactive products")
print("="*80)
