#!/usr/bin/env python3
"""
ATDW Complete Data Capture Test

Tests that we capture 100% of data from ATDW API and store it correctly in OTDB.

Usage:
    python scripts/test_atdw_complete_data_capture.py [--product-id PRODUCT_ID]

If no product ID provided, uses first VIC product.
"""

import os
import sys
import json
import argparse
from datetime import datetime
from typing import Dict, List, Any, Set
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.datasources.atdw_client import ATDWClient
from scripts.load_atdw_v2 import ATDWV2Loader


class ATDWDataCaptureTest:
    """Test complete data capture from ATDW to OTDB."""

    def __init__(self, conn, atdw_client: ATDWClient):
        self.conn = conn
        self.client = atdw_client
        self.atdw_data = None
        self.otdb_data = {}
        self.missing_fields = []
        self.coverage_report = {}

    def fetch_atdw_product(self, product_id: str) -> Dict:
        """Fetch complete product data from ATDW API."""
        print(f"\n{'='*70}")
        print(f"STEP 1: FETCHING PRODUCT FROM ATDW")
        print(f"{'='*70}\n")

        product = self.client.get_product(product_id)

        if not product:
            raise ValueError(f"Product {product_id} not found in ATDW")

        # Display ALL top-level fields
        print(f"Product ID: {product.get('productId')}")
        print(f"Product Name: {product.get('productName')}")
        print(f"\nTop-level fields found: {len(product.keys())}")

        # Categorize fields by type
        arrays = []
        objects = []
        scalars = []

        for key, value in product.items():
            if isinstance(value, list):
                arrays.append(f"  {key}: [{len(value)} items]")
            elif isinstance(value, dict):
                objects.append(f"  {key}: {{object}}")
            else:
                scalars.append(f"  {key}: {type(value).__name__}")

        print(f"\nArray fields ({len(arrays)}):")
        for item in sorted(arrays):
            print(item)

        print(f"\nObject fields ({len(objects)}):")
        for item in sorted(objects):
            print(item)

        print(f"\nScalar fields ({len(scalars)}):")
        for item in sorted(scalars):
            print(item)

        # Deep dive into important arrays
        print(f"\n{'='*70}")
        print("DETAILED FIELD ANALYSIS")
        print(f"{'='*70}\n")

        # Addresses
        addresses = product.get('addresses', [])
        print(f"ADDRESSES: {len(addresses)} found")
        if addresses:
            print(f"  Sample keys: {list(addresses[0].keys())[:10]}")

        # Communication
        communication = product.get('communication', [])
        print(f"COMMUNICATION: {len(communication)} found")
        if communication:
            print(f"  Sample keys: {list(communication[0].keys())}")

        # Multimedia
        multimedia = product.get('multimedia', [])
        print(f"MULTIMEDIA: {len(multimedia)} found")
        if multimedia:
            print(f"  Sample keys: {list(multimedia[0].keys())[:10]}")

        # Attributes
        attributes = product.get('attributes', [])
        print(f"ATTRIBUTES: {len(attributes)} found")
        if attributes:
            print(f"  Sample keys: {list(attributes[0].keys())}")

        # Services (rooms/tours)
        services = product.get('services', [])
        print(f"SERVICES: {len(services)} found")
        if services:
            print(f"  Sample keys: {list(services[0].keys())[:10]}")

        # Rates/Pricing
        rates = product.get('rates', [])
        print(f"RATES: {len(rates)} found")
        if rates:
            print(f"  Sample keys: {list(rates[0].keys())[:10]}")

        # Deals/Offers
        deals = product.get('deals', [])
        print(f"DEALS: {len(deals)} found")
        if deals:
            print(f"  Sample keys: {list(deals[0].keys())[:10]}")

        # Opening hours
        opening_hours = product.get('openingHours', [])
        print(f"OPENING HOURS: {len(opening_hours)} found")
        if opening_hours:
            print(f"  Sample keys: {list(opening_hours[0].keys())[:10]}")

        # Store for later comparison
        self.atdw_data = product

        # Calculate coverage statistics
        self.coverage_report['atdw_total_fields'] = len(product.keys())
        self.coverage_report['addresses_count'] = len(addresses)
        self.coverage_report['communication_count'] = len(communication)
        self.coverage_report['multimedia_count'] = len(multimedia)
        self.coverage_report['attributes_count'] = len(attributes)
        self.coverage_report['services_count'] = len(services)
        self.coverage_report['rates_count'] = len(rates)
        self.coverage_report['deals_count'] = len(deals)
        self.coverage_report['opening_hours_count'] = len(opening_hours)

        return product

    def load_to_otdb(self, product: Dict):
        """Load product into OTDB using V2 loader."""
        print(f"\n{'='*70}")
        print(f"STEP 2: LOADING INTO OTDB")
        print(f"{'='*70}\n")

        # Clear existing data for this product
        product_id = product.get('productId')
        with self.conn.cursor() as cur:
            cur.execute("""
                DELETE FROM products
                WHERE source = 'ATDW' AND external_id = %s
            """, (product_id,))
            self.conn.commit()
            print(f"Cleared existing product {product_id} from OTDB")

        # Load using V2 loader
        loader = ATDWV2Loader(self.conn, self.client, auto_accept_attributes=True)

        # Manually call _load_product to load just this one
        loader._load_product(product)

        print(f"\nProduct loaded successfully!")
        print(f"  Products processed: {loader.stats['products_processed']}")
        print(f"  Attributes added: {loader.stats['attributes_added']}")
        print(f"  Media added: {loader.stats['media_added']}")
        print(f"  Errors: {loader.stats['errors']}")

    def fetch_from_otdb(self, external_id: str):
        """Fetch product and all related data from OTDB."""
        print(f"\n{'='*70}")
        print(f"STEP 3: FETCHING FROM OTDB")
        print(f"{'='*70}\n")

        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Get main product
            cur.execute("""
                SELECT * FROM products
                WHERE source = 'ATDW' AND external_id = %s
            """, (external_id,))
            product = cur.fetchone()

            if not product:
                raise ValueError(f"Product {external_id} not found in OTDB")

            pid = product['product_id']
            self.otdb_data['product'] = dict(product)

            # Get addresses
            cur.execute("SELECT * FROM addresses WHERE product_id = %s", (pid,))
            self.otdb_data['addresses'] = [dict(row) for row in cur.fetchall()]

            # Get communication
            cur.execute("SELECT * FROM communication WHERE product_id = %s", (pid,))
            self.otdb_data['communication'] = [dict(row) for row in cur.fetchall()]

            # Get attributes
            cur.execute("""
                SELECT a.code, a.label, pa.*
                FROM product_attribute pa
                JOIN attribute_def a ON pa.attribute_id = a.attribute_id
                WHERE pa.product_id = %s
            """, (pid,))
            self.otdb_data['attributes'] = [dict(row) for row in cur.fetchall()]

            # Get media
            cur.execute("""
                SELECT pm.*, ma.url, ma.media_type, ma.meta
                FROM product_media pm
                JOIN media_asset ma ON pm.asset_id = ma.asset_id
                WHERE pm.product_id = %s
                ORDER BY pm.ordinal
            """, (pid,))
            self.otdb_data['media'] = [dict(row) for row in cur.fetchall()]

            # Get services
            cur.execute("SELECT * FROM services WHERE product_id = %s", (pid,))
            self.otdb_data['services'] = [dict(row) for row in cur.fetchall()]

            # Get rates
            cur.execute("SELECT * FROM rates WHERE product_id = %s", (pid,))
            self.otdb_data['rates'] = [dict(row) for row in cur.fetchall()]

            # Get deals
            cur.execute("SELECT * FROM deals WHERE product_id = %s", (pid,))
            self.otdb_data['deals'] = [dict(row) for row in cur.fetchall()]

        print(f"OTDB Data Retrieved:")
        print(f"  Product: {self.otdb_data['product']['product_name']}")
        print(f"  Addresses: {len(self.otdb_data['addresses'])}")
        print(f"  Communication: {len(self.otdb_data['communication'])}")
        print(f"  Attributes: {len(self.otdb_data['attributes'])}")
        print(f"  Media: {len(self.otdb_data['media'])}")
        print(f"  Services: {len(self.otdb_data['services'])}")
        print(f"  Rates: {len(self.otdb_data['rates'])}")
        print(f"  Deals: {len(self.otdb_data['deals'])}")

        # Update coverage report
        self.coverage_report['otdb_addresses_count'] = len(self.otdb_data['addresses'])
        self.coverage_report['otdb_communication_count'] = len(self.otdb_data['communication'])
        self.coverage_report['otdb_attributes_count'] = len(self.otdb_data['attributes'])
        self.coverage_report['otdb_media_count'] = len(self.otdb_data['media'])
        self.coverage_report['otdb_services_count'] = len(self.otdb_data['services'])
        self.coverage_report['otdb_rates_count'] = len(self.otdb_data['rates'])
        self.coverage_report['otdb_deals_count'] = len(self.otdb_data['deals'])

    def compare_data(self):
        """Compare ATDW vs OTDB data field by field."""
        print(f"\n{'='*70}")
        print(f"STEP 4: DATA COMPARISON - ATDW vs OTDB")
        print(f"{'='*70}\n")

        issues = []
        successes = []

        # Compare counts
        print("=== COUNT COMPARISON ===\n")

        comparisons = [
            ('Addresses', self.coverage_report['addresses_count'],
             self.coverage_report['otdb_addresses_count']),
            ('Communication', self.coverage_report['communication_count'],
             self.coverage_report['otdb_communication_count']),
            ('Attributes', self.coverage_report['attributes_count'],
             self.coverage_report['otdb_attributes_count']),
            ('Multimedia', self.coverage_report['multimedia_count'],
             self.coverage_report['otdb_media_count']),
            ('Services', self.coverage_report['services_count'],
             self.coverage_report['otdb_services_count']),
            ('Rates', self.coverage_report['rates_count'],
             self.coverage_report['otdb_rates_count']),
            ('Deals', self.coverage_report['deals_count'],
             self.coverage_report['otdb_deals_count']),
        ]

        for name, atdw_count, otdb_count in comparisons:
            match = "[OK]" if atdw_count == otdb_count else "[!!]"
            status = "OK" if atdw_count == otdb_count else "MISMATCH"
            print(f"{match} {name:20} ATDW: {atdw_count:3} | OTDB: {otdb_count:3} | {status}")

            if atdw_count != otdb_count:
                issues.append(f"{name} count mismatch: ATDW={atdw_count}, OTDB={otdb_count}")
            else:
                successes.append(f"{name} count matches")

        # Compare core product fields
        print(f"\n=== CORE PRODUCT FIELDS ===\n")

        product = self.otdb_data['product']
        atdw = self.atdw_data

        field_checks = [
            ('Product Name', atdw.get('productName'), product['product_name']),
            ('Category', atdw.get('productCategoryId'), product['category']),
            ('State', atdw.get('stateName'), product['state']),
            ('City', atdw.get('cityName'), product['city']),
            ('Region', atdw.get('areaName'), product['region']),
            ('Active Status', True, product['is_active']),  # All fetched products should be active
        ]

        for name, atdw_val, otdb_val in field_checks:
            match = "[OK]" if atdw_val == otdb_val else "[!!]"
            status = "OK" if atdw_val == otdb_val else "MISMATCH"
            print(f"{match} {name:20} ATDW: {str(atdw_val)[:30]:30} | OTDB: {str(otdb_val)[:30]:30} | {status}")

            if atdw_val != otdb_val:
                issues.append(f"{name} mismatch: ATDW='{atdw_val}', OTDB='{otdb_val}'")
            else:
                successes.append(f"{name} matches")

        # Check coordinates - use PHYSICAL address (matches load_atdw_to_database.py logic)
        addresses = atdw.get('addresses', [])
        atdw_lat = 0
        atdw_lng = 0
        if addresses:
            # Find PHYSICAL address with coordinates (same logic as loader)
            for addr in addresses:
                if addr.get('addressType') == 'PHYSICAL':
                    lat = addr.get('geocodeGdaLatitude')
                    lng = addr.get('geocodeGdaLongitude')
                    if lat and lng:
                        atdw_lat = float(lat)
                        atdw_lng = float(lng)
                        break

            # Fallback: any address with coords
            if atdw_lat == 0 or atdw_lng == 0:
                for addr in addresses:
                    lat = addr.get('geocodeGdaLatitude')
                    lng = addr.get('geocodeGdaLongitude')
                    if lat and lng:
                        atdw_lat = float(lat)
                        atdw_lng = float(lng)
                        break

            otdb_lat = float(product['latitude'] or 0)
            otdb_lng = float(product['longitude'] or 0)

            lat_match = abs(atdw_lat - otdb_lat) < 0.0001 if atdw_lat and otdb_lat else False
            lng_match = abs(atdw_lng - otdb_lng) < 0.0001 if atdw_lng and otdb_lng else False

            lat_status = "OK" if lat_match else "MISMATCH"
            lng_status = "OK" if lng_match else "MISMATCH"

            print(f"{'[OK]' if lat_match else '[!!]'} Latitude:            ATDW: {atdw_lat:30} | OTDB: {otdb_lat:30} | {lat_status}")
            print(f"{'[OK]' if lng_match else '[!!]'} Longitude:           ATDW: {atdw_lng:30} | OTDB: {otdb_lng:30} | {lng_status}")

            if not lat_match:
                issues.append(f"Latitude mismatch: ATDW={atdw_lat}, OTDB={otdb_lat}")
            if not lng_match:
                issues.append(f"Longitude mismatch: ATDW={atdw_lng}, OTDB={otdb_lng}")

        # Check for missing data structures
        print(f"\n=== MISSING DATA STRUCTURES ===\n")

        missing_structures = []

        if self.coverage_report['opening_hours_count'] > 0 and self.coverage_report.get('otdb_opening_hours_count', 0) == 0:
            missing_structures.append(f"Opening Hours: ATDW has {self.coverage_report['opening_hours_count']}, OTDB has 0")

        if missing_structures:
            for item in missing_structures:
                print(f"[!!] {item}")
                issues.append(item)
        else:
            print("[OK] No major data structures missing")

        # Final summary
        print(f"\n{'='*70}")
        print(f"FINAL RESULTS")
        print(f"{'='*70}\n")

        print(f"Successes: {len(successes)}")
        print(f"Issues: {len(issues)}")

        if issues:
            print(f"\nISSUES FOUND:")
            for i, issue in enumerate(issues, 1):
                print(f"  {i}. {issue}")

        coverage_pct = (len(successes) / (len(successes) + len(issues)) * 100) if (successes or issues) else 0
        print(f"\nData Capture Coverage: {coverage_pct:.1f}%")

        if coverage_pct == 100:
            print("\n*** 100% DATA CAPTURE - ALL TESTS PASSED! ***")
        else:
            print(f"\n*** INCOMPLETE DATA CAPTURE - {len(issues)} issues to fix ***")

        return len(issues) == 0

    def save_comparison_report(self, filename: str = None):
        """Save detailed comparison to JSON file."""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"data/atdw_otdb_comparison_{timestamp}.json"

        report = {
            'test_timestamp': datetime.now().isoformat(),
            'product_id': self.atdw_data.get('productId'),
            'product_name': self.atdw_data.get('productName'),
            'coverage_report': self.coverage_report,
            'atdw_sample': {
                'addresses': self.atdw_data.get('addresses', [])[:1],
                'communication': self.atdw_data.get('communication', [])[:1],
                'multimedia': self.atdw_data.get('multimedia', [])[:1],
                'attributes': self.atdw_data.get('attributes', [])[:3],
                'services': self.atdw_data.get('services', [])[:1],
            },
            'otdb_sample': {
                'addresses': self.otdb_data.get('addresses', [])[:1],
                'communication': self.otdb_data.get('communication', [])[:1],
                'media': self.otdb_data.get('media', [])[:1],
                'attributes': self.otdb_data.get('attributes', [])[:3],
                'services': self.otdb_data.get('services', [])[:1],
            }
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)

        print(f"\nDetailed comparison report saved to: {filename}")


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(
        description='Test complete data capture from ATDW to OTDB'
    )
    parser.add_argument(
        '--product-id',
        help='ATDW product ID to test (uses first VIC product if not specified)'
    )
    parser.add_argument(
        '--save-report',
        action='store_true',
        help='Save detailed comparison report to JSON file'
    )

    args = parser.parse_args()

    # Connect to OTDB
    conn = psycopg2.connect(
        host=os.getenv('OTDB_DB_HOST'),
        port=os.getenv('OTDB_DB_PORT', '5432'),
        database=os.getenv('OTDB_DB_NAME', 'postgres'),
        user=os.getenv('OTDB_DB_USER', 'postgres'),
        password=os.getenv('OTDB_DB_PASSWORD')
    )

    # Initialize ATDW client
    atdw_client = ATDWClient(api_key=os.getenv('ATDW_API_KEY'))

    # Get product ID
    if args.product_id:
        product_id = args.product_id
    else:
        print("No product ID specified, using first VIC product...")
        products = atdw_client.search_products(state='VIC')
        if not products:
            print("ERROR: No VIC products found")
            sys.exit(1)
        product_id = products[0]['productId']
        print(f"Using product: {product_id}")

    # Run test
    test = ATDWDataCaptureTest(conn, atdw_client)

    try:
        # Step 1: Fetch from ATDW
        product = test.fetch_atdw_product(product_id)

        # Step 2: Load to OTDB
        test.load_to_otdb(product)

        # Step 3: Fetch from OTDB
        test.fetch_from_otdb(product_id)

        # Step 4: Compare
        success = test.compare_data()

        # Save report if requested
        if args.save_report:
            test.save_comparison_report()

        sys.exit(0 if success else 1)

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        conn.close()


if __name__ == "__main__":
    main()
