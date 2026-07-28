from flask import Blueprint, render_template, session, request
from utils.auth import login_required
from utils.helpers import get_current_season, get_mock_weather, get_season_name
from models.crop import Crop
from models.expense import Expense
from models.notification import Notification
from models.user import User
from services.weather_service import WeatherService

dashboard_bp = Blueprint("dashboard", __name__)

DISTRICT_ZONES = {
    "Cauvery Delta Zone": [
        "Thanjavur", "Tiruvarur", "Nagapattinam", "Mayiladuthurai",
    ],
    "North Eastern Zone": [
        "Chennai", "Chengalpattu", "Kancheepuram", "Tiruvallur",
        "Cuddalore", "Villupuram", "Kallakurichi", "Vellore",
        "Ranipet", "Tirupattur", "Tiruvannamalai",
    ],
    "Western Zone": [
        "Coimbatore", "Tiruppur", "Erode", "Karur",
        "Namakkal", "Dindigul", "Theni",
    ],
    "Southern Zone": [
        "Madurai", "Virudhunagar", "Thoothukudi", "Tirunelveli",
        "Tenkasi", "Sivaganga", "Ramanathapuram", "Pudukkottai",
    ],
    "Hilly Zone": ["Nilgiris"],
    "High Rainfall Zone": ["Kanniyakumari"],
}

ZONE_INFO = {
    "Cauvery Delta Zone": {
        "description": "The Cauvery Delta region is the traditional rice bowl of Tamil Nadu. Fertile alluvial and clay soils, fed by the Cauvery River network, make this zone ideal for intensive paddy cultivation.",
        "ta_description": "காவிரி டெல்டா பகுதி தமிழ்நாட்டின் பாரம்பரிய நெற்களஞ்சியமாகும். வளமான வண்டல் மற்றும் களிமண் மண் காவிரி ஆற்றின் நீர்ப்பாசன வசதியுடன் தீவிர நெல் சாகுபடிக்கு ஏற்றது.",
        "soil": "Alluvial, Clay, Saline",
        "ta_soil": "வண்டல் மண், களிமண், உவர் மண்",
        "major_crops": "Paddy, Sugarcane, Banana, Pulses, Groundnut",
        "ta_major_crops": "நெல், கரும்பு, வாழை, பயறு வகைகள், நிலக்கடலை",
        "climate": "Tropical — Hot and humid. Temperature: 25–37°C. Rainfall: 900–1100 mm.",
        "ta_climate": "வெப்பமண்டலம் — வெப்பம் மற்றும் ஈரப்பதம். வெப்பநிலை: 25–37°C. மழைப்பொழிவு: 900–1100 மிமீ.",
        "icon": "fas fa-water",
        "color": "#0d9488",
    },
    "North Eastern Zone": {
        "description": "This zone covers the northern coastal plains and interior districts, featuring red sandy loams, clay loams, and coastal alluvium with diverse agricultural production.",
        "ta_description": "இந்த மண்டலம் வடக்கு கடலோர சமவெளிகள் மற்றும் உள்நாட்டு மாவட்டங்களை உள்ளடக்கியது. சிவப்பு மணற்களி, களிமண் மற்றும் கடலோர வண்டல் மண் ஆகியவற்றைக் கொண்டுள்ளது.",
        "soil": "Red Sandy Loam, Clay Loam, Coastal Alluvium, Laterite",
        "ta_soil": "சிவப்பு மணற்களி, களிமண், கடலோர வண்டல் மண், சிகப்பு மண்",
        "major_crops": "Paddy, Sugarcane, Groundnut, Vegetables, Mango, Cashew",
        "ta_major_crops": "நெல், கரும்பு, நிலக்கடலை, காய்கறிகள், மாம்பழம், முந்திரி",
        "climate": "Sub-tropical — Moderate. Temperature: 22–35°C. Rainfall: 900–1200 mm.",
        "ta_climate": "துணை வெப்பமண்டலம் — மிதமான. வெப்பநிலை: 22–35°C. மழைப்பொழிவு: 900–1200 மிமீ.",
        "icon": "fas fa-cloud-sun",
        "color": "#2563eb",
    },
    "Western Zone": {
        "description": "The Western zone covers the rain-shadow region of the Western Ghats with red loam, black soils, and mixed soils, supporting cotton, oilseeds, and horticulture.",
        "ta_description": "மேற்கு மண்டலம் மேற்குத் தொடர்ச்சி மலையின் மழைநிழல் பகுதியை உள்ளடக்கியது. சிவப்பு மண், கருப்பு மண் மற்றும் கலப்பு மண் பருத்தி, எண்ணெய் வித்துக்கள் மற்றும் தோட்டக்கலைக்கு துணைபுரிகிறது.",
        "soil": "Red Loam, Black Soil, Mixed Soil, Laterite",
        "ta_soil": "சிவப்பு மண், கருப்பு மண், கலப்பு மண், சிகப்பு மண்",
        "major_crops": "Cotton, Maize, Sorghum, Turmeric, Coconut, Millets",
        "ta_major_crops": "பருத்தி, மக்காச்சோளம், சோளம், மஞ்சள், தேங்காய், சிறுதானியங்கள்",
        "climate": "Semi-arid tropical — Hot and dry. Temperature: 24–39°C. Rainfall: 600–900 mm.",
        "ta_climate": "அரை வறண்ட வெப்பமண்டலம் — வெப்பம் மற்றும் உலர்ந்த. வெப்பநிலை: 24–39°C. மழைப்பொழிவு: 600–900 மிமீ.",
        "icon": "fas fa-sun",
        "color": "#d97706",
    },
    "Southern Zone": {
        "description": "The Southern zone covers the southern plains with red sandy soils, deep red soils, and black cotton soils, supporting cotton, chillies, and paddy cultivation.",
        "ta_description": "தெற்கு மண்டலம் சிவப்பு மண், ஆழமான சிவப்பு மண் மற்றும் கருப்பு பருத்தி மண் பகுதிகளை உள்ளடக்கியது. பருத்தி, மிளகாய் மற்றும் நெல் சாகுபடிக்கு துணைபுரிகிறது.",
        "soil": "Red Sandy Soil, Deep Red Soil, Black Cotton Soil, Coastal Alluvium",
        "ta_soil": "சிவப்பு மணல் மண், ஆழமான சிவப்பு மண், கருப்பு பருத்தி மண், கடலோர வண்டல் மண்",
        "major_crops": "Cotton, Chillies, Paddy, Groundnut, Sugarcane, Mango",
        "ta_major_crops": "பருத்தி, மிளகாய், நெல், நிலக்கடலை, கரும்பு, மாம்பழம்",
        "climate": "Tropical — Hot and moderately humid. Temperature: 25–36°C. Rainfall: 700–1100 mm.",
        "ta_climate": "வெப்பமண்டலம் — வெப்பம் மற்றும் மிதமான ஈரப்பதம். வெப்பநிலை: 25–36°C. மழைப்பொழிவு: 700–1100 மிமீ.",
        "icon": "fas fa-leaf",
        "color": "#059669",
    },
    "Hilly Zone": {
        "description": "The Nilgiris district features a unique hilly terrain with red loamy, laterite, and peaty forest soils, ideal for plantation crops like tea, coffee, and spices.",
        "ta_description": "நீலகிரி மாவட்டம் சிவப்பு மண், சிகப்பு மண் மற்றும் கரி காட்டு மண் ஆகியவற்றுடன் தனித்துவமான மலைப்பகுதியாகும். தேயிலை, காபி மற்றும் மசாலா பயிர்களுக்கு ஏற்றது.",
        "soil": "Red Loamy Soil, Laterite, Peaty Forest Soil",
        "ta_soil": "சிவப்பு மண், சிகப்பு மண், கரி காட்டு மண்",
        "major_crops": "Tea, Coffee, Spices, Vegetables, Fruits",
        "ta_major_crops": "தேயிலை, காபி, மசாலா பொருட்கள், காய்கறிகள், பழங்கள்",
        "climate": "Montane — Cool and humid. Temperature: 10–25°C. Rainfall: 1200–2000 mm.",
        "ta_climate": "மலைகாலநிலை — குளிர் மற்றும் ஈரப்பதம். வெப்பநிலை: 10–25°C. மழைப்பொழிவு: 1200–2000 மிமீ.",
        "icon": "fas fa-mountain",
        "color": "#7c3aed",
    },
    "High Rainfall Zone": {
        "description": "Kanniyakumari district receives the highest rainfall in Tamil Nadu from both monsoons, with deep red loam and coastal alluvium supporting lush vegetation.",
        "ta_description": "கன்னியாகுமரி மாவட்டம் இரு பருவமழைகளிலிருந்தும் அதிக மழைப்பொழிவைப் பெறுகிறது. ஆழமான சிவப்பு மண் மற்றும் கடலோர வண்டல் மண் பசுமையான தாவரங்களை வளர்க்கிறது.",
        "soil": "Deep Red Loam, Saline Coastal Alluvium, Clay Loam",
        "ta_soil": "ஆழமான சிவப்பு மண், உவர் கடலோர வண்டல் மண், களிமண்",
        "major_crops": "Rubber, Coconut, Tapioca, Pepper, Banana, Cloves",
        "ta_major_crops": "ரப்பர், தேங்காய், மரவள்ளி, மிளகு, வாழை, கிராம்பு",
        "climate": "Tropical — High rainfall. Temperature: 22–33°C. Rainfall: 1500–2500 mm.",
        "ta_climate": "வெப்பமண்டலம் — அதிக மழைப்பொழிவு. வெப்பநிலை: 22–33°C. மழைப்பொழிவு: 1500–2500 மிமீ.",
        "icon": "fas fa-umbrella",
        "color": "#0891b2",
    },
}

ALL_DISTRICTS = [
    "Ariyalur", "Chengalpattu", "Chennai", "Coimbatore",
    "Cuddalore", "Dharmapuri", "Dindigul", "Erode",
    "Kallakurichi", "Kancheepuram", "Kanniyakumari", "Karur",
    "Krishnagiri", "Madurai", "Mayiladuthurai", "Nagapattinam",
    "Namakkal", "Nilgiris", "Perambalur", "Pudukkottai",
    "Ramanathapuram", "Ranipet", "Salem", "Sivaganga",
    "Tenkasi", "Thanjavur", "Theni", "Thoothukudi",
    "Tiruchirappalli", "Tirunelveli", "Tirupattur", "Tiruppur",
    "Tiruvallur", "Tiruvannamalai", "Tiruvarur", "Vellore",
    "Villupuram", "Virudhunagar",
]

# Extend zone mapping for districts listed but not in user's zone definitions
_EXTRA_DISTRICT_ZONES = {
    "Cauvery Delta Zone": ["Ariyalur", "Perambalur", "Tiruchirappalli"],
    "Western Zone": ["Dharmapuri", "Krishnagiri", "Salem"],
}


def get_zone_for_district(district_name):
    for zone, districts in DISTRICT_ZONES.items():
        if district_name in districts:
            return zone
    for zone, districts in _EXTRA_DISTRICT_ZONES.items():
        if district_name in districts:
            return zone
    return None


@dashboard_bp.route("/dashboard")
@login_required
def index():
    user_id = session.get("user_id")
    lang = session.get("lang", "en")
    username = session.get("username", "Farmer")

    selected_district = request.args.get("district", "").strip()
    if selected_district and selected_district not in ALL_DISTRICTS:
        selected_district = ""
    if selected_district:
        session["district"] = selected_district
    else:
        selected_district = session.get("district", "")
    if not selected_district:
        user = User.find_by_id(user_id)
        if user and user.district and user.district in ALL_DISTRICTS:
            selected_district = user.district
            session["district"] = selected_district

    zone = None
    zone_info = None
    if selected_district:
        zone = get_zone_for_district(selected_district)
        zone_info = ZONE_INFO.get(zone)

    season_key = get_current_season()
    season = get_season_name(season_key, lang)

    weather_data = {}
    ai_advice = ""
    if selected_district:
        weather_service = WeatherService()
        weather_data = weather_service.get_current_weather(district=selected_district)
        ai_advice = weather_service.get_ai_farming_advice(weather_data, lang) if weather_data else ""

    crop_count = Crop.count_by_user(user_id)
    expense_summary = Expense.get_summary(user_id)
    unread_notifs = Notification.count_unread(user_id)

    tips = {
        "en": [
            "Water your crops early morning or late evening to reduce evaporation.",
            "Monitor soil moisture regularly to avoid over-watering.",
            "Use organic pesticides for healthier crop growth.",
            "Practice crop rotation to maintain soil fertility.",
            "Keep farm equipment clean and well-maintained.",
        ],
        "ta": [
            "ஆவியாவதை குறைக்க காலை அல்லது மாலையில் பயிர்களுக்கு நீர் பாய்ச்சவும்.",
            "அதிக நீர் ஊற்றுவதை தவிர்க்க மண்ணின் ஈரப்பதத்தை தவறாமல் கண்காணிக்கவும்.",
            "ஆரோக்கியமான பயிர் வளர்ச்சிக்கு இயற்கை பூச்சிக்கொல்லிகளைப் பயன்படுத்தவும்.",
            "மண் வளத்தை பராமரிக்க பயிர் சுழற்சியை கடைப்பிடிக்கவும்.",
            "விவசாய கருவிகளை சுத்தமாகவும் பராமரிப்பாகவும் வைத்திருக்கவும்.",
        ],
    }

    if zone_info:
        zone_tips_en = [
            f"Your region ({zone}) is ideal for {zone_info.get('major_crops', 'diverse crops')}.",
            f"Predominant soil types: {zone_info.get('soil', 'varied soils')}.",
            "Follow local agricultural extension office recommendations for best results.",
        ]
        zone_tips_ta = [
            f"உங்கள் பகுதி ({zone}) {zone_info.get('ta_major_crops', 'பல்வேறு பயிர்கள்')} சாகுபடிக்கு ஏற்றது.",
            f"முக்கிய மண் வகைகள்: {zone_info.get('ta_soil', 'பல்வேறு மண்')}.",
            "சிறந்த முடிவுகளுக்கு உள்ளூர் வேளாண் விரிவாக்க மைய பரிந்துரைகளை பின்பற்றவும்.",
        ]
        tips["en"] = zone_tips_en + tips["en"]
        tips["ta"] = zone_tips_ta + tips["ta"]

    return render_template(
        "dashboard.html",
        username=username,
        season=season,
        weather=weather_data,
        ai_advice=ai_advice,
        crop_count=crop_count,
        income=expense_summary.get("income", 0),
        expenses=expense_summary.get("expense", 0),
        unread_notifications=unread_notifs,
        unread_count=unread_notifs,
        tips=tips.get(lang, tips["en"]),
        lang=lang,
        selected_district=selected_district,
        zone=zone,
        zone_info=zone_info,
        all_districts=ALL_DISTRICTS,
    )
