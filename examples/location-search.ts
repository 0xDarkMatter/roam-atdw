/**
 * Geospatial search examples
 *
 * Run with: npm run example:location
 */

import { createClient } from '../src/index';

async function main() {
  if (!process.env.ATDW_API_KEY) {
    console.error('Error: ATDW_API_KEY environment variable is not set');
    process.exit(1);
  }

  const client = createClient();

  console.log('ATDW Client - Geospatial Search Examples\n');
  console.log('='.repeat(60));

  try {
    // Example 1: Search by location - Byron Bay
    console.log('\n1. Finding attractions near Byron Bay...');
    const byronBay = {
      lat: -28.6450,
      lng: 153.6050,
    };

    const nearByronBay = await client.searchByLocation(
      byronBay.lat,
      byronBay.lng,
      10, // 10km radius
      ['ATTRACTION', 'TOUR'],
      { paginate: false, pageSize: 5 }
    );

    console.log(`Found ${nearByronBay.length} attractions/tours within 10km of Byron Bay`);
    nearByronBay.slice(0, 3).forEach((p) => {
      console.log(`  - ${p.productName}`);
      if (p.boundary) {
        const [lat, lng] = p.boundary.split(',');
        console.log(`    Location: ${lat}, ${lng}`);
      }
    });

    // Example 2: Search by location - Sydney Opera House
    console.log('\n2. Finding accommodation near Sydney Opera House...');
    const operaHouse = {
      lat: -33.8568,
      lng: 151.2153,
    };

    const nearOperaHouse = await client.searchByLocation(
      operaHouse.lat,
      operaHouse.lng,
      5, // 5km radius
      ['ACCOMM'],
      { paginate: false, pageSize: 5 }
    );

    console.log(`Found ${nearOperaHouse.length} accommodation within 5km of Opera House`);
    nearOperaHouse.slice(0, 3).forEach((p) => {
      console.log(`  - ${p.productName}`);
      if (p.rateFrom) {
        console.log(`    From $${p.rateFrom}/night`);
      }
    });

    // Example 3: Search by location - Melbourne CBD
    console.log('\n3. Finding restaurants near Melbourne CBD...');
    const melbourneCBD = {
      lat: -37.8136,
      lng: 144.9631,
    };

    const nearMelbourne = await client.searchProducts({
      lat: melbourneCBD.lat,
      lng: melbourneCBD.lng,
      radiusKm: 3,
      categories: ['RESTAURANT'],
      paginate: false,
      pageSize: 5,
    });

    console.log(`Found ${nearMelbourne.length} restaurants within 3km of Melbourne CBD`);
    nearMelbourne.slice(0, 3).forEach((p) => {
      console.log(`  - ${p.productName}`);
      console.log(`    ${p.city || 'N/A'}, ${p.state || 'N/A'}`);
    });

    // Example 4: Wider search radius
    console.log('\n4. Finding all attractions within 50km of Gold Coast...');
    const goldCoast = {
      lat: -28.0167,
      lng: 153.4000,
    };

    const goldCoastArea = await client.searchByLocation(
      goldCoast.lat,
      goldCoast.lng,
      50, // 50km radius for larger area
      ['ATTRACTION'],
      { paginate: false, pageSize: 10 }
    );

    console.log(`Found ${goldCoastArea.length} attractions within 50km`);

    // Group by city
    const byCityMap = new Map<string, number>();
    goldCoastArea.forEach((p) => {
      const city = p.city || 'Unknown';
      byCityMap.set(city, (byCityMap.get(city) || 0) + 1);
    });

    console.log('Attractions by city:');
    Array.from(byCityMap.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .forEach(([city, count]) => {
        console.log(`  - ${city}: ${count} attractions`);
      });

    console.log('\n' + '='.repeat(60));
    console.log('Location search examples completed successfully!');
  } catch (error) {
    console.error('Error:', error);
    process.exit(1);
  }
}

main();
