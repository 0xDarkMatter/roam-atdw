#!/usr/bin/env python3
"""
ATDW National Data Extractor

Extracts complete tourism product data for all Australian states from ATDW API
using proper HTTP fetch patterns with exponential backoff and progress tracking.

Usage:
    python scripts/extract_atdw_national.py
"""

import csv
import json
import sys
import time
from datetime import datetime
from math import ceil
from pathlib import Path
from typing import Dict, List, Optional
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError

# Constants
BASE_URL = "https://atlas.atdw-online.com.au/api/atlas/products"
API_KEY = "ee37502ebe584551a7eeb42bf2e26450"
PAGE_SIZE = 5000
RATE_LIMIT_DELAY = 1.0  # seconds between requests

# Fields to extract
FIELDS = [
    "product_id", "product_number", "product_name", "product_category_id",
    "product_description", "product_image", "addresses", "boundary",
    "comms_ph", "comms_em", "comms_url", "comms_burl", "status",
    "product_update_date", "atdw_expiry_date", "owning_organisation_name",
    "rate_from", "rate_to", "star_rating", "number_of_rooms"
]

# Australian states
STATES = ["NSW", "VIC", "QLD", "SA", "WA", "TAS", "NT", "ACT"]

# Output directory
OUTPUT_DIR = Path("E:/Projects/Coding/Fathom/data/atdw_national")
PROGRESS_FILE = OUTPUT_DIR / "extraction_progress.json"


def make_request(url: str, max_retries: int = 3) -> Dict:
    """
    Make HTTP request with exponential backoff for rate limiting.

    Args:
        url: URL to fetch
        max_retries: Maximum retry attempts for 429 errors

    Returns:
        JSON response as dictionary
    """
    retry_delay = 60  # Start with 60 seconds as per ATDW policy

    for attempt in range(max_retries + 1):
        try:
            req = Request(url)
            req.add_header('User-Agent', 'FATHOM-DataPlatform/1.0')

            with urlopen(req, timeout=30) as response:
                data = response.read()
                # API returns UTF-16 encoded data
                text = data.decode('utf-16')
                return json.loads(text)

        except HTTPError as e:
            if e.code == 429:
                # Rate limited - check Retry-After header
                retry_after = e.headers.get('Retry-After')
                if retry_after:
                    wait_time = int(retry_after)
                else:
                    wait_time = retry_delay

                if attempt < max_retries:
                    print(f"  [Rate Limited] Waiting {wait_time}s before retry {attempt + 1}/{max_retries}...")
                    time.sleep(wait_time)
                    retry_delay *= 2  # Exponential backoff
                    continue
                else:
                    raise Exception(f"Max retries exceeded for rate limiting: {url}")
            else:
                raise Exception(f"HTTP {e.code} error: {e.reason}")

        except URLError as e:
            if attempt < max_retries:
                print(f"  [Network Error] Retrying in 5s... ({attempt + 1}/{max_retries})")
                time.sleep(5)
                continue
            else:
                raise Exception(f"Network error after {max_retries} retries: {e.reason}")

    raise Exception("Request failed after all retries")


def extract_state_data(state: str) -> Dict:
    """
    Extract all tourism products for a given state.

    Args:
        state: State code (NSW, VIC, etc.)

    Returns:
        Dictionary with extraction stats and products
    """
    print(f"\n[{state}] Starting extraction...")
    start_time = time.time()

    # Build field list parameter
    fl = ",".join(FIELDS)

    # Initial request to get total count
    url = f"{BASE_URL}?key={API_KEY}&st={state}&size={PAGE_SIZE}&pge=1&out=json&fl={fl}"

    print(f"[{state}] Fetching page 1...")
    response = make_request(url)

    total_results = response.get('numberOfResults', 0)
    total_pages = ceil(total_results / PAGE_SIZE)

    print(f"[{state}] Found {total_results:,} products ({total_pages} pages)")

    # Collect all products
    all_products = response.get('products', [])
    api_calls = 1

    # Fetch remaining pages
    for page in range(2, total_pages + 1):
        print(f"[{state}] Fetching page {page}/{total_pages}...")

        # Rate limiting delay
        time.sleep(RATE_LIMIT_DELAY)

        url = f"{BASE_URL}?key={API_KEY}&st={state}&size={PAGE_SIZE}&pge={page}&out=json&fl={fl}"
        response = make_request(url)

        products = response.get('products', [])
        all_products.extend(products)
        api_calls += 1

    duration = time.time() - start_time

    # Calculate contact data completeness
    phone_count = sum(1 for p in all_products if p.get('comms_ph'))
    email_count = sum(1 for p in all_products if p.get('comms_em'))
    website_count = sum(1 for p in all_products if p.get('comms_url'))

    stats = {
        "state": state,
        "count": len(all_products),
        "api_calls": api_calls,
        "duration_seconds": round(duration, 2),
        "phone_pct": round(100 * phone_count / len(all_products), 1) if all_products else 0,
        "email_pct": round(100 * email_count / len(all_products), 1) if all_products else 0,
        "website_pct": round(100 * website_count / len(all_products), 1) if all_products else 0,
    }

    print(f"[{state}] Complete: {len(all_products):,} products in {duration:.1f}s")
    print(f"[{state}] Contact data: {stats['phone_pct']}% phone, {stats['email_pct']}% email, {stats['website_pct']}% website")

    return {
        "stats": stats,
        "products": all_products
    }


def flatten_product(product: Dict) -> Dict:
    """
    Flatten nested product data for CSV export.

    Args:
        product: Product dictionary from API

    Returns:
        Flattened dictionary suitable for CSV
    """
    flat = {}

    # Just copy all fields directly from the product
    # The API returns the exact field names we request
    for key, value in product.items():
        # Skip pixel tracking URLs
        if 'pixel' in key.lower():
            continue

        # Handle nested structures
        if key == 'addresses' and isinstance(value, list) and value:
            addr = value[0]
            flat['address_line'] = addr.get('addressLine', '')
            flat['city'] = addr.get('city', '')
            flat['state'] = addr.get('state', '')
            flat['postcode'] = addr.get('postcode', '')
            flat['latitude'] = addr.get('latitude', '')
            flat['longitude'] = addr.get('longitude', '')
        elif key == 'boundary' and isinstance(value, dict):
            flat['boundary_lat'] = value.get('latitude', '')
            flat['boundary_lng'] = value.get('longitude', '')
        elif isinstance(value, (dict, list)):
            flat[key] = json.dumps(value) if value else ''
        else:
            flat[key] = value if value is not None else ''

    return flat


def save_state_csv(state: str, products: List[Dict], timestamp: str) -> Path:
    """
    Save state products to CSV file.

    Args:
        state: State code
        products: List of products
        timestamp: Timestamp for filename

    Returns:
        Path to saved CSV file
    """
    csv_file = OUTPUT_DIR / f"atdw_{state.lower()}_{timestamp}.csv"

    if not products:
        print(f"[{state}] No products to save")
        return csv_file

    # Flatten products
    flat_products = [flatten_product(p) for p in products]

    # Get all unique fields
    all_fields = set()
    for p in flat_products:
        all_fields.update(p.keys())

    fieldnames = sorted(all_fields)

    # Write CSV with UTF-8-BOM for Excel compatibility
    with open(csv_file, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(flat_products)

    print(f"[{state}] Saved to {csv_file.name}")
    return csv_file


def load_progress() -> Dict:
    """Load extraction progress from file."""
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {
        "started": datetime.now().isoformat(),
        "completed_states": [],
        "failed_states": [],
        "stats": []
    }


def save_progress(progress: Dict):
    """Save extraction progress to file."""
    progress["last_updated"] = datetime.now().isoformat()
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)


def create_consolidated_csv(all_products: List[Dict], timestamp: str) -> Path:
    """
    Create consolidated CSV with all states.

    Args:
        all_products: List of all products from all states
        timestamp: Timestamp for filename

    Returns:
        Path to consolidated CSV
    """
    csv_file = OUTPUT_DIR / f"atdw_australia_complete_{timestamp}.csv"

    # Flatten and deduplicate by product_id
    seen_ids = set()
    unique_products = []

    for product in all_products:
        product_id = product.get('product_id')
        if product_id and product_id not in seen_ids:
            seen_ids.add(product_id)
            unique_products.append(flatten_product(product))

    # Get all unique fields
    all_fields = set()
    for p in unique_products:
        all_fields.update(p.keys())

    fieldnames = sorted(all_fields)

    # Write consolidated CSV
    with open(csv_file, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(unique_products)

    print(f"\n[Consolidated] Saved {len(unique_products):,} unique products to {csv_file.name}")
    return csv_file


def create_summary_report(progress: Dict, timestamp: str, total_duration: float) -> Path:
    """
    Create summary report of extraction.

    Args:
        progress: Progress dictionary with stats
        timestamp: Timestamp for filename
        total_duration: Total extraction duration in seconds

    Returns:
        Path to report file
    """
    report_file = OUTPUT_DIR / f"extraction_report_{timestamp}.txt"

    stats = progress.get('stats', [])
    total_products = sum(s['count'] for s in stats)
    total_api_calls = sum(s['api_calls'] for s in stats)

    with open(report_file, 'w') as f:
        f.write("ATDW National Tourism Data Extraction Report\n")
        f.write("=" * 60 + "\n\n")

        f.write(f"Extraction Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total Duration: {total_duration:.1f} seconds ({total_duration/60:.1f} minutes)\n")
        f.write(f"Total Products: {total_products:,}\n")
        f.write(f"Total API Calls: {total_api_calls}\n")
        f.write(f"States Extracted: {len(stats)}/8\n\n")

        f.write("Breakdown by State:\n")
        f.write("-" * 60 + "\n")

        for stat in sorted(stats, key=lambda x: x['count'], reverse=True):
            f.write(f"\n{stat['state']:3s}: {stat['count']:6,} products\n")
            f.write(f"     API calls: {stat['api_calls']}, Duration: {stat['duration_seconds']:.1f}s\n")
            f.write(f"     Contact data: {stat['phone_pct']:.1f}% phone, {stat['email_pct']:.1f}% email, {stat['website_pct']:.1f}% website\n")

        if progress.get('failed_states'):
            f.write("\n\nFailed States:\n")
            f.write("-" * 60 + "\n")
            for state in progress['failed_states']:
                f.write(f"  - {state}\n")

        f.write("\n\nOutput Files:\n")
        f.write("-" * 60 + "\n")
        f.write(f"  State CSVs: {len(stats)} files (atdw_{{state}}_{{timestamp}}.csv)\n")
        f.write(f"  Consolidated CSV: atdw_australia_complete_{timestamp}.csv\n")
        f.write(f"  Progress tracking: extraction_progress.json\n")

    print(f"\n[Report] Saved to {report_file.name}")
    return report_file


def main():
    """Main extraction process."""
    print("ATDW National Tourism Data Extraction")
    print("=" * 60)

    overall_start = time.time()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load progress
    progress = load_progress()
    completed_states = set(progress.get('completed_states', []))

    if completed_states:
        print(f"\nResuming extraction (already completed: {', '.join(sorted(completed_states))})")

    # Extract each state
    all_products = []

    for state in STATES:
        if state in completed_states:
            print(f"\n[{state}] Skipping (already completed)")
            continue

        try:
            result = extract_state_data(state)

            # Save state CSV
            save_state_csv(state, result['products'], timestamp)

            # Update progress
            progress['stats'].append(result['stats'])
            progress['completed_states'].append(state)
            save_progress(progress)

            # Add to consolidated list
            all_products.extend(result['products'])

        except KeyboardInterrupt:
            print("\n\n[Interrupted] Saving progress...")
            save_progress(progress)
            print(f"Progress saved. Run again to resume from {state}.")
            sys.exit(0)

        except Exception as e:
            print(f"\n[{state}] ERROR: {e}")
            progress['failed_states'].append(state)
            save_progress(progress)
            continue

    # Create consolidated CSV
    if all_products:
        create_consolidated_csv(all_products, timestamp)

    # Create summary report
    total_duration = time.time() - overall_start
    create_summary_report(progress, timestamp, total_duration)

    # Final summary
    print("\n" + "=" * 60)
    print("EXTRACTION COMPLETE")
    print("=" * 60)

    total_products = sum(s['count'] for s in progress['stats'])
    total_api_calls = sum(s['api_calls'] for s in progress['stats'])

    print(f"\nTotal Products: {total_products:,}")
    print(f"States Completed: {len(progress['completed_states'])}/8")
    print(f"API Calls: {total_api_calls}")
    print(f"Duration: {total_duration:.1f}s ({total_duration/60:.1f} minutes)")

    if progress.get('failed_states'):
        print(f"\nFailed States: {', '.join(progress['failed_states'])}")

    print(f"\nOutput Directory: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
