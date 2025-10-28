"""
ATDW (Australian Tourism Data Warehouse) ATLAS2 API Client

Provides access to Australia's national tourism database with 50,000+ tourism products.

API Features:
- Full-text search across tourism products
- Geospatial search (radius and polygon)
- Category filtering (accommodation, attractions, tours, restaurants, events)
- Pagination support
- Product details with multilingual support

Rate Limiting & Pagination:
- ATDW does not specify numeric limits for rate limiting
- Returns HTTP 429 with Retry-After: 60 header when rate limited
- Recommends spreading requests rather than bursting
- Client implements exponential backoff with Retry-After header support
- Maximum page size: 5000 results per request (tested empirically)
- Default page size: 1000 (balances API calls vs response size)

API Documentation:
https://developer.atdw.com.au
Rate Limiting Policy: https://au.intercom.help/atdw/en/articles/44447-api-rate-limiting

Package: Industry package
"""

import os
import requests
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime


class ATDWClient:
    """
    ATDW ATLAS2 API client for Australian tourism data.

    The ATDW (Australian Tourism Data Warehouse) provides access to 50,000+ tourism
    products across accommodation, attractions, tours, restaurants, and events.
    """

    BASE_URL = "https://atlas.atdw-online.com.au/api/atlas"

    # Common product categories
    CATEGORIES = {
        'ACCOMMODATION': 'ACCOMM',
        'ATTRACTION': 'ATTRACTION',
        'TOUR': 'TOUR',
        'RESTAURANT': 'RESTAURANT',
        'EVENT': 'EVENT',
        'HIRE': 'HIRE',
        'TRANSPORT': 'TRANSPORT',
        'GENERAL_SERVICE': 'GENERAL_SERVICE',
        'DESTINATION': 'DESTINATION',
        'JOURNEY': 'JOURNEY'
    }

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize ATDW API client.

        Args:
            api_key: ATDW distributor key (or set ATDW_API_KEY env var)
        """
        self.api_key = api_key or os.getenv('ATDW_API_KEY')
        if not self.api_key:
            raise ValueError(
                "ATDW API key required. "
                "Set ATDW_API_KEY environment variable or pass api_key parameter."
            )

        self.session = requests.Session()

        # Rate limiting - spread requests to avoid bursts (ATDW recommendation)
        # Set to 2 req/sec for data-intensive queries (5000 results with many fields)
        self.last_request_time = 0
        self.min_request_interval = 0.5  # 2 requests per second

        # Retry configuration for 429 responses
        self.max_retries = 3
        self.backoff_factor = 2  # Exponential backoff multiplier

    def _rate_limit(self):
        """Enforce rate limiting between requests."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()

    def _make_request(self, endpoint: str, params: Dict) -> Dict:
        """
        Make API request with authentication, rate limiting, and retry logic.

        Implements exponential backoff for HTTP 429 responses and respects
        the Retry-After header as per ATDW recommendations.

        Args:
            endpoint: API endpoint path (e.g., '/products')
            params: Query parameters

        Returns:
            Response data as dictionary

        Raises:
            requests.exceptions.HTTPError: For HTTP errors (after retries exhausted)
        """
        # Add authentication and JSON output
        params['key'] = self.api_key
        params.setdefault('out', 'json')  # Default to JSON format

        url = f"{self.BASE_URL}{endpoint}"

        # Retry loop with exponential backoff
        for attempt in range(self.max_retries + 1):
            # Apply rate limiting before request
            self._rate_limit()

            response = self.session.get(url, params=params)

            # Success
            if response.status_code == 200:
                return response.json()

            # Rate limited - respect Retry-After header
            if response.status_code == 429:
                # Get retry delay from header (default to 60 seconds per ATDW docs)
                retry_after = int(response.headers.get('Retry-After', 60))

                if attempt < self.max_retries:
                    # Exponential backoff: retry_after * (2^attempt)
                    wait_time = retry_after * (self.backoff_factor ** attempt)
                    print(f"Rate limited (429). Waiting {wait_time}s before retry {attempt + 1}/{self.max_retries}...")
                    time.sleep(wait_time)
                    continue
                else:
                    # Exhausted retries
                    response.raise_for_status()

            # Other HTTP errors
            response.raise_for_status()

        # Should not reach here, but raise if we do
        raise requests.exceptions.HTTPError("Max retries exceeded")

    def search_products(
        self,
        term: Optional[str] = None,
        categories: Optional[List[str]] = None,
        lat: Optional[float] = None,
        lng: Optional[float] = None,
        radius_km: Optional[float] = None,
        state: Optional[str] = None,
        city: Optional[str] = None,
        region: Optional[str] = None,
        min_rate: Optional[float] = None,
        max_rate: Optional[float] = None,
        star_rating: Optional[int] = None,
        fields: Optional[List[str]] = None,
        paginate: bool = True,
        max_pages: Optional[int] = None,
        page_size: int = 1000
    ) -> List[Dict]:
        """
        Search for tourism products with advanced filtering.

        Args:
            term: Full-text search term (searches names, descriptions, attributes)
            categories: List of category codes (use CATEGORIES constant)
            lat: Latitude for geospatial search
            lng: Longitude for geospatial search
            radius_km: Radius in kilometers (requires lat/lng)
            state: Australian state code (NSW, VIC, QLD, SA, WA, TAS, NT, ACT)
            city: City/suburb name
            region: Region name
            min_rate: Minimum price
            max_rate: Maximum price
            star_rating: Star rating (1-5, for accommodation)
            fields: List of fields to return (default returns all standard fields)
            paginate: If True, fetch all pages. If False, only first page. (default: True)
            max_pages: Optional limit on pages to fetch
            page_size: Results per page (default: 1000, max: 5000)

        Returns:
            List of product dictionaries
        """
        params = {}

        # Full-text search
        if term:
            params['term'] = term

        # Category filtering
        if categories:
            # Convert friendly names to codes if needed
            codes = [self.CATEGORIES.get(cat.upper(), cat) for cat in categories]
            params['cats'] = ','.join(codes)

        # Geospatial search
        if lat is not None and lng is not None:
            params['latlong'] = f"{lat},{lng}"
            if radius_km:
                params['dist'] = radius_km

        # Location filtering
        if state:
            params['st'] = state.upper()
        if city:
            params['ct'] = city
        if region:
            params['rg'] = region

        # Price filtering
        if min_rate is not None:
            params['minRate'] = min_rate
        if max_rate is not None:
            params['maxRate'] = max_rate

        # Star rating
        if star_rating is not None:
            params['starrating'] = star_rating

        # Field selection
        if fields:
            params['fl'] = ','.join(fields)

        # Pagination
        params['size'] = page_size

        # Fetch results with pagination
        all_results = []
        page = 1

        while True:
            params['pge'] = page

            try:
                response = self._make_request('/products', params)

                # Extract products from response
                products = response.get('products', [])
                if not products:
                    break

                all_results.extend(products)

                # Check pagination
                if not paginate:
                    break
                if max_pages and page >= max_pages:
                    break

                # Check if more pages available (ATDW uses 'numberOfResults' not 'totalCount')
                total_count = response.get('numberOfResults', 0)
                if len(all_results) >= total_count:
                    break

                page += 1

            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    # No more pages
                    break
                raise

        return all_results

    def get_product(
        self,
        product_id: str,
        language: str = 'ENGLISH'
    ) -> Dict:
        """
        Get detailed information for a specific product.

        Args:
            product_id: Product identifier from search results
            language: Market variant (ENGLISH, CHINESE-T, CHINESE-S)

        Returns:
            Product details dictionary
        """
        params = {
            'productId': product_id,
            'mv': language
        }

        return self._make_request('/product', params)

    def search_by_location(
        self,
        lat: float,
        lng: float,
        radius_km: float = 10,
        categories: Optional[List[str]] = None,
        **kwargs
    ) -> List[Dict]:
        """
        Convenience method for location-based search.

        Args:
            lat: Latitude
            lng: Longitude
            radius_km: Search radius in kilometers (default: 10km)
            categories: List of category codes
            **kwargs: Additional parameters passed to search_products()

        Returns:
            List of products within radius
        """
        return self.search_products(
            lat=lat,
            lng=lng,
            radius_km=radius_km,
            categories=categories,
            **kwargs
        )

    def search_by_region(
        self,
        state: Optional[str] = None,
        region: Optional[str] = None,
        city: Optional[str] = None,
        categories: Optional[List[str]] = None,
        **kwargs
    ) -> List[Dict]:
        """
        Convenience method for region-based search.

        Args:
            state: State code (NSW, VIC, QLD, SA, WA, TAS, NT, ACT)
            region: Region name
            city: City/suburb name
            categories: List of category codes
            **kwargs: Additional parameters passed to search_products()

        Returns:
            List of products in region
        """
        return self.search_products(
            state=state,
            region=region,
            city=city,
            categories=categories,
            **kwargs
        )

    def get_delta(
        self,
        since_date: str,
        categories: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Get products updated since a specific date.

        Args:
            since_date: ISO date string (YYYY-MM-DD)
            categories: Optional category filter

        Returns:
            List of updated products
        """
        params = {
            'updatedSince': since_date
        }

        if categories:
            codes = [self.CATEGORIES.get(cat.upper(), cat) for cat in categories]
            params['cats'] = ','.join(codes)

        return self._make_request('/delta', params).get('products', [])
