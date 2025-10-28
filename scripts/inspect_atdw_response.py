"""
Inspect ATDW API response structure to understand available fields.
"""

import sys
import os
import json

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.datasources import ATDWClient


def main():
    BYRON_LAT = -28.6450
    BYRON_LNG = 153.6050
    RADIUS_KM = 15
    API_KEY = "ee37502ebe584551a7eeb42bf2e26450"

    print("Fetching sample products to inspect structure...")
    client = ATDWClient(api_key=API_KEY)

    # Fetch just first page to inspect
    products = client.search_by_location(
        lat=BYRON_LAT,
        lng=BYRON_LNG,
        radius_km=RADIUS_KM,
        page_size=5,
        paginate=False
    )

    if products:
        print(f"\nFound {len(products)} sample products")
        print("\n" + "=" * 80)
        print("SAMPLE PRODUCT STRUCTURE")
        print("=" * 80)

        # Show first product in detail
        print(f"\nProduct 1: {products[0].get('productName', 'N/A')}")
        print("\nAll available fields:")
        print(json.dumps(products[0], indent=2, default=str))

        print("\n" + "=" * 80)
        print("TOP-LEVEL KEYS ACROSS ALL SAMPLES")
        print("=" * 80)

        # Collect all unique keys
        all_keys = set()
        for p in products:
            all_keys.update(p.keys())

        print(f"\nFound {len(all_keys)} unique top-level keys:")
        for key in sorted(all_keys):
            print(f"  - {key}")
    else:
        print("No products found")


if __name__ == '__main__':
    main()
