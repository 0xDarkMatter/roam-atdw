-- Migration 023: Add Remaining ATDW Data Tables
-- Ensures complete coverage of all ATDW product fields, even rare ones
-- Covers: awards, proximity landmarks, related products, and structured comments

BEGIN;

-- ============================================================================
-- 1. PRODUCT_AWARDS - Tourism awards and certifications
-- ============================================================================

CREATE TABLE IF NOT EXISTS product_awards (
    award_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,

    -- Award details
    award_name TEXT NOT NULL,
    award_type TEXT,                              -- e.g., "Industry Award", "Customer Choice"
    awarding_organization TEXT,                   -- e.g., "Australian Tourism Awards"

    -- Award specifics
    award_category TEXT,                          -- e.g., "Best Accommodation", "Excellence in Tourism"
    award_year INTEGER,                           -- Year awarded
    award_level TEXT,                             -- e.g., "Gold", "Silver", "Bronze", "Winner", "Finalist"

    -- Dates
    award_date DATE,                              -- When award was received
    valid_from DATE,                              -- Award validity period
    valid_to DATE,

    -- Additional info
    description TEXT,
    award_url TEXT,                               -- Link to award details
    certificate_url TEXT,                         -- Link to certificate/badge

    -- Metadata
    source_meta JSONB DEFAULT '{}'::jsonb,        -- Original ATDW data

    -- Audit
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT valid_award_year CHECK (award_year IS NULL OR (award_year >= 1900 AND award_year <= 2100))
);

CREATE INDEX idx_awards_product_id ON product_awards(product_id);
CREATE INDEX idx_awards_year ON product_awards(award_year) WHERE award_year IS NOT NULL;
CREATE INDEX idx_awards_organization ON product_awards(awarding_organization);

COMMENT ON TABLE product_awards IS 'Tourism awards, certifications, and industry recognition';
COMMENT ON COLUMN product_awards.award_level IS 'Award tier: Gold, Silver, Bronze, Winner, Finalist, etc.';

-- ============================================================================
-- 2. PRODUCT_PROXIMITY - Nearby landmarks and points of interest
-- ============================================================================

CREATE TABLE IF NOT EXISTS product_proximity (
    proximity_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,

    -- Nearby place details
    place_name TEXT NOT NULL,                     -- e.g., "Sydney Opera House"
    place_type TEXT,                              -- e.g., "landmark", "attraction", "transport", "beach"

    -- Distance
    distance_km NUMERIC(10,2),                    -- Distance in kilometers
    distance_text TEXT,                           -- Human-readable: "5 minutes walk", "10km drive"

    -- Direction
    direction TEXT,                               -- e.g., "north", "south-east"
    travel_mode TEXT,                             -- e.g., "walk", "drive", "public_transport"
    travel_time_minutes INTEGER,                  -- Estimated travel time

    -- Location (if available)
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,

    -- Additional info
    description TEXT,
    place_url TEXT,                               -- Link to place details

    -- Metadata
    source_meta JSONB DEFAULT '{}'::jsonb,

    -- Audit
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT valid_distance CHECK (distance_km IS NULL OR distance_km >= 0)
);

CREATE INDEX idx_proximity_product_id ON product_proximity(product_id);
CREATE INDEX idx_proximity_type ON product_proximity(place_type);
CREATE INDEX idx_proximity_distance ON product_proximity(distance_km) WHERE distance_km IS NOT NULL;

COMMENT ON TABLE product_proximity IS 'Nearby landmarks, attractions, and points of interest';
COMMENT ON COLUMN product_proximity.place_type IS 'Type: landmark, attraction, transport, beach, airport, etc.';

-- ============================================================================
-- 3. PRODUCT_RELATED - Related and recommended products
-- ============================================================================

CREATE TABLE IF NOT EXISTS product_related (
    relation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,
    related_product_id UUID NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,

    -- Relationship type
    relationship_type TEXT NOT NULL,              -- e.g., "similar", "nearby", "package", "recommended"
    relationship_strength SMALLINT DEFAULT 5,     -- 1-10 scale of relationship strength

    -- Bidirectional flag
    is_bidirectional BOOLEAN DEFAULT false,       -- If true, relationship works both ways

    -- Display order
    display_order INTEGER DEFAULT 0,              -- Order for displaying related products

    -- Description
    relationship_description TEXT,                -- Why these are related

    -- Metadata
    source TEXT DEFAULT 'ATDW',                   -- Source of relationship (ATDW, manual, algorithm)
    source_meta JSONB DEFAULT '{}'::jsonb,

    -- Audit
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT different_products CHECK (product_id != related_product_id),
    CONSTRAINT valid_strength CHECK (relationship_strength >= 1 AND relationship_strength <= 10)
);

CREATE INDEX idx_related_product_id ON product_related(product_id);
CREATE INDEX idx_related_related_id ON product_related(related_product_id);
CREATE INDEX idx_related_type ON product_related(relationship_type);
CREATE INDEX idx_related_strength ON product_related(relationship_strength DESC);

-- Unique constraint: prevent duplicate relationships
CREATE UNIQUE INDEX idx_related_unique ON product_related(
    LEAST(product_id, related_product_id),
    GREATEST(product_id, related_product_id),
    relationship_type
);

COMMENT ON TABLE product_related IS 'Relationships between related tourism products';
COMMENT ON COLUMN product_related.relationship_type IS 'Type: similar, nearby, package, recommended, combo';
COMMENT ON COLUMN product_related.relationship_strength IS 'Strength of relationship (1-10): 10=very strongly related';

-- ============================================================================
-- 4. PRODUCT_COMMENTS - Structured product comments and descriptions
-- ============================================================================

CREATE TABLE IF NOT EXISTS product_comments (
    comment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,

    -- Comment type and content
    comment_type TEXT NOT NULL,                   -- e.g., "description", "facilities", "activities", "history"
    comment_text TEXT NOT NULL,

    -- Language and localization
    language_code TEXT DEFAULT 'en',              -- ISO 639-1 code (en, fr, de, zh, etc.)
    market_variant TEXT,                          -- Market-specific variant

    -- Display
    sequence_number INTEGER DEFAULT 0,            -- Order for display
    is_primary BOOLEAN DEFAULT false,             -- Primary comment for this type

    -- Metadata
    authored_date DATE,                           -- When comment was written
    author TEXT,                                  -- Who wrote it (if available)

    source_meta JSONB DEFAULT '{}'::jsonb,

    -- Audit
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_comments_product_id ON product_comments(product_id);
CREATE INDEX idx_comments_type ON product_comments(comment_type);
CREATE INDEX idx_comments_language ON product_comments(language_code);
CREATE INDEX idx_comments_primary ON product_comments(product_id, is_primary) WHERE is_primary = true;

-- Full-text search on comments
CREATE INDEX idx_comments_text_search ON product_comments USING GIN(to_tsvector('english', comment_text));

COMMENT ON TABLE product_comments IS 'Structured product comments and descriptions (multilingual support)';
COMMENT ON COLUMN product_comments.comment_type IS 'Type: description, facilities, activities, history, directions, etc.';
COMMENT ON COLUMN product_comments.language_code IS 'ISO 639-1 language code (en, fr, de, zh, ja, etc.)';

-- ============================================================================
-- UPDATE TRIGGERS
-- ============================================================================

CREATE TRIGGER awards_set_updated_at
    BEFORE UPDATE ON product_awards
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER proximity_set_updated_at
    BEFORE UPDATE ON product_proximity
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER related_set_updated_at
    BEFORE UPDATE ON product_related
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER comments_set_updated_at
    BEFORE UPDATE ON product_comments
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Get all awards for a product
CREATE OR REPLACE FUNCTION get_product_awards(p_product_id UUID)
RETURNS TABLE (
    award_name TEXT,
    award_year INTEGER,
    award_level TEXT,
    awarding_organization TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        pa.award_name,
        pa.award_year,
        pa.award_level,
        pa.awarding_organization
    FROM product_awards pa
    WHERE pa.product_id = p_product_id
    ORDER BY pa.award_year DESC NULLS LAST, pa.award_name;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_product_awards IS 'Get all awards for a product, ordered by year (most recent first)';

-- Get nearby places
CREATE OR REPLACE FUNCTION get_nearby_places(
    p_product_id UUID,
    p_max_distance_km NUMERIC DEFAULT NULL
)
RETURNS TABLE (
    place_name TEXT,
    place_type TEXT,
    distance_km NUMERIC,
    distance_text TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        pp.place_name,
        pp.place_type,
        pp.distance_km,
        pp.distance_text
    FROM product_proximity pp
    WHERE pp.product_id = p_product_id
      AND (p_max_distance_km IS NULL OR pp.distance_km <= p_max_distance_km)
    ORDER BY pp.distance_km NULLS LAST;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_nearby_places IS 'Get nearby places for a product, optionally filtered by max distance';

-- Get related products
CREATE OR REPLACE FUNCTION get_related_products(
    p_product_id UUID,
    p_relationship_type TEXT DEFAULT NULL
)
RETURNS TABLE (
    related_product_id UUID,
    relationship_type TEXT,
    relationship_strength SMALLINT,
    product_name TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        pr.related_product_id,
        pr.relationship_type,
        pr.relationship_strength,
        p.product_name
    FROM product_related pr
    JOIN products p ON p.product_id = pr.related_product_id
    WHERE pr.product_id = p_product_id
      AND (p_relationship_type IS NULL OR pr.relationship_type = p_relationship_type)
    ORDER BY pr.relationship_strength DESC, pr.display_order, p.product_name;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_related_products IS 'Get related products, optionally filtered by relationship type';

COMMIT;
