-- ============================================================================
-- ATDW / Tourism Catalog - Core Schema Migration V2 (FIXED)
-- ============================================================================
--
-- FIXES APPLIED FROM POSTGRES EXPERT REVIEW:
-- P0 (Critical):
--   ✓ Changed geometry → geography for accurate distance queries
--   ✓ Fixed enforce_attribute_type() trigger logic
--   ✓ Added missing FK indexes (product_attribute, rates, deals)
--   ✓ Added unique index for CONCURRENT materialized view refresh
--
-- P1 (Performance):
--   ✓ Fixed hot attribute projection to clear stale values
--   ✓ Added index on product_attribute(attribute_id)
--   ✓ Changed EAV constraint from <= 1 to = 1 (exactly one value required)
--   ✓ Added auto-hash computation trigger for content_sha256
--   ✓ Added JSONB GIN indexes for fast queries
--   ✓ Added composite indexes for common query patterns
--
-- OPTIMIZED FOR:
-- - Delta updates with hash-based change detection
-- - Idempotent upserts with ON CONFLICT handling
-- - EAV attribute storage (not JSONB) per user preference
-- - High-performance caching and sync operations
--
-- ============================================================================

BEGIN;

-- ---------- 0) Extensions ----------

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS pgcrypto;   -- sha256 via digest()

-- ---------- 1) Utility: timestamp maintenance ----------

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  NEW.updated_at := now();
  RETURN NEW;
END$$;

-- ---------- 2) Core: products & suppliers ----------

CREATE TABLE IF NOT EXISTS supplier (
  supplier_id   BIGSERIAL PRIMARY KEY,
  name          TEXT NOT NULL,
  source        TEXT NOT NULL DEFAULT 'ATDW',
  external_id   TEXT NOT NULL,
  meta          JSONB NOT NULL DEFAULT '{}',
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (source, external_id)
);

CREATE TRIGGER supplier_set_updated_at
BEFORE UPDATE ON supplier
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE IF NOT EXISTS products (
  product_id      BIGSERIAL PRIMARY KEY,
  supplier_id     BIGINT REFERENCES supplier(supplier_id),
  source          TEXT NOT NULL DEFAULT 'ATDW',
  external_id     TEXT NOT NULL,                  -- upstream id
  is_active       BOOLEAN NOT NULL DEFAULT TRUE,

  product_name    TEXT NOT NULL,
  category        TEXT,                           -- ACCOMM/ATTRACTION/EVENT/...
  classification  TEXT,                           -- HOTEL/RESORT/...

  state           TEXT,
  region          TEXT,
  city            TEXT,

  latitude        DOUBLE PRECISION,
  longitude       DOUBLE PRECISION,
  geom            geography(Point,4326),          -- FIXED: geography for accurate distance queries

  raw_source      JSONB NOT NULL DEFAULT '{}',    -- upstream payload for audit
  content_sha256  TEXT,                           -- stable hash of product projection
  media_sha256    TEXT,
  attrs_sha256    TEXT,

  -- Common "hot" projections populated by triggers
  has_wifi        BOOLEAN,
  has_parking     BOOLEAN,
  star_rating     NUMERIC(2,1),

  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT products_source_ext_ux UNIQUE (source, external_id)
);

CREATE TRIGGER products_set_updated_at
BEFORE UPDATE ON products
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- Auto-compute geography point from lat/lon
CREATE OR REPLACE FUNCTION set_product_geom()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.longitude IS NOT NULL AND NEW.latitude IS NOT NULL THEN
    NEW.geom := ST_SetSRID(ST_MakePoint(NEW.longitude, NEW.latitude), 4326)::geography;  -- FIXED: cast to geography
  ELSE
    NEW.geom := NULL;
  END IF;
  RETURN NEW;
END$$;

CREATE TRIGGER products_set_geom
BEFORE INSERT OR UPDATE OF longitude, latitude ON products
FOR EACH ROW EXECUTE FUNCTION set_product_geom();

-- NEW: Auto-compute content_sha256 hash for delta update detection
CREATE OR REPLACE FUNCTION compute_product_content_sha256()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  NEW.content_sha256 := encode(digest(
    COALESCE(NEW.product_name, '') ||
    COALESCE(NEW.category, '') ||
    COALESCE(NEW.classification, '') ||
    COALESCE(NEW.state, '') ||
    COALESCE(NEW.region, '') ||
    COALESCE(NEW.city, '') ||
    COALESCE(NEW.latitude::text, '') ||
    COALESCE(NEW.longitude::text, '') ||
    COALESCE(NEW.is_active::text, '')
  , 'sha256'), 'hex');
  RETURN NEW;
END$$;

CREATE TRIGGER products_compute_content_sha256
BEFORE INSERT OR UPDATE ON products
FOR EACH ROW EXECUTE FUNCTION compute_product_content_sha256();

-- ---------- 3) Addresses ----------

CREATE TABLE IF NOT EXISTS addresses (
  address_id   BIGSERIAL PRIMARY KEY,
  product_id   BIGINT NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,
  kind         TEXT NOT NULL DEFAULT 'physical',    -- physical/postal
  line1        TEXT, line2 TEXT, line3 TEXT,
  city         TEXT, state TEXT, postcode TEXT, country TEXT,
  latitude     DOUBLE PRECISION, longitude DOUBLE PRECISION,
  geom         geography(Point,4326),              -- FIXED: geography
  address_sha256 TEXT,                             -- stable hash for change detection
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TRIGGER addresses_set_updated_at
BEFORE UPDATE ON addresses
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE OR REPLACE FUNCTION set_address_geom()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.longitude IS NOT NULL AND NEW.latitude IS NOT NULL THEN
    NEW.geom := ST_SetSRID(ST_MakePoint(NEW.longitude, NEW.latitude), 4326)::geography;  -- FIXED: cast to geography
  ELSE
    NEW.geom := NULL;
  END IF;
  RETURN NEW;
END$$;

CREATE TRIGGER addresses_set_geom
BEFORE INSERT OR UPDATE OF longitude, latitude ON addresses
FOR EACH ROW EXECUTE FUNCTION set_address_geom();

-- Auto-compute address_sha256 hash for delta update detection
CREATE OR REPLACE FUNCTION compute_address_sha256()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  NEW.address_sha256 := encode(digest(
    COALESCE(NEW.kind, '') ||
    COALESCE(NEW.line1, '') ||
    COALESCE(NEW.line2, '') ||
    COALESCE(NEW.line3, '') ||
    COALESCE(NEW.city, '') ||
    COALESCE(NEW.state, '') ||
    COALESCE(NEW.postcode, '') ||
    COALESCE(NEW.country, '') ||
    COALESCE(NEW.latitude::text, '') ||
    COALESCE(NEW.longitude::text, '')
  , 'sha256'), 'hex');
  RETURN NEW;
END$$;

CREATE TRIGGER addresses_compute_sha256
BEFORE INSERT OR UPDATE ON addresses
FOR EACH ROW EXECUTE FUNCTION compute_address_sha256();

-- ---------- 4) Communication ----------

CREATE TABLE IF NOT EXISTS communication (
  comms_id    BIGSERIAL PRIMARY KEY,
  product_id  BIGINT NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,
  kind        TEXT NOT NULL,         -- phone/email/website/booking/instagram...
  value       TEXT NOT NULL,
  comms_sha256 TEXT,                 -- stable hash for change detection
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TRIGGER communication_set_updated_at
BEFORE UPDATE ON communication
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- Auto-compute comms_sha256 hash for delta update detection
CREATE OR REPLACE FUNCTION compute_communication_sha256()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  NEW.comms_sha256 := encode(digest(
    COALESCE(NEW.kind, '') ||
    COALESCE(NEW.value, '')
  , 'sha256'), 'hex');
  RETURN NEW;
END$$;

CREATE TRIGGER communication_compute_sha256
BEFORE INSERT OR UPDATE ON communication
FOR EACH ROW EXECUTE FUNCTION compute_communication_sha256();

-- ---------- 5) Services (rooms/tours/sessions) ----------

CREATE TABLE IF NOT EXISTS services (
  service_id    BIGSERIAL PRIMARY KEY,
  product_id    BIGINT NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,
  name          TEXT NOT NULL,
  service_kind  TEXT,                 -- room/tour/session/...
  occupancy_adults    SMALLINT,
  occupancy_children  SMALLINT,
  bed_config    TEXT,
  details       JSONB NOT NULL DEFAULT '{}',
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TRIGGER services_set_updated_at
BEFORE UPDATE ON services
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ---------- 6) Media (relational + dedup) ----------

CREATE TABLE IF NOT EXISTS media_asset (
  asset_id     BIGSERIAL PRIMARY KEY,
  provider     TEXT,               -- 'ATDW','S3','YouTube','Cloudflare'
  url          TEXT NOT NULL,
  media_type   TEXT NOT NULL,      -- 'image','video'
  mime_type    TEXT,
  width        INT, height INT, duration_seconds INT,
  bytes        BIGINT,
  checksum     TEXT,               -- sha256 of binary or canonical URL
  meta         JSONB NOT NULL DEFAULT '{}',
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (provider, url)
);

CREATE TRIGGER media_asset_set_updated_at
BEFORE UPDATE ON media_asset
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE IF NOT EXISTS product_media (
  product_id   BIGINT NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,
  asset_id     BIGINT NOT NULL REFERENCES media_asset(asset_id) ON DELETE CASCADE,
  ordinal      INT NOT NULL DEFAULT 1,     -- gallery order
  role         TEXT,                       -- 'hero','gallery','floorplan','thumb'
  tags         TEXT[],
  variants     JSONB NOT NULL DEFAULT '[]',
  source_meta  JSONB NOT NULL DEFAULT '{}',
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (product_id, asset_id)
);

CREATE TRIGGER product_media_set_updated_at
BEFORE UPDATE ON product_media
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ---------- 7) Attributes: dictionary + typed EAV ----------

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'attr_type') THEN
    CREATE TYPE attr_type AS ENUM ('bool','int','numeric','text','date','json');
  END IF;
END$$;

CREATE TABLE IF NOT EXISTS attribute_def (
  attribute_id  SMALLSERIAL PRIMARY KEY,
  code          TEXT UNIQUE NOT NULL,       -- 'wifi','parking','star_rating',...
  label         TEXT,
  data_type     attr_type NOT NULL,
  facet         BOOLEAN NOT NULL DEFAULT FALSE,
  description   TEXT
);

CREATE TABLE IF NOT EXISTS product_attribute (
  product_id    BIGINT NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,
  attribute_id  SMALLINT NOT NULL REFERENCES attribute_def(attribute_id),
  val_bool      BOOLEAN,
  val_int       BIGINT,
  val_num       NUMERIC(18,6),
  val_text      TEXT,
  val_date      DATE,
  val_json      JSONB,
  source_meta   JSONB NOT NULL DEFAULT '{}',
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (product_id, attribute_id),
  CONSTRAINT product_attribute_value_one_ck CHECK (
    -- FIXED: Changed from <= 1 to = 1 (exactly one value required)
    (val_bool IS NOT NULL)::int +
    (val_int  IS NOT NULL)::int +
    (val_num  IS NOT NULL)::int +
    (val_text IS NOT NULL)::int +
    (val_date IS NOT NULL)::int +
    (val_json IS NOT NULL)::int = 1
  )
);

CREATE TRIGGER product_attribute_set_updated_at
BEFORE UPDATE ON product_attribute
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- FIXED: Enforce EAV type correctness with correct logic
CREATE OR REPLACE FUNCTION enforce_attribute_type()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE dtype attr_type;
BEGIN
  SELECT data_type INTO dtype FROM attribute_def WHERE attribute_id = NEW.attribute_id;
  IF dtype IS NULL THEN
    RAISE EXCEPTION 'Unknown attribute_id %', NEW.attribute_id;
  END IF;

  -- FIXED: Use CASE statement instead of broken AND logic
  CASE dtype
    WHEN 'bool' THEN
      IF NEW.val_bool IS NULL THEN
        RAISE EXCEPTION 'Attribute % expects bool value', NEW.attribute_id;
      END IF;
    WHEN 'int' THEN
      IF NEW.val_int IS NULL THEN
        RAISE EXCEPTION 'Attribute % expects int value', NEW.attribute_id;
      END IF;
    WHEN 'numeric' THEN
      IF NEW.val_num IS NULL THEN
        RAISE EXCEPTION 'Attribute % expects numeric value', NEW.attribute_id;
      END IF;
    WHEN 'text' THEN
      IF NEW.val_text IS NULL THEN
        RAISE EXCEPTION 'Attribute % expects text value', NEW.attribute_id;
      END IF;
    WHEN 'date' THEN
      IF NEW.val_date IS NULL THEN
        RAISE EXCEPTION 'Attribute % expects date value', NEW.attribute_id;
      END IF;
    WHEN 'json' THEN
      IF NEW.val_json IS NULL THEN
        RAISE EXCEPTION 'Attribute % expects json value', NEW.attribute_id;
      END IF;
  END CASE;

  RETURN NEW;
END$$;

CREATE TRIGGER product_attribute_type_chk
BEFORE INSERT OR UPDATE ON product_attribute
FOR EACH ROW EXECUTE FUNCTION enforce_attribute_type();

-- FIXED: "Hot" attribute projections - clear stale values instead of keeping them
CREATE OR REPLACE FUNCTION update_product_hot_attrs(p_product_id BIGINT)
RETURNS void LANGUAGE plpgsql AS $$
DECLARE
  _wifi_id SMALLINT;
  _park_id SMALLINT;
  _star_id SMALLINT;
  _has_wifi BOOLEAN;
  _has_parking BOOLEAN;
  _star NUMERIC(2,1);
BEGIN
  SELECT attribute_id INTO _wifi_id FROM attribute_def WHERE code='wifi';
  SELECT attribute_id INTO _park_id FROM attribute_def WHERE code='parking';
  SELECT attribute_id INTO _star_id FROM attribute_def WHERE code='star_rating';

  IF _wifi_id IS NOT NULL THEN
    SELECT val_bool INTO _has_wifi
    FROM product_attribute WHERE product_id=p_product_id AND attribute_id=_wifi_id;
  END IF;

  IF _park_id IS NOT NULL THEN
    SELECT val_bool INTO _has_parking
    FROM product_attribute WHERE product_id=p_product_id AND attribute_id=_park_id;
  END IF;

  IF _star_id IS NOT NULL THEN
    SELECT val_num::NUMERIC(2,1) INTO _star
    FROM product_attribute WHERE product_id=p_product_id AND attribute_id=_star_id;
  END IF;

  -- FIXED: Direct assignment instead of COALESCE (allows clearing stale values)
  UPDATE products
  SET has_wifi   = _has_wifi,      -- NULL if attribute deleted
      has_parking= _has_parking,   -- NULL if attribute deleted
      star_rating= _star,          -- NULL if attribute deleted
      updated_at = now()
  WHERE product_id = p_product_id;
END$$;

-- Fire projection updates when attributes change
CREATE OR REPLACE FUNCTION touch_hot_attrs()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  PERFORM update_product_hot_attrs(NEW.product_id);
  RETURN NEW;
END$$;

CREATE TRIGGER product_attribute_hot_projection_ins
AFTER INSERT ON product_attribute
FOR EACH ROW EXECUTE FUNCTION touch_hot_attrs();

CREATE TRIGGER product_attribute_hot_projection_upd
AFTER UPDATE ON product_attribute
FOR EACH ROW EXECUTE FUNCTION touch_hot_attrs();

-- DELETE trigger needs special handling - can't pass parameters directly in EXECUTE
CREATE OR REPLACE FUNCTION touch_hot_attrs_on_delete()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  PERFORM update_product_hot_attrs(OLD.product_id);
  RETURN OLD;
END$$;

CREATE TRIGGER product_attribute_hot_projection_del
AFTER DELETE ON product_attribute
FOR EACH ROW EXECUTE FUNCTION touch_hot_attrs_on_delete();

-- ---------- 8) Rates / Deals ----------

CREATE TABLE IF NOT EXISTS rates (
  rate_id      BIGSERIAL PRIMARY KEY,
  product_id   BIGINT NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,
  service_id   BIGINT REFERENCES services(service_id) ON DELETE CASCADE,
  price_cents  INTEGER NOT NULL,
  currency     TEXT NOT NULL DEFAULT 'AUD',
  start_date   DATE NOT NULL,
  end_date     DATE NOT NULL,
  constraints_json JSONB NOT NULL DEFAULT '{}',
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TRIGGER rates_set_updated_at
BEFORE UPDATE ON rates
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE IF NOT EXISTS deals (
  deal_id      BIGSERIAL PRIMARY KEY,
  product_id   BIGINT NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,
  service_id   BIGINT REFERENCES services(service_id) ON DELETE CASCADE,
  title        TEXT,
  price_cents  INTEGER,
  currency     TEXT NOT NULL DEFAULT 'AUD',
  start_date   DATE NOT NULL,
  end_date     DATE NOT NULL,
  constraints_json JSONB NOT NULL DEFAULT '{}',
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TRIGGER deals_set_updated_at
BEFORE UPDATE ON deals
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ---------- 9) External systems ----------

CREATE TABLE IF NOT EXISTS external_systems (
  ext_id      BIGSERIAL PRIMARY KEY,
  product_id  BIGINT NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,
  system_code TEXT NOT NULL,           -- 'TRIPADVISOR','INSTAGRAM','BOOKING','X'
  external_ref TEXT NOT NULL,
  meta        JSONB NOT NULL DEFAULT '{}',
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS ext_unique ON external_systems(product_id, system_code);

CREATE TRIGGER external_systems_set_updated_at
BEFORE UPDATE ON external_systems
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ---------- 10) Text search ----------

ALTER TABLE products
  ADD COLUMN IF NOT EXISTS name_tsv tsvector GENERATED ALWAYS AS (
    to_tsvector('english', coalesce(product_name,''))
  ) STORED;

-- ---------- 11) Change log for cache invalidation ----------

CREATE TABLE IF NOT EXISTS change_log (
  change_id    BIGSERIAL PRIMARY KEY,
  product_id   BIGINT NOT NULL,
  change_kind  TEXT NOT NULL,      -- 'product','media','attrs','services','rates','deals'
  payload_hash TEXT,
  changed_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Helper to log a change
CREATE OR REPLACE FUNCTION log_product_change(p_product_id BIGINT, p_kind TEXT, p_hash TEXT)
RETURNS void LANGUAGE plpgsql AS $$
BEGIN
  INSERT INTO change_log(product_id, change_kind, payload_hash) VALUES (p_product_id, p_kind, p_hash);
  PERFORM pg_notify('product_changed', p_product_id::text || ':' || p_kind);
END$$;

-- ---------- 12) Indexes ----------

-- Products
CREATE INDEX IF NOT EXISTS products_active_idx      ON products(is_active);
CREATE INDEX IF NOT EXISTS products_cat_state_idx   ON products(category, state);
CREATE INDEX IF NOT EXISTS products_updated_desc    ON products(updated_at DESC);
CREATE INDEX IF NOT EXISTS products_geom_gix        ON products USING GIST (geom);
CREATE INDEX IF NOT EXISTS products_name_tsv_gin    ON products USING GIN (name_tsv);
CREATE INDEX IF NOT EXISTS products_name_trgm       ON products USING GIN (product_name gin_trgm_ops);

-- NEW: Composite index for active products filtered by category+state (common query pattern)
CREATE INDEX IF NOT EXISTS products_active_cat_state_idx ON products(is_active, category, state) WHERE is_active = true;

-- NEW: Index on content_sha256 for delta update lookups
CREATE INDEX IF NOT EXISTS products_content_sha256_idx ON products(content_sha256);

-- Addresses
CREATE INDEX IF NOT EXISTS addresses_prod_idx       ON addresses(product_id);
CREATE INDEX IF NOT EXISTS addresses_geom_gix       ON addresses USING GIST (geom);
CREATE INDEX IF NOT EXISTS addresses_sha256_idx     ON addresses(address_sha256);

-- Communication
CREATE INDEX IF NOT EXISTS communication_prod_idx   ON communication(product_id);
CREATE INDEX IF NOT EXISTS communication_kind_idx   ON communication(kind);
CREATE INDEX IF NOT EXISTS communication_sha256_idx ON communication(comms_sha256);

-- Services
CREATE INDEX IF NOT EXISTS services_prod_idx        ON services(product_id);

-- NEW: JSONB GIN indexes for fast querying
CREATE INDEX IF NOT EXISTS services_details_gin     ON services USING GIN(details jsonb_path_ops);

-- Media
CREATE INDEX IF NOT EXISTS product_media_ord_idx    ON product_media(product_id, ordinal);
CREATE INDEX IF NOT EXISTS product_media_role_idx   ON product_media(role);

-- NEW: JSONB GIN indexes
CREATE INDEX IF NOT EXISTS media_asset_meta_gin     ON media_asset USING GIN(meta jsonb_path_ops);
CREATE INDEX IF NOT EXISTS product_media_variants_gin ON product_media USING GIN(variants jsonb_path_ops);

-- Attributes
-- NEW: Added missing FK index on attribute_id (P1 fix)
CREATE INDEX IF NOT EXISTS product_attribute_attr_idx ON product_attribute(attribute_id);

-- NEW: Added missing FK index on product_id (P0 fix)
CREATE INDEX IF NOT EXISTS product_attribute_prod_idx ON product_attribute(product_id);

-- Partial indexes for common attribute filters
DO $$
DECLARE wifi_id SMALLINT; park_id SMALLINT; star_id SMALLINT;
BEGIN
  SELECT attribute_id INTO wifi_id FROM attribute_def WHERE code='wifi';
  IF wifi_id IS NOT NULL THEN
    EXECUTE format('CREATE INDEX IF NOT EXISTS pa_wifi_true_idx ON product_attribute (product_id)
                    WHERE attribute_id=%s AND val_bool IS TRUE', wifi_id);
  END IF;

  SELECT attribute_id INTO park_id FROM attribute_def WHERE code='parking';
  IF park_id IS NOT NULL THEN
    EXECUTE format('CREATE INDEX IF NOT EXISTS pa_parking_true_idx ON product_attribute (product_id)
                    WHERE attribute_id=%s AND val_bool IS TRUE', park_id);
  END IF;

  SELECT attribute_id INTO star_id FROM attribute_def WHERE code='star_rating';
  IF star_id IS NOT NULL THEN
    EXECUTE format('CREATE INDEX IF NOT EXISTS pa_star_idx ON product_attribute (val_num)
                    WHERE attribute_id=%s', star_id);
  END IF;
END$$;

-- Rates
-- NEW: Added missing FK index (P0 fix)
CREATE INDEX IF NOT EXISTS rates_prod_idx ON rates(product_id);
CREATE INDEX IF NOT EXISTS rates_service_idx ON rates(service_id);
CREATE INDEX IF NOT EXISTS rates_dates_idx ON rates(start_date, end_date);

-- NEW: JSONB GIN index
CREATE INDEX IF NOT EXISTS rates_constraints_gin ON rates USING GIN(constraints_json jsonb_path_ops);

-- Deals
-- NEW: Added missing FK index (P0 fix)
CREATE INDEX IF NOT EXISTS deals_prod_idx ON deals(product_id);
CREATE INDEX IF NOT EXISTS deals_service_idx ON deals(service_id);
CREATE INDEX IF NOT EXISTS deals_dates_idx ON deals(start_date, end_date);

-- NEW: JSONB GIN index
CREATE INDEX IF NOT EXISTS deals_constraints_gin ON deals USING GIN(constraints_json jsonb_path_ops);

-- External Systems
CREATE INDEX IF NOT EXISTS external_systems_prod_idx ON external_systems(product_id);
CREATE INDEX IF NOT EXISTS external_systems_code_idx ON external_systems(system_code);

-- Change Log
CREATE INDEX IF NOT EXISTS change_log_prod_idx ON change_log(product_id);
CREATE INDEX IF NOT EXISTS change_log_changed_at_idx ON change_log(changed_at DESC);
CREATE INDEX IF NOT EXISTS change_log_kind_idx ON change_log(change_kind);

-- ---------- 13) Materialized "card" view ----------

DROP MATERIALIZED VIEW IF EXISTS product_card_mv CASCADE;

CREATE MATERIALIZED VIEW product_card_mv AS
SELECT
  p.product_id,
  p.product_name,
  p.category,
  p.state,
  p.region,
  p.city,
  p.geom,
  p.has_wifi,
  p.has_parking,
  p.star_rating,
  pm.asset_id AS hero_asset_id,
  ma.url AS hero_image_url      -- NEW: Include actual URL for faster queries
FROM products p
LEFT JOIN LATERAL (
  SELECT asset_id
  FROM product_media
  WHERE product_id = p.product_id AND (role = 'hero' OR role IS NULL)
  ORDER BY ordinal
  LIMIT 1
) pm ON true
LEFT JOIN media_asset ma ON ma.asset_id = pm.asset_id
WHERE p.is_active;

-- NEW: Added unique index for CONCURRENT refresh (P0 fix)
CREATE UNIQUE INDEX product_card_mv_pk ON product_card_mv(product_id);

CREATE INDEX product_card_mv_cat_state_idx ON product_card_mv(category, state);
CREATE INDEX product_card_mv_star_idx      ON product_card_mv(star_rating DESC);
CREATE INDEX product_card_mv_geom_gix      ON product_card_mv USING GIST (geom);

-- ---------- 14) Upsert helpers (set-wise, idempotent) ----------

-- 14.1 Upsert product (content hash computed automatically by trigger)
CREATE OR REPLACE FUNCTION upsert_product(
  p_source TEXT, p_external_id TEXT,
  p_supplier_id BIGINT,
  p_is_active BOOLEAN,
  p_name TEXT, p_category TEXT, p_classification TEXT,
  p_state TEXT, p_region TEXT, p_city TEXT,
  p_lat DOUBLE PRECISION, p_lon DOUBLE PRECISION,
  p_raw_source JSONB,
  p_media_sha256 TEXT DEFAULT NULL,
  p_attrs_sha256 TEXT DEFAULT NULL
) RETURNS BIGINT LANGUAGE plpgsql AS $$
DECLARE
  pid BIGINT;
  existing_content_sha256 TEXT;
  new_content_sha256 TEXT;
BEGIN
  -- Check if product exists and get its current hash
  SELECT product_id, content_sha256 INTO pid, existing_content_sha256
  FROM products
  WHERE source = p_source AND external_id = p_external_id;

  -- Insert or update product
  INSERT INTO products AS x (
    supplier_id, source, external_id, is_active,
    product_name, category, classification,
    state, region, city,
    latitude, longitude, raw_source,
    media_sha256, attrs_sha256
  )
  VALUES (
    p_supplier_id, p_source, p_external_id, COALESCE(p_is_active, TRUE),
    p_name, p_category, p_classification,
    p_state, p_region, p_city,
    p_lat, p_lon, COALESCE(p_raw_source,'{}'::jsonb),
    p_media_sha256, p_attrs_sha256
  )
  ON CONFLICT (source, external_id) DO UPDATE
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
END$$;

-- 14.2 Upsert attributes (delta: insert/update keys present; delete vanished)
CREATE OR REPLACE FUNCTION upsert_product_attributes(p_product_id BIGINT, p_attrs JSONB)
RETURNS void LANGUAGE plpgsql AS $$
DECLARE
  kv RECORD;
  def RECORD;
  v_bool BOOLEAN; v_int BIGINT; v_num NUMERIC; v_text TEXT; v_date DATE; v_json JSONB;
  present_codes TEXT[];
BEGIN
  IF p_attrs IS NULL THEN RETURN; END IF;

  -- track which codes we saw (for deletion of vanished)
  present_codes := ARRAY(SELECT key FROM jsonb_each(p_attrs));

  FOR kv IN SELECT * FROM jsonb_each(p_attrs) LOOP
    SELECT * INTO def FROM attribute_def WHERE code = kv.key;
    IF NOT FOUND THEN
      RAISE EXCEPTION 'Unknown attribute code %, add to attribute_def first', kv.key;
    END IF;

    v_bool := NULL; v_int := NULL; v_num := NULL; v_text := NULL; v_date := NULL; v_json := NULL;
    CASE def.data_type
      WHEN 'bool'    THEN v_bool := (kv.value)::boolean;
      WHEN 'int'     THEN v_int  := (kv.value)::bigint;
      WHEN 'numeric' THEN v_num  := (kv.value)::numeric;
      WHEN 'text'    THEN v_text := (kv.value)::text;
      WHEN 'date'    THEN v_date := (kv.value)::date;
      WHEN 'json'    THEN v_json := (kv.value)::jsonb;
      ELSE RAISE EXCEPTION 'Unhandled data_type %', def.data_type;
    END CASE;

    INSERT INTO product_attribute(product_id, attribute_id, val_bool, val_int, val_num, val_text, val_date, val_json)
    VALUES (p_product_id, def.attribute_id, v_bool, v_int, v_num, v_text, v_date, v_json)
    ON CONFLICT (product_id, attribute_id) DO UPDATE
    SET val_bool = EXCLUDED.val_bool,
        val_int  = EXCLUDED.val_int,
        val_num  = EXCLUDED.val_num,
        val_text = EXCLUDED.val_text,
        val_date = EXCLUDED.val_date,
        val_json = EXCLUDED.val_json,
        updated_at = now();
  END LOOP;

  -- delete vanished attributes (present before, absent now)
  DELETE FROM product_attribute pa
  USING attribute_def d
  WHERE pa.product_id = p_product_id
    AND d.attribute_id = pa.attribute_id
    AND d.code NOT IN (SELECT unnest(present_codes));

  PERFORM update_product_hot_attrs(p_product_id);
  PERFORM log_product_change(p_product_id, 'attrs', NULL);
END$$;

-- 14.3 Upsert media (delta by (provider,url))
CREATE OR REPLACE FUNCTION upsert_product_media(p_product_id BIGINT, p_media JSONB)
RETURNS void LANGUAGE plpgsql AS $$
DECLARE
  itm JSONB;
  _provider TEXT; _url TEXT; _ordinal INT; _role TEXT; _tags TEXT[]; _variants JSONB; _meta JSONB;
  _asset_id BIGINT;
  present_urls TEXT[];
BEGIN
  IF p_media IS NULL THEN RETURN; END IF;

  present_urls := ARRAY(SELECT (x->>'url') FROM jsonb_array_elements(p_media) x);

  FOR itm IN SELECT * FROM jsonb_array_elements(p_media) LOOP
    _provider := COALESCE(itm->>'provider','ATDW');
    _url      := itm->>'url';
    _ordinal  := COALESCE((itm->>'ordinal')::int, 1);
    _role     := itm->>'role';
    _tags     := ARRAY(SELECT jsonb_array_elements_text(COALESCE(itm->'tags','[]'::jsonb)));
    _variants := COALESCE(itm->'variants','[]'::jsonb);
    _meta     := COALESCE(itm->'meta','{}'::jsonb);

    -- upsert asset
    INSERT INTO media_asset(provider, url, media_type, meta)
    VALUES (_provider, _url, COALESCE(itm->>'media_type','image'), _meta)
    ON CONFLICT (provider, url) DO UPDATE
      SET meta = COALESCE(media_asset.meta, '{}'::jsonb) || EXCLUDED.meta,
          updated_at = now()
    RETURNING asset_id INTO _asset_id;

    -- link to product with order/role
    INSERT INTO product_media(product_id, asset_id, ordinal, role, tags, variants, source_meta)
    VALUES (p_product_id, _asset_id, _ordinal, _role, _tags, _variants, _meta)
    ON CONFLICT (product_id, asset_id) DO UPDATE
      SET ordinal = EXCLUDED.ordinal,
          role    = EXCLUDED.role,
          tags    = EXCLUDED.tags,
          variants= EXCLUDED.variants,
          source_meta = EXCLUDED.source_meta,
          updated_at = now();
  END LOOP;

  -- delete vanished links
  DELETE FROM product_media pm
  USING media_asset ma
  WHERE pm.product_id = p_product_id
    AND ma.asset_id = pm.asset_id
    AND ma.url NOT IN (SELECT unnest(present_urls));

  PERFORM log_product_change(p_product_id, 'media', NULL);
END$$;

-- ---------- 15) Materialized view refresh helper ----------

CREATE OR REPLACE FUNCTION refresh_product_card_mv()
RETURNS void LANGUAGE sql AS $$
  REFRESH MATERIALIZED VIEW CONCURRENTLY product_card_mv;
$$;

-- ---------- 16) Summary ----------

DO $$
BEGIN
  RAISE NOTICE '✅ ATDW V2 Schema (FIXED) deployed successfully';
  RAISE NOTICE '';
  RAISE NOTICE 'P0 Critical Fixes Applied:';
  RAISE NOTICE '  ✓ Geography type for accurate distance queries';
  RAISE NOTICE '  ✓ Fixed enforce_attribute_type() trigger logic';
  RAISE NOTICE '  ✓ Added missing FK indexes (product_attribute, rates, deals)';
  RAISE NOTICE '  ✓ Added unique index for CONCURRENT MV refresh';
  RAISE NOTICE '';
  RAISE NOTICE 'P1 Performance Fixes Applied:';
  RAISE NOTICE '  ✓ Fixed hot attribute projection to clear stale values';
  RAISE NOTICE '  ✓ Added index on product_attribute(attribute_id)';
  RAISE NOTICE '  ✓ Changed EAV constraint to exactly one value (= 1)';
  RAISE NOTICE '  ✓ Added auto-hash computation trigger';
  RAISE NOTICE '  ✓ Added JSONB GIN indexes for fast queries';
  RAISE NOTICE '  ✓ Added composite indexes for common patterns';
  RAISE NOTICE '';
  RAISE NOTICE 'Optimized for:';
  RAISE NOTICE '  • Delta updates with hash-based change detection';
  RAISE NOTICE '  • Idempotent upserts with ON CONFLICT handling';
  RAISE NOTICE '  • High-performance caching and sync operations';
  RAISE NOTICE '';
  RAISE NOTICE 'Next steps:';
  RAISE NOTICE '  1. Populate attribute_def table with ATDW attributes';
  RAISE NOTICE '  2. Load test dataset (VIC state)';
  RAISE NOTICE '  3. Validate query performance';
  RAISE NOTICE '  4. Set up daily delta update cron job';
END$$;

COMMIT;
