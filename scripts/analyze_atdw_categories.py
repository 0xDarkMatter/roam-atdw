#!/usr/bin/env python3
"""
Analyze ATDW product categories in detail.
"""

import csv
from collections import Counter
from pathlib import Path

def main():
    consolidated_file = Path('data/atdw_national/atdw_australia_complete_20251026_070730.csv')

    print("="*80)
    print("ATDW CATEGORY ANALYSIS")
    print("="*80)

    categories = Counter()
    states = Counter()
    sample_products = []

    with open(consolidated_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)

        # Get all column names
        fieldnames = reader.fieldnames
        print(f"\nAvailable columns ({len(fieldnames)}):")
        for col in sorted(fieldnames):
            print(f"  - {col}")

        print(f"\nAnalyzing products...")

        for i, row in enumerate(reader):
            # Track categories
            cat_id = row.get('productCategoryId', '')
            if cat_id:
                categories[cat_id] += 1

            # Track states
            state = row.get('state', '')
            if state:
                states[state] += 1

            # Save first 5 products as samples
            if i < 5:
                sample_products.append(row)

    print(f"\nTotal products analyzed: {sum(categories.values()):,}")

    print(f"\n{'='*80}")
    print("PRODUCT CATEGORY BREAKDOWN")
    print(f"{'='*80}")

    for cat, count in categories.most_common(20):
        pct = count / sum(categories.values()) * 100
        print(f"{cat:<40} {count:>8,} ({pct:>5.1f}%)")

    print(f"\n{'='*80}")
    print("STATE BREAKDOWN")
    print(f"{'='*80}")

    for state, count in states.most_common():
        pct = count / sum(states.values()) * 100
        print(f"{state:<10} {count:>8,} ({pct:>5.1f}%)")

    print(f"\n{'='*80}")
    print("SAMPLE PRODUCTS")
    print(f"{'='*80}")

    for i, product in enumerate(sample_products, 1):
        print(f"\nProduct {i}:")
        print(f"  ID: {product.get('productId', 'N/A')}")
        print(f"  Name: {product.get('productName', 'N/A')[:60]}")
        print(f"  Category: {product.get('productCategoryId', 'N/A')}")
        print(f"  State: {product.get('state', 'N/A')}")
        print(f"  City: {product.get('city', 'N/A')}")
        print(f"  Phone: {product.get('comms_ph', 'N/A')}")
        print(f"  Email: {product.get('comms_em', 'N/A')}")
        print(f"  Website: {product.get('comms_url', 'N/A')[:60]}")

if __name__ == '__main__':
    main()
