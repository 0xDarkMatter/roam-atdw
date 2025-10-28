# ATDW Client

A TypeScript/Node.js client for the **Australian Tourism Data Warehouse (ATDW) ATLAS2 API**.

This library provides access to Australia's national tourism database with **50,000+ tourism products** including accommodation, attractions, tours, restaurants, and events.

## About

This project was extracted from the [Fathom](https://github.com/roamhq/fathom) project and is intended for use by **[Roam](https://roamhq.io)** and other applications that need access to Australian tourism data.

The original Python implementation was translated to TypeScript to provide a modern, type-safe client for Node.js and browser environments.

## Features

- **Full-text search** across tourism products
- **Geospatial search** (radius and polygon-based)
- **Category filtering** (accommodation, attractions, tours, restaurants, events)
- **Advanced filtering** by location, price, star rating, and more
- **Pagination support** with automatic page fetching
- **Product details** with multilingual support
- **Delta updates** to fetch products updated since a specific date
- **Rate limiting** with exponential backoff and Retry-After header support
- **Type-safe** with full TypeScript definitions

## Installation

```bash
npm install @roamhq/atdw-client
```

Or with yarn:

```bash
yarn add @roamhq/atdw-client
```

Or with pnpm:

```bash
pnpm add @roamhq/atdw-client
```

## Quick Start

```typescript
import { createClient } from '@roamhq/atdw-client';

// Initialize the client
const client = createClient({
  apiKey: process.env.ATDW_API_KEY
});

// Search for accommodation in Byron Bay
const products = await client.searchProducts({
  term: 'Byron Bay',
  categories: ['ACCOMM'],
  starRating: 4
});

console.log(`Found ${products.length} products`);
```

## API Key

You need an ATDW Distributor API key to use this client. You can:

1. Set the `ATDW_API_KEY` environment variable
2. Pass it directly in the client configuration

```typescript
// Option 1: Environment variable
const client = createClient(); // Reads from process.env.ATDW_API_KEY

// Option 2: Direct configuration
const client = createClient({
  apiKey: 'your-api-key-here'
});
```

## Usage Examples

### Basic Product Search

```typescript
// Search for products by term
const results = await client.searchProducts({
  term: 'beach resort',
  categories: ['ACCOMM']
});
```

### Geospatial Search

```typescript
// Find attractions within 10km of a location
const nearby = await client.searchByLocation(
  -28.6450,  // latitude
  153.6050,  // longitude
  10,        // radius in km
  ['ATTRACTION', 'TOUR']
);
```

### Region-Based Search

```typescript
// Search by state and city
const nswProducts = await client.searchByRegion({
  state: 'NSW',
  city: 'Byron Bay',
  categories: ['RESTAURANT']
});
```

### Advanced Filtering

```typescript
// Combine multiple filters
const filtered = await client.searchProducts({
  state: 'VIC',
  categories: ['ACCOMM'],
  minRate: 100,
  maxRate: 300,
  starRating: 4,
  paginate: true,      // Fetch all pages (default: true)
  pageSize: 1000       // Results per page (default: 1000, max: 5000)
});
```

### Get Product Details

```typescript
// Get detailed information for a specific product
const product = await client.getProduct('56b23538eac3c50eec5e9bd0');

console.log(product.productName);
console.log(product.productDescription);
```

### Delta Updates

```typescript
// Get products updated since a specific date
const updated = await client.getDelta('2025-10-01', ['ACCOMM']);

console.log(`${updated.length} products updated since Oct 1`);
```

### Pagination Control

```typescript
// Fetch only the first page
const firstPage = await client.searchProducts({
  term: 'Sydney',
  paginate: false  // Only fetch first page
});

// Limit number of pages
const limited = await client.searchProducts({
  term: 'Melbourne',
  maxPages: 3  // Fetch only first 3 pages
});
```

## API Reference

### Product Categories

The client provides constants for product categories:

```typescript
import { ATDWClient } from '@roamhq/atdw-client';

ATDWClient.CATEGORIES = {
  ACCOMMODATION: 'ACCOMM',
  ATTRACTION: 'ATTRACTION',
  TOUR: 'TOUR',
  RESTAURANT: 'RESTAURANT',
  EVENT: 'EVENT',
  HIRE: 'HIRE',
  TRANSPORT: 'TRANSPORT',
  GENERAL_SERVICE: 'GENERAL_SERVICE',
  DESTINATION: 'DESTINATION',
  JOURNEY: 'JOURNEY'
}
```

### Australian States

```typescript
type AustralianState = 'NSW' | 'VIC' | 'QLD' | 'SA' | 'WA' | 'TAS' | 'NT' | 'ACT';
```

### Search Parameters

```typescript
interface SearchParams {
  // Search term
  term?: string;

  // Category filtering
  categories?: ProductCategory[];

  // Geospatial search
  lat?: number;
  lng?: number;
  radiusKm?: number;

  // Location filtering
  state?: AustralianState;
  city?: string;
  region?: string;

  // Price filtering
  minRate?: number;
  maxRate?: number;

  // Star rating
  starRating?: number;

  // Field selection
  fields?: string[];

  // Pagination
  paginate?: boolean;  // Default: true
  maxPages?: number;
  pageSize?: number;   // Default: 1000, Max: 5000
}
```

## Rate Limiting

The client implements automatic rate limiting and retry logic:

- **Default rate**: 2 requests per second (500ms between requests)
- **Retry behavior**: Exponential backoff for HTTP 429 responses
- **Retry-After header**: Respected as per ATDW recommendations
- **Max retries**: 3 attempts (configurable)

You can customize rate limiting:

```typescript
const client = createClient({
  apiKey: 'your-key',
  minRequestInterval: 1000,  // 1 second between requests (1 req/sec)
  maxRetries: 5,             // 5 retry attempts
  backoffFactor: 2           // Exponential backoff multiplier
});
```

## TypeScript Support

This library is written in TypeScript and provides full type definitions:

```typescript
import type {
  Product,
  ProductDetail,
  SearchParams,
  AustralianState,
  ProductCategory
} from '@roamhq/atdw-client';
```

## Project Structure

```
atdw-client/
├── src/
│   ├── index.ts      # Main exports
│   ├── client.ts     # ATDWClient implementation
│   └── types.ts      # TypeScript type definitions
├── examples/
│   ├── basic-usage.ts
│   ├── search-products.ts
│   └── location-search.ts
├── dist/             # Compiled output (generated)
├── package.json
├── tsconfig.json
└── README.md
```

## Development

### Build

```bash
npm run build
```

### Build and Watch

```bash
npm run build:watch
```

### Run Examples

```bash
# Make sure to set ATDW_API_KEY environment variable first
export ATDW_API_KEY=your-api-key

# Run examples
npm run example
npm run example:search
npm run example:location
```

## ATDW API Documentation

For more information about the ATDW API:

- **API Documentation**: https://developer.atdw.com.au
- **Rate Limiting Policy**: https://au.intercom.help/atdw/en/articles/44447-api-rate-limiting
- **Industry Package**: This client uses the Industry package

## License

MIT

## Credits

- Extracted from the [Fathom](https://github.com/roamhq/fathom) project
- Developed for [Roam](https://roamhq.io)
- ATDW API by [Australian Tourism Data Warehouse](https://atdw.com.au)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues and questions:
- GitHub Issues: https://github.com/roamhq/atdw-client/issues
- Roam: https://roamhq.io
