"""
Test ATDW extraction on a single state (ACT - smallest state).

This tests the extraction logic before running the full national extraction.
"""

import sys
import os
import csv
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.datasources import ATDWClient


# Fields to request (including contact fields)
FIELDS = [
    'product_id', 'product_number', 'product_name', 'product_category_id',
    'product_description', 'product_image', 'addresses',
    'comms_ph', 'comms_em', 'comms_url', 'comms_burl',
    'rate_from', 'rate_to', 'starrating', 'number_of_rooms',
    'status', 'product_update_date', 'next_occurrence', 'boundary',
    'owning_organisation_name', 'atdw_expiry_date'
]


def test_single_state():
    """Test extraction on ACT (smallest state)."""
    print("="*80)
    print("ATDW SINGLE STATE TEST - ACT (Australian Capital Territory)")
    print("="*80)

    # Initialize client
    client = ATDWClient()

    # Test extraction
    print("\nFetching ACT products (page_size=5000)...")
    start_time = datetime.now()

    products = client.search_products(
        state='ACT',
        fields=FIELDS,
        page_size=5000,
        paginate=True
    )

    duration = (datetime.now() - start_time).total_seconds()

    print(f"\nResults:")
    print(f"- Products fetched: {len(products)}")
    print(f"- Duration: {duration:.2f}s")
    print(f"- API calls: ~{len(products) // 5000 + 1}")

    if products:
        # Analyze first product
        print(f"\nFirst product sample:")
        first = products[0]
        print(f"  ID: {first.get('productId')}")
        print(f"  Name: {first.get('productName')}")
        print(f"  Category: {first.get('productCategoryId')}")
        print(f"  Phone: {first.get('comms_ph', 'N/A')}")
        print(f"  Email: {first.get('comms_em', 'N/A')}")
        print(f"  Website: {first.get('comms_url', 'N/A')}")

        # Category breakdown
        categories = {}
        for p in products:
            cat = p.get('productCategoryId', 'UNKNOWN')
            categories[cat] = categories.get(cat, 0) + 1

        print(f"\nCategory breakdown:")
        for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            print(f"  {cat}: {count}")

        # Contact completeness
        phone_count = sum(1 for p in products if p.get('comms_ph'))
        email_count = sum(1 for p in products if p.get('comms_em'))
        website_count = sum(1 for p in products if p.get('comms_url'))

        print(f"\nContact data completeness:")
        print(f"  Phone: {phone_count}/{len(products)} ({phone_count/len(products)*100:.1f}%)")
        print(f"  Email: {email_count}/{len(products)} ({email_count/len(products)*100:.1f}%)")
        print(f"  Website: {website_count}/{len(products)} ({website_count/len(products)*100:.1f}%)")

        # Save sample
        output_file = 'data/atdw_act_test.csv'
        os.makedirs('data', exist_ok=True)

        # Get all unique keys
        all_keys = set()
        for product in products:
            all_keys.update(product.keys())

        with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=sorted(all_keys))
            writer.writeheader()
            writer.writerows(products)

        print(f"\nSaved to {output_file}")

    print("\n" + "="*80)
    print("TEST COMPLETE - Ready for full national extraction")
    print("="*80)


if __name__ == '__main__':
    test_single_state()
