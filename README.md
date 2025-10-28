# ATDW API Client

A standalone Python client for the Australian Tourism Data Warehouse (ATDW) API.

This client provides access to Australia's national tourism database with 50,000+ tourism products including accommodation, attractions, tours, restaurants, and events.

## Overview

This project was extracted from the Fathom project and is intended for use by [Roam](https://roamhq.io) as a standalone ATDW API client.

## Features

- Full-text search across tourism products
- Geospatial search (radius and polygon-based)
- Category filtering (accommodation, attractions, tours, restaurants, events)
- Region-based search (state, city, region)
- Product details with multilingual support
- Delta updates for incremental synchronization
- Automatic rate limiting and retry logic
- Pagination support

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
from atdw import ATDWClient

# Initialize client (uses ATDW_API_KEY from environment)
client = ATDWClient()

# Search for accommodation in Byron Bay
products = client.search_products(
    term='Byron Bay',
    categories=['ACCOMM'],
    star_rating=4
)

# Location-based search
nearby = client.search_by_location(
    lat=-28.6450,
    lng=153.6050,
    radius_km=10,
    categories=['ATTRACTION']
)

# Get product details
product = client.get_product('product-id-123')
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
│   └── atdw/
│       ├── __init__.py
│       └── client.py                    # Main ATDW API client
├── tests/
│   ├── test_atdw_unit.py               # Unit tests
│   └── test_atdw_integration.py        # Integration tests
├── scripts/                             # 28 utility scripts
│   ├── load_atdw_to_database.py        # Database loader with V2 schema
│   ├── extract_atdw_national.py        # National extraction script
│   ├── extract_atdw_attributes.py      # Attribute extraction
│   ├── extract_byron_atdw.py           # Byron Bay extraction
│   ├── analyze_atdw_extraction.py      # Analysis tools
│   ├── test_atdw*.py                   # Various test scripts
│   └── ...                              # 20+ more scripts
├── migrations/
│   ├── 009_atdw_tourism_schema.sql     # ATDW V1 schema
│   └── 010_atdw_schema_v2_fixed.sql    # ATDW V2 schema
├── data/
│   ├── atdw_default_fields.json        # Default field definitions
│   ├── atdw_attribute_catalog.json     # Attribute catalog
│   ├── atdw_extensive_fields.json      # Extended field definitions
│   ├── atdw_product_detail_example.json # Product examples
│   ├── byron_bay_atdw_*.csv            # Byron Bay extracts
│   └── atdw_national/                   # National extracts (9 CSV files)
│       ├── atdw_australia_complete_*.csv
│       ├── atdw_vic_*.csv
│       └── ...                          # State-by-state CSVs
├── docs/                                # 7 documentation files
│   ├── ATDW_ATTRIBUTE_QUICK_REFERENCE.md
│   ├── ATDW_DATABASE_SCHEMA.md
│   ├── ATDW_ATTRIBUTE_CATALOG.md
│   ├── ATDW_EXTRACTION_READY.md
│   ├── ATDW_NATIONAL_EXTRACTION_PLAN.md
│   ├── ATDW_SCHEMA_V2.md
│   └── ATDW_V2_DEPLOYMENT_STATUS.md
├── requirements.txt
└── README.md
```

## Database Setup

The project includes PostgreSQL schema migrations for storing ATDW data:

```bash
# Apply the ATDW V2 schema
psql -d your_database -f migrations/010_atdw_schema_v2_fixed.sql

# Load ATDW data into database
python scripts/load_atdw_to_database.py --state VIC --yes
```

See `docs/ATDW_DATABASE_SCHEMA.md` for detailed schema documentation.

## Scripts

The `scripts/` directory contains 28+ utility scripts for various ATDW operations:

**Data Extraction:**
- `extract_atdw_national.py` - Extract all Australian tourism products by state
- `extract_atdw_attributes.py` - Extract and analyze product attributes
- `extract_byron_atdw.py` - Extract Byron Bay tourism data

**Database Loading:**
- `load_atdw_to_database.py` - Load ATDW data into PostgreSQL with V2 schema

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

## Rate Limiting

The client implements automatic rate limiting and exponential backoff to comply with ATDW API policies:
- Default: 2 requests per second
- Handles HTTP 429 responses with Retry-After header
- Automatic exponential backoff on rate limit errors

## Documentation

- [ATDW API Documentation](https://developer.atdw.com.au)
- [Rate Limiting Policy](https://au.intercom.help/atdw/en/articles/44447-api-rate-limiting)
- [Roam](https://roamhq.io)

## License

MIT License

## Source

Extracted from the Fathom project at E:\Projects\Coding\Fathom
