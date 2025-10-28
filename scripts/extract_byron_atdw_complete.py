"""
Byron Bay ATDW extraction with full contact fields.

Extracts tourism products from ATDW API with comprehensive contact information:
- Phone numbers (comms_ph)
- Email addresses (comms_em)
- Website URLs (comms_url)
- Booking URLs (comms_burl)
"""

import sys
import os
import csv
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.datasources import ATDWClient


def main():
    """Extract Byron Bay tourism products with full contact fields."""

    # Configuration
    API_KEY = "ee37502ebe584551a7eeb42bf2e26450"
    LAT = -28.6450
    LNG = 153.6050
    RADIUS_KM = 15
    PAGE_SIZE = 1000

    # Fields to request (including contact fields)
    FIELDS = [
        'product_id', 'product_number', 'product_name', 'product_category',
        'product_description', 'product_image', 'address',
        'comms_ph',     # Phone number
        'comms_em',     # Email
        'comms_url',    # Website
        'comms_burl',   # Booking URL
        'rate_from', 'rate_to', 'starrating', 'number_of_rooms',
        'next_occurrence', 'status', 'boundary'
    ]

    # Output file with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(
        os.path.dirname(__file__),
        '..',
        'data',
        f'byron_bay_atdw_complete_{timestamp}.csv'
    )
    output_file = os.path.abspath(output_file)

    print(f"ATDW Byron Bay Extraction")
    print(f"=" * 60)
    print(f"API Key: {API_KEY[:8]}...")
    print(f"Location: {LAT}, {LNG}")
    print(f"Radius: {RADIUS_KM}km")
    print(f"Page size: {PAGE_SIZE}")
    print(f"Fields requested: {len(FIELDS)}")
    print(f"Output: {output_file}")
    print()

    # Initialize client
    client = ATDWClient(api_key=API_KEY)

    # Search products
    print(f"Fetching products...")
    start_time = datetime.now()

    products = client.search_products(
        lat=LAT,
        lng=LNG,
        radius_km=RADIUS_KM,
        fields=FIELDS,
        page_size=PAGE_SIZE,
        paginate=True
    )

    elapsed = (datetime.now() - start_time).total_seconds()
    print(f"Fetched {len(products)} products in {elapsed:.1f}s")
    print()

    if not products:
        print("No products found")
        return

    # Analyze contact data completeness
    contact_stats = {
        'phone': sum(1 for p in products if p.get('comms_ph')),
        'email': sum(1 for p in products if p.get('comms_em')),
        'website': sum(1 for p in products if p.get('comms_url')),
        'booking_url': sum(1 for p in products if p.get('comms_burl')),
    }

    print(f"Contact Data Completeness:")
    print(f"  Phone:       {contact_stats['phone']:4d} / {len(products)} ({contact_stats['phone']/len(products)*100:.1f}%)")
    print(f"  Email:       {contact_stats['email']:4d} / {len(products)} ({contact_stats['email']/len(products)*100:.1f}%)")
    print(f"  Website:     {contact_stats['website']:4d} / {len(products)} ({contact_stats['website']/len(products)*100:.1f}%)")
    print(f"  Booking URL: {contact_stats['booking_url']:4d} / {len(products)} ({contact_stats['booking_url']/len(products)*100:.1f}%)")
    print()

    # Export to CSV
    print(f"Exporting to CSV...")

    # Determine all unique fields in results
    all_fields = set()
    for product in products:
        all_fields.update(product.keys())

    # Sort fields for consistent ordering
    fieldnames = sorted(all_fields)

    with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(products)

    # Get file size
    file_size = os.path.getsize(output_file)
    file_size_mb = file_size / (1024 * 1024)

    print(f"Exported {len(products)} products")
    print(f"File: {output_file}")
    print(f"Size: {file_size_mb:.2f} MB")
    print()
    print("Done!")


if __name__ == '__main__':
    main()
