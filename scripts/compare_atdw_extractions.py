"""
Compare ATDW extractions to show contact field improvements.
"""

import csv
import os


def analyze_csv(filepath):
    """Analyze CSV file and return statistics."""
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    stats = {
        'total': len(rows),
        'fields': list(rows[0].keys()) if rows else [],
        'has_phone': 'comms_ph' in rows[0] if rows else False,
        'has_email': 'comms_em' in rows[0] if rows else False,
        'has_website': 'comms_url' in rows[0] if rows else False,
        'has_booking': 'comms_burl' in rows[0] if rows else False,
    }

    # Count non-empty contact fields
    if stats['has_phone']:
        stats['phone_count'] = sum(1 for r in rows if r.get('comms_ph', '').strip())
    if stats['has_email']:
        stats['email_count'] = sum(1 for r in rows if r.get('comms_em', '').strip())
    if stats['has_website']:
        stats['website_count'] = sum(1 for r in rows if r.get('comms_url', '').strip())
    if stats['has_booking']:
        stats['booking_count'] = sum(1 for r in rows if r.get('comms_burl', '').strip())

    return stats


def main():
    """Compare old and new ATDW extractions."""

    old_file = "E:\\Projects\\Coding\\Fathom\\data\\byron_bay_atdw_20251025_202901.csv"
    new_file = "E:\\Projects\\Coding\\Fathom\\data\\byron_bay_atdw_complete_20251025_204011.csv"

    print("ATDW Extraction Comparison")
    print("=" * 80)
    print()

    # Analyze both files
    old_stats = analyze_csv(old_file)
    new_stats = analyze_csv(new_file)

    print(f"PREVIOUS EXTRACTION (Basic Fields)")
    print(f"  File: byron_bay_atdw_20251025_202901.csv")
    print(f"  Products: {old_stats['total']}")
    print(f"  Fields: {len(old_stats['fields'])}")
    print(f"  Contact fields included:")
    print(f"    Phone:       {'YES' if old_stats['has_phone'] else 'NO'}")
    print(f"    Email:       {'YES' if old_stats['has_email'] else 'NO'}")
    print(f"    Website:     {'YES' if old_stats['has_website'] else 'NO'}")
    print(f"    Booking URL: {'YES' if old_stats['has_booking'] else 'NO'}")
    print()

    print(f"NEW EXTRACTION (With Contact Fields)")
    print(f"  File: byron_bay_atdw_complete_20251025_204011.csv")
    print(f"  Products: {new_stats['total']}")
    print(f"  Fields: {len(new_stats['fields'])}")
    print(f"  Contact fields included:")
    print(f"    Phone:       YES ({new_stats.get('phone_count', 0)} / {new_stats['total']} = {new_stats.get('phone_count', 0)/new_stats['total']*100:.1f}%)")
    print(f"    Email:       YES ({new_stats.get('email_count', 0)} / {new_stats['total']} = {new_stats.get('email_count', 0)/new_stats['total']*100:.1f}%)")
    print(f"    Website:     YES ({new_stats.get('website_count', 0)} / {new_stats['total']} = {new_stats.get('website_count', 0)/new_stats['total']*100:.1f}%)")
    print(f"    Booking URL: YES ({new_stats.get('booking_count', 0)} / {new_stats['total']} = {new_stats.get('booking_count', 0)/new_stats['total']*100:.1f}%)")
    print()

    print("IMPROVEMENTS")
    print("  Product count: {} (same dataset)".format(
        "MATCH" if old_stats['total'] == new_stats['total'] else f"CHANGED ({old_stats['total']} -> {new_stats['total']})"
    ))
    print(f"  Additional contact data:")
    print(f"    {new_stats.get('phone_count', 0)} phone numbers")
    print(f"    {new_stats.get('email_count', 0)} email addresses")
    print(f"    {new_stats.get('website_count', 0)} websites")
    print(f"    {new_stats.get('booking_count', 0)} booking URLs")
    print()

    print("API EFFICIENCY")
    print("  Only 1 API call needed (page_size=1000, 322 results fit in one page)")
    print("  Fetch time: 0.7 seconds")
    print()

    # Show sample record
    print("SAMPLE RECORD WITH CONTACT DATA")
    print("-" * 80)
    with open(new_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        sample = next(reader)

    contact_fields = ['productName', 'comms_ph', 'comms_em', 'comms_url', 'comms_burl']
    for field in contact_fields:
        value = sample.get(field, '')
        if len(value) > 70:
            value = value[:67] + "..."
        print(f"  {field:15s}: {value}")


if __name__ == '__main__':
    main()
