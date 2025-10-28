-- ============================================================================
-- ATDW (Australian Tourism Data Warehouse) Schema Migration
-- ============================================================================
-- This migration creates the schema for storing Australia's national tourism
-- database (~56K products) with optimized caching and delta update support.
--
-- Design Principles:
-- - Normalized tables to minimize redundancy
-- - Content hash-based change detection for efficient daily deltas
-- - Optimized indexes for: ID lookups, geographic search, category filtering,
--   product name search
-- - Memory-friendly structure for effective caching
-- - Current state only (no versioning)
-- ============================================================================

-- ============================================================================
-- STEP 1: Enable required extensions
-- ============================================================================

-- Enable PostGIS for geographic queries
CREATE EXTENSION IF NOT EXISTS postgis;

-- Enable pg_trgm for fuzzy text search
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- ============================================================================
-- STEP 2: Create ATDW schema
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS atdw;
COMMENT ON SCHEMA atdw IS 'ATDW (Australian Tourism Data Warehouse) - National tourism product database';

-- ============================================================================
-- STEP 3: Core Products Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS atdw.products (
  -- Primary identifiers
  product_id VARCHAR(50) PRIMARY KEY,  -- ATDW ObjectId (e.g., "5fd017c6dad46f254f08fb78")
  product_number VARCHAR(20),           -- ATDW product number (e.g., "AU0427746")

  -- Basic product info
  product_name TEXT NOT NULL,
  product_category_id VARCHAR(50),      -- ACCOMM, ATTRACTION, TOUR, RESTAURANT, EVENT, etc.
  product_category_description TEXT,

  -- Status and dates
  status VARCHAR(20) DEFAULT 'ACTIVE',  -- ACTIVE, INACTIVE
  validity_date_from DATE,
  validity_date_to DATE,
  atdw_expiry_date DATE,
  product_update_date TIMESTAMPTZ,

  -- Descriptions
  product_description TEXT,
  product_short_description TEXT,

  -- Organization
  owning_organisation_id VARCHAR(50),
  owning_organisation_number VARCHAR(20),
  owning_organisation_name TEXT,
  australian_business_number VARCHAR(20),

  -- Geographic location (for PostGIS queries)
  latitude DECIMAL(10, 7),
  longitude DECIMAL(10, 7),
  location GEOGRAPHY(POINT, 4326),  -- PostGIS geography for accurate distance queries

  -- Location text fields
  suburb_name TEXT,
  city_name TEXT,
  area_name TEXT,
  state_name TEXT,
  country_name TEXT DEFAULT 'Australia',

  -- Accommodation-specific fields
  number_of_rooms INTEGER,
  total_capacity INTEGER,
  star_rating DECIMAL(2, 1),
  rate_from DECIMAL(10, 2),
  rate_to DECIMAL(10, 2),
  currency VARCHAR(3) DEFAULT 'AUD',
  check_in_time TIME,
  check_out_time TIME,

  -- Opening hours (restaurants, attractions, tours, events)
  opening_time_type VARCHAR(20),  -- SPECIFIC, BY_ARRANGEMENT, etc.
  opening_time_comment TEXT,      -- Free text description of opening hours

  -- Flags
  international_ready_flag BOOLEAN DEFAULT FALSE,
  children_catered_for_flag BOOLEAN DEFAULT FALSE,
  pets_allowed_flag BOOLEAN DEFAULT FALSE,
  disabled_access_flag BOOLEAN DEFAULT FALSE,
  pickup_available_flag BOOLEAN DEFAULT FALSE,
  deal_flag BOOLEAN DEFAULT FALSE,
  job_flag BOOLEAN DEFAULT FALSE,
  free_entry_flag BOOLEAN DEFAULT FALSE,

  -- URLs
  product_pixel_url TEXT,  -- ATDW tracking pixel
  menu_url TEXT,
  winelist_url TEXT,

  -- Content hash for efficient delta updates
  content_hash VARCHAR(32),  -- MD5 hash of all product fields

  -- Timestamps
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE atdw.products IS 'Australian tourism products (accommodation, attractions, tours, restaurants, events)';
COMMENT ON COLUMN atdw.products.content_hash IS 'MD5 hash of product data for O(1) change detection in delta updates';
COMMENT ON COLUMN atdw.products.location IS 'PostGIS geography point for accurate distance calculations';

-- Indexes for products table
CREATE INDEX IF NOT EXISTS idx_products_category ON atdw.products(product_category_id);
CREATE INDEX IF NOT EXISTS idx_products_state ON atdw.products(state_name);
CREATE INDEX IF NOT EXISTS idx_products_category_state ON atdw.products(product_category_id, state_name);
CREATE INDEX IF NOT EXISTS idx_products_updated_at ON atdw.products(updated_at);
CREATE INDEX IF NOT EXISTS idx_products_status ON atdw.products(status);
CREATE INDEX IF NOT EXISTS idx_products_content_hash ON atdw.products(content_hash);

-- PostGIS spatial index for geographic queries
CREATE INDEX IF NOT EXISTS idx_products_location ON atdw.products USING GIST(location);

-- Full-text search index for product names
CREATE INDEX IF NOT EXISTS idx_products_name_tsvector ON atdw.products
  USING GIN(to_tsvector('english', product_name));

-- ============================================================================
-- STEP 4: Addresses Table (1:many)
-- ============================================================================

CREATE TABLE IF NOT EXISTS atdw.addresses (
  id BIGSERIAL PRIMARY KEY,
  product_id VARCHAR(50) NOT NULL REFERENCES atdw.products(product_id) ON DELETE CASCADE,

  -- Address type
  address_type VARCHAR(20),  -- PHYSICAL, POSTAL
  address_type_description TEXT,

  -- Address components
  address_line1 TEXT,
  address_line2 TEXT,
  suburb_name TEXT,
  city_name TEXT,
  area_name TEXT,
  state_name TEXT,
  country_name TEXT,
  postal_code VARCHAR(10),

  -- Geographic coordinates
  latitude DECIMAL(10, 7),
  longitude DECIMAL(10, 7),
  location GEOGRAPHY(POINT, 4326),

  -- Metadata
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE atdw.addresses IS 'Product addresses (physical and postal)';

CREATE INDEX IF NOT EXISTS idx_addresses_product_id ON atdw.addresses(product_id);
CREATE INDEX IF NOT EXISTS idx_addresses_type ON atdw.addresses(address_type);
CREATE INDEX IF NOT EXISTS idx_addresses_location ON atdw.addresses USING GIST(location);

-- ============================================================================
-- STEP 5: Communication Table (1:many)
-- ============================================================================

CREATE TABLE IF NOT EXISTS atdw.communication (
  id BIGSERIAL PRIMARY KEY,
  product_id VARCHAR(50) NOT NULL REFERENCES atdw.products(product_id) ON DELETE CASCADE,

  -- Communication type
  communication_type VARCHAR(50),  -- CAEMENQUIR (email), CAPHENQUIR (phone), CAUBENQUIR (booking URL), CAURENQUIR (website URL)
  communication_type_description TEXT,

  -- Communication details
  isd_code VARCHAR(10),
  area_code VARCHAR(10),
  communication_detail TEXT,  -- Actual phone, email, or URL
  communication_detail_with_tracking TEXT,  -- URL with ATDW tracking

  -- Metadata
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE atdw.communication IS 'Product contact information (phone, email, website, booking URLs)';

CREATE INDEX IF NOT EXISTS idx_communication_product_id ON atdw.communication(product_id);
CREATE INDEX IF NOT EXISTS idx_communication_type ON atdw.communication(communication_type);

-- ============================================================================
-- STEP 6: Services Table (1:many) - Rooms for accommodation
-- ============================================================================

CREATE TABLE IF NOT EXISTS atdw.services (
  service_id VARCHAR(50) PRIMARY KEY,  -- ATDW service ObjectId
  product_id VARCHAR(50) NOT NULL REFERENCES atdw.products(product_id) ON DELETE CASCADE,

  -- Service details
  service_name TEXT NOT NULL,
  service_description TEXT,
  sequence_number INTEGER,

  -- Pricing
  rate_from DECIMAL(10, 2),
  rate_to DECIMAL(10, 2),
  rate_comment TEXT,
  rate_basis VARCHAR(50),
  rate_basis_description TEXT,

  -- Capacity
  minimum_capacity INTEGER,
  maximum_capacity INTEGER,
  number_of_services INTEGER,  -- Number of this room type available

  -- Flags
  children_catered_for_flag BOOLEAN DEFAULT FALSE,
  pets_allowed_flag BOOLEAN DEFAULT FALSE,
  disabled_access_flag BOOLEAN DEFAULT FALSE,
  pickup_available_flag BOOLEAN DEFAULT FALSE,

  -- URLs
  service_booking_url TEXT,
  service_booking_url_with_tracking TEXT,
  tour_booking_url TEXT,
  tour_booking_url_with_tracking TEXT,

  -- Metadata
  service_update_date TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE atdw.services IS 'Product services (rooms for accommodation, tour packages, event sessions)';
COMMENT ON COLUMN atdw.services.service_name IS 'e.g., "Studio", "One Bedroom Apartment", "Deluxe Suite"';

CREATE INDEX IF NOT EXISTS idx_services_product_id ON atdw.services(product_id);
CREATE INDEX IF NOT EXISTS idx_services_sequence ON atdw.services(product_id, sequence_number);

-- ============================================================================
-- STEP 7: Service Multimedia Table (1:many child of services)
-- ============================================================================

CREATE TABLE IF NOT EXISTS atdw.service_multimedia (
  id BIGSERIAL PRIMARY KEY,
  service_id VARCHAR(50) NOT NULL REFERENCES atdw.services(service_id) ON DELETE CASCADE,

  -- Multimedia details
  multimedia_id VARCHAR(50),  -- ATDW multimedia ObjectId
  multimedia_type VARCHAR(20) DEFAULT 'IMAGE',  -- IMAGE, VIDEO

  -- Image details
  server_path TEXT NOT NULL,  -- CDN URL
  width INTEGER,
  height INTEGER,
  size_orientation VARCHAR(10),  -- 4X3, 16X9

  -- Metadata
  alt_text TEXT,
  caption TEXT,
  photographer TEXT,
  copyright TEXT,
  sequence_number INTEGER,
  authored_date DATE,

  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE atdw.service_multimedia IS 'Images and videos for services (room photos, tour images)';

CREATE INDEX IF NOT EXISTS idx_service_multimedia_service_id ON atdw.service_multimedia(service_id);
CREATE INDEX IF NOT EXISTS idx_service_multimedia_sequence ON atdw.service_multimedia(service_id, sequence_number);

-- ============================================================================
-- STEP 8: Multimedia Table (1:many) - Product-level images
-- ============================================================================

CREATE TABLE IF NOT EXISTS atdw.multimedia (
  id BIGSERIAL PRIMARY KEY,
  product_id VARCHAR(50) NOT NULL REFERENCES atdw.products(product_id) ON DELETE CASCADE,

  -- Multimedia details
  multimedia_id VARCHAR(50),  -- ATDW multimedia ObjectId
  multimedia_type VARCHAR(20) DEFAULT 'IMAGE',  -- IMAGE, VIDEO

  -- Image details
  server_path TEXT NOT NULL,  -- CDN URL
  width INTEGER,
  height INTEGER,
  size_orientation VARCHAR(10),  -- 4X3, 16X9

  -- Metadata
  alt_text TEXT,
  caption TEXT,
  photographer TEXT,
  copyright TEXT,
  sequence_number INTEGER,
  authored_date DATE,
  market_variant_id VARCHAR(50),

  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE atdw.multimedia IS 'Product-level multimedia (hero images, gallery photos, videos)';

CREATE INDEX IF NOT EXISTS idx_multimedia_product_id ON atdw.multimedia(product_id);
CREATE INDEX IF NOT EXISTS idx_multimedia_sequence ON atdw.multimedia(product_id, sequence_number);
CREATE INDEX IF NOT EXISTS idx_multimedia_type ON atdw.multimedia(multimedia_type);

-- ============================================================================
-- STEP 9: Attributes Table (1:many) - Amenities and facilities
-- ============================================================================

CREATE TABLE IF NOT EXISTS atdw.attributes (
  id BIGSERIAL PRIMARY KEY,
  product_id VARCHAR(50) NOT NULL REFERENCES atdw.products(product_id) ON DELETE CASCADE,

  -- Attribute type and ID
  attribute_type_id VARCHAR(50),  -- ENTITY FAC, INTERNET, MEMBERSHIP, DISASSIST, etc.
  attribute_type_description TEXT,
  attribute_id VARCHAR(50),  -- 24HOURS, GYM, POOL, FREEWIFI, etc.
  attribute_description TEXT,

  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE atdw.attributes IS 'Product attributes (amenities, facilities, memberships)';
COMMENT ON COLUMN atdw.attributes.attribute_type_id IS 'Category of attribute (e.g., ENTITY FAC for facilities)';
COMMENT ON COLUMN atdw.attributes.attribute_id IS 'Specific attribute code (e.g., POOL, GYM, FREEWIFI)';

CREATE INDEX IF NOT EXISTS idx_attributes_product_id ON atdw.attributes(product_id);
CREATE INDEX IF NOT EXISTS idx_attributes_type ON atdw.attributes(attribute_type_id);
CREATE INDEX IF NOT EXISTS idx_attributes_type_id ON atdw.attributes(attribute_type_id, attribute_id);

-- ============================================================================
-- STEP 10: Rates Table (1:many) - Pricing information
-- ============================================================================

CREATE TABLE IF NOT EXISTS atdw.rates (
  id BIGSERIAL PRIMARY KEY,
  product_id VARCHAR(50) NOT NULL REFERENCES atdw.products(product_id) ON DELETE CASCADE,

  -- Rate details
  rates_type VARCHAR(50),  -- indicativePrices, standardRates, etc.
  rates_type_description TEXT,

  -- Pricing
  price_from DECIMAL(10, 2),
  price_to DECIMAL(10, 2),
  free BOOLEAN DEFAULT FALSE,

  -- Comments
  rate_comment TEXT,

  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE atdw.rates IS 'Product pricing information';

CREATE INDEX IF NOT EXISTS idx_rates_product_id ON atdw.rates(product_id);

-- ============================================================================
-- STEP 11: Deals Table (1:many) - Special offers
-- ============================================================================

CREATE TABLE IF NOT EXISTS atdw.deals (
  deal_id VARCHAR(50) PRIMARY KEY,  -- ATDW deal ObjectId
  product_id VARCHAR(50) NOT NULL REFERENCES atdw.products(product_id) ON DELETE CASCADE,

  -- Deal details
  deal_name TEXT NOT NULL,
  deal_description TEXT,

  -- Validity
  valid_from DATE,
  valid_to DATE,

  -- Pricing
  deal_value DECIMAL(10, 2),
  deal_type VARCHAR(50),

  -- URLs
  deal_url TEXT,
  deal_url_with_tracking TEXT,

  -- Metadata
  sequence_number INTEGER,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE atdw.deals IS 'Special offers and promotions';

CREATE INDEX IF NOT EXISTS idx_deals_product_id ON atdw.deals(product_id);
CREATE INDEX IF NOT EXISTS idx_deals_valid_dates ON atdw.deals(valid_from, valid_to);

-- ============================================================================
-- STEP 12: External Systems Table (1:many) - Third-party integrations
-- ============================================================================

CREATE TABLE IF NOT EXISTS atdw.external_systems (
  id BIGSERIAL PRIMARY KEY,
  product_id VARCHAR(50) NOT NULL REFERENCES atdw.products(product_id) ON DELETE CASCADE,

  -- External system details
  system_code VARCHAR(50),  -- INSTAGRAM, TRIPADVISO, TRIPADVISORID, AUS365ID, BOOKEASY
  system_text TEXT,  -- URL or ID for external system

  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE atdw.external_systems IS 'Links to external systems (TripAdvisor, Instagram, booking platforms)';

CREATE INDEX IF NOT EXISTS idx_external_systems_product_id ON atdw.external_systems(product_id);
CREATE INDEX IF NOT EXISTS idx_external_systems_code ON atdw.external_systems(system_code);

-- ============================================================================
-- STEP 11: Opening Hours Periods
-- ============================================================================

CREATE TABLE IF NOT EXISTS atdw.opening_hours_periods (
  id SERIAL PRIMARY KEY,
  product_id VARCHAR(50) NOT NULL REFERENCES atdw.products(product_id) ON DELETE CASCADE,

  -- Seasonal period dates (NULL = year-round)
  from_date DATE,
  to_date DATE,

  sequence_number INTEGER,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  UNIQUE(product_id, sequence_number)
);

COMMENT ON TABLE atdw.opening_hours_periods IS 'Seasonal opening hours periods (e.g., summer/winter hours, year-round)';

CREATE INDEX IF NOT EXISTS idx_opening_hours_periods_product_id ON atdw.opening_hours_periods(product_id);

-- ============================================================================
-- STEP 12: Opening Hours Daily Schedule
-- ============================================================================

CREATE TABLE IF NOT EXISTS atdw.opening_hours_schedule (
  id SERIAL PRIMARY KEY,
  period_id INTEGER NOT NULL REFERENCES atdw.opening_hours_periods(id) ON DELETE CASCADE,

  -- Day of week schedule
  day_of_week VARCHAR(3) NOT NULL,  -- MON, TUE, WED, THU, FRI, SAT, SUN
  is_closed BOOLEAN DEFAULT FALSE,
  opening_time TIME,
  closing_time TIME,

  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE atdw.opening_hours_schedule IS 'Daily opening/closing times for each day of the week within a period';

CREATE INDEX IF NOT EXISTS idx_opening_hours_schedule_period_id ON atdw.opening_hours_schedule(period_id);
CREATE INDEX IF NOT EXISTS idx_opening_hours_schedule_day ON atdw.opening_hours_schedule(day_of_week);

-- ============================================================================
-- STEP 13: Triggers for automatic timestamp and content hash updates
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION atdw.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for products table
DROP TRIGGER IF EXISTS trigger_products_updated_at ON atdw.products;
CREATE TRIGGER trigger_products_updated_at
  BEFORE UPDATE ON atdw.products
  FOR EACH ROW
  EXECUTE FUNCTION atdw.update_updated_at_column();

-- Function to compute content hash
CREATE OR REPLACE FUNCTION atdw.compute_product_content_hash()
RETURNS TRIGGER AS $$
BEGIN
  -- Compute MD5 hash of all relevant product fields
  NEW.content_hash = MD5(
    COALESCE(NEW.product_name, '') ||
    COALESCE(NEW.product_description, '') ||
    COALESCE(NEW.product_category_id, '') ||
    COALESCE(NEW.status, '') ||
    COALESCE(NEW.product_update_date::TEXT, '') ||
    COALESCE(NEW.latitude::TEXT, '') ||
    COALESCE(NEW.longitude::TEXT, '') ||
    COALESCE(NEW.suburb_name, '') ||
    COALESCE(NEW.city_name, '') ||
    COALESCE(NEW.state_name, '') ||
    COALESCE(NEW.rate_from::TEXT, '') ||
    COALESCE(NEW.rate_to::TEXT, '')
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-compute content hash on INSERT or UPDATE
DROP TRIGGER IF EXISTS trigger_products_content_hash ON atdw.products;
CREATE TRIGGER trigger_products_content_hash
  BEFORE INSERT OR UPDATE ON atdw.products
  FOR EACH ROW
  EXECUTE FUNCTION atdw.compute_product_content_hash();

-- Function to auto-populate PostGIS location from lat/lng
CREATE OR REPLACE FUNCTION atdw.update_product_location()
RETURNS TRIGGER AS $$
BEGIN
  -- Only update if latitude and longitude are provided
  IF NEW.latitude IS NOT NULL AND NEW.longitude IS NOT NULL THEN
    NEW.location = ST_SetSRID(ST_MakePoint(NEW.longitude, NEW.latitude), 4326)::geography;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-populate location
DROP TRIGGER IF EXISTS trigger_products_location ON atdw.products;
CREATE TRIGGER trigger_products_location
  BEFORE INSERT OR UPDATE ON atdw.products
  FOR EACH ROW
  EXECUTE FUNCTION atdw.update_product_location();

-- Function to auto-populate address location from lat/lng
CREATE OR REPLACE FUNCTION atdw.update_address_location()
RETURNS TRIGGER AS $$
BEGIN
  -- Only update if latitude and longitude are provided
  IF NEW.latitude IS NOT NULL AND NEW.longitude IS NOT NULL THEN
    NEW.location = ST_SetSRID(ST_MakePoint(NEW.longitude, NEW.latitude), 4326)::geography;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-populate address location
DROP TRIGGER IF EXISTS trigger_addresses_location ON atdw.addresses;
CREATE TRIGGER trigger_addresses_location
  BEFORE INSERT OR UPDATE ON atdw.addresses
  FOR EACH ROW
  EXECUTE FUNCTION atdw.update_address_location();

-- ============================================================================
-- STEP 14: Materialized views for common queries
-- ============================================================================

-- Materialized view: Products with primary address and image
CREATE MATERIALIZED VIEW IF NOT EXISTS atdw.products_enriched AS
SELECT
  p.*,
  -- Primary physical address
  pa.address_line1,
  pa.address_line2,
  pa.postal_code,
  -- Primary image
  pm.server_path AS primary_image_url,
  pm.alt_text AS primary_image_alt,
  -- Contact information (pivot phone, email, website)
  MAX(CASE WHEN c.communication_type = 'CAPHENQUIR' THEN c.communication_detail END) AS phone,
  MAX(CASE WHEN c.communication_type = 'CAEMENQUIR' THEN c.communication_detail END) AS email,
  MAX(CASE WHEN c.communication_type = 'CAURENQUIR' THEN c.communication_detail END) AS website
FROM atdw.products p
LEFT JOIN LATERAL (
  SELECT * FROM atdw.addresses a
  WHERE a.product_id = p.product_id AND a.address_type = 'PHYSICAL'
  ORDER BY a.created_at
  LIMIT 1
) pa ON TRUE
LEFT JOIN LATERAL (
  SELECT * FROM atdw.multimedia m
  WHERE m.product_id = p.product_id
  ORDER BY m.sequence_number
  LIMIT 1
) pm ON TRUE
LEFT JOIN atdw.communication c ON c.product_id = p.product_id
GROUP BY p.product_id, pa.address_line1, pa.address_line2, pa.postal_code,
         pm.server_path, pm.alt_text;

COMMENT ON MATERIALIZED VIEW atdw.products_enriched IS 'Products with primary address, image, and contact info for fast queries';

-- Index on materialized view
CREATE INDEX IF NOT EXISTS idx_products_enriched_product_id ON atdw.products_enriched(product_id);
CREATE INDEX IF NOT EXISTS idx_products_enriched_category ON atdw.products_enriched(product_category_id);
CREATE INDEX IF NOT EXISTS idx_products_enriched_state ON atdw.products_enriched(state_name);
CREATE INDEX IF NOT EXISTS idx_products_enriched_location ON atdw.products_enriched USING GIST(location);

-- ============================================================================
-- STEP 15: Helper functions for common queries
-- ============================================================================

-- Function to find products within radius (in kilometers)
CREATE OR REPLACE FUNCTION atdw.products_within_radius(
  search_lat DECIMAL,
  search_lng DECIMAL,
  radius_km DECIMAL
)
RETURNS TABLE (
  product_id VARCHAR(50),
  product_name TEXT,
  distance_km DECIMAL
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    p.product_id,
    p.product_name,
    ROUND((ST_Distance(
      p.location,
      ST_SetSRID(ST_MakePoint(search_lng, search_lat), 4326)::geography
    ) / 1000)::NUMERIC, 2) AS distance_km
  FROM atdw.products p
  WHERE ST_DWithin(
    p.location,
    ST_SetSRID(ST_MakePoint(search_lng, search_lat), 4326)::geography,
    radius_km * 1000
  )
  ORDER BY distance_km;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION atdw.products_within_radius IS 'Find products within specified radius (km) of a location';

-- Function to refresh materialized view
CREATE OR REPLACE FUNCTION atdw.refresh_products_enriched()
RETURNS VOID AS $$
BEGIN
  REFRESH MATERIALIZED VIEW CONCURRENTLY atdw.products_enriched;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION atdw.refresh_products_enriched IS 'Refresh the products_enriched materialized view';

-- ============================================================================
-- STEP 16: Grant permissions (adjust for your Supabase setup)
-- ============================================================================

-- Grant usage on schema to anon and authenticated roles (Supabase default)
GRANT USAGE ON SCHEMA atdw TO anon, authenticated;

-- Grant SELECT on all tables to anon and authenticated roles
GRANT SELECT ON ALL TABLES IN SCHEMA atdw TO anon, authenticated;

-- Grant SELECT on materialized views
GRANT SELECT ON atdw.products_enriched TO anon, authenticated;

-- Grant EXECUTE on functions
GRANT EXECUTE ON FUNCTION atdw.products_within_radius TO anon, authenticated;
GRANT EXECUTE ON FUNCTION atdw.refresh_products_enriched TO authenticated;

-- ============================================================================
-- Migration complete
-- ============================================================================

-- Summary
DO $$
BEGIN
  RAISE NOTICE '✅ ATDW tourism schema created successfully';
  RAISE NOTICE '   - 14 tables created (products, addresses, communication, services, opening hours, etc.)';
  RAISE NOTICE '   - PostGIS indexes for geographic queries';
  RAISE NOTICE '   - Full-text search indexes for product names';
  RAISE NOTICE '   - Content hash triggers for efficient delta updates';
  RAISE NOTICE '   - Materialized view for common queries';
  RAISE NOTICE '   - Helper functions for geographic search';
  RAISE NOTICE '';
  RAISE NOTICE '📊 Ready to load ~56K Australian tourism products';
  RAISE NOTICE '   - Use content_hash for efficient daily delta updates';
  RAISE NOTICE '   - Query by location: SELECT * FROM atdw.products_within_radius(-28.6450, 153.6050, 10)';
  RAISE NOTICE '   - Query by name: SELECT * FROM atdw.products WHERE to_tsvector(''english'', product_name) @@ to_tsquery(''cafe'')';
  RAISE NOTICE '   - Refresh cache: SELECT atdw.refresh_products_enriched()';
END $$;
