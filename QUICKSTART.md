# ATDW Client - Quick Start Guide

Get up and running with the ATDW TypeScript client in 5 minutes.

## Prerequisites

- Node.js 18+ installed
- ATDW API key ([get one here](https://developer.atdw.com.au))

## Installation

### 1. Install Dependencies

```bash
cd E:\Projects\Coding\ATDW
npm install
```

### 2. Set Up Environment

```bash
# Copy the example env file
cp .env.example .env

# Edit .env and add your API key
# ATDW_API_KEY=your-actual-api-key-here
```

Or set it directly:

```bash
export ATDW_API_KEY=your-api-key-here
```

### 3. Build the Project

```bash
npm run build
```

## Quick Test

Run the basic example to verify everything works:

```bash
npm run example
```

You should see output listing accommodation in Byron Bay!

## Your First Query

Create a file `test.ts`:

```typescript
import { createClient } from './src/index';

async function main() {
  const client = createClient();

  // Find 5-star hotels in Sydney
  const hotels = await client.searchProducts({
    term: 'Sydney',
    categories: ['ACCOMM'],
    starRating: 5,
    pageSize: 10,
    paginate: false
  });

  console.log(`Found ${hotels.length} luxury hotels in Sydney`);
  hotels.forEach(hotel => {
    console.log(`- ${hotel.productName}`);
  });
}

main();
```

Run it:

```bash
npx tsx test.ts
```

## Common Queries

### Search by Location

```typescript
// Find attractions near coordinates
const results = await client.searchByLocation(
  -33.8688,  // Sydney Opera House latitude
  151.2093,  // Sydney Opera House longitude
  5,         // 5km radius
  ['ATTRACTION']
);
```

### Search by Region

```typescript
// Find restaurants in Melbourne
const restaurants = await client.searchByRegion({
  state: 'VIC',
  city: 'Melbourne',
  categories: ['RESTAURANT']
});
```

### Get Product Details

```typescript
// Get detailed info for a specific product
const productId = '56b23538eac3c50eec5e9bd0';
const details = await client.getProduct(productId);

console.log(details.productDescription);
```

## More Examples

Check out the examples folder:

- `examples/basic-usage.ts` - Basic search and product details
- `examples/search-products.ts` - Advanced filtering and delta updates
- `examples/location-search.ts` - Geospatial queries

Run them:

```bash
npm run example
npm run example:search
npm run example:location
```

## Next Steps

1. Read the full [README.md](./README.md) for complete API documentation
2. Review [SETUP_SUMMARY.md](./SETUP_SUMMARY.md) for technical details
3. Check the [TypeScript types](./src/types.ts) for all available options

## Troubleshooting

### "ATDW_API_KEY environment variable is not set"

Make sure you've set the API key:
```bash
export ATDW_API_KEY=your-key
```

### "Cannot find module"

Build the project first:
```bash
npm run build
```

### Rate limiting (HTTP 429)

The client automatically handles rate limiting. If you see this message:
```
Rate limited (429). Waiting 60s before retry...
```

It's working as expected! The client will retry automatically.

## Getting Help

- ATDW API Documentation: https://developer.atdw.com.au
- Rate Limiting Info: https://au.intercom.help/atdw/en/articles/44447-api-rate-limiting
- Roam: https://roamhq.io

---

**Happy coding!** 🇦🇺
