"""
Test script to find ATDW API pagination limits.

Tests progressively larger page sizes to determine the maximum allowed.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.datasources import ATDWClient


def test_page_size_limits():
    """Test various page sizes to find the maximum."""
    print("=" * 80)
    print("ATDW Pagination Limit Test")
    print("=" * 80)

    client = ATDWClient()

    # Test progressively larger page sizes
    test_sizes = [6000, 7000, 8000, 9000]

    for size in test_sizes:
        print(f"\nTesting page size: {size}")
        print("-" * 80)

        try:
            results = client.search_products(
                categories=['ACCOMMODATION'],
                paginate=False,
                page_size=size
            )

            actual_count = len(results)
            print(f"SUCCESS: Requested {size}, received {actual_count} results")

            # If we got fewer results than requested, we've hit the data limit
            if actual_count < size:
                print(f"  Note: Received fewer results than requested - likely all available data")

        except Exception as e:
            print(f"FAILED with error: {e}")
            print(f"  Maximum page size appears to be less than {size}")
            break

    print("\n" + "=" * 80)
    print("Pagination limit test completed")
    print("=" * 80)


if __name__ == '__main__':
    test_page_size_limits()
