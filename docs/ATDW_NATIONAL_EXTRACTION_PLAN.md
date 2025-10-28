# ATDW National Data Extraction Plan

## Objective

Extract complete Australian tourism data from ATDW (50,000+ products) with minimal API calls while staying within rate limits and best practices.

## Data Scope

**ATDW Database Size:** ~100,000-200,000+ tourism products across Australia

**Categories:**
- ACCOMM (Accommodation)
- ATTRACTION (Attractions)
- TOUR (Tours)
- RESTAURANT (Restaurants & Cafes)
- EVENT (Events)
- HIRE (Equipment Hire)
- TRANSPORT (Transport Services)
- GENERAL_SERVICE (General Services)
- DESTINATION (Destination Info)
- JOURNEY (Journeys)

**Geographic Coverage:**
- States: NSW, VIC, QLD, SA, WA, TAS, NT, ACT
- ~100,000-200,000 products total (user confirmed)

## API Constraints & Optimization

### Rate Limiting
- **ATDW Policy:** No specific numeric limit, returns HTTP 429 when exceeded
- **Our Implementation:** 5 requests/second (conservative)
- **Retry-After Header:** 60 seconds default
- **Exponential Backoff:** Implemented in client

### Pagination Limits
- **Maximum page size:** 5000 results (tested empirically)
- **Optimal page size:** 1000-5000 (depends on response size)
- **Default:** 1000 results per page

### Field Selection
- **Critical Fields to Request:**
  - `product_id`, `product_number`, `product_name`, `product_category`
  - `product_description`, `product_image`
  - `address` (includes all address components)
  - `comms_ph`, `comms_em`, `comms_url`, `comms_burl` (contact fields)
  - `rate_from`, `rate_to`, `starrating`, `number_of_rooms`
  - `status`, `next_occurrence`
  - Geographic: boundary (coordinates)

## Extraction Strategies (Options)

### Option 1: Single National Query (FASTEST)
**Approach:** One search query for all of Australia

**Pros:**
- Minimal API calls (~10-11 calls for 50,000 products at 5000/page)
- Fastest execution (~2-3 seconds at 5 req/sec)
- Simplest implementation

**Cons:**
- No granular control
- Can't track progress by region
- Harder to resume if interrupted

**API Calls Estimate:**
```
Total products: 100,000-200,000
Page size: 5000
API calls: 100,000 / 5000 = 20 calls (or 40 for 200K)
Time: 20-40 calls / 5 req/sec = 4-8 seconds
```

### Option 2: By State (RECOMMENDED)
**Approach:** 8 separate queries, one per state

**Pros:**
- Progress tracking by state
- Can resume if interrupted
- Easier to identify data quality issues by region
- Can run states in parallel (if we want to optimize further)
- Better error handling

**Cons:**
- Slightly more API calls if states are small

**API Calls Estimate:**
```
States: NSW, VIC, QLD, SA, WA, TAS, NT, ACT (8 states)
Products per state: ~12,500-25,000 avg (varies widely)
Page size: 5000
API calls per state: ~3-5 calls avg
Total API calls: ~24-40 calls
Time: 24-40 calls / 5 req/sec = ~5-8 seconds
```

### Option 3: By Category (GRANULAR)
**Approach:** Extract each category separately

**Pros:**
- Category-specific data quality analysis
- Can prioritize high-value categories (ACCOMM, RESTAURANT)
- Better error isolation

**Cons:**
- More API calls
- Products may appear in multiple categories (need deduplication)

**API Calls Estimate:**
```
Categories: 10 types
Products per category: ~5,000 avg (varies)
API calls per category: ~1-2 calls
Total API calls: ~15-20 calls
Time: ~3-4 seconds
```

### Option 4: Hybrid - By State + Category (MAXIMUM CONTROL)
**Approach:** Extract each category within each state

**Pros:**
- Maximum granularity
- Best for incremental updates
- Detailed quality metrics
- Easy to resume/retry specific segments

**Cons:**
- Most API calls
- Need deduplication across segments
- More complex implementation

**API Calls Estimate:**
```
States: 8
Categories: 10
Segments: 80 total
Products per segment: ~625 avg
API calls per segment: ~1 call
Total API calls: ~80 calls
Time: 80 calls / 5 req/sec = ~16 seconds
```

## Recommended Strategy: BY STATE

**Rationale:**
- Balances speed (16 calls, ~3 seconds) with control
- Aligns with Australian geographic structure
- Easy progress tracking
- Can resume if interrupted
- Logical data organization for FATHOM platform

### Implementation Plan

#### Phase 1: Single State Test (NSW)
1. Test extraction on NSW (largest state)
2. Validate data quality
3. Estimate actual API call count
4. Confirm field completeness
5. Test CSV export with UTF-8-BOM

#### Phase 2: State-by-State Extraction
Extract each state sequentially:

1. **NSW** (New South Wales) - Largest state
2. **VIC** (Victoria) - Second largest
3. **QLD** (Queensland) - Major tourism state
4. **SA** (South Australia)
5. **WA** (Western Australia)
6. **TAS** (Tasmania)
7. **NT** (Northern Territory)
8. **ACT** (Australian Capital Territory)

#### Phase 3: Consolidation
1. Combine all state CSVs
2. Deduplicate by `product_id`
3. Validate total count
4. Generate statistics report

## Field Selection for National Extract

```python
fields = [
    # Core identifiers
    'product_id',
    'product_number',
    'product_name',
    'product_category',

    # Content
    'product_description',
    'product_image',

    # Address (returns all components)
    'address',

    # Contact (CRITICAL - not in default response)
    'comms_ph',
    'comms_em',
    'comms_url',
    'comms_burl',

    # Pricing & ratings
    'rate_from',
    'rate_to',
    'starrating',
    'number_of_rooms',

    # Status & dates
    'status',
    'product_update_date',
    'next_occurrence',

    # Geographic
    'boundary'  # Coordinates
]
```

## Expected Output

### File Structure
```
data/atdw_national/
├── atdw_nsw_20251025_HHMMSS.csv
├── atdw_vic_20251025_HHMMSS.csv
├── atdw_qld_20251025_HHMMSS.csv
├── atdw_sa_20251025_HHMMSS.csv
├── atdw_wa_20251025_HHMMSS.csv
├── atdw_tas_20251025_HHMMSS.csv
├── atdw_nt_20251025_HHMMSS.csv
├── atdw_act_20251025_HHMMSS.csv
└── atdw_australia_complete_20251025_HHMMSS.csv  # Consolidated
```

### Statistics Report
```
ATDW National Extraction Report
================================

Extraction Date: 2025-10-25
Total Products: 50,234
Total API Calls: 16
Execution Time: 3.2 seconds

State Breakdown:
- NSW: 15,234 (30.3%)
- VIC: 12,456 (24.8%)
- QLD: 11,234 (22.4%)
- SA: 4,567 (9.1%)
- WA: 3,456 (6.9%)
- TAS: 2,123 (4.2%)
- NT: 876 (1.7%)
- ACT: 288 (0.6%)

Category Breakdown:
- Accommodation: 18,234 (36.3%)
- Attractions: 12,456 (24.8%)
- Tours: 8,765 (17.4%)
- Restaurants: 6,543 (13.0%)
- Events: 2,345 (4.7%)
- Other: 1,891 (3.8%)

Contact Data Completeness:
- Phone: 45,123 (89.8%)
- Email: 46,234 (92.0%)
- Website: 49,876 (99.3%)
- Booking URL: 32,456 (64.6%)
```

## Cost Analysis

### API Calls (By State Strategy)
- **Total Calls:** ~16-20
- **Rate:** 5 calls/second (conservative)
- **Duration:** ~3-4 seconds
- **Cost:** FREE (ATDW search endpoint is free)

### Comparison with Other APIs

| API | Australia Coverage | Est. Cost |
|-----|-------------------|-----------|
| **ATDW** | 100,000-200,000 products | **$0** (free) |
| Google Places | ~500,000 places | ~$16,000 |
| Foursquare | ~300,000 places | ~$6,000 |
| TripAdvisor | Limited by 10/search | ~$0 (free but incomplete) |

**ATDW is the most cost-effective source for Australian tourism data.**

## Error Handling & Resilience

### Retry Strategy
- HTTP 429: Exponential backoff (60s, 120s, 240s)
- Network errors: Retry 3x with backoff
- Failed state: Log and continue to next state

### Progress Tracking
```python
# Save progress after each state
progress = {
    'completed_states': ['NSW', 'VIC'],
    'failed_states': [],
    'last_updated': '2025-10-25T20:45:00',
    'total_products': 27690
}
```

### Resume Capability
- Check which state CSVs already exist
- Skip completed states
- Resume from last incomplete state

## Data Quality Validation

After extraction, validate:
1. **Deduplication:** Ensure no duplicate `product_id`
2. **Completeness:** Verify expected state counts
3. **Contact Data:** Check % with phone/email/website
4. **Geographic:** Validate coordinates are in Australia
5. **Categories:** Ensure all 10 categories represented

## Implementation Timeline

1. **Create extraction script** (~15 min)
2. **Test on NSW** (~5 min)
3. **Run full national extraction** (~1 min)
4. **Consolidate and validate** (~5 min)

**Total Time:** ~30 minutes

## Next Steps

1. Review and approve this plan
2. Choose extraction strategy (recommend: By State)
3. Create extraction script
4. Test on NSW
5. Execute full national extraction
6. Generate statistics report
7. Compare with existing Google/Foursquare data

## Questions to Resolve

1. Do we want to exclude INACTIVE products?
2. Should we include EVENT category (date-specific)?
3. Do we want to set up incremental updates (delta endpoint)?
4. Should we fetch product details for high-value products only?
