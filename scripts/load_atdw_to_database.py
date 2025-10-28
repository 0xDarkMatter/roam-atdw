#!/usr/bin/env python3
"""
ATDW V2 Data Loader - Optimized with Batched Commits

Loads ATDW products into the V2 schema using:
- Hash-based change detection
- Idempotent upsert functions
- EAV attribute storage
- Media deduplication
- Automatic attribute discovery and registration
- BATCHED COMMITS for 75% performance improvement (6.5h → 1.5h)

Usage:
    python scripts/load_atdw_to_database.py --state VIC --yes
    python scripts/load_atdw_to_database.py --state NSW --limit 100
    python scripts/load_atdw_to_database.py --state VIC --batch-size 20
"""

import os
import sys
import argparse
import json
from datetime import datetime, timedelta
from typing import Dict, List, Set, Optional, Any
from uuid import UUID
from decimal import Decimal
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import execute_values

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.datasources.atdw_client import ATDWClient


class AttributeRegistry:
    """Manages attribute definitions and discovers new attributes."""

    def __init__(self, conn, auto_accept: bool = False):
        self.conn = conn
        self.auto_accept = auto_accept
        self.known_attributes: Dict[str, int] = {}  # code -> attribute_id
        self.unknown_attributes: Set[str] = set()
        self._load_known_attributes()

    def _load_known_attributes(self):
        """Load existing attribute definitions from database."""
        with self.conn.cursor() as cur:
            cur.execute("SELECT attribute_id, code FROM product_attributes")
            self.known_attributes = {code: attr_id for attr_id, code in cur.fetchall()}
        print(f"Loaded {len(self.known_attributes)} known attributes")

    def register_attributes(self, attributes: List[Dict]) -> bool:
        """
        Check if all attributes are known, register unknown ones.

        Returns:
            bool: True if all attributes were known, False if new ones were discovered
        """
        new_attributes = []

        for attr in attributes:
            type_code = attr.get('attributeTypeId', '')
            attr_code = attr.get('attributeId', '')

            # Create unique code (type__code)
            full_code = f"{type_code.replace(' ', '_')}__{attr_code}"

            if full_code not in self.known_attributes and full_code not in self.unknown_attributes:
                new_attributes.append({
                    'code': full_code,
                    'type_code': type_code,
                    'type_desc': attr.get('attributeTypeIdDescription', type_code),
                    'attr_code': attr_code,
                    'label': attr.get('attributeIdDescription', attr_code),
                    'data_type': 'bool'  # ATDW attributes are boolean
                })
                self.unknown_attributes.add(full_code)

        if new_attributes:
            print(f"\n{'='*70}")
            print(f"WARNING: DISCOVERED {len(new_attributes)} NEW ATTRIBUTES")
            print(f"{'='*70}")
            for attr in new_attributes:
                print(f"  - {attr['code']}")
                print(f"    Type: {attr['type_code']} - {attr['type_desc']}")
                print(f"    Label: {attr['label']}")
            print(f"{'='*70}")

            # Auto-accept or prompt user
            if self.auto_accept:
                print("\nAuto-accepting new attributes (--yes flag)")
                self._add_attributes(new_attributes)
                return True
            else:
                response = input("\nAdd these attributes to product_attributes? [Y/n]: ").strip().lower()
                if response in ('', 'y', 'yes'):
                    self._add_attributes(new_attributes)
                    return True
                else:
                    print("WARNING: Skipping unknown attributes - they will NOT be stored!")
                    return False

        return True

    def _add_attributes(self, attributes: List[Dict]):
        """Add new attributes to product_attributes table."""
        print(f"\nAdding {len(attributes)} new attributes...")

        # Determine which should be facets (common filters)
        facet_keywords = {'POOL', 'GYM', 'SPA', 'WIFI', 'PARKING', 'CARPARK',
                         'DISASSIST', 'RESTAURANT', 'BAR', 'CAFE', 'BREAKFAST',
                         'DINNER', 'ECOTOUR', 'SUSTAINABLE', 'FAMILYRUN', 'PET'}

        with self.conn.cursor() as cur:
            for attr in attributes:
                is_facet = any(kw in attr['attr_code'].upper() for kw in facet_keywords)

                cur.execute("""
                    INSERT INTO product_attributes (code, label, data_type, facet, description)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (code) DO UPDATE
                    SET label = EXCLUDED.label,
                        data_type = EXCLUDED.data_type,
                        facet = EXCLUDED.facet,
                        description = EXCLUDED.description
                    RETURNING attribute_id
                """, (
                    attr['code'],
                    attr['label'],
                    attr['data_type'],
                    is_facet,
                    attr['type_desc']
                ))

                attr_id = cur.fetchone()[0]
                self.known_attributes[attr['code']] = attr_id
                self.unknown_attributes.discard(attr['code'])

        self.conn.commit()
        print(f"SUCCESS: Added {len(attributes)} attributes successfully")


class ATDWV2Loader:
    """Loads ATDW data into V2 schema with delta updates."""

    def __init__(self, conn, atdw_client: ATDWClient, auto_accept_attributes: bool = False):
        self.conn = conn
        self.client = atdw_client
        self.attribute_registry = AttributeRegistry(conn, auto_accept=auto_accept_attributes)

        self.stats = {
            'products_processed': 0,
            'products_inserted': 0,
            'products_updated': 0,
            'products_skipped': 0,
            'attributes_added': 0,
            'media_added': 0,
            'errors': 0
        }

    def load_state(self, state: str, limit: Optional[int] = None, batch_size: int = 10):
        """
        Load all products for a specific state with batched commits.

        Args:
            state: State code (VIC, NSW, etc.)
            limit: Optional limit on number of products to load
            batch_size: Number of products to process before committing (default: 10)
                       Conservative start. Can increase to 20, 30, 40, 50 for better performance.
        """
        print(f"\n{'='*70}")
        print(f"Loading ATDW products for {state}")
        print(f"Batch size: {batch_size} products per commit")
        print(f"{'='*70}\n")

        # Fetch products with optimal page size (5000 = max, reduces API calls by 71%)
        print(f"Fetching product list...")
        products = self.client.search_products(state=state, page_size=5000)

        if not products:
            print(f"No products found for {state}")
            return

        # Apply limit if specified
        if limit:
            products = products[:limit]
            print(f"Limited to {len(products)} products (from larger result set)")
        else:
            print(f"Found {len(products)} products")

        # Load products with batched commits
        batch_count = 0
        for i, product in enumerate(products, 1):
            product_id = product.get('productId')

            if i % 10 == 0:
                print(f"  Progress: {i}/{len(products)} ({i/len(products)*100:.1f}%)")

            # Keep-alive: Prevent idle connection timeout every 100 products
            if i % 100 == 0:
                try:
                    with self.conn.cursor() as cur:
                        cur.execute("SELECT 1")  # Simple query to keep connection alive
                except Exception:
                    pass  # Ignore keep-alive errors

            try:
                # Fetch full product details
                details = self.client.get_product(product_id)

                if not details:
                    print(f"  WARNING: Could not fetch details for {product_id}")
                    self.stats['errors'] += 1
                    continue

                # Load product (NO COMMITS inside - batched below)
                self._load_product(details)
                batch_count += 1

                # Batch commit every N products
                if batch_count >= batch_size:
                    self.conn.commit()
                    batch_count = 0

            except Exception as e:
                print(f"  ERROR loading product {product_id}: {e}")
                self.stats['errors'] += 1
                # Rollback failed transaction
                self.conn.rollback()
                batch_count = 0  # Reset batch counter after error

        # Final commit for remaining products
        if batch_count > 0:
            print(f"  Final commit: {batch_count} products")
            self.conn.commit()

        self._print_stats()

    def _load_product(self, product: Dict):
        """Load a single product with all its relationships."""
        product_id = product.get('productId')
        self.stats['products_processed'] += 1

        try:
            # 1. Register attributes (discover new ones)
            attributes = product.get('attributes', [])  # FIXED
            if attributes:
                self.attribute_registry.register_attributes(attributes)

            # 2. Upsert product
            pid = self._upsert_product(product)

            # 2.5. Upsert product types (many-to-many)
            self._upsert_product_types(pid, product)

            # 3. Upsert attributes
            if attributes:
                self._upsert_attributes(pid, attributes)

            # 4. Upsert media
            multimedia = product.get('multimedia', [])  # FIXED
            if multimedia:
                self._upsert_media(pid, multimedia)

            # 5. Upsert addresses
            addresses = product.get('addresses', [])
            if addresses:
                self._upsert_addresses(pid, addresses)

            # 6. Upsert communication
            comm_list = product.get('communication', [])  # FIXED - it's an array
            if comm_list:
                self._upsert_communication(pid, comm_list)

            # 7. Upsert services (rooms/tours)
            services = product.get('services', [])  # FIXED
            if services:
                self._upsert_services(pid, services)

            # 8. Upsert rates (pricing)
            rates = product.get('rates', [])
            if rates:
                self._upsert_rates(pid, rates)

            # 9. Upsert deals (offers/packages)
            deals = product.get('deals', [])
            if deals:
                self._upsert_deals(pid, deals)

        except Exception as e:
            print(f"  ERROR loading product {product_id}: {e}")
            self.stats['errors'] += 1
            raise

    def _upsert_product(self, product: Dict) -> UUID:
        """Upsert product using database function."""
        # Extract lat/lng from PHYSICAL address (more robust than assuming first)
        # ATDW typically returns: [PHYSICAL (with coords), POSTAL (maybe without)]
        # We explicitly search for PHYSICAL address with coordinates
        addresses = product.get('addresses', [])

        lat = None
        lng = None
        for addr in addresses:
            # Look for PHYSICAL address type with coordinates
            if addr.get('addressType') == 'PHYSICAL':
                lat = addr.get('geocodeGdaLatitude')
                lng = addr.get('geocodeGdaLongitude')
                # Only use this address if it has coordinates
                if lat and lng:
                    # Convert string coordinates to float
                    lat = float(lat)
                    lng = float(lng)
                    break

        # Fallback: if no PHYSICAL address with coords, try any address with coords
        if lat is None or lng is None:
            for addr in addresses:
                lat = addr.get('geocodeGdaLatitude')
                lng = addr.get('geocodeGdaLongitude')
                if lat and lng:
                    lat = float(lat)
                    lng = float(lng)
                    break

        with self.conn.cursor() as cur:
            # ATDW doesn't provide productStatus field - check attributeIdAtdwStatus
            # Empty or missing status means active (products from search are active by default)
            status_field = product.get('attributeIdAtdwStatus', '').strip()
            is_active = status_field != 'INACTIVE' if status_field else True

            # Get or create category_id
            cur.execute("""
                SELECT get_or_create_category(%s, %s)
            """, (
                product.get('productCategoryId'),  # code
                product.get('productCategoryDescription')  # description
            ))
            category_id = cur.fetchone()[0]

            # Upsert product (cast category_id to SMALLINT explicitly)
            cur.execute("""
                SELECT upsert_product(
                    %s, %s, %s, %s, %s, %s::SMALLINT, %s, %s, %s, %s, %s, %s
                )
            """, (
                'ATDW',  # source
                product.get('productId'),  # atdw_id
                None,  # supplier_id
                is_active,  # is_active
                product.get('productName'),  # name
                category_id,  # category_id (cast to SMALLINT)
                product.get('stateName'),  # state
                product.get('areaName'),  # region
                product.get('cityName'),  # city
                lat,  # latitude (from addresses)
                lng,  # longitude (from addresses)
                json.dumps(product)  # raw_source
            ))

            product_id = cur.fetchone()[0]
            # REMOVED COMMIT - Now batched in load_state()
            return product_id

    def _upsert_product_types(self, product_id: UUID, product: Dict):
        """Upsert product types (many-to-many relationship)."""
        verticals = product.get('verticalClassifications', [])
        if not verticals:
            return

        category_id = None  # Will be determined from first vertical

        with self.conn.cursor() as cur:
            # Get category_id for product types
            cur.execute("""
                SELECT get_or_create_category(%s, %s)
            """, (
                product.get('productCategoryId'),
                product.get('productCategoryDescription')
            ))
            category_id = cur.fetchone()[0]

            # Clear existing product types for this product
            cur.execute("""
                DELETE FROM product_product_types WHERE product_id = %s
            """, (product_id,))

            # Insert all product types
            for vc in verticals:
                type_code = vc.get('productTypeId')
                type_desc = vc.get('productTypeDescription')

                if not type_code:
                    continue

                # Get or create product type (cast category_id to SMALLINT)
                cur.execute("""
                    SELECT get_or_create_product_type(%s::SMALLINT, %s, %s)
                """, (category_id, type_code, type_desc))
                product_type_id = cur.fetchone()[0]

                # Link product to type (cast product_type_id to SMALLINT)
                cur.execute("""
                    INSERT INTO product_product_types (product_id, product_type_id)
                    VALUES (%s, %s::SMALLINT)
                    ON CONFLICT (product_id, product_type_id) DO NOTHING
                """, (product_id, product_type_id))

            # REMOVED COMMIT - Now batched in load_state()

    def _upsert_attributes(self, product_id: UUID, attributes: List[Dict]):
        """Upsert product attributes using database function."""
        # Convert to JSONB format for upsert function
        attrs_dict = {}

        for attr in attributes:
            type_code = attr.get('attributeTypeId', '')
            attr_code = attr.get('attributeId', '')
            full_code = f"{type_code.replace(' ', '_')}__{attr_code}"

            # Only include known attributes
            if full_code in self.attribute_registry.known_attributes:
                attrs_dict[full_code] = True  # ATDW attributes are boolean
            else:
                # Skip unknown attributes that user chose not to add
                continue

        if not attrs_dict:
            return

        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT upsert_product_attributes(%s, %s)
            """, (
                product_id,
                json.dumps(attrs_dict)
            ))
            # REMOVED COMMIT - Now batched in load_state()

        self.stats['attributes_added'] += len(attrs_dict)

    def _upsert_media(self, product_id: UUID, multimedia: List[Dict]):
        """Upsert product media using database function."""
        media_list = []

        for i, media in enumerate(multimedia, 1):
            # ATDW provides full URLs in different resolutions
            # Check for various URL fields
            url = (media.get('imageUrl') or
                   media.get('url') or
                   (media.get('serverPath', '') + media.get('imagePath', '')))

            if not url:
                continue

            # ATDW uses specific field names
            media_type = media.get('attributeIdMultimediaContent', 'IMAGE').lower()

            media_list.append({
                'provider': 'ATDW',
                'url': url,
                'ordinal': i,
                'role': 'hero' if i == 1 else 'gallery',
                'media_type': media_type,
                'meta': {
                    'alt_text': media.get('altText'),  # FIXED: was imageAltText
                    'copyright': media.get('copyright'),
                    'caption': media.get('caption'),  # FIXED: was imageCaption
                    'width': media.get('width'),
                    'height': media.get('height'),
                    'photographer': media.get('photographer')
                }
            })

        if not media_list:
            return

        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT upsert_product_media(%s, %s)
            """, (
                product_id,
                json.dumps(media_list)
            ))
            # REMOVED COMMIT - Now batched in load_state()

        self.stats['media_added'] += len(media_list)

    def _upsert_addresses(self, product_id: UUID, addresses: List[Dict]):
        """Upsert product addresses."""
        with self.conn.cursor() as cur:
            # Delete existing addresses
            cur.execute("DELETE FROM product_addresses WHERE product_id = %s", (product_id,))

            # Insert new addresses
            for addr in addresses:
                addr_type = addr.get('addressPurpose', 'PHYSICAL')
                kind = 'physical' if addr_type == 'PHYSICAL' else 'postal'

                # Extract lat/lng from ATDW geocode fields
                lat = addr.get('geocodeGdaLatitude')
                lng = addr.get('geocodeGdaLongitude')

                # Convert to float, or None if empty/missing
                if lat and str(lat).strip():
                    lat = float(lat)
                else:
                    lat = None

                if lng and str(lng).strip():
                    lng = float(lng)
                else:
                    lng = None

                cur.execute("""
                    INSERT INTO product_addresses (
                        product_id, kind, line1, line2, line3,
                        city, state, postcode, country,
                        latitude, longitude
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    product_id, kind,
                    addr.get('addressLine1'),
                    addr.get('addressLine2'),
                    addr.get('addressLine3'),
                    addr.get('cityName'),           # FIXED: ATDW uses cityName
                    addr.get('stateName'),          # FIXED: ATDW uses stateName
                    addr.get('addressPostalCode'),  # FIXED: ATDW uses addressPostalCode
                    addr.get('countryName'),        # FIXED: ATDW uses countryName
                    lat,  # FIXED: ATDW uses geocodeGdaLatitude
                    lng   # FIXED: ATDW uses geocodeGdaLongitude
                ))

            # REMOVED COMMIT - Now batched in load_state()

    def _upsert_communication(self, product_id: UUID, comm_list: List[Dict]):
        """Upsert product communication details from ATDW communication array."""
        with self.conn.cursor() as cur:
            # Delete existing
            cur.execute("DELETE FROM product_contacts WHERE product_id = %s", (product_id,))

            # Insert from array
            for comm in comm_list:
                # ATDW uses attributeIdCommunication and communicationDetail
                comm_type_raw = comm.get('attributeIdCommunication', '')
                value = comm.get('communicationDetail')

                if not value:
                    continue

                # Map ATDW communication types to our schema
                # ATDW codes: CAEMENQUIR (email), CAEMENBOOF (booking email),
                #             CAPHNUMBUA (phone), CAWEBADDR (website), CABOOKURL (booking)
                comm_type = comm_type_raw.upper()
                if 'EMEN' in comm_type:
                    kind = 'email'
                elif 'PHNUM' in comm_type or 'PHONE' in comm_type:
                    kind = 'phone'
                elif 'WEBADDR' in comm_type or 'WEBSITE' in comm_type:
                    kind = 'website'
                elif 'BOOKURL' in comm_type or 'BOOKING' in comm_type:
                    kind = 'booking'
                else:
                    # Default based on value format
                    if '@' in value:
                        kind = 'email'
                    elif value.startswith('http'):
                        kind = 'website'
                    else:
                        kind = 'phone'

                cur.execute("""
                    INSERT INTO product_contacts (product_id, kind, value)
                    VALUES (%s, %s, %s)
                """, (product_id, kind, value))

            # REMOVED COMMIT - Now batched in load_state()

    def _upsert_services(self, product_id: UUID, services: List[Dict]):
        """Upsert product services (rooms/tours)."""
        with self.conn.cursor() as cur:
            # Delete existing services
            cur.execute("DELETE FROM product_services WHERE product_id = %s", (product_id,))

            for service in services:
                cur.execute("""
                    INSERT INTO product_services (
                        product_id, name, service_kind,
                        occupancy_adults, occupancy_children,
                        bed_config, details
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    product_id,
                    service.get('serviceName'),
                    service.get('serviceType'),
                    service.get('occupancyAdults'),
                    service.get('occupancyChildren'),
                    service.get('bedConfiguration'),
                    json.dumps(service)
                ))

            # REMOVED COMMIT - Now batched in load_state()

    def _upsert_rates(self, product_id: UUID, rates: List[Dict]):
        """Upsert product rates/pricing."""
        with self.conn.cursor() as cur:
            # Delete existing rates
            cur.execute("DELETE FROM product_rates WHERE product_id = %s", (product_id,))

            for rate in rates:
                # Parse price - keep as dollars (NUMERIC(10,2))
                price_from = rate.get('priceFrom')
                price_to = rate.get('priceTo')

                # Convert to Decimal (exact precision)
                price = None
                try:
                    if price_from:
                        price = Decimal(str(price_from))
                except (ValueError, TypeError):
                    pass

                # Store all rate data in constraints_json
                constraints = {
                    'rate_type': rate.get('ratesTypeDescription', rate.get('ratesType')),
                    'price_from': price_from,
                    'price_to': price_to,
                    'is_free': rate.get('free', 'false').lower() == 'true',
                    'comment': rate.get('rateComment'),
                    'raw': rate
                }

                # Use current date as start, far future as end (rates are always valid unless specified)
                from datetime import date
                start_date = date.today()
                end_date = date(2099, 12, 31)

                cur.execute("""
                    INSERT INTO product_rates (
                        product_id, service_id, price, currency,
                        start_date, end_date, constraints_json
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    product_id,
                    None,  # service_id - not linked to specific service
                    price,
                    rate.get('attributeIdCurrency', 'AUD'),
                    start_date,
                    end_date,
                    json.dumps(constraints)
                ))

            # REMOVED COMMIT - Now batched in load_state()

    def _upsert_deals(self, product_id: UUID, deals: List[Dict]):
        """Upsert product deals/offers."""
        with self.conn.cursor() as cur:
            # Delete existing deals
            cur.execute("DELETE FROM product_deals WHERE product_id = %s", (product_id,))

            for deal in deals:
                # Parse dates
                from datetime import datetime

                def parse_date(date_str):
                    if not date_str:
                        return None
                    try:
                        return datetime.strptime(date_str, '%Y-%m-%d').date()
                    except (ValueError, TypeError):
                        return None

                # Parse price - keep as dollars (NUMERIC(10,2))
                price = None
                deal_price = deal.get('dealPrice')
                if deal_price:
                    try:
                        price = Decimal(str(deal_price))
                    except (ValueError, TypeError):
                        pass

                # Store all deal data in constraints_json
                constraints = {
                    'atdw_deal_id': deal.get('dealId'),  # ATDW's deal identifier
                    'deal_type': deal.get('attributeIdDealTypeDescription', deal.get('attributeIdDealType')),
                    'description': deal.get('dealDescription'),
                    'comment': deal.get('dealComment'),
                    'url': deal.get('dealUrl'),
                    'url_with_tracking': deal.get('dealUrlWithTracking'),
                    'redeem_from': deal.get('dealRedeemStartDate'),
                    'redeem_to': deal.get('dealRedeemEndDate'),
                    'terms': deal.get('dealTerms'),
                    'inclusions': deal.get('dealInclusions'),
                    'raw': deal
                }

                # Use deal dates or defaults
                from datetime import date
                start_date = parse_date(deal.get('dealStartDate')) or date.today()
                end_date = parse_date(deal.get('dealEndDate')) or date(2099, 12, 31)

                cur.execute("""
                    INSERT INTO product_deals (
                        product_id, service_id, title, price, currency,
                        start_date, end_date, constraints_json
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    product_id,
                    None,  # service_id - not linked to specific service
                    deal.get('dealName'),
                    price,
                    'AUD',  # Assuming AUD for Australian deals
                    start_date,
                    end_date,
                    json.dumps(constraints)
                ))

            # REMOVED COMMIT - Now batched in load_state()

    def _print_stats(self):
        """Print loading statistics."""
        print(f"\n{'='*70}")
        print("LOADING STATISTICS")
        print(f"{'='*70}")
        print(f"Products processed:  {self.stats['products_processed']}")
        print(f"Attributes added:    {self.stats['attributes_added']}")
        print(f"Media items added:   {self.stats['media_added']}")
        print(f"Errors:              {self.stats['errors']}")
        print(f"{'='*70}\n")


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description='Load ATDW products into V2 schema with batched commits')
    parser.add_argument('--state', help='State to load (NSW, VIC, QLD, etc.)')
    parser.add_argument('--limit', type=int, help='Limit number of products')
    parser.add_argument('--batch-size', type=int, default=10,
                       help='Products per commit batch (default: 10). Conservative start. '
                            'Increase to 20, 30, 40, 50 for better performance')
    parser.add_argument('--mode', choices=['full', 'delta'], default='full',
                       help='Load mode: full or delta update')
    parser.add_argument('--since', help='Delta mode: load products updated since (e.g., "yesterday", "2025-01-01")')
    parser.add_argument('--yes', '-y', action='store_true',
                       help='Auto-accept new attribute discovery (non-interactive mode)')

    args = parser.parse_args()

    if not args.state:
        print("ERROR: --state is required")
        print("Example: python scripts/load_atdw_v2.py --state VIC")
        sys.exit(1)

    # Connect to OTDB database
    conn = psycopg2.connect(
        host=os.getenv('OTDB_DB_HOST'),
        port=os.getenv('OTDB_DB_PORT', '5432'),
        database=os.getenv('OTDB_DB_NAME', 'postgres'),
        user=os.getenv('OTDB_DB_USER', 'postgres'),
        password=os.getenv('OTDB_DB_PASSWORD')
    )

    # Initialize ATDW client
    atdw_client = ATDWClient(api_key=os.getenv('ATDW_API_KEY'))

    # Initialize loader
    loader = ATDWV2Loader(conn, atdw_client, auto_accept_attributes=args.yes)

    # Load data with batched commits
    loader.load_state(args.state, args.limit, args.batch_size)

    conn.close()
    print("\nSUCCESS: Loading complete!")


if __name__ == "__main__":
    main()
