/**
 * Advanced product search examples
 *
 * Run with: npm run example:search
 */

import { createClient } from '../src/index';

async function main() {
  if (!process.env.ATDW_API_KEY) {
    console.error('Error: ATDW_API_KEY environment variable is not set');
    process.exit(1);
  }

  const client = createClient();

  console.log('ATDW Client - Advanced Search Examples\n');
  console.log('='.repeat(60));

  try {
    // Example 1: Filter by state and category
    console.log('\n1. Searching for NSW restaurants...');
    const restaurants = await client.searchProducts({
      state: 'NSW',
      categories: ['RESTAURANT'],
      paginate: false,
      pageSize: 5,
    });

    console.log(`Found ${restaurants.length} restaurants in NSW`);
    restaurants.slice(0, 3).forEach((p) => {
      console.log(`  - ${p.productName} (${p.city || 'Unknown city'})`);
    });

    // Example 2: Filter by price range
    console.log('\n2. Searching for accommodation $100-$300 per night...');
    const affordable = await client.searchProducts({
      categories: ['ACCOMM'],
      minRate: 100,
      maxRate: 300,
      paginate: false,
      pageSize: 5,
    });

    console.log(`Found ${affordable.length} properties in price range`);
    affordable.slice(0, 3).forEach((p) => {
      console.log(
        `  - ${p.productName}: $${p.rateFrom || 'N/A'} - $${p.rateTo || 'N/A'}`
      );
    });

    // Example 3: Filter by star rating
    console.log('\n3. Searching for 5-star accommodation...');
    const luxury = await client.searchProducts({
      categories: ['ACCOMM'],
      starRating: 5,
      paginate: false,
      pageSize: 5,
    });

    console.log(`Found ${luxury.length} 5-star properties`);
    luxury.slice(0, 3).forEach((p) => {
      console.log(`  - ${p.productName} (${p.state || 'N/A'})`);
    });

    // Example 4: Search by region
    console.log('\n4. Using searchByRegion convenience method...');
    const regional = await client.searchByRegion({
      state: 'VIC',
      city: 'Melbourne',
      categories: ['ATTRACTION'],
      pageSize: 5,
      paginate: false,
    });

    console.log(`Found ${regional.length} attractions in Melbourne`);
    regional.slice(0, 3).forEach((p) => {
      console.log(`  - ${p.productName}`);
    });

    // Example 5: Delta updates
    console.log('\n5. Checking for updates since 2025-10-01...');
    const updated = await client.getDelta('2025-10-01', ['ACCOMM']);

    console.log(`Found ${updated.length} accommodation products updated since Oct 1`);
    if (updated.length > 0) {
      console.log('Recent updates:');
      updated.slice(0, 3).forEach((p) => {
        console.log(`  - ${p.productName}`);
      });
    }

    console.log('\n' + '='.repeat(60));
    console.log('Search examples completed successfully!');
  } catch (error) {
    console.error('Error:', error);
    process.exit(1);
  }
}

main();
