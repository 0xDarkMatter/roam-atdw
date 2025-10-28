"""
Analyze the ATDW extraction CSV files to check data quality.
"""

import csv
from pathlib import Path

CSV_FILE = Path("E:/Projects/Coding/Fathom/data/atdw_national/atdw_nsw_20251026_073327.csv")

print("="*80)
print("ATDW Extraction Data Analysis - NSW")
print("="*80)

with open(CSV_FILE, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)

    # Read all rows
    rows = list(reader)

    print(f"\nTotal rows: {len(rows):,}")

    # Count columns
    if rows:
        columns = list(rows[0].keys())
        print(f"Total columns: {len(columns)}")
        print(f"\nColumns:")
        for col in columns:
            print(f"  - {col}")

    # Check for unique productIds
    product_ids = [row.get('productId', '') for row in rows]
    unique_ids = set(product_ids)
    print(f"\nUnique productIds: {len(unique_ids):,}")
    print(f"Duplicate rows: {len(rows) - len(unique_ids):,}")

    # Check data completeness
    print(f"\n{'='*80}")
    print("Data Completeness Analysis:")
    print("="*80)

    fields_to_check = ['productId', 'productName', 'comms_ph', 'comms_em', 'comms_url',
                       'boundary', 'productDescription']

    for field in fields_to_check:
        non_empty = sum(1 for row in rows if row.get(field, '').strip())
        pct = (non_empty / len(rows) * 100) if rows else 0
        print(f"{field:<25} {non_empty:>10,} / {len(rows):>10,}  ({pct:>5.1f}%)")

    # Show sample rows
    print(f"\n{'='*80}")
    print("Sample Products (first 5):")
    print("="*80)

    for i, row in enumerate(rows[:5], 1):
        print(f"\nProduct {i}:")
        print(f"  ID: {row.get('productId', 'N/A')}")
        print(f"  Name: {row.get('productName', 'N/A')[:60]}")
        print(f"  Phone: {row.get('comms_ph', 'N/A')}")
        print(f"  Email: {row.get('comms_em', 'N/A')}")
        print(f"  Website: {row.get('comms_url', 'N/A')[:60]}")
        print(f"  Status: {row.get('status', 'N/A')}")

print("\n" + "="*80)
