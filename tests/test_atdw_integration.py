"""
Integration tests for ATDW database operations.
Tests full product loading workflows with actual database.

Phase 2: Tests require database connection to test schema.
"""

import pytest
import json
from uuid import uuid4
from datetime import datetime


# Mark all tests in this file as integration tests
pytestmark = pytest.mark.integration


class TestProductInsertion:
    """Test basic product insertion into database."""

    def test_insert_minimal_product(self, db_connection, test_schema):
        """
        Test: Insert a minimal product with only required fields.
        Purpose: Verify basic INSERT operation works.
        """
        conn, test_product_ids, _ = db_connection

        product_id = uuid4()
        test_product_ids.append(product_id)

        # Get a valid category_id from reference data
        with conn.cursor() as cur:
            cur.execute(f"""
                SELECT category_id FROM {test_schema}.product_categories LIMIT 1
            """)
            category_id = cur.fetchone()[0]

            cur.execute(f"""
                INSERT INTO {test_schema}.products (
                    product_id, source, atdw_id, is_active,
                    product_name, category_id, raw_source
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s
                )
            """, (
                product_id,
                'ATDW',
                'TEST-001',
                True,
                'Test Product',
                category_id,
                json.dumps({'test': 'data'})
            ))
        conn.commit()

        # Verify product was inserted
        with conn.cursor() as cur:
            cur.execute(f"""
                SELECT product_name, source, atdw_id
                FROM {test_schema}.products
                WHERE product_id = %s
            """, (product_id,))
            result = cur.fetchone()

        assert result is not None, "Product should be inserted"
        assert result[0] == 'Test Product'
        assert result[1] == 'ATDW'
        assert result[2] == 'TEST-001'

    def test_insert_product_with_location(self, db_connection, test_schema, sample_accommodation, default_category_id):
        """
        Test: Insert product with geographic data.
        Purpose: Verify latitude/longitude and PostGIS integration.
        """
        conn, test_product_ids, _ = db_connection

        product_id = uuid4()
        test_product_ids.append(product_id)

        # Extract coordinates from sample
        boundary = sample_accommodation.get('boundary', '-28.6450,153.6050')
        lat, lng = map(float, boundary.split(','))

        with conn.cursor() as cur:
            cur.execute(f"""
                INSERT INTO {test_schema}.products (
                    product_id, source, atdw_id, is_active,
                    product_name, state, city,
                    latitude, longitude, category_id, raw_source
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """, (
                product_id,
                'ATDW',
                sample_accommodation['productId'],
                True,
                sample_accommodation['productName'],
                'NSW',
                'Byron Bay',
                lat,
                lng,
                default_category_id,
                json.dumps(sample_accommodation)
            ))
        conn.commit()

        # Verify location data
        with conn.cursor() as cur:
            cur.execute(f"""
                SELECT state, city, latitude, longitude
                FROM {test_schema}.products
                WHERE product_id = %s
            """, (product_id,))
            result = cur.fetchone()

        assert result[0] == 'NSW'
        assert result[1] == 'Byron Bay'
        assert abs(result[2] - lat) < 0.0001, "Latitude should match"
        assert abs(result[3] - lng) < 0.0001, "Longitude should match"


class TestProductRelationships:
    """Test product relationship tables (addresses, contacts, media, etc.)."""

    def test_insert_product_with_address(self, db_connection, test_schema, default_category_id):
        """
        Test: Insert product with address.
        Purpose: Verify one-to-many relationship (product → addresses).
        """
        conn, test_product_ids, _ = db_connection

        # Insert product
        product_id = uuid4()
        test_product_ids.append(product_id)

        with conn.cursor() as cur:
            cur.execute(f"""
                INSERT INTO {test_schema}.products (
                    product_id, source, atdw_id, is_active,
                    product_name, category_id, raw_source
                ) VALUES (%s, 'ATDW', 'TEST-ADDR-001', true, 'Test Product', %s, '{{}}'::jsonb)
            """, (product_id, default_category_id))

            # Insert address (provide address_id explicitly to avoid uuid_generate_v7)
            address_id = uuid4()
            cur.execute(f"""
                INSERT INTO {test_schema}.product_addresses (
                    address_id, product_id, kind, line1,
                    city, state, postcode
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                address_id,
                product_id,
                'PHYSICAL',
                '123 Test Street',
                'Byron Bay',
                'NSW',
                '2481'
            ))
        conn.commit()

        # Verify address
        with conn.cursor() as cur:
            cur.execute(f"""
                SELECT line1, city, state, postcode
                FROM {test_schema}.product_addresses
                WHERE product_id = %s
            """, (product_id,))
            result = cur.fetchone()

        assert result is not None, "Address should exist"
        assert result[0] == '123 Test Street'
        assert result[1] == 'Byron Bay'
        assert result[2] == 'NSW'
        assert result[3] == '2481'

    def test_insert_product_with_contacts(self, db_connection, test_schema, default_category_id):
        """
        Test: Insert product with multiple contact methods.
        Purpose: Verify product can have phone, email, website.
        """
        conn, test_product_ids, _ = db_connection

        product_id = uuid4()
        test_product_ids.append(product_id)

        with conn.cursor() as cur:
            cur.execute(f"""
                INSERT INTO {test_schema}.products (
                    product_id, source, atdw_id, is_active,
                    product_name, category_id, raw_source
                ) VALUES (%s, 'ATDW', 'TEST-CONTACT-001', true, 'Test Product', %s, '{{}}'::jsonb)
            """, (product_id, default_category_id))

            # Insert contacts (each contact type is a separate row, provide IDs explicitly)
            comms_id_1 = uuid4()
            comms_id_2 = uuid4()
            comms_id_3 = uuid4()

            cur.execute(f"""
                INSERT INTO {test_schema}.product_contacts (
                    comms_id, product_id, kind, value
                ) VALUES
                    (%s, %s, %s, %s),
                    (%s, %s, %s, %s),
                    (%s, %s, %s, %s)
            """, (
                comms_id_1, product_id, 'PHONE', '+61266857777',
                comms_id_2, product_id, 'EMAIL', 'info@test.com.au',
                comms_id_3, product_id, 'WEBSITE', 'https://www.test.com.au'
            ))
        conn.commit()

        # Verify contacts
        with conn.cursor() as cur:
            cur.execute(f"""
                SELECT kind, value
                FROM {test_schema}.product_contacts
                WHERE product_id = %s
                ORDER BY kind
            """, (product_id,))
            results = cur.fetchall()

        assert len(results) == 3, "Should have 3 contact methods"
        # Results ordered by kind: EMAIL, PHONE, WEBSITE
        assert results[0] == ('EMAIL', 'info@test.com.au')
        assert results[1] == ('PHONE', '+61266857777')
        assert results[2] == ('WEBSITE', 'https://www.test.com.au')

    def test_insert_product_with_media(self, db_connection, test_schema, default_category_id):
        """
        Test: Insert product with media items.
        Purpose: Verify product can have multiple images/videos.
        """
        conn, test_product_ids, _ = db_connection

        product_id = uuid4()
        test_product_ids.append(product_id)

        with conn.cursor() as cur:
            cur.execute(f"""
                INSERT INTO {test_schema}.products (
                    product_id, source, atdw_id, is_active,
                    product_name, category_id, raw_source
                ) VALUES (%s, 'ATDW', 'TEST-MEDIA-001', true, 'Test Product', %s, '{{}}'::jsonb)
            """, (product_id, default_category_id))

            # First create media assets, then link them
            # For testing, we'll create simple media entries with asset references
            import uuid

            asset_id_1 = uuid.uuid4()
            asset_id_2 = uuid.uuid4()

            # Insert into media_assets table
            cur.execute(f"""
                INSERT INTO {test_schema}.media_assets (
                    asset_id, url, media_type
                ) VALUES
                    (%s, %s, %s),
                    (%s, %s, %s)
            """, (
                asset_id_1, 'https://cdn.test.com/image1.jpg', 'Image',
                asset_id_2, 'https://cdn.test.com/image2.jpg', 'Image'
            ))

            # Insert media items
            cur.execute(f"""
                INSERT INTO {test_schema}.product_media (
                    product_id, asset_id, ordinal, role
                ) VALUES
                    (%s, %s, %s, %s),
                    (%s, %s, %s, %s)
            """, (
                product_id, asset_id_1, 1, 'PRIMARY',
                product_id, asset_id_2, 2, 'GALLERY'
            ))
        conn.commit()

        # Verify media
        with conn.cursor() as cur:
            cur.execute(f"""
                SELECT COUNT(*),
                       COUNT(*) FILTER (WHERE role = 'PRIMARY') as primary_count
                FROM {test_schema}.product_media
                WHERE product_id = %s
            """, (product_id,))
            total, primary = cur.fetchone()

        assert total == 2, "Should have 2 media items"
        assert primary == 1, "Should have exactly 1 primary image"


class TestEAVPattern:
    """Test Entity-Attribute-Value pattern for product attributes."""

    def test_insert_product_attributes(self, db_connection, test_schema, default_category_id):
        """
        Test: Insert product with EAV attributes.
        Purpose: Verify EAV pattern for flexible attribute storage.
        """
        conn, test_product_ids, _ = db_connection

        product_id = uuid4()
        test_product_ids.append(product_id)

        with conn.cursor() as cur:
            # Insert product
            cur.execute(f"""
                INSERT INTO {test_schema}.products (
                    product_id, source, atdw_id, is_active,
                    product_name, category_id, raw_source
                ) VALUES (%s, 'ATDW', 'TEST-ATTR-001', true, 'Test Product', %s, '{{}}'::jsonb)
            """, (product_id, default_category_id))

            # Get attribute IDs (WiFi, Parking - should exist from migration)
            cur.execute(f"""
                SELECT attribute_id FROM {test_schema}.product_attributes
                WHERE code LIKE '%WIFI%' OR code LIKE '%PARKING%'
                LIMIT 2
            """)
            attr_ids = [row[0] for row in cur.fetchall()]

            if len(attr_ids) >= 2:
                # Insert attribute values (using val_bool for boolean attributes)
                cur.execute(f"""
                    INSERT INTO {test_schema}.product_attribute_values (
                        product_id, attribute_id, val_bool
                    ) VALUES
                        (%s, %s, %s),
                        (%s, %s, %s)
                """, (
                    product_id, attr_ids[0], True,
                    product_id, attr_ids[1], True
                ))
        conn.commit()

        # Verify attributes
        with conn.cursor() as cur:
            cur.execute(f"""
                SELECT COUNT(*)
                FROM {test_schema}.product_attribute_values
                WHERE product_id = %s
            """, (product_id,))
            count = cur.fetchone()[0]

        if len(attr_ids) >= 2:
            assert count == 2, "Should have 2 attribute values"


class TestHashDetection:
    """Test hash-based change detection for delta updates."""

    def test_content_hash_stored(self, db_connection, test_schema, default_category_id):
        """
        Test: Content hash is stored and can be used for change detection.
        Purpose: Verify hash-based delta update mechanism.
        """
        conn, test_product_ids, _ = db_connection

        import hashlib

        product_id = uuid4()
        test_product_ids.append(product_id)

        # Calculate hash of content
        content = {'productName': 'Test Product', 'test': 'data'}
        content_hash = hashlib.sha256(
            json.dumps(content, sort_keys=True).encode('utf-8')
        ).hexdigest()

        with conn.cursor() as cur:
            cur.execute(f"""
                INSERT INTO {test_schema}.products (
                    product_id, source, atdw_id, is_active,
                    product_name, category_id, raw_source, content_sha256
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                product_id,
                'ATDW',
                'TEST-HASH-001',
                True,
                'Test Product',
                default_category_id,
                json.dumps(content),
                content_hash
            ))
        conn.commit()

        # Verify hash
        with conn.cursor() as cur:
            cur.execute(f"""
                SELECT content_sha256
                FROM {test_schema}.products
                WHERE product_id = %s
            """, (product_id,))
            stored_hash = cur.fetchone()[0]

        assert stored_hash == content_hash, "Hash should match"
        assert len(stored_hash) == 64, "SHA256 hash should be 64 characters"


class TestIdempotentOperations:
    """Test that operations are idempotent (can run multiple times safely)."""

    def test_upsert_product_idempotent(self, db_connection, test_schema, default_category_id):
        """
        Test: Upserting same product twice doesn't create duplicates.
        Purpose: Verify ON CONFLICT DO UPDATE works correctly.
        """
        conn, test_product_ids, _ = db_connection

        product_id = uuid4()
        test_product_ids.append(product_id)

        # Insert product first time
        with conn.cursor() as cur:
            cur.execute(f"""
                INSERT INTO {test_schema}.products (
                    product_id, source, atdw_id, is_active,
                    product_name, category_id, raw_source
                ) VALUES (%s, 'ATDW', 'TEST-UPSERT-001', true, 'Original Name', %s, '{{}}'::jsonb)
                ON CONFLICT (source, atdw_id) DO UPDATE
                SET product_name = EXCLUDED.product_name,
                    updated_at = CURRENT_TIMESTAMP
            """, (product_id, default_category_id))
        conn.commit()

        # Update same product (different product_id, same source+atdw_id)
        with conn.cursor() as cur:
            cur.execute(f"""
                INSERT INTO {test_schema}.products (
                    product_id, source, atdw_id, is_active,
                    product_name, category_id, raw_source
                ) VALUES (%s, 'ATDW', 'TEST-UPSERT-001', true, 'Updated Name', %s, '{{}}'::jsonb)
                ON CONFLICT (source, atdw_id) DO UPDATE
                SET product_name = EXCLUDED.product_name,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING product_id
            """, (uuid4(), default_category_id))
            returned_id = cur.fetchone()[0]
        conn.commit()

        # Verify only ONE product exists with UPDATED name
        with conn.cursor() as cur:
            cur.execute(f"""
                SELECT COUNT(*), MAX(product_name)
                FROM {test_schema}.products
                WHERE source = 'ATDW' AND atdw_id = 'TEST-UPSERT-001'
            """)
            count, name = cur.fetchone()

        assert count == 1, "Should have exactly 1 product (no duplicates)"
        assert name == 'Updated Name', "Product should be updated, not duplicated"
        assert returned_id == product_id, "Should return original product_id"


"""
PHASE 2 TEST SUMMARY:

This test suite contains integration tests for database operations:

1. TestProductInsertion (2 tests):
   - Insert minimal product
   - Insert product with location data

2. TestProductRelationships (3 tests):
   - Product with address
   - Product with contacts
   - Product with media

3. TestEAVPattern (1 test):
   - Product with EAV attributes

4. TestHashDetection (1 test):
   - Content hash storage and verification

5. TestIdempotentOperations (1 test):
   - Upsert idempotency (no duplicates)

Total: 8 integration tests

Run with: pytest tests/test_atdw_integration.py -v
"""
