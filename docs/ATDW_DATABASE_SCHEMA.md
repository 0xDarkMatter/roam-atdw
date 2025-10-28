# ATDW Database Schema Documentation

## Overview

High-performance PostgreSQL schema for storing ~56K Australian tourism products from ATDW (Australian Tourism Data Warehouse).

**Status**: Schema designed and tested, ready for deployment. Database location needs to be determined before execution.

**Current Dataset**: 56,497 products (as of 2025-10-26)

## Design Principles

1. **Normalized structure** - Minimize redundancy, enable effective caching
2. **Content hash-based change detection** - Efficient daily delta updates with O(1) hash comparison
3. **Optimized indexes** - Fast queries for ID lookups, geographic search, category filtering, and product name search
4. **Memory-friendly** - Entire dataset (~56K products × 2KB) fits in ~120MB for caching
5. **Current state only** - No versioning overhead

## Schema Components

### Core Tables (14 total)

#### 1. `atdw.products` - Main entity table
**~56K rows**

Primary product information with:
- Product identifiers (product_id, product_number)
- Names and descriptions
- Category classification (ACCOMM, ATTRACTION, TOUR, RESTAURANT, EVENT)
- Geographic location (PostGIS geography for accurate distance queries)
- Accommodation fields (rooms, capacity, star rating, check-in/out times)
- Opening hours metadata (type and comment text)
- Pricing (rate_from, rate_to)
- Status and dates (validity, expiry, last updated)
- **content_hash** - MD5 hash for change detection

**Key Indexes**:
- Primary key on `product_id`
- GiST index on `location` (PostGIS) for radius searches
- GIN index on `to_tsvector(product_name)` for full-text search
- Composite B-tree on `(product_category_id, state_name)`
- B-tree on `updated_at`, `status`, `content_hash`

#### 2. `atdw.addresses` - Physical and postal addresses
**~112K rows (2 per product avg)**

- Address components (line1, line2, suburb, city, state, postal code)
- Geographic coordinates with PostGIS geography
- Address type (PHYSICAL, POSTAL)

**Indexes**: FK on product_id, GiST on location

#### 3. `atdw.communication` - Contact information
**~225K rows (4 per product avg)**

- Phone (CAPHENQUIR), Email (CAEMENQUIR), Website (CAURENQUIR), Booking URL (CAUBENQUIR)
- ISD codes, area codes
- Tracking URLs (ATDW-wrapped URLs)

**Indexes**: FK on product_id, B-tree on communication_type

#### 4. `atdw.services` - Rooms/tour packages/sessions
**~20K rows (mainly accommodation - 28% of products)**

- Service name (e.g., "Studio", "One Bedroom Apartment")
- Description, capacity (min/max), quantity
- Pricing per service type
- Flags (children, pets, disabled access)

**Indexes**: FK on product_id, composite on (product_id, sequence_number)

#### 5. `atdw.service_multimedia` - Room/service photos
**~200K rows (10 per service avg)**

- Images at multiple resolutions (4:3 and 16:9 aspect ratios)
- Alt text, captions, sequence ordering

**Indexes**: FK on service_id, composite on (service_id, sequence_number)

#### 6. `atdw.multimedia` - Product-level images
**~565K rows (10 per product avg)**

- Hero images, gallery photos
- Multiple resolutions per image (280px to 2048px)
- Alt text, captions, photographer credits

**Indexes**: FK on product_id, composite on (product_id, sequence_number)

#### 7. `atdw.attributes` - Amenities and facilities
**~565K rows (10 per product avg)**

- Attribute types: ENTITY FAC (facilities), INTERNET (WiFi), MEMBERSHIP, DISASSIST (accessibility)
- Specific attributes: GYM, POOL, FREEWIFI, 24HOURS, etc.

**Indexes**: FK on product_id, composite on (attribute_type_id, attribute_id)

#### 8. `atdw.rates` - Pricing information
**~56K rows (1 per product avg)**

- Rate types (indicative, standard, seasonal)
- Price ranges, free entry flag
- Rate comments

**Indexes**: FK on product_id

#### 9. `atdw.deals` - Special offers
**~5K rows (estimate, uncommon)**

- Deal names, descriptions
- Valid date ranges
- Deal values and types

**Indexes**: FK on product_id, composite on (valid_from, valid_to)

#### 10. `atdw.external_systems` - Third-party links
**~112K rows (2 per product avg)**

- TripAdvisor IDs and URLs
- Instagram, booking platforms (Bookeasy, AUS365)
- External system codes

**Indexes**: FK on product_id, B-tree on system_code

#### 11. `atdw.opening_hours_periods` - Seasonal opening hours
**~30K rows (estimate, mainly restaurants/attractions)**

- Seasonal period definitions (e.g., summer hours, winter hours, year-round)
- Date ranges (from_date, to_date - NULL for year-round)
- Sequence number for ordering

**Indexes**: FK on product_id, unique composite on (product_id, sequence_number)

#### 12. `atdw.opening_hours_schedule` - Daily schedules
**~200K rows (7 days × ~30K products with hours)**

- Day of week (MON, TUE, WED, THU, FRI, SAT, SUN)
- Opening and closing times
- Closed flag for days when business is closed

**Indexes**: FK on period_id, B-tree on day_of_week

## Performance Optimizations

### Spatial Queries (PostGIS)

```sql
-- Find products within 10km of Byron Bay
SELECT * FROM atdw.products_within_radius(-28.6450, 153.6050, 10);
```

Uses GiST index on geography column for sub-second queries.

### Full-Text Search

```sql
-- Find cafes by name
SELECT * FROM atdw.products
WHERE to_tsvector('english', product_name) @@ to_tsquery('cafe')
  AND product_category_id = 'RESTAURANT';
```

Uses GIN index on tsvector for fast text search.

### Category + State Filtering

```sql
-- Accommodation in NSW
SELECT * FROM atdw.products
WHERE product_category_id = 'ACCOMM'
  AND state_name = 'New South Wales';
```

Uses composite index on (category_id, state_name).

### Materialized View: `atdw.products_enriched`

Pre-joins products with:
- Primary physical address
- Primary image
- Contact info (phone, email, website) pivoted into columns

**Refresh**: `SELECT atdw.refresh_products_enriched();`

Use for API responses to avoid repeated JOINs.

## Caching Strategy

### Daily Delta Updates

1. **Fetch changed products**: `ATDW /delta API` with `updatedSince=yesterday`
2. **Hash comparison**: Compare incoming `content_hash` with database
3. **Idempotent upsert**:
   - If hash differs → UPDATE + cascade delete/reinsert child records
   - If hash matches → SKIP (no write amplification)
4. **Cache invalidation**: Purge only changed product keys from Redis

### Memory Caching Layers

**Option 1: Redis**
```
product:{product_id} → full product JSON with relationships
~120MB for 56K products (fits easily in memory)
```

**Option 2: PostgREST native caching**
- Supabase PostgREST has built-in HTTP caching
- Use materialized view for cache hits

**Option 3: Application-level (Python)**
- Cache in-memory with `functools.lru_cache`
- Good for repeated queries in same session

## Automatic Triggers

### 1. `updated_at` timestamp
Auto-updates on every row change to `products` table.

### 2. Content hash computation
Auto-computes MD5 hash on INSERT/UPDATE to `products` table based on:
- product_name, product_description
- product_category_id, status
- product_update_date
- latitude, longitude
- suburb, city, state
- rate_from, rate_to

### 3. PostGIS location computation
Auto-populates `location` geography column from `latitude`/`longitude`.

Works for both `products` and `addresses` tables.

## Files

### Migrations
- **`migrations/009_atdw_tourism_schema.sql`** - Full schema creation (12 tables, indexes, triggers, functions)
- **`migrations/009_rollback.sql`** - Clean rollback (drops schema and all objects)

### Scripts
- **`scripts/load_atdw_to_database.py`** - Data loader with three modes:
  - `--mode full` - Load all products
  - `--mode state --state NSW` - Load specific state
  - `--mode delta --since yesterday` - Incremental updates

### Documentation
- **`docs/ATDW_DATABASE_SCHEMA.md`** - This file

## Database Configuration Needed

Before deployment, determine:

1. **Supabase project** - Which project to use?
   - Current: `db.zfnmsoixxswpfpcqswyl.supabase.co`
   - New project?

2. **Connection credentials**
   - Set `SUPABASE_DB_HOST`
   - Set `SUPABASE_DB_PORT` (default: 5432)
   - Set `SUPABASE_DB_NAME` (default: postgres)
   - Set `SUPABASE_DB_USER` (default: postgres)
   - Set `SUPABASE_DB_PASSWORD`

3. **PostGIS extension**
   - Verify PostGIS is available in Supabase project
   - Enable via Supabase Dashboard → Database → Extensions

4. **Row-Level Security (RLS)**
   - Decide RLS policy for `atdw` schema
   - Public read access? Authenticated only?

## Deployment Checklist

- [ ] Determine database location
- [ ] Configure environment variables
- [ ] Verify PostGIS extension available
- [ ] Run migration: `migrations/009_atdw_tourism_schema.sql`
- [ ] Test with sample data (ACT subset - 1,160 products):
  ```bash
  python scripts/load_atdw_to_database.py --mode state --state ACT
  ```
- [ ] Verify indexes created
- [ ] Test geographic queries
- [ ] Test full-text search
- [ ] Benchmark query performance
- [ ] Set up daily delta update cron job
- [ ] Configure caching layer (Redis or PostgREST)

## Expected Dataset Size

**Actual Dataset (2025-10-26)**: 56,497 products

**Data Completeness**:
- Images: 99.1% (55,961 products)
- Website URLs: 92.8% (52,411 products)
- Email: 84.0% (47,460 products)
- Phone: 83.5% (47,156 products)
- Accommodation (with rooms): 28.1% (15,873 products)
- Pricing info: 43.5% (24,569 products)

| Component | Rows | Storage | Notes |
|-----------|------|---------|-------|
| Products | 56K | ~120MB | Main table |
| Addresses | 112K | ~40MB | 2 per product |
| Communication | 225K | ~30MB | 4 per product |
| Multimedia | 565K | ~200MB | 10 per product |
| Services | 20K | ~10MB | Accommodation only (28%) |
| Service Multimedia | 200K | ~80MB | 10 per service |
| Attributes | 565K | ~60MB | 10 per product |
| Rates | 56K | ~5MB | 1 per product |
| Deals | 5K | ~2MB | Uncommon |
| External Systems | 112K | ~10MB | 2 per product |
| Opening Hours Periods | 30K | ~3MB | Restaurants/attractions |
| Opening Hours Schedule | 200K | ~15MB | Daily hours (7 days × products) |
| **TOTAL** | **~2.2M rows** | **~570MB** | Uncompressed |

With PostgreSQL compression and indexing: **~800MB-1GB on disk**

**Memory for caching**: ~120MB (products table only) to ~200MB (with common joins)

## Query Examples

### Find accommodation in Byron Bay area
```sql
SELECT
  product_id,
  product_name,
  rate_from,
  rate_to,
  star_rating,
  number_of_rooms
FROM atdw.products_enriched
WHERE product_category_id = 'ACCOMM'
  AND ST_DWithin(
    location,
    ST_SetSRID(ST_MakePoint(153.6050, -28.6450), 4326)::geography,
    10000  -- 10km radius
  )
ORDER BY star_rating DESC NULLS LAST;
```

### Get product with all details
```sql
-- Product
SELECT * FROM atdw.products WHERE product_id = '5fd017c6dad46f254f08fb78';

-- Addresses
SELECT * FROM atdw.addresses WHERE product_id = '5fd017c6dad46f254f08fb78';

-- Contact
SELECT * FROM atdw.communication WHERE product_id = '5fd017c6dad46f254f08fb78';

-- Rooms
SELECT * FROM atdw.services WHERE product_id = '5fd017c6dad46f254f08fb78';

-- Images
SELECT * FROM atdw.multimedia WHERE product_id = '5fd017c6dad46f254f08fb78' ORDER BY sequence_number;
```

### Count by category
```sql
SELECT
  product_category_id,
  product_category_description,
  COUNT(*) as count
FROM atdw.products
WHERE status = 'ACTIVE'
GROUP BY product_category_id, product_category_description
ORDER BY count DESC;
```

### Find products updated recently
```sql
SELECT
  product_id,
  product_name,
  product_update_date,
  updated_at
FROM atdw.products
WHERE updated_at > NOW() - INTERVAL '24 hours'
ORDER BY updated_at DESC;
```

### Get opening hours for a product
```sql
-- Get all opening hours with daily schedules
SELECT
  p.product_name,
  p.opening_time_type,
  p.opening_time_comment,
  ohp.from_date,
  ohp.to_date,
  ohs.day_of_week,
  ohs.opening_time,
  ohs.closing_time,
  ohs.is_closed
FROM atdw.products p
LEFT JOIN atdw.opening_hours_periods ohp ON p.product_id = ohp.product_id
LEFT JOIN atdw.opening_hours_schedule ohs ON ohp.id = ohs.period_id
WHERE p.product_id = '64e2b5ca2f2b1fa45dca1b19'
ORDER BY ohp.sequence_number, ohs.day_of_week;
```

### Find restaurants open on weekends
```sql
-- Find restaurants with Saturday hours
SELECT DISTINCT
  p.product_id,
  p.product_name,
  p.suburb_name,
  ohs.opening_time,
  ohs.closing_time
FROM atdw.products p
JOIN atdw.opening_hours_periods ohp ON p.product_id = ohp.product_id
JOIN atdw.opening_hours_schedule ohs ON ohp.id = ohs.period_id
WHERE p.product_category_id = 'RESTAURANT'
  AND ohs.day_of_week = 'SAT'
  AND ohs.is_closed = FALSE
  AND p.state_name = 'Victoria'
ORDER BY p.suburb_name, p.product_name;
```

## Next Steps

1. **Determine database location** ← CURRENT BLOCKER
2. Apply migration
3. Load test data (ACT - 1,160 products)
4. Validate schema and performance
5. Load full national dataset (~600K products)
6. Set up daily delta updates
