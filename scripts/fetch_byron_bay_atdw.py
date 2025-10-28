"""
Fetch all tourism products from ATDW for Byron Bay.

Uses ATDW ATLAS2 API to fetch all tourism products within 15km radius
of Byron Bay center coordinates with full pagination support.
"""

import sys
import csv
import os
from datetime import datetime
from collections import Counter

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.datasources import ATDWClient


def main():
    # Byron Bay coordinates and search parameters
    BYRON_LAT = -28.6450
    BYRON_LNG = 153.6050
    RADIUS_KM = 15
    API_KEY = "ee37502ebe584551a7eeb42bf2e26450"

    print("=" * 80)
    print("ATDW Tourism Data Extraction - Byron Bay")
    print("=" * 80)
    print(f"\nSearch Parameters:")
    print(f"  Location: Byron Bay ({BYRON_LAT}, {BYRON_LNG})")
    print(f"  Radius: {RADIUS_KM}km")
    print(f"  Page Size: 1000 (optimal for ATDW)")
    print(f"  Pagination: Enabled (fetch all results)")
    print()

    # Initialize client
    print("Initializing ATDW client...")
    client = ATDWClient(api_key=API_KEY)

    # Fetch all products with geospatial search
    print(f"Fetching tourism products within {RADIUS_KM}km of Byron Bay...")
    print("(This may take several minutes for large datasets)\n")

    start_time = datetime.now()

    try:
        products = client.search_by_location(
            lat=BYRON_LAT,
            lng=BYRON_LNG,
            radius_km=RADIUS_KM,
            page_size=1000,  # Optimal page size
            paginate=True    # Fetch all pages
        )

        elapsed = (datetime.now() - start_time).total_seconds()

        print(f"\nFetch completed in {elapsed:.1f}s")
        print(f"  Total products: {len(products)}")

        if not products:
            print("\nNo products found in search area.")
            return

        # Calculate statistics
        print("\n" + "=" * 80)
        print("DATA ANALYSIS")
        print("=" * 80)

        # Category breakdown
        categories = [p.get('productCategoryId', 'UNKNOWN') for p in products]
        category_counts = Counter(categories)

        print("\nCategory Breakdown:")
        for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(products)) * 100
            print(f"  {category:20s} {count:5d} ({percentage:5.1f}%)")

        # Data completeness analysis (for search endpoint fields only)
        fields_to_check = {
            'productName': 'Name',
            'productDescription': 'Description',
            'productImage': 'Image',
            'addresses': 'Address',
            'productCategoryId': 'Category',
            'boundary': 'Coordinates'
        }

        print("\nData Completeness (Search Endpoint):")
        for field, label in fields_to_check.items():
            count = sum(1 for p in products if p.get(field))
            percentage = (count / len(products)) * 100
            print(f"  {label:20s} {count:5d}/{len(products)} ({percentage:5.1f}%)")

        print("\nNote: Search endpoint returns summary data only.")
        print("Full details (phone, website, email) require get_product() calls.")

        # Export to CSV
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_file = f"data/byron_bay_atdw_{timestamp}.csv"

        print(f"\n" + "=" * 80)
        print("EXPORTING TO CSV")
        print("=" * 80)
        print(f"\nOutput file: {csv_file}")

        # Define CSV columns (based on search endpoint fields)
        columns = [
            'product_id',
            'product_number',
            'product_name',
            'category',
            'description',
            'status',
            'owner_org',
            'expiry_date',
            'update_date',
            'address_line',
            'address_line2',
            'city',
            'state',
            'postcode',
            'country',
            'area',
            'region',
            'latitude',
            'longitude',
            'image_url',
            'distance_km'
        ]

        # Write CSV with UTF-8-BOM for Excel compatibility
        with open(csv_file, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()

            for p in products:
                # Extract address (first address if multiple)
                address = p.get('addresses', [{}])[0] if p.get('addresses') else {}

                # Extract coordinates from boundary field (format: "lat,lng")
                boundary = p.get('boundary', '')
                lat, lng = None, None
                if boundary and ',' in boundary:
                    parts = boundary.split(',')
                    if len(parts) == 2:
                        try:
                            lat = float(parts[0])
                            lng = float(parts[1])
                        except ValueError:
                            pass

                # Extract area and region (may be lists)
                area = address.get('area', [])
                region = address.get('region', [])
                area_str = ', '.join(area) if isinstance(area, list) else str(area) if area else ''
                region_str = ', '.join(region) if isinstance(region, list) else str(region) if region else ''

                writer.writerow({
                    'product_id': p.get('productId'),
                    'product_number': p.get('productNumber'),
                    'product_name': p.get('productName'),
                    'category': p.get('productCategoryId'),
                    'description': p.get('productDescription', '').replace('\n', ' ').replace('\r', '')[:1000],  # Truncate very long descriptions
                    'status': p.get('status'),
                    'owner_org': p.get('owningOrganisationName'),
                    'expiry_date': p.get('atdwExpiryDate'),
                    'update_date': p.get('productUpdateDate'),
                    'address_line': address.get('address_line'),
                    'address_line2': address.get('address_line2'),
                    'city': address.get('city'),
                    'state': address.get('state'),
                    'postcode': address.get('postcode'),
                    'country': address.get('country'),
                    'area': area_str,
                    'region': region_str,
                    'latitude': lat,
                    'longitude': lng,
                    'image_url': p.get('productImage'),
                    'distance_km': round(p.get('distanceToLocation', 0), 2)
                })

        # Get file size
        file_size_bytes = os.path.getsize(csv_file)
        file_size_kb = file_size_bytes / 1024

        print(f"Export completed")
        print(f"  File size: {file_size_kb:.1f} KB ({file_size_bytes:,} bytes)")
        print(f"  Rows: {len(products) + 1} (including header)")
        print(f"  Columns: {len(columns)}")

        # API call estimation
        estimated_api_calls = (len(products) // 1000) + 1

        print(f"\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"\nSuccessfully fetched {len(products):,} tourism products from ATDW")
        print(f"  Search area: {RADIUS_KM}km radius around Byron Bay")
        print(f"  Execution time: {elapsed:.1f}s")
        print(f"  Estimated API calls: ~{estimated_api_calls}")
        print(f"  Output file: {csv_file} ({file_size_kb:.1f} KB)")
        print(f"\nTop categories:")
        for category, count in list(category_counts.most_common(5)):
            percentage = (count / len(products)) * 100
            print(f"  {category}: {count} ({percentage:.1f}%)")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
