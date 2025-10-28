/**
 * Type definitions for ATDW (Australian Tourism Data Warehouse) ATLAS2 API
 *
 * These types represent the data structures returned by the ATDW API.
 * Based on the ATDW API documentation and real-world API responses.
 */

/**
 * Product categories supported by ATDW
 */
export type ProductCategory =
  | 'ACCOMM'
  | 'ATTRACTION'
  | 'TOUR'
  | 'RESTAURANT'
  | 'EVENT'
  | 'HIRE'
  | 'TRANSPORT'
  | 'GENERAL_SERVICE'
  | 'DESTINATION'
  | 'JOURNEY';

/**
 * Australian state codes
 */
export type AustralianState = 'NSW' | 'VIC' | 'QLD' | 'SA' | 'WA' | 'TAS' | 'NT' | 'ACT';

/**
 * Language/market variants supported by ATDW
 */
export type MarketVariant = 'ENGLISH' | 'CHINESE-T' | 'CHINESE-S';

/**
 * Product attribute from ATDW API
 */
export interface ProductAttribute {
  attributeId: string;
  label?: string;
  value?: string;
}

/**
 * Product address information
 */
export interface ProductAddress {
  addressLine?: string;
  city?: string;
  state?: AustralianState;
  postcode?: string;
  country?: string;
}

/**
 * Product contact information
 */
export interface ProductContact {
  phone?: string;
  email?: string;
  website?: string;
  fax?: string;
}

/**
 * Media item (image or video)
 */
export interface MediaItem {
  mediaUrl: string;
  mediaType: 'Image' | 'Video';
  caption?: string;
  isPrimary?: boolean;
}

/**
 * Basic product information returned in search results
 */
export interface Product {
  productId: string;
  productName: string;
  productDescription?: string;
  productCategoryId?: string;
  productCategory?: string;

  // Location
  boundary?: string; // Format: "lat,lng"
  state?: AustralianState;
  city?: string;
  region?: string;

  // Pricing
  rateFrom?: number;
  rateTo?: number;

  // Ratings
  starRating?: number;

  // Attributes
  productAttribute?: ProductAttribute[];

  // Media
  productImage?: MediaItem[];

  // Contact
  productAddress?: ProductAddress;
  productContact?: ProductContact;

  // Metadata
  productWebsiteUrl?: string;
  verticalType?: string;

  // Additional fields may be present depending on API query
  [key: string]: any;
}

/**
 * Detailed product information (from get_product endpoint)
 */
export interface ProductDetail extends Product {
  // Extended fields available in detailed view
  fullDescription?: string;
  shortDescription?: string;

  // Additional media
  productVideo?: MediaItem[];

  // Detailed attributes
  facilities?: ProductAttribute[];
  services?: ProductAttribute[];

  // Operating information
  operatingHours?: any;
  bookingInformation?: any;
}

/**
 * Search response from ATDW API
 */
export interface SearchResponse {
  products: Product[];
  numberOfResults: number;
  page?: number;
  pageSize?: number;
}

/**
 * Delta response for updated products
 */
export interface DeltaResponse {
  products: Product[];
  updatedSince: string;
}

/**
 * Search parameters for product search
 */
export interface SearchParams {
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
  paginate?: boolean;
  maxPages?: number;
  pageSize?: number;
}

/**
 * Client configuration options
 */
export interface ATDWClientConfig {
  apiKey?: string;
  minRequestInterval?: number; // milliseconds between requests
  maxRetries?: number;
  backoffFactor?: number;
}
