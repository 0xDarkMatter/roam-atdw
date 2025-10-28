-- ============================================================================
-- Migration 015: Rename external_id to atdw_id
-- ============================================================================
--
-- CLARITY IMPROVEMENT: Make column names explicit about data source
--
-- Changes:
-- - products.external_id → products.atdw_id
-- - supplier.external_id → supplier.source_id (keep generic for multi-source)
-- - Update unique constraint names
-- - Update upsert_product() function parameter
--
-- Rationale:
-- - ATDW DB is designed to be multi-source (ATDW, TripAdvisor, Google, Foursquare)
-- - Current "external_id" is ambiguous - external to what?
-- - "atdw_id" clearly indicates this is ATDW's product identifier
-- - Keeps supplier.external_id generic since suppliers can be from any source
--
-- ============================================================================

BEGIN;

-- ---------- 1) Rename columns ----------

-- Products table: external_id → atdw_id
ALTER TABLE products RENAME COLUMN external_id TO atdw_id;

-- Supplier table: external_id → source_id (keep generic)
ALTER TABLE supplier RENAME COLUMN external_id TO source_id;

-- ---------- 2) Update constraint names for clarity ----------

-- Drop old constraint
ALTER TABLE products DROP CONSTRAINT IF EXISTS products_source_ext_ux;

-- Recreate with clearer name
ALTER TABLE products ADD CONSTRAINT products_source_atdw_ux UNIQUE (source, atdw_id);

-- Supplier constraint (already has good name, just verify)
ALTER TABLE supplier DROP CONSTRAINT IF EXISTS supplier_source_external_id_key;
ALTER TABLE supplier ADD CONSTRAINT supplier_source_id_ux UNIQUE (source, source_id);

-- ---------- 3) Update upsert_product() function ----------

DROP FUNCTION IF EXISTS upsert_product CASCADE;

CREATE OR REPLACE FUNCTION upsert_product(
  p_source TEXT,
  p_atdw_id TEXT,  -- RENAMED from p_external_id
  p_supplier_id UUID,
  p_is_active BOOLEAN,
  p_name TEXT,
  p_category TEXT,
  p_classification TEXT,
  p_state TEXT,
  p_region TEXT,
  p_city TEXT,
  p_lat DOUBLE PRECISION,
  p_lon DOUBLE PRECISION,
  p_raw_source JSONB,
  p_media_sha256 TEXT DEFAULT NULL,
  p_attrs_sha256 TEXT DEFAULT NULL
) RETURNS UUID
LANGUAGE plpgsql
AS $$
DECLARE
  pid UUID;
  existing_content_sha256 TEXT;
  new_content_sha256 TEXT;
BEGIN
  -- Check if product exists and get its current hash
  SELECT product_id, content_sha256 INTO pid, existing_content_sha256
  FROM products
  WHERE source = p_source AND atdw_id = p_atdw_id;  -- UPDATED

  -- Insert or update product
  INSERT INTO products AS x (
    supplier_id, source, atdw_id, is_active,  -- UPDATED column name
    product_name, category, classification,
    state, region, city,
    latitude, longitude, raw_source,
    media_sha256, attrs_sha256
  )
  VALUES (
    p_supplier_id, p_source, p_atdw_id, COALESCE(p_is_active, TRUE),  -- UPDATED param
    p_name, p_category, p_classification,
    p_state, p_region, p_city,
    p_lat, p_lon, COALESCE(p_raw_source,'{}'::jsonb),
    p_media_sha256, p_attrs_sha256
  )
  ON CONFLICT (source, atdw_id) DO UPDATE  -- UPDATED column name
  SET is_active      = EXCLUDED.is_active,
      product_name   = EXCLUDED.product_name,
      category       = EXCLUDED.category,
      classification = EXCLUDED.classification,
      state          = EXCLUDED.state,
      region         = EXCLUDED.region,
      city           = EXCLUDED.city,
      latitude       = EXCLUDED.latitude,
      longitude      = EXCLUDED.longitude,
      raw_source     = EXCLUDED.raw_source,
      media_sha256   = EXCLUDED.media_sha256,
      attrs_sha256   = EXCLUDED.attrs_sha256,
      updated_at     = now()
  RETURNING product_id, content_sha256 INTO pid, new_content_sha256;

  -- Log change only if content actually changed
  IF existing_content_sha256 IS NULL OR existing_content_sha256 != new_content_sha256 THEN
    PERFORM log_product_change(pid, 'product', new_content_sha256);
  END IF;

  RETURN pid;
END;
$$;

COMMENT ON FUNCTION upsert_product IS
  'Upserts product from ATDW data. Updated in migration 015 to use atdw_id instead of external_id.';

-- ---------- 4) Update comments for clarity ----------

COMMENT ON COLUMN products.atdw_id IS
  'ATDW product identifier (productId field from ATDW API). This is ATDW''s unique ID for this product.';

COMMENT ON COLUMN products.source IS
  'Data source identifier (e.g., ''ATDW'', ''TRIPADVISOR'', ''GOOGLE'', ''FOURSQUARE''). Used with atdw_id for deduplication.';

COMMENT ON COLUMN supplier.source_id IS
  'External identifier from source system (e.g., ATDW supplier ID). Generic name allows multi-source support.';

-- ---------- 5) Create helpful index ----------

-- Index on atdw_id for direct ATDW lookups (common in API)
CREATE INDEX IF NOT EXISTS products_atdw_id_idx ON products(atdw_id);

-- ---------- 6) Summary ----------

DO $$
BEGIN
  RAISE NOTICE '✅ Migration 015: Rename external_id to atdw_id - COMPLETED';
  RAISE NOTICE '';
  RAISE NOTICE 'Changes Applied:';
  RAISE NOTICE '  ✓ products.external_id → products.atdw_id';
  RAISE NOTICE '  ✓ supplier.external_id → supplier.source_id';
  RAISE NOTICE '  ✓ Updated unique constraint: products_source_atdw_ux';
  RAISE NOTICE '  ✓ Updated upsert_product() function parameter';
  RAISE NOTICE '  ✓ Added index on products.atdw_id';
  RAISE NOTICE '';
  RAISE NOTICE 'Benefits:';
  RAISE NOTICE '  • Column names now explicitly indicate data source';
  RAISE NOTICE '  • Clearer API design (atdw_id vs ambiguous external_id)';
  RAISE NOTICE '  • Maintains multi-source architecture';
  RAISE NOTICE '';
  RAISE NOTICE 'Next Steps:';
  RAISE NOTICE '  1. Update Python loader to use atdw_id parameter';
  RAISE NOTICE '  2. Update API responses to use atdw_id field name';
  RAISE NOTICE '  3. Update documentation to reference atdw_id';
END$$;

COMMIT;
