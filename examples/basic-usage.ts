/**
 * Basic usage example for ATDW Client
 *
 * Run with: npm run example
 */

import { createClient } from '../src/index';

async function main() {
  // Check for API key
  if (!process.env.ATDW_API_KEY) {
    console.error('Error: ATDW_API_KEY environment variable is not set');
    console.error('Set it with: export ATDW_API_KEY=your-api-key');
    process.exit(1);
  }

  // Create the client
  const client = createClient();

  console.log('ATDW Client - Basic Usage Example\n');
  console.log('='.repeat(50));

  try {
    // Example 1: Simple search by term
    console.log('\n1. Searching for "Byron Bay" accommodation...');
    const products = await client.searchProducts({
      term: 'Byron Bay',
      categories: ['ACCOMM'],
      paginate: false, // Only first page for demo
      pageSize: 5,
    });

    console.log(`Found ${products.length} products\n`);

    products.slice(0, 3).forEach((product, index) => {
      console.log(`${index + 1}. ${product.productName}`);
      console.log(`   ID: ${product.productId}`);
      console.log(`   Category: ${product.productCategory || 'N/A'}`);
      if (product.rateFrom) {
        console.log(`   Price from: $${product.rateFrom}`);
      }
      console.log();
    });

    // Example 2: Get detailed product information
    if (products.length > 0) {
      console.log('\n2. Getting detailed information for first product...');
      const productId = products[0]?.productId;
      if (productId) {
        const detail = await client.getProduct(productId);
        console.log(`\nProduct: ${detail.productName}`);
        console.log(`Description: ${detail.productDescription?.substring(0, 150)}...`);
        console.log(`Website: ${detail.productWebsiteUrl || 'N/A'}`);
      }
    }

    console.log('\n' + '='.repeat(50));
    console.log('Example completed successfully!');
  } catch (error) {
    console.error('Error:', error);
    process.exit(1);
  }
}

main();
