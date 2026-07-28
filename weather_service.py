import os
import time
import requests
from datetime import datetime, timedelta

class WeatherService:
    def __init__(self):
        self.api_key = os.getenv("WEATHER_API_KEY", "")
        self.base_url = "https://api.weatherapi.com/v1"
        self.cache = {}
        self.cache_ttl = 600

    def _cache_key(self, district, town):
        return (district.strip().lower(), town.strip().lower())

    def _get_cached(self, district, town):
        key = self._cache_key(district, town)
        if key in self.cache:
            entry = self.cache[key]
            if time.time() - entry["ts"] < self.cache_ttl:
                return entry["data"]
        return None

    def _set_cache(self, district, town, data):
        key = self._cache_key(district, town)
        self.cache[key] = {"data": data, "ts": time.time()}

    def get_current_weather(self, district="", town=""):
        data = self.fetch_all(district, town)
        if data.get("error"):
            return None
        current = data.get("current", {})
        if not current:
            return None
        return {
            "temperature": current.get("temp", 0),
            "condition": current.get("condition_raw", current.get("condition", "unknown")),
            "humidity": current.get("humidity", 0),
            "wind_speed": current.get("wind_speed", 0),
            "rain_probability": data.get("daily", [{}])[0].get("rain", 0) if data.get("daily") else 0,
        }

    def get_ai_farming_advice(self, weather_data, lang="en"):
        if not weather_data:
            return ""
        from models.crop import Crop
        from flask import session
        try:
            user_id = session.get("user_id")
            crops = Crop.find_by_user(user_id) if user_id else []
            crop_names = ", ".join([c.get("crop_name", "") for c in crops]) if crops else "general crops"
            temp = weather_data.get("temp", 0)
            humidity = weather_data.get("humidity", 0)
            condition = weather_data.get("condition_raw", weather_data.get("condition", "unknown"))
            prompt = (
                f"Given current weather: {temp}C, {humidity}% humidity, {condition}. "
                f"Farmer is growing: {crop_names}. "
                f"Provide 2-3 short actionable farming tips in {'Tamil' if lang == 'ta' else 'English'}."
            )
            from services.ai_service import AIService
            ai = AIService()
            return ai.get_response(prompt)
        except Exception:
            return ""

    def clear_cache(self, district="", town=""):
        if district and town:
            key = self._cache_key(district, town)
            self.cache.pop(key, None)
        else:
            self.cache.clear()

    CONDITION_MAP = {
        1000: "sunny", 1003: "cloudy", 1006: "cloudy", 1009: "cloudy",
        1030: "mist", 1063: "rain", 1066: "snow", 1069: "sleet",
        1072: "drizzle", 1087: "thunderstorm", 1114: "snow", 1117: "snow",
        1135: "fog", 1147: "fog", 1150: "drizzle", 1153: "drizzle",
        1168: "drizzle", 1171: "drizzle", 1180: "rain", 1183: "rain",
        1186: "rain", 1189: "rain", 1192: "rain", 1195: "rain",
        1198: "rain", 1201: "rain", 1204: "sleet", 1207: "sleet",
        1210: "snow", 1213: "snow", 1216: "snow", 1219: "snow",
        1222: "snow", 1225: "snow", 1237: "snow", 1240: "rain",
        1243: "rain", 1246: "rain", 1249: "sleet", 1252: "sleet",
        1255: "snow", 1258: "snow", 1261: "snow", 1264: "snow",
        1273: "thunderstorm", 1276: "thunderstorm", 1279: "thunderstorm",
        1282: "thunderstorm",
    }

    def _get_condition(self, code):
        return self.CONDITION_MAP.get(code, "cloudy")

    def fetch_all(self, district, town):
        cached = self._get_cached(district, town)
        if cached:
            return cached

        query = f"{town},{district},India"
        results = {}

        try:
            url = f"{self.base_url}/forecast.json"
            params = {"key": self.api_key, "q": query, "days": 7, "aqi": "no", "alerts": "yes"}
            resp = requests.get(url, params=params, timeout=10)
            if resp.status_code == 200:
                d = resp.json()
                results["current"] = self._parse_current(d)
                results["uv"] = d.get("current", {}).get("uv")
                results["hourly"] = self._parse_hourly(d)
                results["daily"] = self._parse_daily(d)
            else:
                err_data = resp.json()
                err_msg = err_data.get("error", {}).get("message", f"API returned {resp.status_code}")
                results["error"] = err_msg
                return results
        except requests.Timeout:
            results["error"] = "Weather API timed out. Please try again."
            return results
        except Exception as e:
            results["error"] = f"Failed to fetch weather: {str(e)}"
            return results

        self._set_cache(district, town, results)
        return results

    def _parse_current(self, d):
        location = d.get("location", {})
        current = d.get("current", {})
        cond = current.get("condition", {})
        today = d.get("forecast", {}).get("forecastday", [{}])[0]
        astro = today.get("astro", {}) if today else {}

        def _to_epoch(time_str, date_str):
            if not time_str or not date_str:
                return 0
            try:
                dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %I:%M %p")
                return int(dt.timestamp())
            except ValueError:
                return 0

        date_str = today.get("date", "") if today else ""

        return {
            "temp": round(current.get("temp_c", 0)),
            "feels_like": round(current.get("feelslike_c", 0)),
            "condition": self._get_condition(cond.get("code", 1000)),
            "condition_raw": cond.get("text", ""),
            "icon": self._map_icon(cond.get("code", 1000), current.get("is_day", 1)),
            "humidity": current.get("humidity", 0),
            "pressure": current.get("pressure_mb", 0),
            "visibility": int(current.get("vis_km", 0) * 1000),
            "wind_speed": round(current.get("wind_kph", 0), 1),
            "wind_deg": current.get("wind_degree", 0),
            "clouds": current.get("cloud", 0),
            "rain_1h": 0,
            "rain_3h": current.get("precip_mm", 0),
            "sunrise": _to_epoch(astro.get("sunrise", ""), date_str),
            "sunset": _to_epoch(astro.get("sunset", ""), date_str),
            "lat": location.get("lat", 0),
            "lon": location.get("lon", 0),
            "dt": int(datetime.now().timestamp()),
        }

    def _map_icon(self, code, is_day):
        day_map = {1000: "01d", 1003: "02d", 1006: "03d", 1009: "04d",
                   1030: "50d", 1063: "10d", 1087: "11d", 1135: "50d",
                   1150: "09d", 1153: "09d", 1180: "10d", 1183: "10d",
                   1186: "10d", 1189: "10d", 1192: "10d", 1195: "10d",
                   1240: "10d", 1243: "10d", 1246: "10d", 1273: "11d",
                   1276: "11d"}
        night_map = {k: v.replace("d", "n") for k, v in day_map.items()}
        m = day_map if is_day else night_map
        return m.get(code, "01d" if is_day else "01n")

    def _parse_hourly(self, d):
        days = d.get("forecast", {}).get("forecastday", [])
        result = []
        now = datetime.now()
        for day in days:
            for h in day.get("hour", []):
                h_dt = datetime.strptime(h.get("time", ""), "%Y-%m-%d %H:%M") if h.get("time") else now
                if h_dt < now - timedelta(hours=1):
                    continue
                cond = h.get("condition", {})
                result.append({
                    "time": h_dt.strftime("%I %p").lstrip("0"),
                    "temp": round(h.get("temp_c", 0)),
                    "humidity": h.get("humidity", 0),
                    "rain": h.get("chance_of_rain", 0),
                    "condition": self._get_condition(cond.get("code", 1000)),
                    "icon": self._map_icon(cond.get("code", 1000), h.get("is_day", 1)),
                })
                if len(result) >= 24:
                    return result
        return result

    def _parse_daily(self, d):
        days = d.get("forecast", {}).get("forecastday", [])
        result = []
        for day in days[:7]:
            d_data = day.get("day", {})
            cond = d_data.get("condition", {})
            dt_obj = datetime.strptime(day.get("date", ""), "%Y-%m-%d") if day.get("date") else datetime.now()
            result.append({
                "date": day.get("date", ""),
                "day_name": dt_obj.strftime("%a"),
                "temp_min": round(d_data.get("mintemp_c", 0)),
                "temp_max": round(d_data.get("maxtemp_c", 0)),
                "humidity": d_data.get("avghumidity", 0),
                "rain": d_data.get("daily_chance_of_rain", 0),
                "condition": self._get_condition(cond.get("code", 1000)),
                "icon": self._map_icon(cond.get("code", 1000), 1),
            })
        return result
