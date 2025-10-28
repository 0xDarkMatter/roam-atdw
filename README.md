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
│       └── client.py       # Main ATDW client
├── tests/
│   ├── test_atdw_unit.py
│   └── test_atdw_integration.py
├── scripts/
│   └── test_atdw.py       # Example usage script
├── data/
│   └── atdw_default_fields.json
├── docs/
│   ├── ATDW_ATTRIBUTE_QUICK_REFERENCE.md
│   └── ATDW_DATABASE_SCHEMA.md
├── requirements.txt
└── README.md
```

## Testing

Run tests with pytest:
```bash
pytest tests/
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
