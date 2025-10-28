"""
Extract all tourism products for Byron Bay from ATDW (Australian Tourism Data Warehouse).

This script fetches comprehensive tourism data including:
- Accommodation
- Attractions
- Tours
- Restaurants
- Events
- Transport services
- General services
- Hire services
- Destinations
- Journeys

Uses geospatial search with 15km radius from Byron Bay coordinates.
"""

import csv
import sys
from datetime import datetime
from typing import Dict, List
from collections import Counter

# Add parent directory to path for imports
sys.path.insert(0, 'E:\\Projects\\Coding\\Fathom')

from src.datasources import ATDWClient


def flatten_product(product: Dict) -> Dict:
    """
    Flatten ATDW product structure for CSV export.

    Args:
        product: Product dictionary from ATDW API

    Returns:
        Flattened dictionary suitable for CSV writing
    """
    flat = {}

    # Core identifiers
    flat['product_id'] = product.get('productId', '')
    flat['product_name'] = product.get('productName', '')
    flat['product_category'] = product.get('productCategoryId', '')

    # Location data
    location = product.get('location', {})
    flat['address'] = location.get('address1', '')
    flat['suburb'] = location.get('suburb', '')
    flat['state'] = location.get('state', '')
    flat['postcode'] = location.get('postcode', '')
    flat['country'] = location.get('country', '')
    flat['latitude'] = location.get('latitude', '')
    flat['longitude'] = location.get('longitude', '')

    # Contact details
    contact = product.get('contactDetails', {})
    flat['phone'] = contact.get('phone', '')
    flat['mobile'] = contact.get('mobile', '')
    flat['email'] = contact.get('email', '')
    flat['website'] = contact.get('websiteUrl', '')
    flat['facebook'] = contact.get('facebookUrl', '')
    flat['instagram'] = contact.get('instagramUrl', '')
    flat['twitter'] = contact.get('twitterUrl', '')

    # Description
    flat['description'] = product.get('productDescription', '')

    # Rating
    flat['star_rating'] = product.get('starRating', '')

    # Rate information
    rate_info = product.get('rateFrom', {})
    flat['rate_from'] = rate_info.get('amount', '') if rate_info else ''
    flat['rate_currency'] = rate_info.get('currency', '') if rate_info else ''

    # Multimedia
    images = product.get('multimedia', {}).get('images', [])
    flat['image_count'] = len(images)
    flat['primary_image'] = images[0].get('imageUrl', '') if images else ''

    # Timestamps
    flat['created'] = product.get('created', '')
    flat['updated'] = product.get('updated', '')

    return flat


def main():
    """Fetch all Byron Bay tourism products from ATDW."""

    # Byron Bay coordinates
    BYRON_LAT = -28.6450
    BYRON_LNG = 153.6050
    RADIUS_KM = 15

    print("ATDW Byron Bay Tourism Data Extraction")
    print("=" * 60)
    print(f"Search Parameters:")
    print(f"  Location: Byron Bay (lat: {BYRON_LAT}, lng: {BYRON_LNG})")
    print(f"  Radius: {RADIUS_KM}km")
    print(f"  Categories: ALL")
    print()

    # Initialize client
    try:
        client = ATDWClient()
    except ValueError as e:
        print(f"Error: {e}")
        print("Please set ATDW_API_KEY environment variable")
        sys.exit(1)

    # Fetch all products within radius (no category filter = all categories)
    print("Fetching products from ATDW...")
    print("(Using pagination with 1000 results per page)")
    print()

    start_time = datetime.now()

    try:
        products = client.search_products(
            lat=BYRON_LAT,
            lng=BYRON_LNG,
            radius_km=RADIUS_KM,
            paginate=True,  # Fetch all pages
            page_size=1000  # Optimal page size
        )
    except Exception as e:
        print(f"Error fetching products: {e}")
        sys.exit(1)

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    print(f"Fetched {len(products)} products in {duration:.1f} seconds")
    print()

    # Category breakdown
    category_counts = Counter(p.get('productCategoryId', 'UNKNOWN') for p in products)

    print("Category Breakdown:")
    print("-" * 60)
    for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {category:30s} {count:5d} ({count/len(products)*100:5.1f}%)")
    print()

    # Data completeness analysis
    fields_to_check = {
        'website': lambda p: bool(p.get('contactDetails', {}).get('websiteUrl')),
        'phone': lambda p: bool(p.get('contactDetails', {}).get('phone')),
        'email': lambda p: bool(p.get('contactDetails', {}).get('email')),
        'description': lambda p: bool(p.get('productDescription')),
        'images': lambda p: len(p.get('multimedia', {}).get('images', [])) > 0,
        'coordinates': lambda p: bool(p.get('location', {}).get('latitude')),
        'star_rating': lambda p: bool(p.get('starRating')),
    }

    print("Data Completeness:")
    print("-" * 60)
    for field_name, checker in fields_to_check.items():
        count = sum(1 for p in products if checker(p))
        pct = count / len(products) * 100 if products else 0
        print(f"  {field_name:20s} {count:5d} / {len(products)} ({pct:5.1f}%)")
    print()

    # Export to CSV
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    csv_file = f"E:\\Projects\\Coding\\Fathom\\data\\byron_bay_atdw_{timestamp}.csv"

    print(f"Exporting to CSV: {csv_file}")

    # Flatten all products
    flattened = [flatten_product(p) for p in products]

    if flattened:
        # Get all unique keys across all products
        fieldnames = set()
        for item in flattened:
            fieldnames.update(item.keys())
        fieldnames = sorted(fieldnames)

        # Write CSV with UTF-8-BOM for Excel compatibility
        with open(csv_file, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(flattened)

        print(f"Successfully exported {len(flattened)} products")
    else:
        print("No products to export")

    print()
    print("Summary:")
    print("-" * 60)
    print(f"Total products: {len(products)}")
    print(f"API calls made: ~{(len(products) // 1000) + 1}")
    print(f"Duration: {duration:.1f} seconds")
    print(f"Output file: {csv_file}")
    print()


if __name__ == '__main__':
    main()
