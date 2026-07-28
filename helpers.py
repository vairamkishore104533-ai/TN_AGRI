import json
import os
from datetime import datetime, date

def json_serialize(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    return str(obj)

def parse_date(date_str):
    if not date_str:
        return None
    formats = ["%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None

def get_current_season():
    month = datetime.now().month
    if 6 <= month <= 10:
        return "kharif"
    elif 11 <= month <= 3:
        return "rabi"
    else:
        return "summer"

def get_season_name(season_key, lang="en"):
    from utils.translations import get_text
    key = f"season_{season_key}"
    return get_text(key, lang) if get_text(key, lang) != key else season_key.capitalize()

def get_soil_types():
    return [
        "alluvial", "black", "red", "laterite", "sandy", "clay", "loamy"
    ]

def get_crop_list():
    return [
        "paddy", "wheat", "cotton", "sugarcane", "coconut", "banana",
        "tomato", "brinjal", "chilli", "groundnut", "sunflower",
        "maize", "millets", "turmeric", "tapioca"
    ]

def get_expense_categories():
    return ["seeds", "fertilizer", "labour", "transport", "machinery", "other"]

def get_districts():
    return [
        "Ariyalur", "Chengalpattu", "Chennai", "Coimbatore", "Cuddalore",
        "Dharmapuri", "Dindigul", "Erode", "Kallakurichi", "Kanchipuram",
        "Karur", "Krishnagiri", "Madurai", "Mayiladuthurai", "Nagapattinam",
        "Namakkal", "Nilgiris", "Perambalur", "Pudukkottai", "Ramanathapuram",
        "Ranipet", "Salem", "Sivaganga", "Tenkasi", "Thanjavur", "Theni",
        "Thoothukudi", "Tiruchirappalli", "Tirunelveli", "Tirupathur",
        "Tiruppur", "Tiruvallur", "Tiruvannamalai", "Tiruvarur",
        "Vellore", "Viluppuram", "Virudhunagar"
    ]

def get_mock_weather():
    return {
        "temperature": 32,
        "humidity": 68,
        "wind_speed": 12,
        "rain_probability": 30,
        "condition": "partly_cloudy",
        "forecast": [
            {"day": "Mon", "temp": 32, "rain": 30},
            {"day": "Tue", "temp": 31, "rain": 40},
            {"day": "Wed", "temp": 33, "rain": 20},
            {"day": "Thu", "temp": 34, "rain": 10},
            {"day": "Fri", "temp": 32, "rain": 50},
            {"day": "Sat", "temp": 30, "rain": 60},
            {"day": "Sun", "temp": 31, "rain": 35},
        ]
    }

def get_mock_market_prices():
    return [
        {"crop": "Paddy", "price": 22, "market": "Thanjavur Regulated Market", "district": "Thanjavur", "trend": "up", "best_time": "October-December"},
        {"crop": "Coconut", "price": 35, "market": "Pollachi Market", "district": "Coimbatore", "trend": "stable", "best_time": "Year round"},
        {"crop": "Banana", "price": 28, "market": "Rasipuram Market", "district": "Namakkal", "trend": "up", "best_time": "January-March"},
        {"crop": "Sugarcane", "price": 3.5, "market": "Erode Market", "district": "Erode", "trend": "stable", "best_time": "November-February"},
        {"crop": "Tomato", "price": 18, "market": "Thally Market", "district": "Krishnagiri", "trend": "down", "best_time": "April-June"},
        {"crop": "Groundnut", "price": 45, "market": "Tiruppur Market", "district": "Tiruppur", "trend": "up", "best_time": "February-April"},
        {"crop": "Cotton", "price": 62, "market": "Salem Market", "district": "Salem", "trend": "stable", "best_time": "March-May"},
        {"crop": "Chilli", "price": 55, "market": "Virudhunagar Market", "district": "Virudhunagar", "trend": "up", "best_time": "January-March"},
    ]

def get_mock_schemes():
    return [
        {
            "name": "Pradhan Mantri Fasal Bima Yojana",
            "benefits": "Comprehensive crop insurance against natural calamities, pests, and diseases.",
            "eligibility": "All farmers growing notified crops in notified areas.",
            "documents": "Aadhaar Card, Land Records, Bank Account Details",
            "link": "https://pmfby.gov.in"
        },
        {
            "name": "PM-KISAN Scheme",
            "benefits": "Annual financial benefit of Rs. 6000 to farmer families.",
            "eligibility": "All landholding farmer families.",
            "documents": "Aadhaar Card, Land Records, Bank Account",
            "link": "https://pmkisan.gov.in"
        },
        {
            "name": "Tamil Nadu Organic Farming Policy",
            "benefits": "Subsidy for organic certification, training, and marketing support.",
            "eligibility": "Farmers willing to practice organic farming.",
            "documents": "Land Records, Application Form, Farm Plan",
            "link": "https://www.tn.gov.in"
        },
        {
            "name": "National Agriculture Market (e-NAM)",
            "benefits": "Online trading platform for better price discovery.",
            "eligibility": "All farmers registered with APMC.",
            "documents": "Aadhaar, Bank Account, Mobile Number",
            "link": "https://www.enam.gov.in"
        },
        {
            "name": "Tamil Nadu Micro Irrigation Scheme",
            "benefits": "Subsidy up to 80% on drip and sprinkler irrigation systems.",
            "eligibility": "Small and marginal farmers in Tamil Nadu.",
            "documents": "Land Records, Aadhaar, Bank Details",
            "link": "https://www.tn.gov.in"
        },
        {
            "name": "Soil Health Card Scheme",
            "benefits": "Free soil testing and customized fertilizer recommendations.",
            "eligibility": "All farmers.",
            "documents": "Land Records, Farmer ID",
            "link": "https://soilhealth.dac.gov.in"
        },
    ]
