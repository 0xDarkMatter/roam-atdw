# ATDW API Client

A comprehensive Python client for the Australian Tourism Data Warehouse (ATDW) API v2.

This client provides complete access to Australia's national tourism database with 50,000+ verified tourism products including accommodation, attractions, tours, restaurants, and events.

## Overview

This project was extracted from the [Fathom](https://github.com/0xDarkMatter/fathom-abn) data platform and is maintained for use by [Roam](https://roamhq.io) as a standalone ATDW API integration.

**What's Included:**
- Production-ready Python ATDW API client with automatic rate limiting and pagination
- 25+ utility scripts for data extraction, analysis, and testing
- PostgreSQL database schema (V2) optimized for performance and change detection
- 7 comprehensive documentation files covering schema, attributes, and extraction strategies
- Sample datasets and extraction results
- Global Claude Code agent (`atdw-expert`) with comprehensive ATDW API knowledge

## Features

### API Client
- Full-text search across tourism products
- Geospatial search (radius and polygon-based)
- Category filtering (accommodation, attractions, tours, restaurants, events)
- Region-based search (state, city, region)
- Product details with multilingual support
- Delta updates for incremental synchronization
- Automatic rate limiting and retry logic
- Pagination support (up to 5,000 results per request)

### Database Features
- **Hash-based change detection** - SHA256 hashing of products, addresses, communication, and services for efficient delta updates (75%+ reduction in processing time)
- **Geography fields** - PostGIS `geography(Point,4326)` type for accurate distance-based queries
- **Auto-computed geolocation** - Automatic geography point generation from lat/lon coordinates
- **Change tracking** - Comprehensive audit log of all product modifications
- **Idempotent upserts** - Safe to run imports multiple times without duplicates
- **EAV attribute storage** - Flexible attribute system with automatic discovery
- **Media deduplication** - Prevents duplicate images and videos using content hashing
- **Optimized services table** - Structured columns for common filters (capacity, accessibility, pets) with 90% reduction in JSONB storage

## Installation

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up your ATDW API key:
   ```bash
   cp .env.example .env
   # Edit .env and add your ATDW_API_KEY
   ```

## Quick Start

```python
from src.datasources.atdw_client import ATDWClient

# Initialize client (uses ATDW_API_KEY from environment)
client = ATDWClient()

# Search for accommodation in Byron Bay
products = client.search_products(
    term='Byron Bay',
    categories=['ACCOMM'],
    star_rating=4
)

# Location-based search (radius-based)
nearby = client.search_by_location(
    lat=-28.6450,
    lng=153.6050,
    radius_km=10,
    categories=['ATTRACTION']
)

# Polygon-based search
polygon_results = client.search_by_polygon(
    coordinates=[
        [153.60, -28.65],
        [153.61, -28.65],
        [153.61, -28.64],
        [153.60, -28.64],
        [153.60, -28.65]
    ],
    categories=['RESTAURANT']
)

# Get detailed product information
product = client.get_product('product-id-123')

# Delta updates for incremental sync (products updated since a date)
updates = client.get_delta(
    since_date='2024-01-01',
    categories=['ACCOMM'],
    state='VIC',
    status=['ACTIVE']
)
```

## API Categories

The client supports the following product categories:
- `ACCOMM` - Accommodation
- `ATTRACTION` - Attractions
- `TOUR` - Tours
- `RESTAURANT` - Restaurants
- `EVENT` - Events
- `HIRE` - Hire services
- `TRANSPORT` - Transport
- `GENERAL_SERVICE` - General services
- `DESTINATION` - Destinations
- `JOURNEY` - Journeys

## Project Structure

```
ATDW/
├── src/
│   └── datasources/
│       └── atdw_client.py               # Main ATDW API client
├── tests/
│   ├── test_atdw_unit.py               # Unit tests
│   └── test_atdw_integration.py        # Integration tests
├── scripts/                             # 25+ utility scripts
│   ├── load_atdw_to_database.py        # Database loader with V2 schema
│   ├── extract_atdw_national.py        # National extraction script
│   ├── extract_atdw_attributes.py      # Attribute extraction
│   ├── analyze_atdw_extraction.py      # Analysis tools
│   ├── compare_atdw_extractions.py     # Compare extractions
│   ├── debug_atdw_*.py                 # Debug tools
│   └── test_atdw*.py                   # 18+ API test scripts
├── migrations/
│   ├── 010_atdw_schema_v2_fixed.sql    # ATDW V2 schema (primary)
│   ├── 015_rename_external_id_to_atdw_id.sql  # Field rename migration
│   ├── 023_add_remaining_atdw_tables.sql      # Additional tables
│   └── 025_optimize_services_table.sql # Services table optimization
├── data/
│   ├── atdw_default_fields.json        # Default field definitions
│   ├── atdw_attribute_catalog.json     # Complete attribute catalog
│   ├── atdw_extensive_fields.json      # Extended field definitions
│   ├── atdw_product_detail_example.json # Sample product structure
│   └── atdw_national/                   # National extracts (9 CSV files)
│       ├── atdw_australia_complete_*.csv
│       ├── atdw_nsw_*.csv
│       ├── atdw_vic_*.csv
│       ├── atdw_qld_*.csv
│       └── ...                          # All states/territories
├── docs/                                # 7 comprehensive documentation files
│   ├── ATDW SCHEMA V2.md               # V2 schema design
│   ├── ATDW_ATTRIBUTE_CATALOG.md       # Complete attribute reference
│   ├── ATDW_ATTRIBUTE_QUICK_REFERENCE.md # Quick attribute lookup
│   ├── ATDW_DATABASE_SCHEMA.md         # PostgreSQL schema docs
│   ├── ATDW_EXTRACTION_READY.md        # Extraction guide
│   ├── ATDW_NATIONAL_EXTRACTION_PLAN.md # National extraction strategy
│   └── ATDW_V2_DEPLOYMENT_STATUS.md    # V2 deployment status
├── .env.example                         # Environment variable template
├── .gitignore
├── CLAUDE.md                            # Developer guide for Claude Code
├── LICENSE
├── README.md
└── requirements.txt
```

## Database Setup

The project includes PostgreSQL schema migrations with advanced features for efficient data storage and querying.

### V2 Schema Features

The V2 schema (`migrations/010_atdw_schema_v2_fixed.sql`) includes:

- **PostGIS geography fields** - Accurate distance calculations using `geography(Point,4326)`
- **Automatic hash computation** - SHA256 hashes for products, addresses, communication, and services via database triggers
- **Change detection** - Delta updates skip unchanged records, reducing processing time by 75%+
- **Idempotent upserts** - Safe to re-run imports without creating duplicates
- **EAV attribute system** - Flexible attribute storage with automatic discovery of new attributes
- **Media deduplication** - Content-based hashing prevents duplicate images
- **Comprehensive indexes** - Optimized for common query patterns (category, state, geolocation, capacity, accessibility)
- **Optimized services storage** - Structured columns replace JSONB for frequently queried fields (90% storage reduction)

### Setup

```bash
# Apply the ATDW V2 schema (requires PostGIS extension)
psql -d your_database -f migrations/010_atdw_schema_v2_fixed.sql

# Load ATDW data into database with batched commits
python scripts/load_atdw_to_database.py --state VIC --yes --batch-size 50

# The loader automatically:
# - Computes content hashes for change detection
# - Discovers and registers new attributes
# - Deduplicates media (images, videos)
# - Tracks all changes in audit log
# - Computes geography points from lat/lon
```

### Change Detection in Action

```bash
# First run: loads 10,000 products (takes ~30 minutes)
python scripts/load_atdw_to_database.py --state VIC --yes

# Second run: skips unchanged products (takes ~2 minutes)
# Only processes products where content_sha256 changed
python scripts/load_atdw_to_database.py --state VIC --yes
```

See `docs/ATDW_DATABASE_SCHEMA.md` for detailed schema documentation.

### Geospatial Queries

The V2 schema uses PostGIS `geography` type for accurate distance calculations:

```sql
-- Find all products within 10km of Byron Bay
SELECT
  product_name,
  category,
  ST_Distance(geom, ST_SetSRID(ST_MakePoint(153.6050, -28.6450), 4326)::geography) / 1000 as distance_km
FROM products
WHERE ST_DWithin(
  geom,
  ST_SetSRID(ST_MakePoint(153.6050, -28.6450), 4326)::geography,
  10000  -- 10km in meters
)
ORDER BY distance_km;

-- Count products by category within radius
SELECT category, COUNT(*)
FROM products
WHERE ST_DWithin(geom, ST_SetSRID(ST_MakePoint(153.6050, -28.6450), 4326)::geography, 10000)
GROUP BY category
ORDER BY COUNT(*) DESC;
```

**Why `geography` instead of `geometry`?**
- `geography` uses meters for distance calculations (accurate real-world distances)
- `geometry` uses degrees (inaccurate for distance queries)
- Example: 10km radius is exactly 10,000 meters, not ~0.09 degrees (which varies by latitude)

### Optimized Service Queries

The services table is optimized for common accommodation and tour searches:

```sql
-- Find pet-friendly accommodation with capacity for 4+ people
SELECT p.product_name, s.name, s.max_capacity
FROM products p
JOIN services s ON s.product_id = p.product_id
WHERE p.category = 'ACCOMM'
  AND s.pets_allowed = true
  AND s.max_capacity >= 4
ORDER BY s.sequence;

-- Find accessible tours
SELECT p.product_name, s.name, s.description
FROM products p
JOIN services s ON s.product_id = p.product_id
WHERE p.category = 'TOUR'
  AND s.accessible = true
ORDER BY p.product_name;

-- Count services by capacity
SELECT max_capacity, COUNT(*)
FROM services
WHERE max_capacity IS NOT NULL
GROUP BY max_capacity
ORDER BY max_capacity;
```

## Scripts

The `scripts/` directory contains 25+ utility scripts for various ATDW operations:

**Data Extraction:**
- `extract_atdw_national.py` - Extract all Australian tourism products by state
- `extract_atdw_attributes.py` - Extract and analyze product attributes

**Database Loading:**
- `load_atdw_to_database.py` - Load ATDW data into PostgreSQL with V2 schema
  - Hash-based change detection (75%+ faster on subsequent runs)
  - Batched commits for optimal performance (1.5h vs 6.5h)
  - Automatic attribute discovery and registration
  - Media deduplication via content hashing

**Testing & Analysis:**
- `test_atdw*.py` - Various API testing scripts (pagination, fields, categories, etc.)
- `analyze_atdw_extraction.py` - Analyze extraction results
- `compare_atdw_extractions.py` - Compare different extractions
- `debug_atdw_*.py` - Debug tools for fields and product structure

## Testing

Run tests with pytest:
```bash
pytest tests/
```

Run a specific test script:
```bash
python scripts/test_atdw.py
```

## Performance

### Hash-Based Change Detection

The V2 schema implements SHA256 content hashing to detect actual changes in products:

```python
# Database automatically computes these hashes via triggers:
# - content_sha256: Core product fields (name, category, location, etc.)
# - media_sha256: Images, videos, and multimedia
# - attrs_sha256: Product attributes

# On upsert, the loader compares hashes to determine if update is needed
# Result: 75%+ reduction in processing time on subsequent runs
```

**Performance Impact:**
- **First run** (VIC state): ~30 minutes (10,000 products, full processing)
- **Second run** (no changes): ~2 minutes (skips unchanged products)
- **Batched commits**: 1.5 hours vs 6.5 hours (75% faster with batch_size=50)

### Geospatial Query Performance

PostGIS geography fields enable fast radius queries:

```sql
-- Index-optimized geospatial query (uses GIST index on geom column)
-- Finds products within 10km in ~50ms (on 50k products)
SELECT * FROM products
WHERE ST_DWithin(geom, ST_MakePoint(153.6050, -28.6450)::geography, 10000);
```

## Delta Updates (Incremental Sync)

The delta update functionality allows you to efficiently sync only products that have changed since a specific date/time.

### How It Works

- Uses `/products` endpoint with `delta` parameter
- Returns products with `status` field: `ACTIVE` (updated), `INACTIVE` (deleted), or `EXPIRED` (past validity)
- Supports all standard filters (state, category, etc.)
- Fully paginated for large result sets
- Date/time in AEST timezone

### Usage Examples

```python
from datetime import datetime, timedelta
from src.datasources.atdw_client import ATDWClient

client = ATDWClient()

# Get all Victorian products updated in last 30 days
thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
updates = client.get_delta(
    since_date=thirty_days_ago,
    state='VIC',
    status=['ACTIVE']  # Only active products
)
print(f"Found {len(updates)} updated products")

# Get accommodation updates by category
accomm_updates = client.get_delta(
    since_date='2024-01-01',
    categories=['ACCOMM'],
    state='NSW',
    status=['ACTIVE', 'INACTIVE']  # Include deleted products
)

# High-precision sync with timestamp
recent_updates = client.get_delta(
    since_date='2025-01-15 14:30:00',  # AEST timezone
    state='QLD'
)
```

### Performance

Delta queries are highly efficient for incremental synchronization:

**Victorian Products Updated:**
- Last 7 days: ~715 products (0.6-2s)
- Last 30 days: ~1,739 products (1.9s)
- Last 90 days: ~3,433 products (3-5s)
- Last 6 months: ~4,711 products (5-8s)

### Understanding Product Changes

The delta endpoint returns products with changes, but doesn't explicitly label them as "NEW" or "UPDATED". You need to compare against your database to determine the change type:

| Change Type | API Status | Meaning | How to Detect |
|-------------|------------|---------|---------------|
| **NEW** | ACTIVE | First time appearing in ATDW | Product ID not in your database |
| **UPDATED** | ACTIVE | Existing product modified | Product ID exists in your database |
| **DELETED** | INACTIVE | Removed from ATDW | Status = INACTIVE |
| **EXPIRED** | EXPIRED | Past validity date | Status = EXPIRED |

**Implementation Example:**

```python
# Load existing product IDs from your database
existing_product_ids = {row['product_id'] for row in db.query("SELECT product_id FROM products")}

# Fetch delta updates
updates = client.get_delta(since_date='2024-01-01', state='VIC')

for product in updates:
    product_id = product['productId']
    status = product['status']

    if status == 'ACTIVE':
        # Check if product is NEW or UPDATED
        if product_id in existing_product_ids:
            # UPDATED: Product exists - update it
            db.update_product(product)
        else:
            # NEW: Product doesn't exist - insert it
            db.insert_product(product)

    elif status == 'INACTIVE':
        # DELETED: Product was removed from ATDW
        # IMPORTANT: Use soft delete - update status, don't physically delete
        db.update_product_status(product_id, status='INACTIVE', deleted_at=datetime.now())

    elif status == 'EXPIRED':
        # EXPIRED: Product past validity date
        # Update status to expired, preserve the product data
        db.update_product_status(product_id, status='EXPIRED', expiry_date=product.get('atdwExpiryDate'))
```

**Key Insights**:
- The ATDW API doesn't distinguish between NEW and UPDATED products - both have `status='ACTIVE'`. You must compare against your existing data to determine if a product is truly new.
- **Never physically delete products** - Use soft deletes (status updates) to preserve historical data, maintain referential integrity, and enable analytics on closed businesses.

**Critical: INACTIVE ≠ Business Closed**

INACTIVE status means the product was **removed from ATDW**, but this does NOT necessarily mean the business has closed:

**Common Reasons for INACTIVE Status:**
- Operator stopped paying for ATDW listing (especially in states where ATDW has fees)
- Operator let their listing lapse
- Operator temporarily suspended listing
- Business is operational but not using ATDW

**DMO Best Practice (All Australian States):**

Destination Marketing Organizations (DMOs) and Regional Tourism Boards (RTBs) preserve INACTIVE listings while attempting to re-engage operators. They:
1. Keep INACTIVE products in their databases (soft delete)
2. Use custom product management features (like Roam) to maintain listings
3. Attempt to convince operators to renew their ATDW listings
4. Separately track actual business closures vs ATDW listing lapses

**Recommendation**: Your database should track TWO separate statuses:
- `atdw_status`: What ATDW reports (ACTIVE/INACTIVE/EXPIRED)
- `operational_status`: Your own verification (OPEN/CLOSED/SEASONAL/UNKNOWN)

### Best Practices

1. **Store last sync timestamp** - Save the timestamp after successful sync
2. **Use soft deletes** - Update status field instead of physically deleting records
3. **Filter by status** - Use `status=['ACTIVE']` to skip deleted products in queries
4. **Use state filter** - Filter at API level for better performance
5. **Handle pagination** - Delta queries can return thousands of results
6. **Process incrementally** - Run delta sync daily/hourly for freshness
7. **Track first seen date** - Store your own timestamp when inserting NEW products

**Database Schema Recommendation:**
```sql
CREATE TABLE products (
    product_id VARCHAR PRIMARY KEY,
    product_name VARCHAR,

    -- ATDW status (what the API reports)
    atdw_status VARCHAR DEFAULT 'ACTIVE',  -- ACTIVE, INACTIVE, EXPIRED
    atdw_status_changed_at TIMESTAMP,

    -- YOUR operational status (what you've verified)
    operational_status VARCHAR DEFAULT 'UNKNOWN',  -- OPEN, CLOSED, SEASONAL, UNKNOWN
    operational_status_updated_at TIMESTAMP,

    -- Tracking timestamps
    first_seen_at TIMESTAMP,
    atdw_expiry_date DATE,  -- From atdwExpiryDate field

    ...
);

-- Query for ATDW active products only
SELECT * FROM products WHERE atdw_status = 'ACTIVE';

-- Query for businesses you believe are OPEN (regardless of ATDW status)
SELECT * FROM products
WHERE operational_status = 'OPEN'
  OR (atdw_status = 'ACTIVE' AND operational_status = 'UNKNOWN');

-- Analytics: ATDW listing lapses (not business closures)
SELECT COUNT(*), DATE_TRUNC('month', atdw_status_changed_at)
FROM products
WHERE atdw_status = 'INACTIVE'
  AND operational_status != 'CLOSED'
GROUP BY DATE_TRUNC('month', atdw_status_changed_at);
```

## Rate Limiting

The client implements automatic rate limiting and exponential backoff to comply with ATDW API policies:
- Default: 2 requests per second
- Handles HTTP 429 responses with Retry-After header
- Automatic exponential backoff on rate limit errors
- Optimal page size: 5,000 results per request (reduces API calls by 71%)

## For Developers

### Claude Code Integration

This project includes comprehensive support for [Claude Code](https://claude.com/claude-code):

**CLAUDE.md** - Developer guide covering:
- Project architecture and code organization
- ATDW API integration patterns
- Database schema design (V1 and V2)
- Git commit conventions
- Testing strategies
- Common development tasks

**atdw-expert Agent** - Global Claude agent with comprehensive ATDW API knowledge:
- Detailed API endpoint documentation
- Field and attribute guidance
- Best practices for extraction and pagination
- Schema design recommendations

The agent is automatically available in Claude Code sessions when working with this repository.

### Development Workflow

This project follows structured, granular commits with conventional commit format:

```bash
# Examples
feat(client): add polygon-based search support
fix(client): handle pagination edge case with empty results
refactor(scripts): consolidate extraction scripts
docs(schema): update V2 deployment status
```

See `CLAUDE.md` for complete development guidelines.

## Documentation

**Project Documentation:**
- [ATDW_DATABASE_SCHEMA.md](docs/ATDW_DATABASE_SCHEMA.md) - PostgreSQL schema documentation
- [ATDW_EXTRACTION_READY.md](docs/ATDW_EXTRACTION_READY.md) - Complete extraction guide
- [ATDW_ATTRIBUTE_CATALOG.md](docs/ATDW_ATTRIBUTE_CATALOG.md) - Complete attribute reference
- [ATDW_ATTRIBUTE_QUICK_REFERENCE.md](docs/ATDW_ATTRIBUTE_QUICK_REFERENCE.md) - Quick attribute lookup
- [ATDW_NATIONAL_EXTRACTION_PLAN.md](docs/ATDW_NATIONAL_EXTRACTION_PLAN.md) - National extraction strategy
- [ATDW_V2_DEPLOYMENT_STATUS.md](docs/ATDW_V2_DEPLOYMENT_STATUS.md) - V2 schema deployment status
- [ATDW SCHEMA V2.md](docs/ATDW%20SCHEMA%20V2.md) - V2 schema design

**External Resources:**
- [ATDW API Documentation](https://developer.atdw.com.au)
- [ATDW Rate Limiting Policy](https://au.intercom.help/atdw/en/articles/44447-api-rate-limiting)
- [Roam](https://roamhq.io)

## Contributing

Contributions are welcome! Please:
1. Follow the commit conventions outlined in `CLAUDE.md`
2. Add tests for new features
3. Update documentation as needed
4. Ensure all tests pass before submitting

## License

MIT License

## Acknowledgments

This project was extracted from the [Fathom](https://github.com/0xDarkMatter/fathom-abn) data platform, which provides ABN-first business intelligence for Australian companies.

Built for [Roam](https://roamhq.io) - Your AI Travel Companion.

---

**Repository:** https://github.com/0xDarkMatter/roam-atdw
