# ATDW Attribute Quick Reference

Quick lookup guide for ATDW attribute types and their most common codes.

## Quick Stats

- **23** Attribute Types
- **198** Unique Attribute Codes
- Discovered from **160** product samples across **8** categories

## Most Common Attribute Types

### ENTITY FAC (45 attributes)
Facilities and amenities available at the venue.

**Top codes**: 24HOURS, BAR, BBQ, CAFE, CARPARK, GYM, POOL, RESTAURANT, SPA, WIFI

### CUISINE (40 attributes)
Restaurant cuisine types and dining styles.

**Top codes**: AUSTRALIAN, ASIAN, CHINESE, ITALIAN, JAPANESE, SEAFOOD, THAI, VEGETARIAN

### TAG (17 attributes)
Thematic tags for categorization and discovery.

**Top codes**: AboriginalCulture, Adventure, Art&Culture, Beaches&Surf, Eco-Tourism, Food&Wine, FamilyFriendly, Luxury

### ACTIVITY (16 attributes)
Activities available at or near the venue.

**Top codes**: 4WD, BIKEMOUNT, BOAT, CAMP, CYCLE, FISH, SURF, SWIM, WALK, WALKHIKE, WINETASTE

## Accessibility

### ACCESSIBILITY (3 codes)
- DISASSIST: Actively welcomes people with access needs
- DISTASSIST: Contact operator for details
- NOASSIST: Does not cater for access needs

### DISASSIST (9 codes - detailed accessibility)
- ACCESSINCLSTMNT: Access statement available
- ALERGYINTOLRNCE: Caters for allergies/intolerances
- AMBULANT: Mobility aids supported
- COMMUNICATION: Learning/communication support
- HEARING: Hearing impairment support
- SIGHTASSIST: Vision impairment support

## Quality & Certification

### ACCREDITN (14 codes)
- ATAP: Quality Tourism Accreditation
- ECOTOUR: ECO Certified (Ecotourism)
- NATTOUR: ECO Certified (Nature Tourism)
- SUSTAINABLE: Sustainable Tourism Accreditation
- ATICTERC: Emission Reduction Commitment

### MEMBERSHIP (10 codes)
- ATEC: Australian Tourism Export Council
- AGLTA: Gay and Lesbian Tourism Australia
- NATRUST: National Trust
- RTO: Regional Tourism Organisation

## Restaurant-Specific

### MEALTYPES (4 codes)
BREAKFAST, LUNCH, DINNER, LATEDINE

### REST PRICE (4 codes)
UNDER20, BTW20AND30, OVER30, NOTSPECIFIED

### BYOLICENCE (2 codes)
NOBYO (Fully licensed), NOLIC (Not licensed)

### WINE PRICE (3 codes)
BTW0AND20, BTW20AND40, OVER40

## Internet Access

### INTERNET (3 codes)
- FREEWIFI: Free WiFi
- INTERNETBB: Broadband Internet
- PAIDWIFI: Paid WiFi

## Special Interest

### INDIGENOUS (2 codes)
- EXPERIENCE: Indigenous cultural immersion
- THEMES: Indigenous themes/interpretation

### WINEMAKE (3 codes)
- ESTATEGROW: Estate Grown
- FAMILYRUN: Family Run
- HANDPICK: Hand-picked

## Regional Classification

### TOURISMORG (13 codes)
Regional Tourism Organizations by state/region
Examples: RTOBNBT (QLD Bundaberg), RTOEP (WA Perth)

### WINEREGIONS (2 codes)
BARZNE (Barossa), MUDGEE

## Journey Attributes

### DIST UNIT (1 code)
KMS: Kilometres

### TIME UNIT (1 code)
HRS: Hours

## Usage Pattern

```python
# Query products with specific attributes
products_with_pool = search_products(
    categories=['ACCOMM'],
    # Note: Attribute filtering may require custom implementation
)

# Check product attributes after fetching
detailed_product = client.get_product(product_id)
for attr in detailed_product.get('attributes', []):
    if attr['attributeTypeId'] == 'ENTITY FAC':
        if attr['attributeId'] == 'POOL':
            print("Has swimming pool")
```

## Database Schema

```sql
-- Attribute definitions
SELECT * FROM attribute_def
WHERE attribute_type = 'ENTITY FAC'
ORDER BY attribute_code;

-- Product attributes
SELECT p.product_name, pa.attribute_type, pa.attribute_code
FROM product p
JOIN product_attribute pa ON p.product_id = pa.product_id
WHERE pa.attribute_type = 'ENTITY FAC'
  AND pa.attribute_code = 'POOL';
```

## File Locations

- **JSON Catalog**: `data/atdw_attribute_catalog.json`
- **SQL Migration**: `migrations/011_populate_attribute_def.sql`
- **Full Documentation**: `docs/ATDW_ATTRIBUTE_CATALOG.md`
- **Extraction Script**: `scripts/extract_atdw_attributes.py`

## Extending the Catalog

To discover more attributes:

1. Edit `scripts/extract_atdw_attributes.py`
2. Increase sample size per category (currently 20)
3. Add geographic filtering for regional attributes
4. Run: `python scripts/extract_atdw_attributes.py`
5. Apply migration: `psql -d otdb < migrations/011_populate_attribute_def.sql`
