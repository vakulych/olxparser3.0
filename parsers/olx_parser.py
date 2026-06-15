"""
OLX GraphQL Parser v2
- Нет искусственных задержек между нормальными запросами
- Задержки только при ошибках (429/403) и между retry
- Ротация User-Agent
- Поддержка прокси
"""
import asyncio
import random
from dataclasses import dataclass
from typing import Optional
from curl_cffi.requests import AsyncSession
from utils.logger import logger
from config.settings import settings

SEARCH_QUERY = """
query ListingSearchQuery($searchParameters: [SearchParameter!] = []) {
  clientCompatibleListings(searchParameters: $searchParameters) {
    __typename
    ... on ListingSuccess {
      __typename
      data {
        id
        title
        description
        url
        created_time
        location { city { name } }
        contact { name phone }
        photos { link }
        user {
          id
          name
          created
          is_online
          last_seen
        }
        params {
          key
          name
          value {
            __typename
            ... on PriceParam { value currency }
          }
        }
      }
    }
    ... on ListingError {
      __typename
      error { title detail }
    }
  }
}
"""

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/605.1.15 Version/17.0 Safari/605.1.15",
]


@dataclass
class OLXListing:
    olx_id: str
    title: str
    description: str
    price: float
    currency: str
    url: str
    city: str
    photo_url: str
    seller_name: str
    seller_id: str
    seller_created: str
    phone: str
    keyword: str = ""


class OLXParser:
    BASE_URL = "https://m.olx.ua/apigateway/graphql"
    MAX_RETRIES = 3

    def __init__(self):
        self._proxies = settings.proxy_list
        self._proxy_idx = 0

    def _next_proxy(self) -> Optional[str]:
        if not self._proxies:
            return None
        proxy = self._proxies[self._proxy_idx % len(self._proxies)]
        self._proxy_idx += 1
        return proxy

    def _build_proxy(self, proxy_url: Optional[str]) -> Optional[dict]:
        if not proxy_url:
            return None
        return {"http": proxy_url, "https": proxy_url}

    def _headers(self) -> dict:
        return {
            "accept": "application/json",
            "content-type": "application/json",
            "origin": "https://m.olx.ua",
            "referer": "https://m.olx.ua/",
            "x-client": "MWEB",
            "user-agent": random.choice(USER_AGENTS),
        }

    async def _request(self, keyword: str, limit: int = 25) -> Optional[dict]:
        payload = {
            "query": SEARCH_QUERY,
            "variables": {
                "searchParameters": [
                    {"key": "offset", "value": "0"},
                    {"key": "limit", "value": str(limit)},
                    {"key": "query", "value": keyword},
                    {"key": "sort", "value": "created_at:desc"},
                ]
            },
        }

        proxy = self._next_proxy()

        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                async with AsyncSession(impersonate="chrome120") as session:
                    response = await session.post(
                        self.BASE_URL,
                        headers=self._headers(),
                        json=payload,
                        timeout=15,
                        proxies=self._build_proxy(proxy),
                    )

                if response.status_code == 200:
                    return response.json()

                if response.status_code in (429, 403):
                    wait = random.uniform(15, 30)
                    logger.warning(f"OLX rate limit for '{keyword}', waiting {wait:.0f}s (attempt {attempt})")
                    await asyncio.sleep(wait)
                    proxy = self._next_proxy()
                else:
                    logger.warning(f"OLX {response.status_code} for '{keyword}' (attempt {attempt})")
                    await asyncio.sleep(random.uniform(2, 5))

            except Exception as e:
                logger.error(f"Parser error '{keyword}' attempt {attempt}: {e}")
                await asyncio.sleep(random.uniform(2, 6))

        return None

    async def search(self, keyword: str, limit: int = 25) -> list[OLXListing]:
        data = await self._request(keyword, limit=limit)
        if not data:
            return []

        try:
            root = data["data"]["clientCompatibleListings"]
        except (KeyError, TypeError):
            logger.error(f"Unexpected OLX structure for '{keyword}'")
            return []

        if root.get("__typename") != "ListingSuccess":
            err = root.get("error", {})
            logger.warning(f"OLX error for '{keyword}': {err.get('title')} — {err.get('detail')}")
            return []

        listings = []
        for item in root.get("data", []):
            try:
                listing = self._parse_item(item, keyword)
                if listing:
                    listings.append(listing)
            except Exception as e:
                logger.error(f"Parse item error: {e}")

        return listings

    def _parse_item(self, item: dict, keyword: str) -> Optional[OLXListing]:
        price = 0.0
        currency = "UAH"
        for param in item.get("params", []):
            if param.get("key") == "price":
                val = param.get("value", {})
                if val and "value" in val:
                    price = float(val["value"])
                    currency = val.get("currency", "UAH")
                    break

        photos = item.get("photos", [])
        photo_url = photos[0].get("link", "") if photos else ""
        user = item.get("user") or {}
        contact = item.get("contact") or {}
        location = item.get("location") or {}
        city_obj = location.get("city") or {}

        return OLXListing(
            olx_id=str(item.get("id", "")),
            title=item.get("title", ""),
            description=item.get("description", "") or "",
            price=price,
            currency=currency,
            url=item.get("url", ""),
            city=city_obj.get("name", ""),
            photo_url=photo_url,
            seller_name=user.get("name") or contact.get("name") or "Неизвестен",
            seller_id=str(user.get("id", "")),
            seller_created=str(user.get("created", "")),
            phone=contact.get("phone") or "",
            keyword=keyword,
        )
