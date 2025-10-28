"""
Debug script to examine ATDW product structure and find where attributes are stored.
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from datasources.atdw_client import ATDWClient


def main():
    print("ATDW Product Structure Debugger")
    print("=" * 80)

    client = ATDWClient()

    # Fetch one product from accommodation
    print("\nFetching sample accommodation product...")
    products = client.search_products(
        categories=['ACCOMM'],
        paginate=False,
        page_size=1
    )

    if not products:
        print("No products found!")
        return

    product = products[0]

    # Save full product structure
    output_file = Path(__file__).parent.parent / 'data' / 'atdw_sample_product_structure.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(product, f, indent=2, ensure_ascii=False)

    print(f"\nSample product saved to: {output_file}")

    # Print top-level keys
    print("\n" + "=" * 80)
    print("TOP-LEVEL KEYS:")
    print("=" * 80)
    for key in sorted(product.keys()):
        value = product[key]
        value_type = type(value).__name__

        if isinstance(value, (list, dict)):
            if isinstance(value, list):
                length = len(value)
                if length > 0:
                    first_type = type(value[0]).__name__
                    print(f"  {key}: {value_type} ({length} items, first type: {first_type})")
                else:
                    print(f"  {key}: {value_type} (empty)")
            else:
                print(f"  {key}: {value_type} ({len(value)} keys)")
        else:
            value_str = str(value)[:50]
            print(f"  {key}: {value_type} = {value_str}")

    # Look for attribute-related keys
    print("\n" + "=" * 80)
    print("ATTRIBUTE-RELATED KEYS:")
    print("=" * 80)

    attr_keys = [k for k in product.keys() if 'attr' in k.lower() or 'feature' in k.lower() or 'amenity' in k.lower()]

    if attr_keys:
        for key in attr_keys:
            print(f"\n{key}:")
            print(f"  Type: {type(product[key]).__name__}")
            print(f"  Value: {json.dumps(product[key], indent=4)[:500]}")
    else:
        print("No obvious attribute keys found in top-level structure")

    # Check for nested structures
    print("\n" + "=" * 80)
    print("CHECKING FOR NESTED ATTRIBUTE STRUCTURES:")
    print("=" * 80)

    for key, value in product.items():
        if isinstance(value, dict):
            # Check if this dict contains attribute-like data
            nested_attr_keys = [k for k in value.keys() if 'attr' in k.lower() or 'feature' in k.lower()]
            if nested_attr_keys:
                print(f"\nFound in {key}:")
                for nested_key in nested_attr_keys:
                    print(f"  {nested_key}: {type(value[nested_key]).__name__}")


if __name__ == '__main__':
    main()
