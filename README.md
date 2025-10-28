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
- **Hash-based change detection** - SHA256 hashing of product content, media, and attributes for efficient delta updates
- **Geography fields** - PostGIS `geography(Point,4326)` type for accurate distance-based queries
- **Auto-computed geolocation** - Automatic geography point generation from lat/lon coordinates
- **Change tracking** - Comprehensive audit log of all product modifications
- **Idempotent upserts** - Safe to run imports multiple times without duplicates
- **EAV attribute storage** - Flexible attribute system with automatic discovery
- **Media deduplication** - Prevents duplicate images and videos using content hashing

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

# Delta updates for incremental sync
updates = client.get_delta_updates(
    last_sync_date='2024-01-01',
    categories=['ACCOMM']
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
│   └── 023_add_remaining_atdw_tables.sql      # Additional tables
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
- **Automatic hash computation** - SHA256 hashes for content, media, and attributes via database triggers
- **Change detection** - Delta updates skip unchanged products, reducing processing time by 75%+
- **Idempotent upserts** - Safe to re-run imports without creating duplicates
- **EAV attribute system** - Flexible attribute storage with automatic discovery of new attributes
- **Media deduplication** - Content-based hashing prevents duplicate images
- **Comprehensive indexes** - Optimized for common query patterns (category, state, geolocation)

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
