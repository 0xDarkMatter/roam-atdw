"""
Test script for ATDW client.

Tests basic functionality of the ATDW ATLAS2 API client.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.datasources import ATDWClient


def test_search_products():
    """Test product search with various filters."""
    print("=" * 80)
    print("ATDW Client Test")
    print("=" * 80)

    # Initialize client
    client = ATDWClient()

    # Test 1: Simple location search
    print("\nTest 1: Search accommodation (first page only)")
    print("-" * 80)
    results = client.search_products(
        categories=['ACCOMMODATION'],
        paginate=False,
        page_size=5
    )
    print(f"Found {len(results)} results")
    if results:
        print(f"First result: {results[0].get('productName', 'N/A')}")
        print(f"Location: {results[0].get('address', {}).get('city', 'N/A')}, "
              f"{results[0].get('address', {}).get('state', 'N/A')}")

    # Test 2: Geospatial search
    print("\nTest 2: Geospatial search (lat/lng with radius)")
    print("-" * 80)
    results = client.search_by_location(
        lat=-33.8688,  # Generic coordinates
        lng=151.2093,
        radius_km=10,
        categories=['RESTAURANT'],
        paginate=False,
        page_size=5
    )
    print(f"Found {len(results)} results within 10km")
    if results:
        print(f"First result: {results[0].get('productName', 'N/A')}")

    # Test 3: State/city search
    print("\nTest 3: Search by state and category")
    print("-" * 80)
    results = client.search_products(
        state='NSW',
        categories=['ATTRACTION'],
        paginate=False,
        page_size=5
    )
    print(f"Found {len(results)} results")
    if results:
        print(f"First result: {results[0].get('productName', 'N/A')}")

    # Test 4: Full-text search
    print("\nTest 4: Full-text search with term")
    print("-" * 80)
    results = client.search_products(
        term='beach',
        paginate=False,
        page_size=5
    )
    print(f"Found {len(results)} results matching 'beach'")
    if results:
        print(f"First result: {results[0].get('productName', 'N/A')}")

    # Test 5: Get product details
    if results:
        print("\nTest 5: Get product details")
        print("-" * 80)
        product_id = results[0].get('productId')
        if product_id:
            details = client.get_product(product_id)
            print(f"Product: {details.get('productName', 'N/A')}")
            print(f"Category: {details.get('productCategory', 'N/A')}")
            print(f"Description: {details.get('productDescription', 'N/A')[:100]}...")

    print("\n" + "=" * 80)
    print("All tests completed successfully!")
    print("=" * 80)


if __name__ == '__main__':
    test_search_products()
