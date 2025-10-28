/**
 * ATDW (Australian Tourism Data Warehouse) ATLAS2 API Client
 *
 * Provides access to Australia's national tourism database with 50,000+ tourism products.
 *
 * API Features:
 * - Full-text search across tourism products
 * - Geospatial search (radius and polygon)
 * - Category filtering (accommodation, attractions, tours, restaurants, events)
 * - Pagination support
 * - Product details with multilingual support
 *
 * Rate Limiting & Pagination:
 * - ATDW does not specify numeric limits for rate limiting
 * - Returns HTTP 429 with Retry-After: 60 header when rate limited
 * - Recommends spreading requests rather than bursting
 * - Client implements exponential backoff with Retry-After header support
 * - Maximum page size: 5000 results per request (tested empirically)
 * - Default page size: 1000 (balances API calls vs response size)
 *
 * API Documentation:
 * https://developer.atdw.com.au
 * Rate Limiting Policy: https://au.intercom.help/atdw/en/articles/44447-api-rate-limiting
 *
 * Package: Industry package
 */

import type {
  ATDWClientConfig,
  AustralianState,
  DeltaResponse,
  MarketVariant,
  Product,
  ProductCategory,
  ProductDetail,
  SearchParams,
  SearchResponse,
} from './types';

/**
 * ATDW ATLAS2 API client for Australian tourism data.
 *
 * The ATDW (Australian Tourism Data Warehouse) provides access to 50,000+ tourism
 * products across accommodation, attractions, tours, restaurants, and events.
 *
 * @example
 * ```typescript
 * const client = new ATDWClient({ apiKey: 'your-api-key' });
 *
 * // Search for accommodation in Byron Bay
 * const products = await client.searchProducts({
 *   term: 'Byron Bay',
 *   categories: ['ACCOMM']
 * });
 * ```
 */
export class ATDWClient {
  private readonly BASE_URL = 'https://atlas.atdw-online.com.au/api/atlas';

  /**
   * Common product categories
   */
  public static readonly CATEGORIES: Record<string, ProductCategory> = {
    ACCOMMODATION: 'ACCOMM',
    ATTRACTION: 'ATTRACTION',
    TOUR: 'TOUR',
    RESTAURANT: 'RESTAURANT',
    EVENT: 'EVENT',
    HIRE: 'HIRE',
    TRANSPORT: 'TRANSPORT',
    GENERAL_SERVICE: 'GENERAL_SERVICE',
    DESTINATION: 'DESTINATION',
    JOURNEY: 'JOURNEY',
  };

  private apiKey: string;
  private lastRequestTime = 0;
  private minRequestInterval: number; // milliseconds
  private maxRetries: number;
  private backoffFactor: number;

  /**
   * Initialize ATDW API client.
   *
   * @param config - Client configuration
   * @param config.apiKey - ATDW distributor key (or set ATDW_API_KEY env var)
   * @param config.minRequestInterval - Minimum milliseconds between requests (default: 500ms = 2 req/sec)
   * @param config.maxRetries - Maximum retry attempts for rate limiting (default: 3)
   * @param config.backoffFactor - Exponential backoff multiplier (default: 2)
   * @throws {Error} If API key is not provided
   */
  constructor(config: ATDWClientConfig = {}) {
    const apiKey = config.apiKey || process.env.ATDW_API_KEY;
    if (!apiKey) {
      throw new Error(
        'ATDW API key required. Set ATDW_API_KEY environment variable or pass apiKey in config.'
      );
    }

    this.apiKey = apiKey;
    this.minRequestInterval = config.minRequestInterval ?? 500; // 2 requests per second
    this.maxRetries = config.maxRetries ?? 3;
    this.backoffFactor = config.backoffFactor ?? 2;
  }

  /**
   * Enforce rate limiting between requests
   */
  private async rateLimit(): Promise<void> {
    const now = Date.now();
    const elapsed = now - this.lastRequestTime;

    if (elapsed < this.minRequestInterval) {
      const delay = this.minRequestInterval - elapsed;
      await new Promise((resolve) => setTimeout(resolve, delay));
    }

    this.lastRequestTime = Date.now();
  }

  /**
   * Make API request with authentication, rate limiting, and retry logic.
   *
   * Implements exponential backoff for HTTP 429 responses and respects
   * the Retry-After header as per ATDW recommendations.
   *
   * @param endpoint - API endpoint path (e.g., '/products')
   * @param params - Query parameters
   * @returns Response data
   * @throws {Error} For HTTP errors (after retries exhausted)
   */
  private async makeRequest(endpoint: string, params: Record<string, any>): Promise<any> {
    // Add authentication and JSON output
    const queryParams = {
      ...params,
      key: this.apiKey,
      out: params.out || 'json',
    };

    const url = new URL(`${this.BASE_URL}${endpoint}`);
    Object.entries(queryParams).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        url.searchParams.append(key, String(value));
      }
    });

    // Retry loop with exponential backoff
    for (let attempt = 0; attempt <= this.maxRetries; attempt++) {
      // Apply rate limiting before request
      await this.rateLimit();

      const response = await fetch(url.toString());

      // Success
      if (response.ok) {
        return await response.json();
      }

      // Rate limited - respect Retry-After header
      if (response.status === 429) {
        const retryAfter = parseInt(response.headers.get('Retry-After') || '60', 10);

        if (attempt < this.maxRetries) {
          // Exponential backoff: retry_after * (2^attempt)
          const waitTime = retryAfter * Math.pow(this.backoffFactor, attempt) * 1000;
          console.warn(
            `Rate limited (429). Waiting ${waitTime / 1000}s before retry ${attempt + 1}/${
              this.maxRetries
            }...`
          );
          await new Promise((resolve) => setTimeout(resolve, waitTime));
          continue;
        }
      }

      // Other HTTP errors
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    throw new Error('Max retries exceeded');
  }

  /**
   * Search for tourism products with advanced filtering.
   *
   * @param params - Search parameters
   * @returns List of products matching search criteria
   *
   * @example
   * ```typescript
   * // Search for accommodation in Byron Bay
   * const products = await client.searchProducts({
   *   term: 'Byron Bay',
   *   categories: ['ACCOMM'],
   *   starRating: 4
   * });
   *
   * // Geospatial search within 10km radius
   * const nearby = await client.searchProducts({
   *   lat: -28.6450,
   *   lng: 153.6050,
   *   radiusKm: 10,
   *   categories: ['ATTRACTION']
   * });
   * ```
   */
  async searchProducts(params: SearchParams = {}): Promise<Product[]> {
    const apiParams: Record<string, any> = {};

    // Full-text search
    if (params.term) {
      apiParams.term = params.term;
    }

    // Category filtering
    if (params.categories && params.categories.length > 0) {
      apiParams.cats = params.categories.join(',');
    }

    // Geospatial search
    if (params.lat !== undefined && params.lng !== undefined) {
      apiParams.latlong = `${params.lat},${params.lng}`;
      if (params.radiusKm) {
        apiParams.dist = params.radiusKm;
      }
    }

    // Location filtering
    if (params.state) {
      apiParams.st = params.state.toUpperCase();
    }
    if (params.city) {
      apiParams.ct = params.city;
    }
    if (params.region) {
      apiParams.rg = params.region;
    }

    // Price filtering
    if (params.minRate !== undefined) {
      apiParams.minRate = params.minRate;
    }
    if (params.maxRate !== undefined) {
      apiParams.maxRate = params.maxRate;
    }

    // Star rating
    if (params.starRating !== undefined) {
      apiParams.starrating = params.starRating;
    }

    // Field selection
    if (params.fields && params.fields.length > 0) {
      apiParams.fl = params.fields.join(',');
    }

    // Pagination
    const pageSize = params.pageSize || 1000;
    apiParams.size = pageSize;

    const paginate = params.paginate !== false; // Default to true
    const maxPages = params.maxPages;

    // Fetch results with pagination
    const allResults: Product[] = [];
    let page = 1;

    while (true) {
      apiParams.pge = page;

      try {
        const response: SearchResponse = await this.makeRequest('/products', apiParams);

        // Extract products from response
        const products = response.products || [];
        if (products.length === 0) {
          break;
        }

        allResults.push(...products);

        // Check pagination
        if (!paginate) {
          break;
        }
        if (maxPages && page >= maxPages) {
          break;
        }

        // Check if more pages available
        const totalCount = response.numberOfResults || 0;
        if (allResults.length >= totalCount) {
          break;
        }

        page++;
      } catch (error: any) {
        // No more pages (404) or other error
        if (error.message?.includes('404')) {
          break;
        }
        throw error;
      }
    }

    return allResults;
  }

  /**
   * Get detailed information for a specific product.
   *
   * @param productId - Product identifier from search results
   * @param language - Market variant (default: ENGLISH)
   * @returns Detailed product information
   *
   * @example
   * ```typescript
   * const product = await client.getProduct('56b23538eac3c50eec5e9bd0');
   * console.log(product.productDescription);
   * ```
   */
  async getProduct(productId: string, language: MarketVariant = 'ENGLISH'): Promise<ProductDetail> {
    const params = {
      productId,
      mv: language,
    };

    return await this.makeRequest('/product', params);
  }

  /**
   * Convenience method for location-based search.
   *
   * @param lat - Latitude
   * @param lng - Longitude
   * @param radiusKm - Search radius in kilometers (default: 10km)
   * @param categories - List of category codes
   * @param extraParams - Additional search parameters
   * @returns List of products within radius
   *
   * @example
   * ```typescript
   * const nearby = await client.searchByLocation(
   *   -28.6450,
   *   153.6050,
   *   20,
   *   ['ACCOMM', 'RESTAURANT']
   * );
   * ```
   */
  async searchByLocation(
    lat: number,
    lng: number,
    radiusKm = 10,
    categories?: ProductCategory[],
    extraParams: Partial<SearchParams> = {}
  ): Promise<Product[]> {
    return this.searchProducts({
      lat,
      lng,
      radiusKm,
      categories,
      ...extraParams,
    });
  }

  /**
   * Convenience method for region-based search.
   *
   * @param options - Region search options
   * @returns List of products in region
   *
   * @example
   * ```typescript
   * const nswProducts = await client.searchByRegion({
   *   state: 'NSW',
   *   city: 'Byron Bay',
   *   categories: ['ATTRACTION']
   * });
   * ```
   */
  async searchByRegion(options: {
    state?: AustralianState;
    region?: string;
    city?: string;
    categories?: ProductCategory[];
    [key: string]: any;
  }): Promise<Product[]> {
    return this.searchProducts(options);
  }

  /**
   * Get products updated since a specific date.
   *
   * @param sinceDate - ISO date string (YYYY-MM-DD)
   * @param categories - Optional category filter
   * @returns List of updated products
   *
   * @example
   * ```typescript
   * const updated = await client.getDelta('2025-10-01');
   * console.log(`${updated.length} products updated since Oct 1`);
   * ```
   */
  async getDelta(sinceDate: string, categories?: ProductCategory[]): Promise<Product[]> {
    const params: Record<string, any> = {
      updatedSince: sinceDate,
    };

    if (categories && categories.length > 0) {
      params.cats = categories.join(',');
    }

    const response: DeltaResponse = await this.makeRequest('/delta', params);
    return response.products || [];
  }
}

/**
 * Create a new ATDW client instance
 *
 * @param config - Client configuration
 * @returns Configured ATDW client
 *
 * @example
 * ```typescript
 * import { createClient } from '@roamhq/atdw-client';
 *
 * const client = createClient({ apiKey: process.env.ATDW_API_KEY });
 * ```
 */
export function createClient(config?: ATDWClientConfig): ATDWClient {
  return new ATDWClient(config);
}
