/**
 * ATDW (Australian Tourism Data Warehouse) API Client
 *
 * A TypeScript client for accessing Australia's national tourism database.
 *
 * @packageDocumentation
 */

export { ATDWClient, createClient } from './client';
export type {
  ATDWClientConfig,
  AustralianState,
  DeltaResponse,
  MarketVariant,
  MediaItem,
  Product,
  ProductAddress,
  ProductAttribute,
  ProductCategory,
  ProductContact,
  ProductDetail,
  SearchParams,
  SearchResponse,
} from './types';
