# ATDW National Extraction - Ready to Execute

## Status: READY ✓

All scripts and configurations are complete. Waiting for stable internet connection to execute.

## What We're Extracting

**Total Expected:** 100,000-200,000 Australian tourism products
**API Calls:** ~24-40 calls (5000 products per page)
**Duration:** ~24-40 seconds (1 req/sec for data-intensive queries)
**Cost:** $0 (FREE)

## Fields Being Extracted (21 fields)

From testing, these fields are confirmed working:

### Core Fields
- `productId` - Unique identifier
- `productNumber` - ATDW product number (e.g., AU1529120)
- `productName` - Business name
- `productCategoryId` - Category (RESTAURANT, ACCOMM, ATTRACTION, etc.)
- `productDescription` - Full description
- `productImage` - Image URL

### Contact Fields (90%+ completeness)
- `comms_ph` - Phone (88.8% have it)
- `comms_em` - Email (91.0% have it)
- `comms_url` - Website (98.7% have it)
- `comms_burl` - Booking URL (optional)

### Address Fields
- `addresses` - Full address array with:
  - `address_line` - Street address
  - `address_line2` - Additional address
  - `city` - City/suburb
  - `state` - State code (NSW, VIC, etc.)
  - `postcode` - Postcode
  - `country` - Australia
  - `area` - Area classification
  - `region` - Regional classification

### Geographic
- `boundary` - Coordinates (lat,lng)

### Metadata
- `status` - ACTIVE/INACTIVE
- `product_update_date` - Last updated
- `atdw_expiry_date` - Listing expiry
- `owning_organisation_name` - Owner organization

### Pricing (for accommodation)
- `rate_from` - Minimum rate
- `rate_to` - Maximum rate
- `star_rating` - Star rating (1-5)
- `number_of_rooms` - Room count

## Extraction Strategy

**Method:** State-by-state extraction (8 states)
**Page Size:** 5000 (maximum efficiency)
**Rate Limit:** 1 request per second (data-intensive queries)
**Resumable:** Yes - saves progress after each state
**Error Handling:** Failed states logged, extraction continues

### States (in order)
1. NSW (New South Wales) - ~30,000-60,000 products
2. VIC (Victoria) - ~20,000-40,000 products
3. QLD (Queensland) - ~20,000-40,000 products
4. SA (South Australia) - ~8,000-15,000 products
5. WA (Western Australia) - ~6,000-12,000 products
6. TAS (Tasmania) - ~4,000-8,000 products
7. NT (Northern Territory) - ~1,500-3,000 products
8. ACT (Australian Capital Territory) - ~1,200 products (tested)

## How to Execute

### When Internet is Stable:

```bash
# Run full national extraction
python scripts/extract_atdw_national.py
```

### If Interrupted:

The script automatically saves progress. Just run it again:
```bash
# Resume from where it left off
python scripts/extract_atdw_national.py
```

It will skip completed states and continue.

## Output Files

All files saved to: `data/atdw_national/`

### Individual State CSVs
- `atdw_nsw_YYYYMMDD_HHMMSS.csv`
- `atdw_vic_YYYYMMDD_HHMMSS.csv`
- `atdw_qld_YYYYMMDD_HHMMSS.csv`
- `atdw_sa_YYYYMMDD_HHMMSS.csv`
- `atdw_wa_YYYYMMDD_HHMMSS.csv`
- `atdw_tas_YYYYMMDD_HHMMSS.csv`
- `atdw_nt_YYYYMMDD_HHMMSS.csv`
- `atdw_act_YYYYMMDD_HHMMSS.csv`

### Consolidated File
- `atdw_australia_complete_YYYYMMDD_HHMMSS.csv`
  - All states combined
  - Deduplicated by productId
  - UTF-8-BOM encoding (Excel-friendly)

### Progress & Reports
- `extraction_progress.json` - Resumable progress tracking
- `atdw_extraction_report_YYYYMMDD_HHMMSS.txt` - Full statistics

## Expected Statistics

Based on ACT test (1,160 products):

**Contact Data Completeness:**
- Phone: ~89%
- Email: ~91%
- Website: ~99%

**Category Distribution (estimated):**
- Accommodation: ~36%
- Attractions: ~25%
- Tours: ~17%
- Restaurants: ~13%
- Events: ~5%
- Other: ~4%

## Progress Tracking

The script saves to `extraction_progress.json` after each state:

```json
{
  "started": "2025-10-25T20:45:00",
  "completed_states": ["NSW", "VIC", "QLD"],
  "failed_states": [],
  "stats": [...],
  "last_updated": "2025-10-25T20:48:23"
}
```

## Error Handling

- **HTTP 429 (Rate Limited):** Automatic retry with exponential backoff (60s, 120s, 240s)
- **Network Errors:** Logged, marked as failed, extraction continues
- **Keyboard Interrupt (Ctrl+C):** Saves progress cleanly, can resume
- **Failed State:** Logged to progress file, can retry individually

## Comparison with Existing Data

Once extracted, you can compare with your existing Byron Bay datasets:

**Byron Bay Coverage Comparison:**
- ATDW: 322 products (tested)
- Google Places: 920 products
- Foursquare: 363 products
- TripAdvisor: 275 products

**ATDW Advantages:**
- Official Australian tourism data
- 99% website coverage
- 91% email coverage
- Free API
- Clean, structured data

## Next Steps (When Internet Stable)

1. ✅ **Run extraction:** `python scripts/extract_atdw_national.py`
2. ⏳ **Wait ~5-8 seconds** for completion
3. ✅ **Check results:**
   - Total products fetched
   - Category breakdown
   - Contact data completeness
   - Any failed states
4. ✅ **Compare with existing datasets** (Google/Foursquare/TripAdvisor)
5. ✅ **Merge into FATHOM database**

## Technical Details

**Client:** `src/datasources/atdw_client.py`
- Rate limiting: 5 req/sec
- Pagination: Up to 5000 per page
- Retry logic: 3 attempts with exponential backoff
- Field selection: Optimized for contact data

**Script:** `scripts/extract_atdw_national.py`
- Resumable: ✓
- Progress tracking: ✓
- Error handling: ✓
- UTF-8-BOM encoding: ✓

## Questions Resolved

✅ **Category field?** Yes - `productCategoryId` works (was using wrong field name)
✅ **Contact fields?** Yes - `comms_ph`, `comms_em`, `comms_url` (90%+ coverage)
✅ **Address data?** Yes - Full structured addresses in `addresses` array
✅ **Resumable?** Yes - Saves progress after each state
✅ **Field names?** Documented - tested with actual API responses
✅ **Using fetch-expert?** Not needed - direct Python script is sufficient

All ready to go when internet is stable! 🚀
