# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**roam-atdw** is a standalone Python client for the Australian Tourism Data Warehouse (ATDW) API.

### About This Project

This repository was extracted from the FATHOM data platform and is intended for use by [Roam](https://roamhq.io) as a dedicated ATDW API client.

The ATDW (Australian Tourism Data Warehouse) is Australia's national tourism database containing 50,000+ verified tourism products including accommodation, attractions, tours, restaurants, and events. This client provides:

- **Full-text search** across tourism products
- **Geospatial search** (radius and polygon-based)
- **Category filtering** (accommodation, attractions, tours, restaurants, events)
- **Region-based search** (state, city, region)
- **Product details** with multilingual support
- **Delta updates** for incremental synchronization
- **Automatic rate limiting** and retry logic
- **Pagination support**

### This Component

This repository provides:
- Python ATDW API client (`src/datasources/atdw_client.py`)
- 28+ utility scripts for extraction, analysis, and testing
- PostgreSQL database schemas (V1 and V2)
- Comprehensive documentation on ATDW data structures
- Sample data and extraction results

## Commands

### Quick Start

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
```

### Data Extraction Scripts

```bash
# Extract all Australian tourism products by state
python scripts/extract_atdw_national.py

# Extract and analyze product attributes
python scripts/extract_atdw_attributes.py
```

### Database Loading

```bash
# Apply the ATDW V2 schema
psql -d your_database -f migrations/010_atdw_schema_v2_fixed.sql

# Load ATDW data into PostgreSQL
python scripts/load_atdw_to_database.py --state VIC --yes
```

### Testing

```bash
# Run pytest test suite
pytest tests/

# Run specific test script
python scripts/test_atdw.py

# Test API pagination
python scripts/test_atdw_pagination.py

# Test all categories
python scripts/test_atdw_categories.py
```

## Technical Documentation

For detailed technical documentation on specific components, see the `/docs` directory:

- **[docs/ATDW_DATABASE_SCHEMA.md](docs/ATDW_DATABASE_SCHEMA.md)** - PostgreSQL schema documentation (V1 and V2)
- **[docs/ATDW_EXTRACTION_READY.md](docs/ATDW_EXTRACTION_READY.md)** - Complete extraction guide and status
- **[docs/ATDW_NATIONAL_EXTRACTION_PLAN.md](docs/ATDW_NATIONAL_EXTRACTION_PLAN.md)** - National extraction strategy
- **[docs/ATDW_ATTRIBUTE_CATALOG.md](docs/ATDW_ATTRIBUTE_CATALOG.md)** - Complete attribute catalog
- **[docs/ATDW_ATTRIBUTE_QUICK_REFERENCE.md](docs/ATDW_ATTRIBUTE_QUICK_REFERENCE.md)** - Quick reference guide
- **[docs/ATDW_V2_DEPLOYMENT_STATUS.md](docs/ATDW_V2_DEPLOYMENT_STATUS.md)** - V2 schema deployment status
- **[docs/ATDW SCHEMA V2.md](docs/ATDW%20SCHEMA%20V2.md)** - V2 schema design

**External Documentation:**
- [ATDW API Documentation](https://developer.atdw.com.au)
- [ATDW Rate Limiting Policy](https://au.intercom.help/atdw/en/articles/44447-api-rate-limiting)

## Code Architecture

### ATDW Client Design

The main client implementation is in `src/datasources/atdw_client.py` - a comprehensive Python client for the ATDW API v2.

**Core Components:**

**Rate Limiting & Retry Logic**
- Implements automatic rate limiting (2 requests per second)
- Exponential backoff for HTTP 429 responses
- Respects `Retry-After` header from API
- Configurable retry attempts and delays

**Search Methods**
- `search_products()` - Full-text and filtered search
- `search_by_location()` - Geospatial radius search
- `search_by_polygon()` - Polygon-based search
- `get_product()` - Fetch detailed product information
- `get_delta_updates()` - Incremental synchronization

**Pagination Support**
- Automatic pagination handling for all search methods
- Default page size: 100 products
- Configurable `max_pages` for controlled extraction

**Data Extraction**
- Handles complex nested JSON structures
- Extracts images, locations, attributes, communications
- Normalizes data for CSV export
- UTF-8-BOM encoding for international characters

### API Categories

The ATDW API supports the following product categories:
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

### Database Schema

The project uses the PostgreSQL V2 schema:

**V2 Schema** (`migrations/010_atdw_schema_v2_fixed.sql`)
- Enhanced schema with comprehensive attribute support
- PostGIS geography fields for accurate distance queries
- SHA256 hash-based change detection
- Tables: products, suppliers, addresses, communications, media, attributes, services, rates, deals
- Full support for ATDW product detail structure
- Optimized for delta updates and high-performance caching

See `docs/ATDW_DATABASE_SCHEMA.md` for detailed schema documentation.

## Development Workflow

### Git Commit Guidelines

This project follows **structured, granular commits** with conventional commit format:

**Commit Format:**
```
type(scope): brief description

Optional body with more details
```

**IMPORTANT:** Do NOT add "Generated with Claude Code" or similar attributions to commit messages.

**Commit Types:**
- `feat`: New feature or capability
- `fix`: Bug fix
- `refactor`: Code refactoring (no functional change)
- `perf`: Performance improvement
- `chore`: Maintenance tasks (docs, cleanup, dependencies)
- `docs`: Documentation only
- `test`: Adding or updating tests

**Scopes (examples):**
- `client`: ATDW API client
- `scripts`: Extraction/analysis scripts
- `migrations`: Database migrations
- `docs`: Documentation updates
- `tests`: Test suite

**When to Commit:**

✅ **DO commit after:**
- Completing a single function or method
- Finishing a test suite
- Completing a refactor of a component
- Fixing a bug
- Adding a feature module

❌ **DON'T commit:**
- Multiple unrelated changes together
- Work-in-progress code that doesn't work
- Large monolithic changes spanning multiple components

**Examples:**

```bash
# Good: Granular, focused commits
feat(client): add polygon-based search support
fix(client): handle pagination edge case with empty results
refactor(scripts): consolidate extraction scripts
docs(atdw): add V2 schema deployment guide

# Bad: Too broad or mixed concerns
fix: various updates
feat: add everything
```

**Benefits:**
- Clear history for code review
- Easy to identify which commit introduced a bug
- Simple to cherry-pick or revert specific changes
- Better understanding of development evolution

### Code Organization

**Directory Structure:**
- `src/datasources/` - ATDW API client implementation
- `scripts/` - Extraction, analysis, and testing scripts (28+)
- `migrations/` - Database schema migrations
- `docs/` - Comprehensive documentation (7 files)
- `tests/` - Test suites
- `data/` - Sample data and extraction results

**Naming Conventions:**
- Python files: `snake_case.py`
- Classes: `PascalCase`
- Functions/variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`

### API Integration Guidelines

When working with the ATDW API or implementing additional features:

**CRITICAL: Always Implement Pagination**

All API integrations MUST check for and implement pagination support:

✅ **Required Approach:**
1. **Research pagination first** - Check API docs for pagination mechanism before implementing
2. **Implement pagination support** - Handle `nextPageToken`, cursor, offset, or link-based pagination
3. **Default to fetching all results** - Add `paginate=True` parameter (default) to fetch all pages
4. **Add page limit option** - Allow `max_pages=N` to cap expensive queries during testing
5. **Document pagination** - Note pagination method and limits in docstrings

**ATDW Pagination:**
- Uses `start` and `size` parameters
- Default page size: 100 products
- Maximum page size: 100 products
- The client automatically handles pagination in all search methods

**Example Implementation Pattern:**
```python
def search_products(self, term: str = None, paginate: bool = True, max_pages: Optional[int] = None):
    """
    Search for products with automatic pagination.

    Args:
        term: Search query
        paginate: If True, fetch all pages. If False, only first page. (default: True)
        max_pages: Optional limit on pages to fetch (useful for testing)
    """
    all_results = []
    start = 0
    page_count = 0

    while True:
        # Make request
        response = self._make_request(start=start, size=100)
        products = response.get('products', [])
        all_results.extend(products)
        page_count += 1

        # Check for more pages
        if not paginate:
            break
        if max_pages and page_count >= max_pages:
            break
        if len(products) < 100:  # Last page
            break

        start += 100

    return all_results
```

**Rate Limiting:**
- ATDW API rate limit: 2 requests per second
- Client implements automatic rate limiting
- Handles HTTP 429 with exponential backoff
- Respects `Retry-After` header

### CSV Export Best Practices

When exporting data to CSV files:

**CRITICAL: Use UTF-8-BOM for International Characters**

Always use `encoding='utf-8-sig'` when writing CSV files that may contain international characters (accents, apostrophes, etc.):

```python
# ❌ WRONG - Excel will show mojibake (â€™ instead of ')
with open(csv_file, 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)

# ✅ CORRECT - Excel recognizes UTF-8 with BOM
with open(csv_file, 'w', encoding='utf-8-sig', newline='') as f:
    writer = csv.writer(f)
```

**Why This Matters:**
- `utf-8` alone: Excel assumes Windows-1252, displays "Café" as "CafÃ©"
- `utf-8-sig`: Adds BOM (Byte Order Mark), Excel recognizes UTF-8 correctly
- No data loss, perfect rendering of: é, ñ, ', ", —, etc.

**Common Character Issues Without BOM:**
- Woolworths' → Woolworthsâ€™s
- Café → CafÃ©
- Let's → Letâ€™s
- Piñata → PiÃ±ata

**Always test CSV exports with:**
- Business names containing apostrophes (Jimmy's, Let's)
- Accented characters (Café, São Paulo)
- Special punctuation (em dash —, quotes "")

### Testing

**Test Scripts:**
```bash
# Run pytest test suite
pytest tests/

# Test single product fetch
python scripts/test_atdw.py

# Test pagination functionality
python scripts/test_atdw_pagination.py

# Test all categories
python scripts/test_atdw_categories.py

# Test comprehensive data capture
python scripts/test_atdw_complete_data_capture.py

# Analyze extraction results
python scripts/analyze_atdw_extraction.py
```

**Before Committing:**
1. Ensure code runs without errors
2. Test with sample data if applicable
3. Update documentation if behavior changed
4. Check for any debug/temporary code
5. Verify imports are clean

## ATDW Agent

A global Claude agent (`atdw-expert`) is available with comprehensive ATDW API knowledge. This agent provides:
- Detailed API endpoint documentation
- Field and attribute guidance
- Best practices for extraction
- Schema design recommendations

The agent is located at: `$APPDATA/Claude/agents/atdw-expert.md`

## Common Tasks

### Extracting All Australian Tourism Data

```bash
# National extraction (all states)
python scripts/extract_atdw_national.py

# Single state extraction
python scripts/extract_atdw_national.py --state NSW
```

### Loading Data into Database

```bash
# Apply V2 schema
psql -d fathom -f migrations/010_atdw_schema_v2_fixed.sql

# Load data
python scripts/load_atdw_to_database.py --state VIC --yes
```

### Analyzing Attributes

```bash
# Extract and analyze all attributes
python scripts/extract_atdw_attributes.py

# Debug product structure
python scripts/debug_atdw_product_structure.py
```

## Known Limitations

1. **Rate Limiting**: ATDW API limits to 2 requests/second
2. **Pagination**: Maximum 100 products per page
3. **Search Radius**: Maximum search radius varies by region
4. **Product Updates**: Use delta updates for incremental sync

## References

- **ATDW Developer Portal**: https://developer.atdw.com.au
- **Roam**: https://roamhq.io
- **Source Project**: Fathom (E:\Projects\Coding\Fathom)
