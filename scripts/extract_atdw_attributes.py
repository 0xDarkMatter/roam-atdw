"""
Extract comprehensive catalog of all ATDW attribute types and codes.

This script:
1. Fetches samples from all product categories
2. Uses detailed product API to get full attribute information
3. Extracts all unique attribute structures
4. Documents all attribute type codes and specific codes
5. Determines data types for each attribute
6. Generates JSON catalog and SQL migration
"""

import os
import sys
import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Any
from dotenv import load_dotenv
import time

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from datasources.atdw_client import ATDWClient


def process_attributes_list(
    attributes: List[Dict],
    attribute_catalog: Dict,
    category_name: str
):
    """
    Process a list of attributes from the 'attributes' field.

    Structure:
    {
        "attributeTypeId": "ENTITY FAC",
        "attributeTypeIdDescription": "Entity Facility",
        "attributeId": "24HOURS",
        "attributeIdDescription": "24 Hour Reception"
    }
    """
    for attr in attributes:
        attr_type = attr.get('attributeTypeId', 'UNKNOWN')
        attr_type_desc = attr.get('attributeTypeIdDescription', '')
        attr_id = attr.get('attributeId', '')
        attr_desc = attr.get('attributeIdDescription', '')

        if not attr_id:
            continue

        # Initialize type if new
        if attr_type not in attribute_catalog:
            attribute_catalog[attr_type] = {
                'type_code': attr_type,
                'description': attr_type_desc,
                'attributes': {},
                'sample_categories': set()
            }

        # Update description if we have a better one
        if attr_type_desc and not attribute_catalog[attr_type]['description']:
            attribute_catalog[attr_type]['description'] = attr_type_desc

        # Initialize attribute if new
        if attr_id not in attribute_catalog[attr_type]['attributes']:
            attribute_catalog[attr_type]['attributes'][attr_id] = {
                'code': attr_id,
                'label': attr_desc,
                'data_type': 'bool',  # Most ATDW attributes are presence flags
                'sample_categories': set()
            }

        # Update label if we have a better one
        if attr_desc and not attribute_catalog[attr_type]['attributes'][attr_id]['label']:
            attribute_catalog[attr_type]['attributes'][attr_id]['label'] = attr_desc

        # Track categories
        attribute_catalog[attr_type]['sample_categories'].add(category_name)
        attribute_catalog[attr_type]['attributes'][attr_id]['sample_categories'].add(category_name)


def process_accessibility_attributes(
    attributes: List[Dict],
    attribute_catalog: Dict,
    category_name: str
):
    """
    Process accessibility attributes.

    Structure:
    {
        "attributeTypeId": "ACCESSIBILITY",
        "attributeTypeIdDescription": "Accessibility",
        "attributeSubType1Id": "DISTASSIST",
        "attributeSubType1IdDescription": "Disabled access available, contact operator for details."
    }
    """
    for attr in attributes:
        attr_type = attr.get('attributeTypeId', 'UNKNOWN')
        attr_type_desc = attr.get('attributeTypeIdDescription', '')
        attr_id = attr.get('attributeSubType1Id', '')
        attr_desc = attr.get('attributeSubType1IdDescription', '')

        if not attr_id:
            continue

        # Initialize type if new
        if attr_type not in attribute_catalog:
            attribute_catalog[attr_type] = {
                'type_code': attr_type,
                'description': attr_type_desc,
                'attributes': {},
                'sample_categories': set()
            }

        # Update description if we have a better one
        if attr_type_desc and not attribute_catalog[attr_type]['description']:
            attribute_catalog[attr_type]['description'] = attr_type_desc

        # Initialize attribute if new
        if attr_id not in attribute_catalog[attr_type]['attributes']:
            attribute_catalog[attr_type]['attributes'][attr_id] = {
                'code': attr_id,
                'label': attr_desc,
                'data_type': 'bool',
                'sample_categories': set()
            }

        # Update label if we have a better one
        if attr_desc and not attribute_catalog[attr_type]['attributes'][attr_id]['label']:
            attribute_catalog[attr_type]['attributes'][attr_id]['label'] = attr_desc

        # Track categories
        attribute_catalog[attr_type]['sample_categories'].add(category_name)
        attribute_catalog[attr_type]['attributes'][attr_id]['sample_categories'].add(category_name)


def main():
    print("ATDW Attribute Catalog Extractor")
    print("=" * 80)

    # Initialize client
    client = ATDWClient()

    # Track all attributes
    attribute_catalog = {}

    # Fetch samples from ALL categories
    categories = {
        'ACCOMM': 'Accommodation',
        'ATTRACTION': 'Attraction',
        'TOUR': 'Tour',
        'RESTAURANT': 'Restaurant',
        'EVENT': 'Event',
        'HIRE': 'Hire',
        'TRANSPORT': 'Transport',
        'GENERAL_SERVICE': 'General Service',
        'DESTINATION': 'Destination',
        'JOURNEY': 'Journey'
    }

    total_products_searched = 0
    total_products_detailed = 0

    for category_code, category_name in categories.items():
        print(f"\nProcessing {category_name} ({category_code})...")

        try:
            # First, get product IDs (lightweight search)
            print(f"  Searching for product IDs...")
            products = client.search_products(
                categories=[category_code],
                paginate=True,
                max_pages=1,  # 1 page = up to 1000 products
                page_size=100  # Get 100 products per category
            )

            if not products:
                print(f"  No products found")
                continue

            print(f"  Found {len(products)} products")
            total_products_searched += len(products)

            # Now fetch detailed info for each product (this has the attributes)
            product_count = 0
            for product in products[:20]:  # Limit to 20 detailed fetches per category to avoid rate limits
                product_id = product.get('productId')
                if not product_id:
                    continue

                try:
                    # Get detailed product info
                    detailed_product = client.get_product(product_id)

                    # Process all attribute types
                    if 'attributes' in detailed_product:
                        process_attributes_list(
                            detailed_product['attributes'],
                            attribute_catalog,
                            category_name
                        )

                    if 'accessibilityAttributes' in detailed_product:
                        process_accessibility_attributes(
                            detailed_product['accessibilityAttributes'],
                            attribute_catalog,
                            category_name
                        )

                    if 'productWineVarietyAttributes' in detailed_product:
                        process_attributes_list(
                            detailed_product['productWineVarietyAttributes'],
                            attribute_catalog,
                            category_name
                        )

                    if 'productWineTastingAttributes' in detailed_product:
                        process_attributes_list(
                            detailed_product['productWineTastingAttributes'],
                            attribute_catalog,
                            category_name
                        )

                    product_count += 1
                    total_products_detailed += 1

                    # Rate limiting - be gentle with the API
                    if product_count % 10 == 0:
                        print(f"    Processed {product_count} detailed products...")

                except Exception as e:
                    print(f"    Error fetching product {product_id}: {e}")
                    continue

            print(f"  Completed: {product_count} detailed products processed")

        except Exception as e:
            print(f"  Error processing {category_name}: {e}")
            continue

    print(f"\n{'=' * 80}")
    print(f"Total products searched: {total_products_searched}")
    print(f"Total products detailed: {total_products_detailed}")
    print(f"Total attribute types found: {len(attribute_catalog)}")

    # Count total attributes
    total_attrs = sum(len(type_data['attributes']) for type_data in attribute_catalog.values())
    print(f"Total unique attributes found: {total_attrs}")

    # Convert sets to lists for JSON serialization
    catalog_json = {
        'metadata': {
            'generated_by': str(Path(__file__).name),
            'total_products_searched': total_products_searched,
            'total_products_detailed': total_products_detailed,
            'total_attribute_types': len(attribute_catalog),
            'total_attributes': total_attrs,
            'note': 'This catalog was generated from a sample of ATDW products. Additional attributes may exist.'
        },
        'attribute_types': []
    }

    # Sort by type code for consistency
    for type_code in sorted(attribute_catalog.keys()):
        type_data = attribute_catalog[type_code]

        # Convert attributes dict to sorted list
        attrs_list = []
        for attr_code in sorted(type_data['attributes'].keys()):
            attr_data = type_data['attributes'][attr_code]
            attrs_list.append({
                'code': attr_data['code'],
                'label': attr_data['label'] or attr_data['code'].replace('_', ' ').title(),
                'data_type': attr_data['data_type'],
                'sample_categories': sorted(list(attr_data['sample_categories']))
            })

        catalog_json['attribute_types'].append({
            'type_code': type_data['type_code'],
            'description': type_data['description'] or type_data['type_code'].replace('_', ' ').title(),
            'attribute_count': len(attrs_list),
            'sample_categories': sorted(list(type_data['sample_categories'])),
            'attributes': attrs_list
        })

    # Write JSON catalog
    json_path = Path(__file__).parent.parent / 'data' / 'atdw_attribute_catalog.json'
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(catalog_json, f, indent=2, ensure_ascii=False)

    print(f"\nJSON catalog written to: {json_path}")

    # Generate SQL migration
    sql_path = Path(__file__).parent.parent / 'migrations' / '011_populate_attribute_def.sql'

    with open(sql_path, 'w', encoding='utf-8') as f:
        f.write("-- ATDW Attribute Definitions\n")
        f.write("-- Generated from ATDW API comprehensive extraction\n")
        f.write(f"-- Total attribute types: {len(attribute_catalog)}\n")
        f.write(f"-- Total attributes: {total_attrs}\n")
        f.write("--\n")
        f.write("-- This migration populates the attribute_def table with all known\n")
        f.write("-- ATDW attribute types and codes discovered from API samples.\n")
        f.write("--\n")
        f.write("-- NOTE: Additional attributes may exist that were not in the sample.\n")
        f.write("-- The application should handle unknown attributes gracefully.\n\n")

        f.write("BEGIN;\n\n")

        # Insert attribute types and codes
        for type_data in catalog_json['attribute_types']:
            type_code = type_data['type_code']
            description = type_data['description']

            f.write(f"-- {description} ({type_data['attribute_count']} attributes)\n")
            f.write(f"-- Found in: {', '.join(type_data['sample_categories'])}\n")

            for attr in type_data['attributes']:
                code = attr['code']
                label = attr['label']
                data_type = attr['data_type']

                # Escape single quotes in SQL
                label_escaped = label.replace("'", "''")
                description_escaped = description.replace("'", "''")

                f.write(
                    f"INSERT INTO attribute_def (attribute_type, attribute_code, attribute_label, data_type) "
                    f"VALUES ('{type_code}', '{code}', '{label_escaped}', '{data_type}')\n"
                    f"ON CONFLICT (attribute_type, attribute_code) DO UPDATE "
                    f"SET attribute_label = EXCLUDED.attribute_label, data_type = EXCLUDED.data_type;\n"
                )

            f.write("\n")

        f.write("COMMIT;\n")

    print(f"SQL migration written to: {sql_path}")

    # Print summary statistics
    print(f"\n{'=' * 80}")
    print("ATTRIBUTE TYPE SUMMARY")
    print(f"{'=' * 80}")

    for type_data in catalog_json['attribute_types']:
        print(f"\n{type_data['type_code']}: {type_data['description']}")
        print(f"  Attributes: {type_data['attribute_count']}")
        print(f"  Categories: {', '.join(type_data['sample_categories'])}")

        # Show a few sample attributes
        if type_data['attributes']:
            print(f"  Examples:")
            for attr in type_data['attributes'][:5]:
                print(f"    - {attr['code']}: {attr['label']}")
            if len(type_data['attributes']) > 5:
                print(f"    ... and {len(type_data['attributes']) - 5} more")

    print(f"\n{'=' * 80}")
    print("Extraction complete!")
    print(f"{'=' * 80}")


if __name__ == '__main__':
    main()
