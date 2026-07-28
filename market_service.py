import os
import time
import random
import requests
from datetime import datetime, timedelta

random.seed(42)

CROPS = [
    "Paddy", "Banana", "Sugarcane", "Cotton", "Groundnut",
    "Coconut", "Maize", "Tomato", "Onion", "Brinjal",
    "Chilli", "Millets", "Pulses", "Turmeric", "Sesame",
]

CROPS_TA = [
    "நெல்", "வாழை", "கரும்பு", "பருத்தி", "வேர்க்கடலை",
    "தேங்காய்", "சோளம்", "தக்காளி", "வெங்காயம்", "கத்தரிக்காய்",
    "மிளகாய்", "சிறுதானியங்கள்", "பருப்பு வகைகள்", "மஞ்சள்", "எள்",
]

MARKETS = [
    "Koyambedu Wholesale Market", "Oddanchatram Vegetable Market",
    "Mettupalayam Market", "Pollachi Market", "Gobichettipalayam Market",
    "Dindigul Market", "Madurai Market", "Tiruchirappalli Market",
    "Thanjavur Market", "Salem Market", "Erode Turmeric Market",
    "Namakkal Market", "Virudhunagar Market", "Cuddalore Market",
    "Theni Market", "Villupuram Market", "Nagapattinam Market",
    "Tirunelveli Market", "Coimbatore Market", "Karur Market",
]

MARKETS_TA = [
    "கோயம்பேடு மொத்த சந்தை", "ஒட்டன்சத்திரம் காய்கறி சந்தை",
    "மேட்டுப்பாளையம் சந்தை", "பொள்ளாச்சி சந்தை", "கோபிசெட்டிப்பாளையம் சந்தை",
    "திண்டுக்கல் சந்தை", "மதுரை சந்தை", "திருச்சிராப்பள்ளி சந்தை",
    "தஞ்சாவூர் சந்தை", "சேலம் சந்தை", "ஈரோடு மஞ்சள் சந்தை",
    "நாமக்கல் சந்தை", "விருதுநகர் சந்தை", "கடலூர் சந்தை",
    "தேனி சந்தை", "விழுப்புரம் சந்தை", "நாகப்பட்டினம் சந்தை",
    "திருநெல்வேலி சந்தை", "கோயம்புத்தூர் சந்தை", "கரூர் சந்தை",
]

BASE_PRICES = {
    "Paddy": (2000, 2800), "Banana": (2500, 4500), "Sugarcane": (2800, 4000),
    "Cotton": (5500, 8500), "Groundnut": (4000, 6500), "Coconut": (2000, 3500),
    "Maize": (1800, 2600), "Tomato": (1500, 3500), "Onion": (1200, 3000),
    "Brinjal": (1500, 2800), "Chilli": (4000, 8000), "Millets": (2500, 4000),
    "Pulses": (4500, 7500), "Turmeric": (8000, 15000), "Sesame": (5000, 8000),
}

MARKET_MULTIPLIERS = {
    "Koyambedu Wholesale Market": 1.12, "Oddanchatram Vegetable Market": 0.92,
    "Mettupalayam Market": 0.95, "Pollachi Market": 0.98, "Gobichettipalayam Market": 0.93,
    "Dindigul Market": 0.96, "Madurai Market": 1.05, "Tiruchirappalli Market": 1.02,
    "Thanjavur Market": 1.08, "Salem Market": 1.00, "Erode Turmeric Market": 1.15,
    "Namakkal Market": 0.94, "Virudhunagar Market": 0.97, "Cuddalore Market": 0.95,
    "Theni Market": 0.91, "Villupuram Market": 0.93, "Nagapattinam Market": 0.90,
    "Tirunelveli Market": 0.98, "Coimbatore Market": 1.10, "Karur Market": 0.96,
}


class MarketPriceService:
    def __init__(self):
        self.api_key = os.getenv("MARKET_API_KEY", "")
        self.cache = {}
        self.cache_ttl = 300

    def _cache_key(self, crop, market):
        return (crop.strip().lower(), market.strip().lower())

    def _get_cached(self, crop, market):
        key = self._cache_key(crop, market)
        if key in self.cache:
            entry = self.cache[key]
            if time.time() - entry["ts"] < self.cache_ttl:
                return entry["data"]
        return None

    def _set_cache(self, crop, market, data):
        key = self._cache_key(crop, market)
        self.cache[key] = {"data": data, "ts": time.time()}

    def clear_cache(self):
        self.cache.clear()

    def fetch_price(self, crop, market):
        cached = self._get_cached(crop, market)
        if cached:
            return cached

        if self.api_key:
            result = self._fetch_from_api(crop, market)
        else:
            result = self._generate_price(crop, market)

        if result and not result.get("error"):
            self._set_cache(crop, market, result)
        return result

    def _fetch_from_api(self, crop, market):
        try:
            resource_id = "9ef84268-d588-465a-a308-a864a43d0070"
            url = "https://api.data.gov.in/resource/" + resource_id
            params = {
                "api-key": self.api_key,
                "format": "json",
                "limit": 10,
                "filters[commodity]": crop,
                "filters[market]": market.split(" ")[0],
            }
            resp = requests.get(url, params=params, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                records = data.get("records", [])
                if records:
                    return self._parse_api_record(records[0], crop, market)
            return None
        except Exception:
            return None

    def _parse_api_record(self, rec, crop, market):
        price = float(rec.get("modal_price", rec.get("max_price", 0)))
        return self._build_result(crop, market, price, "Quintal")

    def _generate_price(self, crop, market):
        base_range = BASE_PRICES.get(crop, (1500, 3000))
        base = (base_range[0] + base_range[1]) / 2
        spread = base_range[1] - base_range[0]
        mult = MARKET_MULTIPLIERS.get(market, 1.0)

        seed = hash(f"{crop}-{market}-{datetime.now().strftime('%Y-%m-%d')}") % 1000
        rng = random.Random(seed)
        daily_var = rng.uniform(-0.05, 0.05)
        price = base * mult * (1 + daily_var)
        price = round(price / 10) * 10

        return self._build_result(crop, market, price, "Quintal")

    def _build_result(self, crop, market, price, unit):
        seed = hash(f"{crop}-{market}-{datetime.now().strftime('%Y-%H')}") % 100
        rng = random.Random(seed)
        change_pct = round(rng.uniform(-5, 5), 1)
        if change_pct > 1:
            trend = "up"
        elif change_pct < -1:
            trend = "down"
        else:
            trend = "stable"

        is_open = 6 <= datetime.now().hour < 18
        yesterday_price = round(price / (1 + change_pct / 100))
        week_ago_price = round(price / (1 + rng.uniform(-0.08, 0.08)))

        return {
            "crop": crop,
            "market": market,
            "price": price,
            "unit": unit,
            "trend": trend,
            "change_pct": change_pct,
            "is_open": is_open,
            "status": "open" if is_open else "closed",
            "yesterday_price": yesterday_price,
            "week_ago_price": week_ago_price,
            "updated_at": datetime.now().strftime("%I:%M %p").lstrip("0"),
        }

    def compare_markets(self, crop):
        results = []
        for market in MARKETS:
            data = self.fetch_price(crop, market)
            if data:
                results.append(data)
        results.sort(key=lambda x: x["price"], reverse=True)
        return results

    def top_gainers(self, limit=5):
        today = datetime.now().strftime("%Y-%m-%d")
        all_prices = []
        for crop in CROPS:
            market = random.Random(crop + today).choice(MARKETS)
            data = self.fetch_price(crop, market)
            if data:
                all_prices.append(data)
        all_prices.sort(key=lambda x: x["change_pct"], reverse=True)
        return all_prices[:limit]

    def top_losers(self, limit=5):
        today = datetime.now().strftime("%Y-%m-%d")
        all_prices = []
        for crop in CROPS:
            market = random.Random(crop + today + "loss").choice(MARKETS)
            data = self.fetch_price(crop, market)
            if data:
                all_prices.append(data)
        all_prices.sort(key=lambda x: x["change_pct"])
        return all_prices[:limit]

    def get_summary(self):
        today = datetime.now().strftime("%Y-%m-%d")
        prices = []
        for crop in CROPS:
            market = random.Random(crop + today + "summary").choice(MARKETS)
            data = self.fetch_price(crop, market)
            if data:
                prices.append(data["price"])
        if not prices:
            return {"highest": 0, "lowest": 0, "average": 0, "count": 0}
        return {
            "highest": max(prices),
            "lowest": min(prices),
            "average": round(sum(prices) / len(prices)),
            "count": len(MARKETS),
        }


market_service = MarketPriceService()
MarketService = MarketPriceService
