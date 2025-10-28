"""
Debug script to see what fields ATDW actually returns.
"""

import sys
import os
import json

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.datasources import ATDWClient


def debug_fields():
    """Check what fields are actually returned."""
    print("="*80)
    print("ATDW Field Debug")
    print("="*80)

    client = ATDWClient()

    # Test 1: Default fields (no field list specified)
    print("\nTest 1: Default fields (no fl parameter)")
    print("-"*80)
    products = client.search_products(
        state='ACT',
        page_size=1,
        paginate=False
    )

    if products:
        print("Fields returned:")
        for key in sorted(products[0].keys()):
            value = products[0][key]
            if isinstance(value, (dict, list)):
                print(f"  {key}: {type(value).__name__}")
            else:
                print(f"  {key}: {str(value)[:50]}")

    # Test 2: Request contact fields specifically
    print("\n\nTest 2: With contact fields requested")
    print("-"*80)
    products = client.search_products(
        state='ACT',
        fields=['product_name', 'comms', 'comms_ph', 'comms_em', 'comms_url'],
        page_size=1,
        paginate=False
    )

    if products:
        print("Fields returned:")
        for key in sorted(products[0].keys()):
            value = products[0][key]
            if isinstance(value, (dict, list)):
                print(f"  {key}: {type(value).__name__}")
                if isinstance(value, dict):
                    for k, v in value.items():
                        print(f"    {k}: {v}")
            else:
                print(f"  {key}: {str(value)[:50]}")

        print("\nFull product data:")
        print(json.dumps(products[0], indent=2))

    print("\n" + "="*80)


if __name__ == '__main__':
    debug_fields()
