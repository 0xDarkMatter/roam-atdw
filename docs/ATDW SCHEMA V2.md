-- ============================================================

-- ATDW / Tourism Catalog - Core Schema Migration

-- ============================================================



BEGIN;



-- ---------- 0) Extensions ----------

CREATE EXTENSION IF NOT EXISTS postgis;

CREATE EXTENSION IF NOT EXISTS pg\_trgm;

CREATE EXTENSION IF NOT EXISTS pgcrypto;   -- sha256 via digest()



-- ---------- 1) Utility: timestamp maintenance ----------

CREATE OR REPLACE FUNCTION set\_updated\_at()

RETURNS trigger LANGUAGE plpgsql AS $$

BEGIN

&nbsp; NEW.updated\_at := now();

&nbsp; RETURN NEW;

END$$;



-- ---------- 2) Core: products \& suppliers (optional) ----------

CREATE TABLE IF NOT EXISTS supplier (

&nbsp; supplier\_id   BIGSERIAL PRIMARY KEY,

&nbsp; name          TEXT NOT NULL,

&nbsp; source        TEXT NOT NULL DEFAULT 'ATDW',

&nbsp; external\_id   TEXT NOT NULL,

&nbsp; meta          JSONB NOT NULL DEFAULT '{}',

&nbsp; created\_at    TIMESTAMPTZ NOT NULL DEFAULT now(),

&nbsp; updated\_at    TIMESTAMPTZ NOT NULL DEFAULT now(),

&nbsp; UNIQUE (source, external\_id)

);



CREATE TABLE IF NOT EXISTS products (

&nbsp; product\_id      BIGSERIAL PRIMARY KEY,

&nbsp; supplier\_id     BIGINT REFERENCES supplier(supplier\_id),

&nbsp; source          TEXT NOT NULL DEFAULT 'ATDW',

&nbsp; external\_id     TEXT NOT NULL,                  -- upstream id

&nbsp; is\_active       BOOLEAN NOT NULL DEFAULT TRUE,



&nbsp; product\_name    TEXT NOT NULL,

&nbsp; category        TEXT,                           -- ACCOMM/ATTRACTION/EVENT/...

&nbsp; classification  TEXT,                           -- HOTEL/RESORT/...



&nbsp; state           TEXT,

&nbsp; region          TEXT,

&nbsp; city            TEXT,



&nbsp; latitude        DOUBLE PRECISION,

&nbsp; longitude       DOUBLE PRECISION,

&nbsp; geom            geometry(Point,4326),           -- populated when lat/lon set



&nbsp; raw\_source      JSONB NOT NULL DEFAULT '{}',    -- upstream payload for audit

&nbsp; content\_sha256  TEXT,                           -- stable hash of product projection

&nbsp; media\_sha256    TEXT,

&nbsp; attrs\_sha256    TEXT,



&nbsp; -- Common "hot" projections populated by triggers (see §7)

&nbsp; has\_wifi        BOOLEAN,

&nbsp; has\_parking     BOOLEAN,

&nbsp; star\_rating     NUMERIC(2,1),



&nbsp; created\_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

&nbsp; updated\_at      TIMESTAMPTZ NOT NULL DEFAULT now(),



&nbsp; CONSTRAINT products\_source\_ext\_ux UNIQUE (source, external\_id)

);



CREATE TRIGGER products\_set\_updated\_at

BEFORE UPDATE ON products

FOR EACH ROW EXECUTE FUNCTION set\_updated\_at();



-- keep geom in sync when lat/lon change

CREATE OR REPLACE FUNCTION set\_product\_geom()

RETURNS trigger LANGUAGE plpgsql AS $$

BEGIN

&nbsp; IF NEW.longitude IS NOT NULL AND NEW.latitude IS NOT NULL THEN

&nbsp;   NEW.geom := ST\_SetSRID(ST\_MakePoint(NEW.longitude, NEW.latitude), 4326);

&nbsp; ELSE

&nbsp;   NEW.geom := NULL;

&nbsp; END IF;

&nbsp; RETURN NEW;

END$$;



CREATE TRIGGER products\_set\_geom

BEFORE INSERT OR UPDATE OF longitude, latitude ON products

FOR EACH ROW EXECUTE FUNCTION set\_product\_geom();



-- ---------- 3) Addresses ----------

CREATE TABLE IF NOT EXISTS addresses (

&nbsp; address\_id   BIGSERIAL PRIMARY KEY,

&nbsp; product\_id   BIGINT NOT NULL REFERENCES products(product\_id) ON DELETE CASCADE,

&nbsp; kind         TEXT NOT NULL DEFAULT 'physical',    -- physical/postal

&nbsp; line1        TEXT, line2 TEXT, line3 TEXT,

&nbsp; city         TEXT, state TEXT, postcode TEXT, country TEXT,

&nbsp; latitude     DOUBLE PRECISION, longitude DOUBLE PRECISION,

&nbsp; geom         geometry(Point,4326),

&nbsp; created\_at   TIMESTAMPTZ NOT NULL DEFAULT now(),

&nbsp; updated\_at   TIMESTAMPTZ NOT NULL DEFAULT now()

);



CREATE TRIGGER addresses\_set\_updated\_at

BEFORE UPDATE ON addresses

FOR EACH ROW EXECUTE FUNCTION set\_updated\_at();



CREATE OR REPLACE FUNCTION set\_address\_geom()

RETURNS trigger LANGUAGE plpgsql AS $$

BEGIN

&nbsp; IF NEW.longitude IS NOT NULL AND NEW.latitude IS NOT NULL THEN

&nbsp;   NEW.geom := ST\_SetSRID(ST\_MakePoint(NEW.longitude, NEW.latitude), 4326);

&nbsp; ELSE

&nbsp;   NEW.geom := NULL;

&nbsp; END IF;

&nbsp; RETURN NEW;

END$$;



CREATE TRIGGER addresses\_set\_geom

BEFORE INSERT OR UPDATE OF longitude, latitude ON addresses

FOR EACH ROW EXECUTE FUNCTION set\_address\_geom();



-- ---------- 4) Communication ----------

CREATE TABLE IF NOT EXISTS communication (

&nbsp; comms\_id    BIGSERIAL PRIMARY KEY,

&nbsp; product\_id  BIGINT NOT NULL REFERENCES products(product\_id) ON DELETE CASCADE,

&nbsp; kind        TEXT NOT NULL,         -- phone/email/website/booking/instagram...

&nbsp; value       TEXT NOT NULL,

&nbsp; created\_at  TIMESTAMPTZ NOT NULL DEFAULT now(),

&nbsp; updated\_at  TIMESTAMPTZ NOT NULL DEFAULT now()

);



CREATE TRIGGER communication\_set\_updated\_at

BEFORE UPDATE ON communication

FOR EACH ROW EXECUTE FUNCTION set\_updated\_at();



-- ---------- 5) Services (rooms/tours/sessions) ----------

CREATE TABLE IF NOT EXISTS services (

&nbsp; service\_id    BIGSERIAL PRIMARY KEY,

&nbsp; product\_id    BIGINT NOT NULL REFERENCES products(product\_id) ON DELETE CASCADE,

&nbsp; name          TEXT NOT NULL,

&nbsp; service\_kind  TEXT,                 -- room/tour/session/...

&nbsp; occupancy\_adults    SMALLINT,

&nbsp; occupancy\_children  SMALLINT,

&nbsp; bed\_config    TEXT,

&nbsp; details       JSONB NOT NULL DEFAULT '{}',

&nbsp; created\_at    TIMESTAMPTZ NOT NULL DEFAULT now(),

&nbsp; updated\_at    TIMESTAMPTZ NOT NULL DEFAULT now()

);



CREATE TRIGGER services\_set\_updated\_at

BEFORE UPDATE ON services

FOR EACH ROW EXECUTE FUNCTION set\_updated\_at();



-- ---------- 6) Media (relational + dedup) ----------

CREATE TABLE IF NOT EXISTS media\_asset (

&nbsp; asset\_id     BIGSERIAL PRIMARY KEY,

&nbsp; provider     TEXT,               -- 'ATDW','S3','YouTube','Cloudflare'

&nbsp; url          TEXT NOT NULL,

&nbsp; media\_type   TEXT NOT NULL,      -- 'image','video'

&nbsp; mime\_type    TEXT,

&nbsp; width        INT, height INT, duration\_seconds INT,

&nbsp; bytes        BIGINT,

&nbsp; checksum     TEXT,               -- sha256 of binary or canonical URL

&nbsp; meta         JSONB NOT NULL DEFAULT '{}',

&nbsp; created\_at   TIMESTAMPTZ NOT NULL DEFAULT now(),

&nbsp; updated\_at   TIMESTAMPTZ NOT NULL DEFAULT now(),

&nbsp; UNIQUE (provider, url)

);



CREATE TRIGGER media\_asset\_set\_updated\_at

BEFORE UPDATE ON media\_asset

FOR EACH ROW EXECUTE FUNCTION set\_updated\_at();



CREATE TABLE IF NOT EXISTS product\_media (

&nbsp; product\_id   BIGINT NOT NULL REFERENCES products(product\_id) ON DELETE CASCADE,

&nbsp; asset\_id     BIGINT NOT NULL REFERENCES media\_asset(asset\_id) ON DELETE CASCADE,

&nbsp; ordinal      INT NOT NULL DEFAULT 1,     -- gallery order

&nbsp; role         TEXT,                       -- 'hero','gallery','floorplan','thumb'

&nbsp; tags         TEXT\[],

&nbsp; variants     JSONB NOT NULL DEFAULT '\[]',

&nbsp; source\_meta  JSONB NOT NULL DEFAULT '{}',

&nbsp; created\_at   TIMESTAMPTZ NOT NULL DEFAULT now(),

&nbsp; updated\_at   TIMESTAMPTZ NOT NULL DEFAULT now(),

&nbsp; PRIMARY KEY (product\_id, asset\_id)

);



CREATE TRIGGER product\_media\_set\_updated\_at

BEFORE UPDATE ON product\_media

FOR EACH ROW EXECUTE FUNCTION set\_updated\_at();



-- ---------- 7) Attributes: dictionary + typed EAV ----------

DO $$

BEGIN

&nbsp; IF NOT EXISTS (SELECT 1 FROM pg\_type WHERE typname = 'attr\_type') THEN

&nbsp;   CREATE TYPE attr\_type AS ENUM ('bool','int','numeric','text','date','json');

&nbsp; END IF;

END$$;



CREATE TABLE IF NOT EXISTS attribute\_def (

&nbsp; attribute\_id  SMALLSERIAL PRIMARY KEY,

&nbsp; code          TEXT UNIQUE NOT NULL,       -- 'wifi','parking','star\_rating',...

&nbsp; label         TEXT,

&nbsp; data\_type     attr\_type NOT NULL,

&nbsp; facet         BOOLEAN NOT NULL DEFAULT FALSE,

&nbsp; description   TEXT

);



CREATE TABLE IF NOT EXISTS product\_attribute (

&nbsp; product\_id    BIGINT NOT NULL REFERENCES products(product\_id) ON DELETE CASCADE,

&nbsp; attribute\_id  SMALLINT NOT NULL REFERENCES attribute\_def(attribute\_id),

&nbsp; val\_bool      BOOLEAN,

&nbsp; val\_int       BIGINT,

&nbsp; val\_num       NUMERIC(18,6),

&nbsp; val\_text      TEXT,

&nbsp; val\_date      DATE,

&nbsp; val\_json      JSONB,

&nbsp; source\_meta   JSONB NOT NULL DEFAULT '{}',

&nbsp; created\_at    TIMESTAMPTZ NOT NULL DEFAULT now(),

&nbsp; updated\_at    TIMESTAMPTZ NOT NULL DEFAULT now(),

&nbsp; PRIMARY KEY (product\_id, attribute\_id),

&nbsp; CONSTRAINT product\_attribute\_value\_one\_ck CHECK (

&nbsp;   (val\_bool IS NOT NULL)::int +

&nbsp;   (val\_int  IS NOT NULL)::int +

&nbsp;   (val\_num  IS NOT NULL)::int +

&nbsp;   (val\_text IS NOT NULL)::int +

&nbsp;   (val\_date IS NOT NULL)::int +

&nbsp;   (val\_json IS NOT NULL)::int <= 1

&nbsp; )

);



CREATE TRIGGER product\_attribute\_set\_updated\_at

BEFORE UPDATE ON product\_attribute

FOR EACH ROW EXECUTE FUNCTION set\_updated\_at();



-- Enforce EAV type correctness (attribute\_def.data\_type vs populated column)

CREATE OR REPLACE FUNCTION enforce\_attribute\_type()

RETURNS trigger LANGUAGE plpgsql AS $$

DECLARE dtype attr\_type;

BEGIN

&nbsp; SELECT data\_type INTO dtype FROM attribute\_def WHERE attribute\_id = NEW.attribute\_id;

&nbsp; IF dtype IS NULL THEN

&nbsp;   RAISE EXCEPTION 'Unknown attribute\_id %', NEW.attribute\_id;

&nbsp; END IF;



&nbsp; IF (dtype='bool'    AND NEW.val\_bool  IS NULL) AND

&nbsp;    (dtype='int'     AND NEW.val\_int   IS NULL) AND

&nbsp;    (dtype='numeric' AND NEW.val\_num   IS NULL) AND

&nbsp;    (dtype='text'    AND NEW.val\_text  IS NULL) AND

&nbsp;    (dtype='date'    AND NEW.val\_date  IS NULL) AND

&nbsp;    (dtype='json'    AND NEW.val\_json  IS NULL) THEN

&nbsp;   RAISE EXCEPTION 'Attribute % expects % value', NEW.attribute\_id, dtype;

&nbsp; END IF;

&nbsp; RETURN NEW;

END$$;



CREATE TRIGGER product\_attribute\_type\_chk

BEFORE INSERT OR UPDATE ON product\_attribute

FOR EACH ROW EXECUTE FUNCTION enforce\_attribute\_type();



-- "Hot" attribute projections maintenance on products (has\_wifi, has\_parking, star\_rating)

CREATE OR REPLACE FUNCTION update\_product\_hot\_attrs(p\_product\_id BIGINT)

RETURNS void LANGUAGE plpgsql AS $$

DECLARE

&nbsp; \_wifi\_id SMALLINT;

&nbsp; \_park\_id SMALLINT;

&nbsp; \_star\_id SMALLINT;

&nbsp; \_has\_wifi BOOLEAN;

&nbsp; \_has\_parking BOOLEAN;

&nbsp; \_star NUMERIC(2,1);

BEGIN

&nbsp; SELECT attribute\_id INTO \_wifi\_id FROM attribute\_def WHERE code='wifi';

&nbsp; SELECT attribute\_id INTO \_park\_id FROM attribute\_def WHERE code='parking';

&nbsp; SELECT attribute\_id INTO \_star\_id FROM attribute\_def WHERE code='star\_rating';



&nbsp; IF \_wifi\_id IS NOT NULL THEN

&nbsp;   SELECT val\_bool INTO \_has\_wifi

&nbsp;   FROM product\_attribute WHERE product\_id=p\_product\_id AND attribute\_id=\_wifi\_id;

&nbsp; END IF;



&nbsp; IF \_park\_id IS NOT NULL THEN

&nbsp;   SELECT val\_bool INTO \_has\_parking

&nbsp;   FROM product\_attribute WHERE product\_id=p\_product\_id AND attribute\_id=\_park\_id;

&nbsp; END IF;



&nbsp; IF \_star\_id IS NOT NULL THEN

&nbsp;   SELECT val\_num::NUMERIC(2,1) INTO \_star

&nbsp;   FROM product\_attribute WHERE product\_id=p\_product\_id AND attribute\_id=\_star\_id;

&nbsp; END IF;



&nbsp; UPDATE products

&nbsp; SET has\_wifi   = COALESCE(\_has\_wifi, has\_wifi),

&nbsp;     has\_parking= COALESCE(\_has\_parking, has\_parking),

&nbsp;     star\_rating= COALESCE(\_star, star\_rating),

&nbsp;     updated\_at = now()

&nbsp; WHERE product\_id = p\_product\_id;

END$$;



-- Fire projection updates when attributes change (and when product row is inserted)

CREATE OR REPLACE FUNCTION touch\_hot\_attrs()

RETURNS trigger LANGUAGE plpgsql AS $$

BEGIN

&nbsp; PERFORM update\_product\_hot\_attrs(NEW.product\_id);

&nbsp; RETURN NEW;

END$$;



CREATE TRIGGER product\_attribute\_hot\_projection\_ins

AFTER INSERT ON product\_attribute

FOR EACH ROW EXECUTE FUNCTION touch\_hot\_attrs();



CREATE TRIGGER product\_attribute\_hot\_projection\_upd

AFTER UPDATE ON product\_attribute

FOR EACH ROW EXECUTE FUNCTION touch\_hot\_attrs();



CREATE TRIGGER product\_attribute\_hot\_projection\_del

AFTER DELETE ON product\_attribute

FOR EACH ROW EXECUTE FUNCTION update\_product\_hot\_attrs(OLD.product\_id);



-- ---------- 8) Rates / Deals ----------

CREATE TABLE IF NOT EXISTS rates (

&nbsp; rate\_id      BIGSERIAL PRIMARY KEY,

&nbsp; product\_id   BIGINT NOT NULL REFERENCES products(product\_id) ON DELETE CASCADE,

&nbsp; service\_id   BIGINT REFERENCES services(service\_id) ON DELETE CASCADE,

&nbsp; price\_cents  INTEGER NOT NULL,

&nbsp; currency     TEXT NOT NULL DEFAULT 'AUD',

&nbsp; start\_date   DATE NOT NULL,

&nbsp; end\_date     DATE NOT NULL,

&nbsp; constraints\_json JSONB NOT NULL DEFAULT '{}',

&nbsp; created\_at   TIMESTAMPTZ NOT NULL DEFAULT now(),

&nbsp; updated\_at   TIMESTAMPTZ NOT NULL DEFAULT now()

);

CREATE TRIGGER rates\_set\_updated\_at

BEFORE UPDATE ON rates

FOR EACH ROW EXECUTE FUNCTION set\_updated\_at();



CREATE TABLE IF NOT EXISTS deals (

&nbsp; deal\_id      BIGSERIAL PRIMARY KEY,

&nbsp; product\_id   BIGINT NOT NULL REFERENCES products(product\_id) ON DELETE CASCADE,

&nbsp; service\_id   BIGINT REFERENCES services(service\_id) ON DELETE CASCADE,

&nbsp; title        TEXT,

&nbsp; price\_cents  INTEGER,

&nbsp; currency     TEXT NOT NULL DEFAULT 'AUD',

&nbsp; start\_date   DATE NOT NULL,

&nbsp; end\_date     DATE NOT NULL,

&nbsp; constraints\_json JSONB NOT NULL DEFAULT '{}',

&nbsp; created\_at   TIMESTAMPTZ NOT NULL DEFAULT now(),

&nbsp; updated\_at   TIMESTAMPTZ NOT NULL DEFAULT now()

);

CREATE TRIGGER deals\_set\_updated\_at

BEFORE UPDATE ON deals

FOR EACH ROW EXECUTE FUNCTION set\_updated\_at();



-- ---------- 9) External systems ----------

CREATE TABLE IF NOT EXISTS external\_systems (

&nbsp; ext\_id      BIGSERIAL PRIMARY KEY,

&nbsp; product\_id  BIGINT NOT NULL REFERENCES products(product\_id) ON DELETE CASCADE,

&nbsp; system\_code TEXT NOT NULL,           -- 'TRIPADVISOR','INSTAGRAM','BOOKING','X'

&nbsp; external\_ref TEXT NOT NULL,

&nbsp; meta        JSONB NOT NULL DEFAULT '{}',

&nbsp; created\_at  TIMESTAMPTZ NOT NULL DEFAULT now(),

&nbsp; updated\_at  TIMESTAMPTZ NOT NULL DEFAULT now()

);

CREATE UNIQUE INDEX IF NOT EXISTS ext\_unique ON external\_systems(product\_id, system\_code);

CREATE TRIGGER external\_systems\_set\_updated\_at

BEFORE UPDATE ON external\_systems

FOR EACH ROW EXECUTE FUNCTION set\_updated\_at();



-- ---------- 10) Text search ----------

ALTER TABLE products

&nbsp; ADD COLUMN IF NOT EXISTS name\_tsv tsvector GENERATED ALWAYS AS (

&nbsp;   to\_tsvector('english', coalesce(product\_name,''))

&nbsp; ) STORED;



-- ---------- 11) Change log for cache invalidation ----------

CREATE TABLE IF NOT EXISTS change\_log (

&nbsp; change\_id    BIGSERIAL PRIMARY KEY,

&nbsp; product\_id   BIGINT NOT NULL,

&nbsp; change\_kind  TEXT NOT NULL,      -- 'product','media','attrs','services','rates','deals'

&nbsp; payload\_hash TEXT,

&nbsp; changed\_at   TIMESTAMPTZ NOT NULL DEFAULT now()

);



-- Helper to log a change

CREATE OR REPLACE FUNCTION log\_product\_change(p\_product\_id BIGINT, p\_kind TEXT, p\_hash TEXT)

RETURNS void LANGUAGE plpgsql AS $$

BEGIN

&nbsp; INSERT INTO change\_log(product\_id, change\_kind, payload\_hash) VALUES (p\_product\_id, p\_kind, p\_hash);

&nbsp; PERFORM pg\_notify('product\_changed', p\_product\_id::text || ':' || p\_kind);

END$$;



-- ---------- 12) Indexes ----------

-- Products

CREATE INDEX IF NOT EXISTS products\_active\_idx      ON products(is\_active);

CREATE INDEX IF NOT EXISTS products\_cat\_state\_idx   ON products(category, state);

CREATE INDEX IF NOT EXISTS products\_updated\_desc    ON products(updated\_at DESC);

CREATE INDEX IF NOT EXISTS products\_geom\_gix        ON products USING GIST (geom);

CREATE INDEX IF NOT EXISTS products\_name\_tsv\_gin    ON products USING GIN (name\_tsv);

CREATE INDEX IF NOT EXISTS products\_name\_trgm       ON products USING GIN (product\_name gin\_trgm\_ops);



-- Addresses

CREATE INDEX IF NOT EXISTS addresses\_prod\_idx       ON addresses(product\_id);

CREATE INDEX IF NOT EXISTS addresses\_geom\_gix       ON addresses USING GIST (geom);



-- Communication

CREATE INDEX IF NOT EXISTS communication\_prod\_idx   ON communication(product\_id);

CREATE INDEX IF NOT EXISTS communication\_kind\_idx   ON communication(kind);



-- Services

CREATE INDEX IF NOT EXISTS services\_prod\_idx        ON services(product\_id);



-- Media

CREATE INDEX IF NOT EXISTS product\_media\_ord\_idx    ON product\_media(product\_id, ordinal);

CREATE INDEX IF NOT EXISTS product\_media\_role\_idx   ON product\_media(role);



-- Attributes (selective partial indexes: create only if you actually filter on them)

-- Example: wifi, parking, star\_rating (adjust to your needs)

DO $$

DECLARE wifi\_id SMALLINT; park\_id SMALLINT; star\_id SMALLINT;

BEGIN

&nbsp; SELECT attribute\_id INTO wifi\_id FROM attribute\_def WHERE code='wifi';

&nbsp; IF wifi\_id IS NOT NULL THEN

&nbsp;   EXECUTE format('CREATE INDEX IF NOT EXISTS pa\_wifi\_true\_idx ON product\_attribute (product\_id)

&nbsp;                   WHERE attribute\_id=%s AND val\_bool IS TRUE', wifi\_id);

&nbsp; END IF;



&nbsp; SELECT attribute\_id INTO park\_id FROM attribute\_def WHERE code='parking';

&nbsp; IF park\_id IS NOT NULL THEN

&nbsp;   EXECUTE format('CREATE INDEX IF NOT EXISTS pa\_parking\_true\_idx ON product\_attribute (product\_id)

&nbsp;                   WHERE attribute\_id=%s AND val\_bool IS TRUE', park\_id);

&nbsp; END IF;



&nbsp; SELECT attribute\_id INTO star\_id FROM attribute\_def WHERE code='star\_rating';

&nbsp; IF star\_id IS NOT NULL THEN

&nbsp;   EXECUTE format('CREATE INDEX IF NOT EXISTS pa\_star\_idx ON product\_attribute (val\_num)

&nbsp;                   WHERE attribute\_id=%s', star\_id);

&nbsp; END IF;

END$$;



-- ---------- 13) Materialized "card" view (optional) ----------

-- Single hero image, a few hot facets for catalog cards

DROP MATERIALIZED VIEW IF EXISTS product\_card\_mv;

CREATE MATERIALIZED VIEW product\_card\_mv AS

SELECT

&nbsp; p.product\_id,

&nbsp; p.product\_name,

&nbsp; p.category,

&nbsp; p.state,

&nbsp; p.region,

&nbsp; p.city,

&nbsp; p.geom,

&nbsp; p.has\_wifi,

&nbsp; p.has\_parking,

&nbsp; p.star\_rating,

&nbsp; pm.asset\_id AS hero\_asset\_id

FROM products p

LEFT JOIN LATERAL (

&nbsp; SELECT asset\_id

&nbsp; FROM product\_media

&nbsp; WHERE product\_id = p.product\_id AND (role = 'hero' OR role IS NULL)

&nbsp; ORDER BY ordinal

&nbsp; LIMIT 1

) pm ON true

WHERE p.is\_active;



CREATE INDEX product\_card\_mv\_cat\_state\_idx ON product\_card\_mv(category, state);

CREATE INDEX product\_card\_mv\_star\_idx      ON product\_card\_mv(star\_rating DESC);

CREATE INDEX product\_card\_mv\_geom\_gix      ON product\_card\_mv USING GIST (geom);



-- ---------- 14) Upsert helpers (set-wise, idempotent) ----------

-- 14.1 Upsert product (content hash is supplied by ETL as sha256 of a stable JSON projection)

CREATE OR REPLACE FUNCTION upsert\_product(

&nbsp; p\_source TEXT, p\_external\_id TEXT,

&nbsp; p\_supplier\_id BIGINT,

&nbsp; p\_is\_active BOOLEAN,

&nbsp; p\_name TEXT, p\_category TEXT, p\_classification TEXT,

&nbsp; p\_state TEXT, p\_region TEXT, p\_city TEXT,

&nbsp; p\_lat DOUBLE PRECISION, p\_lon DOUBLE PRECISION,

&nbsp; p\_raw\_source JSONB, p\_content\_sha256 TEXT,

&nbsp; p\_media\_sha256 TEXT, p\_attrs\_sha256 TEXT

) RETURNS BIGINT LANGUAGE plpgsql AS $$

DECLARE pid BIGINT;

BEGIN

&nbsp; INSERT INTO products AS x (

&nbsp;   supplier\_id, source, external\_id, is\_active,

&nbsp;   product\_name, category, classification,

&nbsp;   state, region, city,

&nbsp;   latitude, longitude, raw\_source,

&nbsp;   content\_sha256, media\_sha256, attrs\_sha256

&nbsp; )

&nbsp; VALUES (

&nbsp;   p\_supplier\_id, p\_source, p\_external\_id, COALESCE(p\_is\_active, TRUE),

&nbsp;   p\_name, p\_category, p\_classification,

&nbsp;   p\_state, p\_region, p\_city,

&nbsp;   p\_lat, p\_lon, COALESCE(p\_raw\_source,'{}'::jsonb),

&nbsp;   p\_content\_sha256, p\_media\_sha256, p\_attrs\_sha256

&nbsp; )

&nbsp; ON CONFLICT (source, external\_id) DO UPDATE

&nbsp; SET is\_active      = EXCLUDED.is\_active,

&nbsp;     product\_name   = EXCLUDED.product\_name,

&nbsp;     category       = EXCLUDED.category,

&nbsp;     classification = EXCLUDED.classification,

&nbsp;     state          = EXCLUDED.state,

&nbsp;     region         = EXCLUDED.region,

&nbsp;     city           = EXCLUDED.city,

&nbsp;     latitude       = EXCLUDED.latitude,

&nbsp;     longitude      = EXCLUDED.longitude,

&nbsp;     raw\_source     = EXCLUDED.raw\_source,

&nbsp;     content\_sha256 = EXCLUDED.content\_sha256,

&nbsp;     media\_sha256   = EXCLUDED.media\_sha256,

&nbsp;     attrs\_sha256   = EXCLUDED.attrs\_sha256,

&nbsp;     updated\_at     = now()

&nbsp; RETURNING product\_id INTO pid;



&nbsp; PERFORM log\_product\_change(pid, 'product', p\_content\_sha256);

&nbsp; RETURN pid;

END$$;



-- 14.2 Upsert attributes (delta: insert/update keys present; delete vanished)

-- Pass a jsonb object of {attribute\_code: typed\_value}

CREATE OR REPLACE FUNCTION upsert\_product\_attributes(p\_product\_id BIGINT, p\_attrs JSONB)

RETURNS void LANGUAGE plpgsql AS $$

DECLARE

&nbsp; kv RECORD;

&nbsp; def RECORD;

&nbsp; v\_bool BOOLEAN; v\_int BIGINT; v\_num NUMERIC; v\_text TEXT; v\_date DATE; v\_json JSONB;

&nbsp; present\_codes TEXT\[];

BEGIN

&nbsp; IF p\_attrs IS NULL THEN RETURN; END IF;



&nbsp; -- track which codes we saw (for deletion of vanished)

&nbsp; present\_codes := ARRAY(SELECT key FROM jsonb\_each(p\_attrs));



&nbsp; FOR kv IN SELECT \* FROM jsonb\_each(p\_attrs) LOOP

&nbsp;   SELECT \* INTO def FROM attribute\_def WHERE code = kv.key;

&nbsp;   IF NOT FOUND THEN

&nbsp;     RAISE EXCEPTION 'Unknown attribute code %, add to attribute\_def first', kv.key;

&nbsp;   END IF;



&nbsp;   v\_bool := NULL; v\_int := NULL; v\_num := NULL; v\_text := NULL; v\_date := NULL; v\_json := NULL;

&nbsp;   CASE def.data\_type

&nbsp;     WHEN 'bool'    THEN v\_bool := (kv.value)::boolean;

&nbsp;     WHEN 'int'     THEN v\_int  := (kv.value)::bigint;

&nbsp;     WHEN 'numeric' THEN v\_num  := (kv.value)::numeric;

&nbsp;     WHEN 'text'    THEN v\_text := (kv.value)::text;

&nbsp;     WHEN 'date'    THEN v\_date := (kv.value)::date;

&nbsp;     WHEN 'json'    THEN v\_json := (kv.value)::jsonb;

&nbsp;     ELSE RAISE EXCEPTION 'Unhandled data\_type %', def.data\_type;

&nbsp;   END CASE;



&nbsp;   INSERT INTO product\_attribute(product\_id, attribute\_id, val\_bool, val\_int, val\_num, val\_text, val\_date, val\_json)

&nbsp;   VALUES (p\_product\_id, def.attribute\_id, v\_bool, v\_int, v\_num, v\_text, v\_date, v\_json)

&nbsp;   ON CONFLICT (product\_id, attribute\_id) DO UPDATE

&nbsp;   SET val\_bool = COALESCE(EXCLUDED.val\_bool, product\_attribute.val\_bool),

&nbsp;       val\_int  = COALESCE(EXCLUDED.val\_int,  product\_attribute.val\_int),

&nbsp;       val\_num  = COALESCE(EXCLUDED.val\_num,  product\_attribute.val\_num),

&nbsp;       val\_text = COALESCE(EXCLUDED.val\_text, product\_attribute.val\_text),

&nbsp;       val\_date = COALESCE(EXCLUDED.val\_date, product\_attribute.val\_date),

&nbsp;       val\_json = COALESCE(EXCLUDED.val\_json, product\_attribute.val\_json),

&nbsp;       updated\_at = now();

&nbsp; END LOOP;



&nbsp; -- delete vanished attributes (present before, absent now)

&nbsp; DELETE FROM product\_attribute pa

&nbsp; USING attribute\_def d

&nbsp; WHERE pa.product\_id = p\_product\_id

&nbsp;   AND d.attribute\_id = pa.attribute\_id

&nbsp;   AND d.code NOT IN (SELECT unnest(present\_codes));



&nbsp; PERFORM update\_product\_hot\_attrs(p\_product\_id);

&nbsp; PERFORM log\_product\_change(p\_product\_id, 'attrs', NULL);

END$$;



-- 14.3 Upsert media (delta by (provider,url))

-- p\_media: array of objects \[{provider,url,ordinal,role,tags,variants,meta}]

CREATE OR REPLACE FUNCTION upsert\_product\_media(p\_product\_id BIGINT, p\_media JSONB)

RETURNS void LANGUAGE plpgsql AS $$

DECLARE

&nbsp; itm JSONB;

&nbsp; \_provider TEXT; \_url TEXT; \_ordinal INT; \_role TEXT; \_tags TEXT\[]; \_variants JSONB; \_meta JSONB;

&nbsp; \_asset\_id BIGINT;

&nbsp; present\_urls TEXT\[];

BEGIN

&nbsp; IF p\_media IS NULL THEN RETURN; END IF;



&nbsp; present\_urls := ARRAY(SELECT (x->>'url') FROM jsonb\_array\_elements(p\_media) x);



&nbsp; FOR itm IN SELECT \* FROM jsonb\_array\_elements(p\_media) LOOP

&nbsp;   \_provider := COALESCE(itm->>'provider','ATDW');

&nbsp;   \_url      := itm->>'url';

&nbsp;   \_ordinal  := COALESCE((itm->>'ordinal')::int, 1);

&nbsp;   \_role     := itm->>'role';

&nbsp;   \_tags     := ARRAY(SELECT jsonb\_array\_elements\_text(COALESCE(itm->'tags','\[]'::jsonb)));

&nbsp;   \_variants := COALESCE(itm->'variants','\[]'::jsonb);

&nbsp;   \_meta     := COALESCE(itm->'meta','{}'::jsonb);



&nbsp;   -- upsert asset

&nbsp;   INSERT INTO media\_asset(provider, url, media\_type, meta)

&nbsp;   VALUES (\_provider, \_url, COALESCE(itm->>'media\_type','image'), \_meta)

&nbsp;   ON CONFLICT (provider, url) DO UPDATE

&nbsp;     SET meta = COALESCE(media\_asset.meta, '{}'::jsonb) || EXCLUDED.meta,

&nbsp;         updated\_at = now()

&nbsp;   RETURNING asset\_id INTO \_asset\_id;



&nbsp;   -- link to product with order/role

&nbsp;   INSERT INTO product\_media(product\_id, asset\_id, ordinal, role, tags, variants, source\_meta)

&nbsp;   VALUES (p\_product\_id, \_asset\_id, \_ordinal, \_role, \_tags, \_variants, \_meta)

&nbsp;   ON CONFLICT (product\_id, asset\_id) DO UPDATE

&nbsp;     SET ordinal = EXCLUDED.ordinal,

&nbsp;         role    = COALESCE(EXCLUDED.role, product\_media.role),

&nbsp;         tags    = COALESCE(EXCLUDED.tags, product\_media.tags),

&nbsp;         variants= COALESCE(EXCLUDED.variants, product\_media.variants),

&nbsp;         source\_meta = COALESCE(EXCLUDED.source\_meta, product\_media.source\_meta),

&nbsp;         updated\_at = now();

&nbsp; END LOOP;



&nbsp; -- delete vanished links

&nbsp; DELETE FROM product\_media pm

&nbsp; USING media\_asset ma

&nbsp; WHERE pm.product\_id = p\_product\_id

&nbsp;   AND ma.asset\_id = pm.asset\_id

&nbsp;   AND ma.url NOT IN (SELECT unnest(present\_urls));



&nbsp; PERFORM log\_product\_change(p\_product\_id, 'media', NULL);

END$$;



-- ---------- 15) Text search \& nearest-N examples (for your reference) ----------

-- name search (tsquery)

-- SELECT product\_id, product\_name FROM products WHERE name\_tsv @@ plainto\_tsquery('english',$1) LIMIT 50;

-- fuzzy / prefix

-- SELECT product\_id, product\_name FROM products WHERE product\_name ILIKE $1 || '%' OR similarity(product\_name,$1) > 0.4 ORDER BY greatest(similarity(product\_name,$1), 0)::float DESC LIMIT 50;

-- nearest-N

-- SELECT product\_id, product\_name FROM products ORDER BY geom <-> ST\_SetSRID(ST\_MakePoint($lon,$lat),4326) LIMIT 50;

-- radius (spheroid distance)

-- SELECT product\_id, product\_name FROM products WHERE ST\_DWithin(geom::geography, ST\_SetSRID(ST\_MakePoint($lon,$lat),4326)::geography, $meters);



-- ---------- 16) Materialized view refresh helper ----------

CREATE OR REPLACE FUNCTION refresh\_product\_card\_mv()

RETURNS void LANGUAGE sql AS $$

&nbsp; REFRESH MATERIALIZED VIEW CONCURRENTLY product\_card\_mv;

$$;



COMMIT;



