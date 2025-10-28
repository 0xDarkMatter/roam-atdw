# ATDW Attribute Catalog

Comprehensive documentation of all Australian Tourism Data Warehouse (ATDW) attribute types and codes discovered through API sampling.

## Overview

**Generated from**: 160 detailed product samples across 8 product categories
**Total Attribute Types**: 23
**Total Unique Attributes**: 198

This catalog documents all attribute types and specific attribute codes found in the ATDW API. Attributes are used to describe product features, facilities, accessibility options, memberships, and other characteristics.

**Note**: This catalog was generated from a sample of ATDW products. Additional attributes may exist that were not encountered in the sample. The application should handle unknown attributes gracefully by storing them even if not in this catalog.

## Data Files

- **JSON Catalog**: `E:\Projects\Coding\Fathom\data\atdw_attribute_catalog.json`
- **SQL Migration**: `E:\Projects\Coding\Fathom\migrations\011_populate_attribute_def.sql`

## Attribute Structure

ATDW attributes follow this structure in the API:

```json
{
  "attributeTypeId": "ENTITY FAC",
  "attributeTypeIdDescription": "Entity Facility",
  "attributeId": "24HOURS",
  "attributeIdDescription": "24 Hour Reception"
}
```

Accessibility attributes have a slightly different structure:

```json
{
  "attributeTypeId": "ACCESSIBILITY",
  "attributeTypeIdDescription": "Accessibility",
  "attributeSubType1Id": "DISASSIST",
  "attributeSubType1IdDescription": "Actively welcomes people with access needs."
}
```

## Attribute Type Summary

### 1. ACCESSIBILITY (3 attributes)
**Description**: Accessibility options for people with access needs

**Found in**: Accommodation, Attraction, Event, Hire, Restaurant, Tour, Transport

**Attributes**:
- `DISASSIST`: Actively welcomes people with access needs
- `DISTASSIST`: Disabled access available, contact operator for details
- `NOASSIST`: Does not cater for people with access needs

### 2. ACCREDITN (14 attributes)
**Description**: Industry accreditations and certifications

**Found in**: Accommodation, Event, Hire, Restaurant, Tour, Transport

**Key Attributes**:
- `ATAP`: Quality Tourism Accreditation
- `ECOTOUR`: ECO Certified (Ecotourism) by Ecotourism Australia
- `NATTOUR`: ECO Certified (Nature Tourism) by Ecotourism Australia
- `SUSTAINABLE`: Sustainable Tourism Accreditation by ATIC
- `ATICTERC`: Tourism Emission Reduction Commitment
- `ATECDR`: ATEC Domestic Ready
- `ATECTTR`: ATEC Tourism Trade Ready
- `INTREADY`: International Ready Accreditation

### 3. ACTIVITY (16 attributes)
**Description**: Available activities

**Found in**: Attraction, Hire, Journey, Restaurant, Tour

**Attributes**:
- `4WD`: Four Wheel Driving
- `BIKEMOUNT`: Mountain Biking
- `BIRDWATCH`: Birdwatching
- `BOAT`: Boating
- `CAMP`: Camping
- `CANOE`: Canoeing/Kayaking
- `CYCLE`: Cycling
- `FISH`: Fishing
- `SAIL`: Sailing
- `SURF`: Surfing
- `SWIM`: Swimming
- `WALK`: Walks
- `WALKHIKE`: Hiking
- `WINE`: Wine
- `WINETASTE`: Wine tasting

### 4. ALTWINESTYLES (2 attributes)
**Description**: Alternative wine production styles

**Found in**: Restaurant

**Attributes**:
- `ORGANICWIN`: Organic Wine
- `SUSTPROD`: Sustainably Produced Wine

### 5. BYOLICENCE (2 attributes)
**Description**: Liquor licensing status

**Found in**: Restaurant

**Attributes**:
- `NOBYO`: Fully licensed
- `NOLIC`: Not licensed

### 6. CUISINE (40 attributes)
**Description**: Cuisine types and dining styles

**Found in**: Restaurant

**Key Attributes**:
- `AUSTRALIAN`: Australian
- `ASIAN`: Asian
- `CHINESE`: Chinese
- `FRENCH`: French
- `GREEK`: Greek
- `INDIAN`: Indian
- `ITALIAN`: Italian
- `JAPANESE`: Japanese
- `MEDITERRANEAN`: Mediterranean
- `MEXICAN`: Mexican
- `SEAFOOD`: Seafood
- `THAI`: Thai
- `VIETNAMESE`: Vietnamese
- `VEGETARIAN`: Vegetarian

### 7. DISASSIST (9 attributes)
**Description**: Detailed accessibility assistance options

**Found in**: Accommodation, Attraction, Event, Hire, Restaurant, Tour, Transport

**Key Attributes**:
- `ACCESSINCLSTMNT`: Access and inclusion statement available
- `ALERGYINTOLRNCE`: Caters for allergies and intolerances
- `AMBULANT`: Caters for people with mobility aids
- `COMMUNICATION`: Welcomes people with learning/communication challenges
- `HEARING`: Caters for hearing impairment
- `SIGHTASSIST`: Caters for vision impairment

### 8. DIST UNIT (1 attribute)
**Description**: Distance measurement units

**Found in**: Journey

**Attributes**:
- `KMS`: Kilometres

### 9. ENTITY FAC (45 attributes)
**Description**: Entity facilities and amenities

**Found in**: Accommodation, Attraction, Event, Hire, Restaurant, Tour, Transport

**Key Attributes**:
- `24HOURS`: 24 Hour Reception
- `BAR`: Bar
- `BBQ`: Barbeque
- `BOATRAMP`: Boat Ramp
- `BUSINESSFC`: Business Facilities
- `CAFE`: Cafe
- `CARPARK`: Carpark
- `CELLARDOOR`: Cellar Door
- `COACHPARK`: Coach Parking
- `CONFCENT`: Conference Centre
- `CONVFAC`: Conference/Convention Facilities
- `ENVFRIEND`: Environmentally Friendly
- `FREEWIFI`: Free WiFi (Note: This is a duplicate - also appears in INTERNET)
- `FUNCROOM`: Function Room
- `GALLERY`: Gallery
- `GYM`: Gymnasium
- `GUESTLAUND`: Guest Laundry
- `KIOSK`: Kiosk
- `LIBRARY`: Library
- `ONSITE`: On Site Accommodation
- `PETFRIEND`: Pet Friendly
- `PICNICFAC`: Picnic Facilities
- `PLAYGROUND`: Playground
- `POOL`: Swimming Pool
- `RESTAURANT`: Restaurant
- `ROOM`: Room Service
- `SHOP`: Shop/Gift Shop
- `SPA`: Day Spa
- `TOILET`: Public Toilet

### 10. INDIGENOUS (2 attributes)
**Description**: Indigenous culture offerings

**Found in**: Tour

**Attributes**:
- `EXPERIENCE`: Indigenous experiences and/or cultural immersion
- `THEMES`: Indigenous themes and/or interpretation

### 11. INTERNET (3 attributes)
**Description**: Internet connectivity options

**Found in**: Accommodation, Attraction, Event, Hire, Restaurant, Tour, Transport

**Attributes**:
- `FREEWIFI`: Free WiFi
- `INTERNETBB`: Broadband Internet Access
- `PAIDWIFI`: Paid WiFi

### 12. INTNLREACH (1 attribute)
**Description**: Event reach/scope

**Found in**: Event

**Attributes**:
- `STATE`: State-level event

### 13. MEALTYPES (4 attributes)
**Description**: Meal service times

**Found in**: Restaurant

**Attributes**:
- `BREAKFAST`: Breakfast
- `LUNCH`: Lunch
- `DINNER`: Dinner
- `LATEDINE`: Late night dining

### 14. MEMBERSHIP (10 attributes)
**Description**: Industry memberships and associations

**Found in**: Accommodation, Attraction, Event, Hire, Restaurant, Tour, Transport

**Key Attributes**:
- `AGLTA`: Gay and Lesbian Tourism Australia (GALTA)
- `ATEC`: Australian Tourism Export Council
- `NATRUST`: National Trust
- `RTO`: Regional Tourist/Tourism Association/Organisation
- `SATC`: South Australian Tourism Commission
- `TICACT`: Tourism Industry Council ACT
- `TICTAS`: Tourism Industry Council Tasmania

### 15. REST PRICE (4 attributes)
**Description**: Restaurant price ranges

**Found in**: Restaurant

**Attributes**:
- `UNDER20`: Under $20 per person
- `BTW20AND30`: Between $20 and $30
- `OVER30`: Over $30
- `NOTSPECIFIED`: Not Specified

### 16. STARRATING (1 attribute)
**Description**: Accommodation star ratings

**Found in**: Accommodation

**Attributes**:
- `4`: 4 Stars (Note: Other star ratings likely exist: 1, 2, 3, 5)

### 17. TAG (17 attributes)
**Description**: Thematic tags for categorization

**Found in**: Accommodation, Attraction, Event, Hire, Journey, Restaurant, Tour, Transport

**Key Attributes**:
- `AboriginalCulture`: Aboriginal Culture
- `Adventure`: Adventure
- `AgriTourism`: Agri Tourism
- `Art&Culture`: Art & Culture
- `Beaches&Surf`: Beaches & Surf
- `Eco-Tourism`: Eco-Tourism
- `Food&Wine`: Food & Wine
- `FamilyFriendly`: Family Friendly
- `Luxury`: Luxury
- `Nature&Wildlife`: Nature & Wildlife
- `Outback`: Outback
- `PetFriendly`: Pet Friendly

### 18. TIME UNIT (1 attribute)
**Description**: Time measurement units

**Found in**: Journey

**Attributes**:
- `HRS`: Hours

### 19. TOURISMORG (13 attributes)
**Description**: Regional tourism organizations

**Found in**: Event, Hire, Journey, Restaurant, Tour, Transport

**Key Attributes**:
- Regional Tourism Organizations (RTOs) by state/region
- Examples: RTOBNBT (QLD - Bundaberg North Burnett Tourism), RTOEP (WA - Destination Perth)

### 20. WINE PRICE (3 attributes)
**Description**: Wine price ranges

**Found in**: Restaurant

**Attributes**:
- `BTW0AND20`: Between $0 and $20
- `BTW20AND40`: Between $20 and $40
- `OVER40`: Over $40

### 21. WINEMAKE (3 attributes)
**Description**: Winemaking and viticultural practices

**Found in**: Restaurant

**Attributes**:
- `ESTATEGROW`: Estate Grown
- `FAMILYRUN`: Family Run
- `HANDPICK`: Hand-picked

### 22. WINEORG (2 attributes)
**Description**: Wine industry organizations

**Found in**: Restaurant, Tour

**Attributes**:
- `RWOBWGA`: SA - Barossa Grape & Wine Association
- `RWOMWGGA`: NSW - Mudgee Wine Association

### 23. WINEREGIONS (2 attributes)
**Description**: Australian wine regions

**Found in**: Restaurant, Tour

**Attributes**:
- `BARZNE`: Barossa (zone)
- `MUDGEE`: Mudgee

## Data Types

All attributes discovered in this catalog use `bool` (boolean) data type, indicating presence/absence of the feature. However, the schema supports other data types for future attributes:

- `bool`: Boolean (true/false, presence flag)
- `integer`: Whole numbers
- `decimal`: Decimal numbers
- `string`: Short text values
- `text`: Long text values
- `array`: Lists of values
- `object`: Structured data

## Usage in Database

The `attribute_def` table stores attribute definitions:

```sql
CREATE TABLE attribute_def (
    attribute_type VARCHAR(50) NOT NULL,
    attribute_code VARCHAR(50) NOT NULL,
    attribute_label VARCHAR(255) NOT NULL,
    data_type VARCHAR(20) NOT NULL DEFAULT 'bool',
    PRIMARY KEY (attribute_type, attribute_code)
);
```

The `product_attribute` junction table links products to their attributes:

```sql
CREATE TABLE product_attribute (
    product_id INTEGER NOT NULL REFERENCES product(product_id),
    attribute_type VARCHAR(50) NOT NULL,
    attribute_code VARCHAR(50) NOT NULL,
    FOREIGN KEY (attribute_type, attribute_code)
        REFERENCES attribute_def(attribute_type, attribute_code),
    PRIMARY KEY (product_id, attribute_type, attribute_code)
);
```

## Completeness Notes

This catalog was generated from 160 detailed product samples across 8 categories:
- Accommodation (20 products)
- Attraction (20 products)
- Tour (20 products)
- Restaurant (20 products)
- Event (20 products)
- Hire (20 products)
- Transport (20 products)
- Journey (20 products)

**Known Gaps**:
1. Categories with no products in sample:
   - General Service (0 products found)
   - Destination (0 products found)

2. Limited coverage:
   - Star ratings: Only `4` discovered, but 1-5 star ratings likely exist
   - Regional tourism organizations: Only 13 discovered, but more likely exist
   - Wine regions: Only 2 discovered, but many more exist in Australia
   - Cuisine types: 40 discovered, but specialty cuisines may be missing

**Recommendation**: The application should be designed to handle unknown attributes gracefully:
1. Accept and store attributes not in the catalog
2. Log new attribute discoveries for catalog updates
3. Use attribute codes as fallback labels when descriptions are missing

## Attribute API Endpoints

Attributes appear in the detailed product endpoint:

```
GET /api/atlas/product?productId={id}&key={key}
```

Look for these fields in the response:
- `attributes[]`: Main product attributes
- `accessibilityAttributes[]`: Accessibility-specific attributes
- `productWineVarietyAttributes[]`: Wine variety attributes (for wineries)
- `productWineTastingAttributes[]`: Wine tasting attributes (for wineries)

## Updates and Maintenance

To update this catalog with more comprehensive data:

1. Run the extraction script with larger samples:
   ```bash
   python scripts/extract_atdw_attributes.py
   ```

2. Modify the script to:
   - Increase products per category (currently 20)
   - Add state/region filtering for geographic coverage
   - Target specific product categories for deep dives

3. Re-run the migration after updates:
   ```bash
   psql -d otdb < migrations/011_populate_attribute_def.sql
   ```

## Related Documentation

- **ATDW API Docs**: https://developer.atdw.com.au
- **Database Schema**: E:\Projects\Coding\Fathom\docs\ATDW_DATABASE_SCHEMA.md
- **Field Reference**: E:\Projects\Coding\Fathom\docs\ATDW_API_FIELDS.md
