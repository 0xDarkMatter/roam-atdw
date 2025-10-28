"""
Comprehensive ATDW API testing:
- Status filtering (active vs inactive)
- Location-based searches (Melbourne, Yarra Ranges)
- RTO code filtering
"""

import json
from urllib.request import urlopen, Request
import time

API_KEY = "ee37502ebe584551a7eeb42bf2e26450"
BASE_URL = "https://atlas.atdw-online.com.au/api/atlas/products"

def get_count(params_str, description=""):
    """Get product count with custom parameters."""
    url = f"{BASE_URL}?key={API_KEY}&size=1&out=json"
    if params_str:
        url += f"&{params_str}"

    req = Request(url)
    req.add_header('User-Agent', 'FATHOM-DataPlatform/1.0')

    try:
        with urlopen(req, timeout=30) as response:
            data = response.read()
            text = data.decode('utf-16')
            result = json.loads(text)
            count = result.get('numberOfResults', 0)
            print(f"  {description:<40} {count:>10,}")
            return count
    except Exception as e:
        print(f"  {description:<40} ERROR: {e}")
        return None

print("="*80)
print("ATDW COMPREHENSIVE API TEST")
print("="*80)

# TEST 1: Status filtering investigation
print("\n[TEST 1] Status Parameter Investigation:")
print("-"*80)
print("Testing if status parameter works correctly...")
time.sleep(1)

baseline = get_count("", "No filter (baseline)")
time.sleep(1)

# Test with NSW to see behavior
nsw_no_status = get_count("st=NSW", "NSW - no status filter")
time.sleep(1)
nsw_active = get_count("st=NSW&status=A", "NSW - status=A (Active)")
time.sleep(1)
nsw_inactive = get_count("st=NSW&status=I", "NSW - status=I (Inactive)")
time.sleep(1)

print("\nAnalysis:")
if nsw_active == nsw_no_status:
    print("  -> API defaults to Active products only (status=A)")
    print("  -> status=I may be returning same results (API bug or misunderstanding)")
elif nsw_active + nsw_inactive == nsw_no_status:
    print("  -> Status filtering working correctly")
    print("  -> No filter returns both active AND inactive")
else:
    print("  -> Unexpected behavior - need to investigate further")

# TEST 2: Location-based searches
print("\n[TEST 2] Location-Based Searches:")
print("-"*80)
print("Testing city/region-based filtering...")
time.sleep(1)

# Melbourne searches
melbourne_city = get_count("city=Melbourne", "Melbourne (city parameter)")
time.sleep(1)
melbourne_dest = get_count("dest=Melbourne", "Melbourne (dest parameter)")
time.sleep(1)
melbourne_area = get_count("area=Melbourne", "Melbourne (area parameter)")
time.sleep(1)

# Yarra Ranges
yarra_city = get_count("city=Yarra Ranges", "Yarra Ranges (city parameter)")
time.sleep(1)
yarra_dest = get_count("dest=Yarra Ranges", "Yarra Ranges (dest parameter)")
time.sleep(1)
yarra_area = get_count("area=Yarra Ranges", "Yarra Ranges (area parameter)")
time.sleep(1)

# TEST 3: RTO code filtering
print("\n[TEST 3] RTO Code Filtering:")
print("-"*80)
print("Testing RTO (Regional Tourism Organization) filtering...")
time.sleep(1)

# Common Victorian RTOs
rto_tests = [
    ("rto=VIC01", "Melbourne RTO (VIC01)"),
    ("rto=VIC02", "Phillip Island RTO (VIC02)"),
    ("rto=VIC03", "Yarra Valley RTO (VIC03)"),
    ("rtoId=VIC01", "Melbourne RTO (rtoId parameter)"),
]

for param, desc in rto_tests:
    get_count(param, desc)
    time.sleep(1)

# TEST 4: Boundary/coordinate search
print("\n[TEST 4] Geographic Boundary Search:")
print("-"*80)
print("Testing geographic filtering...")
time.sleep(1)

# Melbourne area (approximate bounding box)
# lat: -37.7-37.9, lng: 144.9-145.1
melbourne_bounds = get_count(
    "latmax=-37.7&latmin=-37.9&lngmax=145.1&lngmin=144.9",
    "Melbourne bounding box"
)
time.sleep(1)

# TEST 5: Text search
print("\n[TEST 5] Text Search:")
print("-"*80)
print("Testing keyword search...")
time.sleep(1)

text_search = get_count("query=Melbourne", "Text search: Melbourne")
time.sleep(1)

# SUMMARY
print("\n" + "="*80)
print("KEY FINDINGS:")
print("="*80)
print("\n1. Status Filtering:")
print(f"   - Baseline (no filter): {baseline:,}")
print(f"   - NSW no status: {nsw_no_status:,}")
print(f"   - NSW active: {nsw_active:,}")
print(f"   - NSW inactive: {nsw_inactive:,}")

print("\n2. Location Searches:")
print("   Check which parameter works best for location filtering")

print("\n3. Next Steps:")
if nsw_active == nsw_inactive == nsw_no_status:
    print("   -> Status parameter may not work as expected")
    print("   -> API may only return active products by default")
    print("   -> Need to check API documentation for correct status values")
else:
    print("   -> Re-run extraction with explicit status=A to be safe")
    print("   -> Consider extracting inactive products separately if needed")

print("="*80)
