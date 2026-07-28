from flask import Blueprint, render_template, request, jsonify, session
from utils.auth import login_required
from models.irrigation import Irrigation
from utils.helpers import get_districts
from datetime import datetime
import traceback
import json

irrigation_bp = Blueprint("irrigation", __name__)

CROPS = [
    "Paddy", "Banana", "Sugarcane", "Cotton", "Groundnut", "Coconut",
    "Turmeric", "Maize", "Tomato", "Brinjal", "Chilli", "Onion",
    "Millets", "Black Gram", "Green Gram", "Mango", "Tapioca",
    "Sunflower", "Sesame", "Horse Gram", "Red Gram", "Cashew",
    "Papaya", "Guava", "Okra", "Cabbage", "Cauliflower", "Carrot",
    "Beans", "Drumstick", "Watermelon", "Pumpkin", "Other"
]

CROPS_TA = [
    "நெல்", "வாழை", "கரும்பு", "பருத்தி", "வேர்க்கடலை", "தேங்காய்",
    "மஞ்சள்", "சோளம்", "தக்காளி", "கத்திரி", "மிளகாய்", "வெங்காயம்",
    "சிறுதானியங்கள்", "உளுந்து", "பச்சைப்பயறு", "மாம்பழம்", "மரவள்ளி",
    "சூரியகாந்தி", "எள்", "கொள்ளு", "துவரை", "முந்திரி",
    "பப்பாளி", "கொய்யா", "வெண்டை", "முட்டைகோஸ்", "காலிஃபிளவர்", "கேரட்",
    "பீன்ஸ்", "முருங்கை", "தர்பூசணி", "பூசணி", "மற்றவை"
]

CROP_WATER = {
    "Paddy": {"water_en": "1200–1500 mm/season. Standing water required.", "water_ta": "1200–1500 மிமீ/பருவம். தேங்கும் நீர் தேவை.", "duration_en": "120–150 days", "duration_ta": "120–150 நாட்கள்", "districts_en": "Thanjavur, Tiruvallur, Cuddalore, Nagapattinam", "districts_ta": "தஞ்சாவூர், திருவள்ளூர், கடலூர், நாகப்பட்டினம்"},
    "Banana": {"water_en": "900–1200 mm/season. Consistent moisture needed.", "water_ta": "900–1200 மிமீ/பருவம். நிலையான ஈரப்பதம் தேவை.", "duration_en": "10–12 months", "duration_ta": "10–12 மாதங்கள்", "districts_en": "Tiruchirappalli, Theni, Thoothukudi", "districts_ta": "திருச்சி, தேனி, தூத்துக்குடி"},
    "Sugarcane": {"water_en": "2000–2500 mm/season. High water requirement.", "water_ta": "2000–2500 மிமீ/பருவம். அதிக நீர் தேவை.", "duration_en": "10–12 months", "duration_ta": "10–12 மாதங்கள்", "districts_en": "Vellore, Dharmapuri, Salem, Erode", "districts_ta": "வேலூர், தர்மபுரி, சேலம், ஈரோடு"},
    "Cotton": {"water_en": "500–800 mm/season. Moderate water requirement.", "water_ta": "500–800 மிமீ/பருவம். மிதமான நீர் தேவை.", "duration_en": "150–180 days", "duration_ta": "150–180 நாட்கள்", "districts_en": "Coimbatore, Salem, Virudhunagar, Ramanathapuram", "districts_ta": "கோயம்புத்தூர், சேலம், விருதுநகர், இராமநாதபுரம்"},
    "Groundnut": {"water_en": "400–500 mm/season. Low-moderate water.", "water_ta": "400–500 மிமீ/பருவம். குறைந்த-மிதமான நீர்.", "duration_en": "90–120 days", "duration_ta": "90–120 நாட்கள்", "districts_en": "Tiruvannamalai, Vellore, Cuddalore", "districts_ta": "திருவண்ணாமலை, வேலூர், கடலூர்"},
    "Coconut": {"water_en": "1000–1500 mm/year. Tolerates drought once mature.", "water_ta": "1000–1500 மிமீ/ஆண்டு. முதிர்ந்த பின் வறட்சியை தாங்கும்.", "duration_en": "Year-round (perennial)", "duration_ta": "ஆண்டு முழுவதும் (பல ஆண்டு)", "districts_en": "Kanyakumari, Thanjavur, Tiruppur, Pollachi", "districts_ta": "கன்னியாகுமரி, தஞ்சாவூர், திருப்பூர், பொள்ளாச்சி"},
    "Turmeric": {"water_en": "800–1000 mm/season. Consistent moisture critical.", "water_ta": "800–1000 மிமீ/பருவம். நிலையான ஈரப்பதம் முக்கியமானது.", "duration_en": "7–9 months", "duration_ta": "7–9 மாதங்கள்", "districts_en": "Erode, Salem, Namakkal", "districts_ta": "ஈரோடு, சேலம், நாமக்கல்"},
    "Maize": {"water_en": "500–800 mm/season. Sensitive to water stress at flowering.", "water_ta": "500–800 மிமீ/பருவம். பூக்கும் போது நீர் அழுத்தத்திற்கு உணர்திறன்.", "duration_en": "90–110 days", "duration_ta": "90–110 நாட்கள்", "districts_en": "Perambalur, Tiruchi, Dindigul", "districts_ta": "பெரம்பலூர், திருச்சி, திண்டுக்கல்"},
    "Tomato": {"water_en": "400–600 mm/season. Regular watering essential.", "water_ta": "400–600 மிமீ/பருவம். வழக்கமான நீர்ப்பாசனம் அவசியம்.", "duration_en": "70–90 days", "duration_ta": "70–90 நாட்கள்", "districts_en": "Krishnagiri, Dharmapuri, Madurai, Theni", "districts_ta": "கிருஷ்ணகிரி, தர்மபுரி, மதுரை, தேனி"},
    "Brinjal": {"water_en": "600–800 mm/season. Moderate water needs.", "water_ta": "600–800 மிமீ/பருவம். மிதமான நீர் தேவைகள்.", "duration_en": "100–120 days", "duration_ta": "100–120 நாட்கள்", "districts_en": "Coimbatore, Dindigul, Theni", "districts_ta": "கோயம்புத்தூர், திண்டுக்கல், தேனி"},
    "Chilli": {"water_en": "500–700 mm/season. Avoid waterlogging.", "water_ta": "500–700 மிமீ/பருவம். நீர் தேக்கத்தை தவிர்க்கவும்.", "duration_en": "90–120 days", "duration_ta": "90–120 நாட்கள்", "districts_en": "Virudhunagar, Tuticorin, Ramanathapuram", "districts_ta": "விருதுநகர், தூத்துக்குடி, இராமநாதபுரம்"},
    "Onion": {"water_en": "350–550 mm/season. Reduce water at maturity.", "water_ta": "350–550 மிமீ/பருவம். முதிர்ச்சியில் நீரை குறைக்கவும்.", "duration_en": "90–120 days", "duration_ta": "90–120 நாட்கள்", "districts_en": "Tiruchirappalli, Perambalur, Dindigul", "districts_ta": "திருச்சி, பெரம்பலூர், திண்டுக்கல்"},
    "Millets": {"water_en": "300–450 mm/season. Drought-tolerant.", "water_ta": "300–450 மிமீ/பருவம். வறட்சியை தாங்கும்.", "duration_en": "75–120 days", "duration_ta": "75–120 நாட்கள்", "districts_en": "Dharmapuri, Krishnagiri, Salem", "districts_ta": "தர்மபுரி, கிருஷ்ணகிரி, சேலம்"},
    "Black Gram": {"water_en": "300–400 mm/season. Low water requirement.", "water_ta": "300–400 மிமீ/பருவம். குறைந்த நீர் தேவை.", "duration_en": "70–90 days", "duration_ta": "70–90 நாட்கள்", "districts_en": "Thanjavur, Tiruvallur, Cuddalore", "districts_ta": "தஞ்சாவூர், திருவள்ளூர், கடலூர்"},
    "Green Gram": {"water_en": "300–400 mm/season. Low water requirement.", "water_ta": "300–400 மிமீ/பருவம். குறைந்த நீர் தேவை.", "duration_en": "60–75 days", "duration_ta": "60–75 நாட்கள்", "districts_en": "Tiruvannamalai, Vellore, Salem", "districts_ta": "திருவண்ணாமலை, வேலூர், சேலம்"},
    "Mango": {"water_en": "600–1000 mm/year. Sensitive to water stress during flowering.", "water_ta": "600–1000 மிமீ/ஆண்டு. பூக்கும் போது நீர் அழுத்தத்திற்கு உணர்திறன்.", "duration_en": "4–5 months (seasonal)", "duration_ta": "4–5 மாதங்கள் (பருவகாலம்)", "districts_en": "Krishnagiri, Dharmapuri, Theni", "districts_ta": "கிருஷ்ணகிரி, தர்மபுரி, தேனி"},
    "Tapioca": {"water_en": "750–1000 mm/season. Moderate water needs.", "water_ta": "750–1000 மிமீ/பருவம். மிதமான நீர் தேவைகள்.", "duration_en": "8–10 months", "duration_ta": "8–10 மாதங்கள்", "districts_en": "Salem, Namakkal, Erode, Villupuram", "districts_ta": "சேலம், நாமக்கல், ஈரோடு, விழுப்புரம்"},
    "Sunflower": {"water_en": "400–600 mm/season. Drought-tolerant once established.", "water_ta": "400–600 மிமீ/பருவம். நிலைபெற்ற பின் வறட்சியை தாங்கும்.", "duration_en": "80–100 days", "duration_ta": "80–100 நாட்கள்", "districts_en": "Villupuram, Cuddalore, Tiruvannamalai", "districts_ta": "விழுப்புரம், கடலூர், திருவண்ணாமலை"},
    "Sesame": {"water_en": "350–450 mm/season. Low water requirement.", "water_ta": "350–450 மிமீ/பருவம். குறைந்த நீர் தேவை.", "duration_en": "75–90 days", "duration_ta": "75–90 நாட்கள்", "districts_en": "Ramanathapuram, Virudhunagar, Sivaganga", "districts_ta": "இராமநாதபுரம், விருதுநகர், சிவகங்கை"},
    "Horse Gram": {"water_en": "250–350 mm/season. Highly drought-tolerant.", "water_ta": "250–350 மிமீ/பருவம். மிகவும் வறட்சியை தாங்கும்.", "duration_en": "90–120 days", "duration_ta": "90–120 நாட்கள்", "districts_en": "Dharmapuri, Krishnagiri, Tiruvannamalai", "districts_ta": "தர்மபுரி, கிருஷ்ணகிரி, திருவண்ணாமலை"},
    "Red Gram": {"water_en": "400–600 mm/season. Moderate water needs.", "water_ta": "400–600 மிமீ/பருவம். மிதமான நீர் தேவைகள்.", "duration_en": "120–180 days", "duration_ta": "120–180 நாட்கள்", "districts_en": "Villupuram, Cuddalore, Tiruvannamalai", "districts_ta": "விழுப்புரம், கடலூர், திருவண்ணாமலை"},
    "Cashew": {"water_en": "500–800 mm/year. Drought-tolerant tree crop.", "water_ta": "500–800 மிமீ/ஆண்டு. வறட்சியை தாங்கும் மரப்பயிர்.", "duration_en": "Year-round (perennial)", "duration_ta": "ஆண்டு முழுவதும் (பல ஆண்டு)", "districts_en": "Cuddalore, Villupuram, Kanyakumari", "districts_ta": "கடலூர், விழுப்புரம், கன்னியாகுமரி"},
    "Papaya": {"water_en": "800–1200 mm/year. Requires consistent moisture.", "water_ta": "800–1200 மிமீ/ஆண்டு. நிலையான ஈரப்பதம் தேவை.", "duration_en": "8–10 months", "duration_ta": "8–10 மாதங்கள்", "districts_en": "Coimbatore, Madurai, Theni", "districts_ta": "கோயம்புத்தூர், மதுரை, தேனி"},
    "Guava": {"water_en": "500–800 mm/year. Tolerates dry spells.", "water_ta": "500–800 மிமீ/ஆண்டு. வறண்ட காலங்களை தாங்கும்.", "duration_en": "Year-round (perennial)", "duration_ta": "ஆண்டு முழுவதும் (பல ஆண்டு)", "districts_en": "Tiruchirappalli, Madurai, Theni", "districts_ta": "திருச்சி, மதுரை, தேனி"},
    "Okra": {"water_en": "400–600 mm/season. Regular watering important.", "water_ta": "400–600 மிமீ/பருவம். வழக்கமான நீர்ப்பாசனம் முக்கியமானது.", "duration_en": "50–70 days", "duration_ta": "50–70 நாட்கள்", "districts_en": "Erode, Salem, Coimbatore", "districts_ta": "ஈரோடு, சேலம், கோயம்புத்தூர்"},
    "Cabbage": {"water_en": "500–700 mm/season. Consistent moisture for head formation.", "water_ta": "500–700 மிமீ/பருவம். தலை உருவாவதற்கு நிலையான ஈரப்பதம்.", "duration_en": "70–100 days", "duration_ta": "70–100 நாட்கள்", "districts_en": "Krishnagiri, Dharmapuri, Nilgiris", "districts_ta": "கிருஷ்ணகிரி, தர்மபுரி, நீலகிரி"},
    "Cauliflower": {"water_en": "500–700 mm/season. Sensitive to moisture stress.", "water_ta": "500–700 மிமீ/பருவம். ஈரப்பத அழுத்தத்திற்கு உணர்திறன்.", "duration_en": "70–120 days", "duration_ta": "70–120 நாட்கள்", "districts_en": "Krishnagiri, Dharmapuri, Nilgiris", "districts_ta": "கிருஷ்ணகிரி, தர்மபுரி, நீலகிரி"},
    "Carrot": {"water_en": "400–600 mm/season. Even moisture for root quality.", "water_ta": "400–600 மிமீ/பருவம். வேர் தரத்திற்கு சீரான ஈரப்பதம்.", "duration_en": "60–80 days", "duration_ta": "60–80 நாட்கள்", "districts_en": "Krishnagiri, Nilgiris, Dindigul", "districts_ta": "கிருஷ்ணகிரி, நீலகிரி, திண்டுக்கல்"},
    "Beans": {"water_en": "300–500 mm/season. Moderate water needs.", "water_ta": "300–500 மிமீ/பருவம். மிதமான நீர் தேவைகள்.", "duration_en": "50–70 days", "duration_ta": "50–70 நாட்கள்", "districts_en": "Krishnagiri, Dharmapuri, Theni", "districts_ta": "கிருஷ்ணகிரி, தர்மபுரி, தேனி"},
    "Drumstick": {"water_en": "400–600 mm/year. Drought-tolerant once established.", "water_ta": "400–600 மிமீ/ஆண்டு. நிலைபெற்ற பின் வறட்சியை தாங்கும்.", "duration_en": "Year-round (perennial)", "duration_ta": "ஆண்டு முழுவதும் (பல ஆண்டு)", "districts_en": "Virudhunagar, Ramanathapuram, Thoothukudi", "districts_ta": "விருதுநகர், இராமநாதபுரம், தூத்துக்குடி"},
    "Watermelon": {"water_en": "500–700 mm/season. Deep watering at roots.", "water_ta": "500–700 மிமீ/பருவம். வேர்களில் ஆழமான நீர்ப்பாசனம்.", "duration_en": "75–90 days", "duration_ta": "75–90 நாட்கள்", "districts_en": "Thanjavur, Tiruvallur, Cuddalore", "districts_ta": "தஞ்சாவூர், திருவள்ளூர், கடலூர்"},
    "Pumpkin": {"water_en": "500–700 mm/season. Moderate water needs.", "water_ta": "500–700 மிமீ/பருவம். மிதமான நீர் தேவைகள்.", "duration_en": "90–120 days", "duration_ta": "90–120 நாட்கள்", "districts_en": "Dindigul, Theni, Madurai", "districts_ta": "திண்டுக்கல், தேனி, மதுரை"},
    "Other": {"water_en": "Varies by crop. Consult local agricultural officer.", "water_ta": "பயிருக்கு ஏற்ப மாறுபடும். உள்ளூர் வேளாண் அலுவலரை அணுகவும்.", "duration_en": "Varies", "duration_ta": "மாறுபடும்", "districts_en": "Varies by crop", "districts_ta": "பயிருக்கு ஏற்ப மாறுபடும்"},
}

DISTRICTS = [
    {"en": "Ariyalur", "ta": "அரியலூர்", "climate_en": "Semi-arid", "climate_ta": "மித வறட்சி", "rainfall": "850 mm", "water_en": "Moderate — Canal and borewell dependent", "water_ta": "மிதமான — கால்வாய் மற்றும் போர்வெல் சார்ந்தது", "crops_en": "Paddy, Sugarcane, Groundnut", "crops_ta": "நெல், கரும்பு, வேர்க்கடலை"},
    {"en": "Chengalpattu", "ta": "செங்கல்பட்டு", "climate_en": "Coastal tropical", "climate_ta": "கடற்கரை வெப்ப மண்டலம்", "rainfall": "1200 mm", "water_en": "Good — Tanks and canals", "water_ta": "நல்ல — குளங்கள் மற்றும் கால்வாய்கள்", "crops_en": "Paddy, Sugarcane, Groundnut", "crops_ta": "நெல், கரும்பு, வேர்க்கடலை"},
    {"en": "Chennai", "ta": "சென்னை", "climate_en": "Coastal tropical", "climate_ta": "கடற்கரை வெப்ப மண்டலம்", "rainfall": "1400 mm", "water_en": "Urban — Limited agriculture", "water_ta": "நகர்ப்புறம் — வரையறுக்கப்பட்ட விவசாயம்", "crops_en": "Vegetables, Fruits", "crops_ta": "காய்கறிகள், பழங்கள்"},
    {"en": "Coimbatore", "ta": "கோயம்புத்தூர்", "climate_en": "Moderate tropical", "climate_ta": "மிதமான வெப்ப மண்டலம்", "rainfall": "700 mm", "water_en": "Moderate — Borewell and tank fed", "water_ta": "மிதமான — போர்வெல் மற்றும் குளம் சார்ந்தது", "crops_en": "Cotton, Maize, Vegetables, Coconut", "crops_ta": "பருத்தி, சோளம், காய்கறிகள், தேங்காய்"},
    {"en": "Cuddalore", "ta": "கடலூர்", "climate_en": "Coastal tropical", "climate_ta": "கடற்கரை வெப்ப மண்டலம்", "rainfall": "1100 mm", "water_en": "Good — Canals and tanks", "water_ta": "நல்ல — கால்வாய்கள் மற்றும் குளங்கள்", "crops_en": "Paddy, Cashew, Groundnut, Sugarcane", "crops_ta": "நெல், முந்திரி, வேர்க்கடலை, கரும்பு"},
    {"en": "Dharmapuri", "ta": "தர்மபுரி", "climate_en": "Semi-arid", "climate_ta": "மித வறட்சி", "rainfall": "800 mm", "water_en": "Low — Rainfed predominant", "water_ta": "குறைவு — மழை சார்ந்த விவசாயம் முதன்மை", "crops_en": "Mango, Tomato, Millets, Groundnut", "crops_ta": "மாம்பழம், தக்காளி, சிறுதானியங்கள், வேர்க்கடலை"},
    {"en": "Dindigul", "ta": "திண்டுக்கல்", "climate_en": "Semi-arid to moderate", "climate_ta": "மித வறட்சி முதல் மிதமான", "rainfall": "750 mm", "water_en": "Moderate — Borewell dependent", "water_ta": "மிதமான — போர்வெல் சார்ந்தது", "crops_en": "Onion, Tomato, Coconut, Flowers", "crops_ta": "வெங்காயம், தக்காளி, தேங்காய், பூக்கள்"},
    {"en": "Erode", "ta": "ஈரோடு", "climate_en": "Semi-arid", "climate_ta": "மித வறட்சி", "rainfall": "650 mm", "water_en": "Moderate — Canals and borewells", "water_ta": "மிதமான — கால்வாய்கள் மற்றும் போர்வெல்கள்", "crops_en": "Turmeric, Sugarcane, Coconut, Banana", "crops_ta": "மஞ்சள், கரும்பு, தேங்காய், வாழை"},
    {"en": "Kallakurichi", "ta": "கள்ளக்குறிச்சி", "climate_en": "Semi-arid", "climate_ta": "மித வறட்சி", "rainfall": "900 mm", "water_en": "Moderate — Tanks and borewells", "water_ta": "மிதமான — குளங்கள் மற்றும் போர்வெல்கள்", "crops_en": "Paddy, Sugarcane, Groundnut, Millets", "crops_ta": "நெல், கரும்பு, வேர்க்கடலை, சிறுதானியங்கள்"},
    {"en": "Kanchipuram", "ta": "காஞ்சிபுரம்", "climate_en": "Coastal tropical", "climate_ta": "கடற்கரை வெப்ப மண்டலம்", "rainfall": "1100 mm", "water_en": "Good — Tanks and canals", "water_ta": "நல்ல — குளங்கள் மற்றும் கால்வாய்கள்", "crops_en": "Paddy, Sugarcane, Groundnut, Vegetables", "crops_ta": "நெல், கரும்பு, வேர்க்கடலை, காய்கறிகள்"},
    {"en": "Karur", "ta": "கரூர்", "climate_en": "Semi-arid", "climate_ta": "மித வறட்சி", "rainfall": "700 mm", "water_en": "Moderate — Borewell and canal", "water_ta": "மிதமான — போர்வெல் மற்றும் கால்வாய்", "crops_en": "Banana, Sugarcane, Coconut, Groundnut", "crops_ta": "வாழை, கரும்பு, தேங்காய், வேர்க்கடலை"},
    {"en": "Krishnagiri", "ta": "கிருஷ்ணகிரி", "climate_en": "Semi-arid", "climate_ta": "மித வறட்சி", "rainfall": "750 mm", "water_en": "Low — Rainfed, some tanks", "water_ta": "குறைவு — மழை சார்ந்த, சில குளங்கள்", "crops_en": "Mango, Tomato, Vegetables, Millets", "crops_ta": "மாம்பழம், தக்காளி, காய்கறிகள், சிறுதானியங்கள்"},
    {"en": "Madurai", "ta": "மதுரை", "climate_en": "Semi-arid", "climate_ta": "மித வறட்சி", "rainfall": "850 mm", "water_en": "Moderate — Tank and borewell", "water_ta": "மிதமான — குளம் மற்றும் போர்வெல்", "crops_en": "Paddy, Sugarcane, Cotton, Vegetables", "crops_ta": "நெல், கரும்பு, பருத்தி, காய்கறிகள்"},
    {"en": "Mayiladuthurai", "ta": "மயிலாடுதுறை", "climate_en": "Coastal tropical", "climate_ta": "கடற்கரை வெப்ப மண்டலம்", "rainfall": "1000 mm", "water_en": "Good — Cauvery delta, canal network", "water_ta": "நல்ல — காவிரி டெல்டா, கால்வாய் வலையமைப்பு", "crops_en": "Paddy, Banana, Sugarcane", "crops_ta": "நெல், வாழை, கரும்பு"},
    {"en": "Nagapattinam", "ta": "நாகப்பட்டினம்", "climate_en": "Coastal tropical", "climate_ta": "கடற்கரை வெப்ப மண்டலம்", "rainfall": "1200 mm", "water_en": "Good — Cauvery delta region", "water_ta": "நல்ல — காவிரி டெல்டா பகுதி", "crops_en": "Paddy, Sugarcane, Banana, Pulses", "crops_ta": "நெல், கரும்பு, வாழை, பயறு வகைகள்"},
    {"en": "Namakkal", "ta": "நாமக்கல்", "climate_en": "Semi-arid", "climate_ta": "மித வறட்சி", "rainfall": "700 mm", "water_en": "Moderate — Borewell dependent", "water_ta": "மிதமான — போர்வெல் சார்ந்தது", "crops_en": "Tapioca, Turmeric, Sugarcane, Coconut", "crops_ta": "மரவள்ளி, மஞ்சள், கரும்பு, தேங்காய்"},
    {"en": "Nilgiris", "ta": "நீலகிரி", "climate_en": "Cool mountain", "climate_ta": "குளிர் மலை", "rainfall": "1800 mm", "water_en": "High — Perennial streams", "water_ta": "அதிகம் — நிரந்தர நீரோடைகள்", "crops_en": "Tea, Coffee, Vegetables, Spices", "crops_ta": "தேயிலை, காபி, காய்கறிகள், மசாலாப் பொருட்கள்"},
    {"en": "Perambalur", "ta": "பெரம்பலூர்", "climate_en": "Semi-arid", "climate_ta": "மித வறட்சி", "rainfall": "800 mm", "water_en": "Low — Rainfed, limited irrigation", "water_ta": "குறைவு — மழை சார்ந்த, வரையறுக்கப்பட்ட பாசனம்", "crops_en": "Maize, Paddy, Groundnut, Millets", "crops_ta": "சோளம், நெல், வேர்க்கடலை, சிறுதானியங்கள்"},
    {"en": "Pudukkottai", "ta": "புதுக்கோட்டை", "climate_en": "Semi-arid", "climate_ta": "மித வறட்சி", "rainfall": "800 mm", "water_en": "Low — Tank and borewell", "water_ta": "குறைவு — குளம் மற்றும் போர்வெல்", "crops_en": "Paddy, Groundnut, Millets, Cotton", "crops_ta": "நெல், வேர்க்கடலை, சிறுதானியங்கள், பருத்தி"},
    {"en": "Ramanathapuram", "ta": "இராமநாதபுரம்", "climate_en": "Arid coastal", "climate_ta": "வறண்ட கடற்கரை", "rainfall": "650 mm", "water_en": "Low — Groundwater scarce", "water_ta": "குறைவு — நிலத்தடி நீர் பற்றாக்குறை", "crops_en": "Cotton, Chilli, Groundnut, Millets", "crops_ta": "பருத்தி, மிளகாய், வேர்க்கடலை, சிறுதானியங்கள்"},
    {"en": "Ranipet", "ta": "ராணிப்பேட்டை", "climate_en": "Semi-arid", "climate_ta": "மித வறட்சி", "rainfall": "850 mm", "water_en": "Moderate — Tanks and borewells", "water_ta": "மிதமான — குளங்கள் மற்றும் போர்வெல்கள்", "crops_en": "Paddy, Sugarcane, Groundnut, Mango", "crops_ta": "நெல், கரும்பு, வேர்க்கடலை, மாம்பழம்"},
    {"en": "Salem", "ta": "சேலம்", "climate_en": "Semi-arid", "climate_ta": "மித வறட்சி", "rainfall": "800 mm", "water_en": "Moderate — Borewell and tank", "water_ta": "மிதமான — போர்வெல் மற்றும் குளம்", "crops_en": "Mango, Tapioca, Turmeric, Sugarcane", "crops_ta": "மாம்பழம், மரவள்ளி, மஞ்சள், கரும்பு"},
    {"en": "Sivaganga", "ta": "சிவகங்கை", "climate_en": "Semi-arid", "climate_ta": "மித வறட்சி", "rainfall": "750 mm", "water_en": "Low — Tank dependent", "water_ta": "குறைவு — குளம் சார்ந்தது", "crops_en": "Paddy, Cotton, Millets, Groundnut", "crops_ta": "நெல், பருத்தி, சிறுதானியங்கள், வேர்க்கடலை"},
    {"en": "Tenkasi", "ta": "தென்காசி", "climate_en": "Tropical moderate", "climate_ta": "வெப்ப மிதமான", "rainfall": "900 mm", "water_en": "Moderate — Rivers and tanks", "water_ta": "மிதமான — ஆறுகள் மற்றும் குளங்கள்", "crops_en": "Paddy, Banana, Coconut, Sugarcane", "crops_ta": "நெல், வாழை, தேங்காய், கரும்பு"},
    {"en": "Thanjavur", "ta": "தஞ்சாவூர்", "climate_en": "Coastal delta", "climate_ta": "கடற்கரை டெல்டா", "rainfall": "950 mm", "water_en": "Good — Cauvery delta, extensive canals", "water_ta": "நல்ல — காவிரி டெல்டா, விரிவான கால்வாய்கள்", "crops_en": "Paddy (major), Banana, Sugarcane, Coconut", "crops_ta": "நெல் (முதன்மை), வாழை, கரும்பு, தேங்காய்"},
    {"en": "Theni", "ta": "தேனி", "climate_en": "Moderate tropical", "climate_ta": "மிதமான வெப்ப மண்டலம்", "rainfall": "900 mm", "water_en": "Good — Perennial rivers, canals", "water_ta": "நல்ல — நிரந்தர ஆறுகள், கால்வாய்கள்", "crops_en": "Banana, Sugarcane, Coconut, Vegetables", "crops_ta": "வாழை, கரும்பு, தேங்காய், காய்கறிகள்"},
    {"en": "Thoothukudi", "ta": "தூத்துக்குடி", "climate_en": "Arid coastal", "climate_ta": "வறண்ட கடற்கரை", "rainfall": "600 mm", "water_en": "Low — Groundwater saline in many areas", "water_ta": "குறைவு — பல பகுதிகளில் நிலத்தடி நீர் உவர்", "crops_en": "Cotton, Chilli, Groundnut, Millets", "crops_ta": "பருத்தி, மிளகாய், வேர்க்கடலை, சிறுதானியங்கள்"},
    {"en": "Tiruchirappalli", "ta": "திருச்சிராப்பள்ளி", "climate_en": "Semi-arid", "climate_ta": "மித வறட்சி", "rainfall": "850 mm", "water_en": "Moderate — Cauvery river, canals", "water_ta": "மிதமான — காவிரி ஆறு, கால்வாய்கள்", "crops_en": "Paddy, Banana, Sugarcane, Onion", "crops_ta": "நெல், வாழை, கரும்பு, வெங்காயம்"},
    {"en": "Tirunelveli", "ta": "திருநெல்வேலி", "climate_en": "Semi-arid tropical", "climate_ta": "மித வறட்சி வெப்ப மண்டலம்", "rainfall": "800 mm", "water_en": "Moderate — Tank and river based", "water_ta": "மிதமான — குளம் மற்றும் ஆறு சார்ந்தது", "crops_en": "Paddy, Cotton, Sugarcane, Coconut", "crops_ta": "நெல், பருத்தி, கரும்பு, தேங்காய்"},
    {"en": "Tirupathur", "ta": "திருப்பத்தூர்", "climate_en": "Semi-arid", "climate_ta": "மித வறட்சி", "rainfall": "800 mm", "water_en": "Low — Rainfed predominant", "water_ta": "குறைவு — மழை சார்ந்த விவசாயம் முதன்மை", "crops_en": "Millets, Groundnut, Mango, Vegetables", "crops_ta": "சிறுதானியங்கள், வேர்க்கடலை, மாம்பழம், காய்கறிகள்"},
    {"en": "Tiruppur", "ta": "திருப்பூர்", "climate_en": "Semi-arid", "climate_ta": "மித வறட்சி", "rainfall": "650 mm", "water_en": "Low — Borewell dependent", "water_ta": "குறைவு — போர்வெல் சார்ந்தது", "crops_en": "Coconut, Sugarcane, Banana, Vegetables", "crops_ta": "தேங்காய், கரும்பு, வாழை, காய்கறிகள்"},
    {"en": "Tiruvallur", "ta": "திருவள்ளூர்", "climate_en": "Coastal tropical", "climate_ta": "கடற்கரை வெப்ப மண்டலம்", "rainfall": "1100 mm", "water_en": "Good — Tanks and canals", "water_ta": "நல்ல — குளங்கள் மற்றும் கால்வாய்கள்", "crops_en": "Paddy, Sugarcane, Groundnut, Pulses", "crops_ta": "நெல், கரும்பு, வேர்க்கடலை, பயறு வகைகள்"},
    {"en": "Tiruvannamalai", "ta": "திருவண்ணாமலை", "climate_en": "Semi-arid", "climate_ta": "மித வறட்சி", "rainfall": "900 mm", "water_en": "Moderate — Tank and borewell", "water_ta": "மிதமான — குளம் மற்றும் போர்வெல்", "crops_en": "Paddy, Groundnut, Millets, Sugarcane", "crops_ta": "நெல், வேர்க்கடலை, சிறுதானியங்கள், கரும்பு"},
    {"en": "Tiruvarur", "ta": "திருவாரூர்", "climate_en": "Coastal delta", "climate_ta": "கடற்கரை டெல்டா", "rainfall": "1000 mm", "water_en": "Good — Cauvery delta, abundant water", "water_ta": "நல்ல — காவிரி டெல்டா, ஏராளமான நீர்", "crops_en": "Paddy (major), Banana, Sugarcane", "crops_ta": "நெல் (முதன்மை), வாழை, கரும்பு"},
    {"en": "Vellore", "ta": "வேலூர்", "climate_en": "Semi-arid", "climate_ta": "மித வறட்சி", "rainfall": "850 mm", "water_en": "Moderate — Tanks and borewells", "water_ta": "மிதமான — குளங்கள் மற்றும் போர்வெல்கள்", "crops_en": "Paddy, Sugarcane, Groundnut, Mango", "crops_ta": "நெல், கரும்பு, வேர்க்கடலை, மாம்பழம்"},
    {"en": "Viluppuram", "ta": "விழுப்புரம்", "climate_en": "Semi-arid coastal", "climate_ta": "மித வறட்சி கடற்கரை", "rainfall": "1000 mm", "water_en": "Moderate — Tanks and canals", "water_ta": "மிதமான — குளங்கள் மற்றும் கால்வாய்கள்", "crops_en": "Paddy, Sugarcane, Groundnut, Cashew", "crops_ta": "நெல், கரும்பு, வேர்க்கடலை, முந்திரி"},
    {"en": "Virudhunagar", "ta": "விருதுநகர்", "climate_en": "Arid to semi-arid", "climate_ta": "வறண்ட முதல் மித வறட்சி", "rainfall": "700 mm", "water_en": "Low — Rainfed predominant", "water_ta": "குறைவு — மழை சார்ந்து முதன்மை", "crops_en": "Cotton, Chilli, Groundnut, Millets", "crops_ta": "பருத்தி, மிளகாய், வேர்க்கடலை, சிறுதானியங்கள்"},
]

SEASONS = [
    {"id": "kuruvai", "en": "Kuruvai", "ta": "குறுவை", "months_en": "June to September", "months_ta": "ஜூன் முதல் செப்டம்பர் வரை", "rainfall_en": "South-West Monsoon (400–600 mm)", "rainfall_ta": "தென்மேற்கு பருவமழை (400–600 மிமீ)", "water_en": "Moderate — Monsoon dependent", "water_ta": "மிதமான — பருவமழை சார்ந்தது"},
    {"id": "samba", "en": "Samba", "ta": "சம்பா", "months_en": "August to January", "months_ta": "ஆகஸ்ட் முதல் ஜனவரி வரை", "rainfall_en": "North-East Monsoon (500–800 mm)", "rainfall_ta": "வடகிழக்கு பருவமழை (500–800 மிமீ)", "water_en": "Good — Dual monsoon support", "water_ta": "நல்ல — இரட்டை பருவமழை ஆதரவு"},
    {"id": "thaladi", "en": "Thaladi", "ta": "தாளடி", "months_en": "September to February", "months_ta": "செப்டம்பர் முதல் பிப்ரவரி வரை", "rainfall_en": "Post-monsoon (300–500 mm)", "rainfall_ta": "பருவமழைக்குப் பின் (300–500 மிமீ)", "water_en": "Moderate — Residual moisture", "water_ta": "மிதமான — எஞ்சிய ஈரப்பதம்"},
    {"id": "navarai", "en": "Navarai", "ta": "நவரை", "months_en": "December to March", "months_ta": "டிசம்பர் முதல் மார்ச் வரை", "rainfall_en": "Dry season, irrigation-dependent", "rainfall_ta": "வறண்ட காலம், பாசனம் சார்ந்தது", "water_en": "Low — Fully irrigation dependent", "water_ta": "குறைவு — முழுமையாக பாசனம் சார்ந்தது"},
    {"id": "summer", "en": "Summer", "ta": "கோடை", "months_en": "March to June", "months_ta": "மார்ச் முதல் ஜூன் வரை", "rainfall_en": "Dry, hot season (<200 mm)", "rainfall_ta": "வறண்ட, வெப்பமான காலம் (<200 மிமீ)", "water_en": "Very low — Heavy irrigation needed", "water_ta": "மிகவும் குறைவு — அதிக நீர்ப்பாசனம் தேவை"},
    {"id": "rainy", "en": "Rainy Season", "ta": "மழைக்காலம்", "months_en": "October to December", "months_ta": "அக்டோபர் முதல் டிசம்பர் வரை", "rainfall_en": "Heavy rainfall (800–1200 mm)", "rainfall_ta": "அதிக மழைப்பொழிவு (800–1200 மிமீ)", "water_en": "High — Reduce irrigation frequency", "water_ta": "அதிகம் — நீர்ப்பாசன அதிர்வெண்ணை குறைக்கவும்"},
    {"id": "winter", "en": "Winter", "ta": "குளிர்காலம்", "months_en": "January to February", "months_ta": "ஜனவரி முதல் பிப்ரவரி வரை", "rainfall_en": "Low rainfall (100–200 mm)", "rainfall_ta": "குறைந்த மழைப்பொழிவு (100–200 மிமீ)", "water_en": "Low — Light irrigation sufficient", "water_ta": "குறைவு — மெல்லிய நீர்ப்பாசனம் போதுமானது"},
    {"id": "custom", "en": "Custom Season", "ta": "தனிப்பயன் பருவம்", "months_en": "As specified", "months_ta": "குறிப்பிட்டபடி", "rainfall_en": "Varies by region", "rainfall_ta": "பகுதிக்கு ஏற்ப மாறுபடும்", "water_en": "Varies — Check weather forecast", "water_ta": "மாறுபடும் — வானிலை முன்னறிவிப்பை சரிபார்க்கவும்"},
]

IRRIGATION_METHODS = [
    {"id": "drip", "en": "Drip Irrigation", "ta": "சொட்டு நீர் பாசனம்", "explanation_en": "Water applied directly to root zone through emitters at low pressure. 80–90% efficiency. Best for vegetables, fruits, and row crops. Reduces water use by 40–60% compared to flood irrigation.", "explanation_ta": "நீர் நேரடியாக வேர் பகுதிக்கு சொட்டு முனைகள் மூலம் குறைந்த அழுத்தத்தில் வழங்கப்படுகிறது. 80–90% திறன். காய்கறிகள், பழங்கள் மற்றும் வரிசை பயிர்களுக்கு சிறந்தது. வெள்ள பாசனத்துடன் ஒப்பிடும்போது நீர் பயன்பாட்டை 40–60% குறைக்கிறது."},
    {"id": "flood", "en": "Flood Irrigation", "ta": "வெள்ளப் பாசனம்", "explanation_en": "Entire field submerged in water. 40–50% efficiency. Traditional for paddy. High water losses through evaporation and percolation. Requires level fields.", "explanation_ta": "முழு வயலும் நீரில் மூழ்கும். 40–50% திறன். நெல்லுக்கு பாரம்பரிய முறை. ஆவியாதல் மற்றும் கசிவு மூலம் அதிக நீர் இழப்பு. சமநில நிலம் தேவை."},
    {"id": "sprinkler", "en": "Sprinkler Irrigation", "ta": "தெளிப்பு பாசனம்", "explanation_en": "Water sprayed over crops like rainfall through overhead sprinklers. 60–70% efficiency. Suitable for vegetables, pulses, and plantation crops. Good for sloping or sandy soils.", "explanation_ta": "நீர் மேல்நிலை தெளிப்பான்கள் மூலம் மழை போல பயிர்களுக்கு தெளிக்கப்படுகிறது. 60–70% திறன். காய்கறிகள், பயறுகள் மற்றும் தோட்டப்பயிர்களுக்கு ஏற்றது. சரிவு அல்லது மணல் மண்ணுக்கு நல்லது."},
    {"id": "rainfed", "en": "Rainfed Farming", "ta": "மழை சார்ந்த விவசாயம்", "explanation_en": "Crop cultivation depends entirely on rainfall. No irrigation infrastructure. Requires drought-tolerant crops. Moisture conservation practices essential. Suitable for semi-arid regions.", "explanation_ta": "பயிர் சாகுபடி முழுமையாக மழையை சார்ந்துள்ளது. நீர்ப்பாசன கட்டமைப்பு இல்லை. வறட்சியை தாங்கும் பயிர்கள் தேவை. ஈரப்பத பாதுகாப்பு நடைமுறைகள் அவசியம். மித வறட்சி பகுதிகளுக்கு ஏற்றது."},
    {"id": "furrow", "en": "Furrow Irrigation", "ta": "சால் பாசனம்", "explanation_en": "Water flows through furrows between crop rows. 50–60% efficiency. Common for row crops like cotton, maize, sugarcane. Reduced water use compared to flood irrigation. Better for medium-textured soils.", "explanation_ta": "நீர் பயிர் வரிசைகளுக்கு இடையே உள்ள சால்கள் வழியாக பாய்கிறது. 50–60% திறன். பருத்தி, சோளம், கரும்பு போன்ற வரிசை பயிர்களுக்கு பொதுவானது. வெள்ள பாசனத்துடன் ஒப்பிடும்போது குறைந்த நீர் பயன்பாடு. மிதமான அமைப்பு மண்ணுக்கு ஏற்றது."},
    {"id": "basin", "en": "Basin Irrigation", "ta": "குட்டை பாசனம்", "explanation_en": "Water applied to closed basins around plants. 40–50% efficiency. Common for orchards and tree crops. Good water distribution. Requires careful soil leveling.", "explanation_ta": "நீர் செடிகளைச் சுற்றி மூடிய குட்டைகளில் வழங்கப்படுகிறது. 40–50% திறன். பழத்தோட்டங்கள் மற்றும் மரப்பயிர்களுக்கு பொதுவானது. நல்ல நீர் பகிர்வு. கவனமான மண் சமன்படுத்துதல் தேவை."},
    {"id": "manual", "en": "Manual Irrigation", "ta": "கைமுறை பாசனம்", "explanation_en": "Watering done by hand using hose, bucket, or watering can. Labor-intensive. Suitable for small plots, kitchen gardens, and nurseries. Full control over water quantity per plant.", "explanation_ta": "குழாய், வாளி அல்லது நீர்ப்பாசன கேன் மூலம் கையால் நீர்ப்பாசனம். உழைப்பு மிகுந்தது. சிறிய நிலங்கள், சமையல் தோட்டங்கள் மற்றும் நாற்றங்கால்களுக்கு ஏற்றது. ஒவ்வொரு செடிக்கும் நீர் அளவின் மீது முழு கட்டுப்பாடு."},
    {"id": "other", "en": "Other", "ta": "மற்றவை", "explanation_en": "Any other irrigation method used locally. Consult your local agricultural officer for method-specific recommendations.", "explanation_ta": "உள்நாட்டில் பயன்படுத்தப்படும் வேறு ஏதேனும் நீர்ப்பாசன முறை. முறை சார்ந்த பரிந்துரைகளுக்கு உங்கள் உள்ளூர் வேளாண் அலுவலரை அணுகவும்."},
]


@irrigation_bp.route("/irrigation", methods=["GET"])
@login_required
def index():
    lang = session.get("lang", "en")
    user_id = session.get("user_id")
    stats = Irrigation.get_stats(user_id)
    history = Irrigation.find_by_user(user_id)
    crop_list = []
    for i, c in enumerate(CROPS):
        info = CROP_WATER.get(c, {"water_en": "", "water_ta": "", "duration_en": "", "duration_ta": "", "districts_en": "", "districts_ta": ""})
        crop_list.append({"en": c, "ta": CROPS_TA[i] if i < len(CROPS_TA) else c, **info})
    return render_template(
        "irrigation.html",
        crops=crop_list,
        crops_json=json.dumps(crop_list),
        districts=DISTRICTS,
        districts_json=json.dumps(DISTRICTS),
        seasons=SEASONS,
        seasons_json=json.dumps(SEASONS),
        irrigation_methods=IRRIGATION_METHODS,
        irrigation_json=json.dumps(IRRIGATION_METHODS),
        stats=stats,
        history=[h.to_dict() for h in history],
        lang=lang,
    )


@irrigation_bp.route("/api/irrigation/generate", methods=["POST"])
@login_required
def generate():
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"success": False, "error": "Invalid JSON in request body"}), 400

        crop = data.get("crop", "").strip()
        district = data.get("district", "").strip()
        season_id = data.get("season", "").strip()
        method_id = data.get("irrigation_method", "").strip()
        lang = session.get("lang", "en")

        if not crop:
            msg = "Please select a crop." if lang == "en" else "தயவுசெய்து ஒரு பயிரைத் தேர்ந்தெடுக்கவும்."
            return jsonify({"success": False, "error": msg}), 400
        if not district:
            msg = "Please select a district." if lang == "en" else "தயவுசெய்து ஒரு மாவட்டத்தைத் தேர்ந்தெடுக்கவும்."
            return jsonify({"success": False, "error": msg}), 400
        if not season_id:
            msg = "Please select an agricultural season." if lang == "en" else "தயவுசெய்து ஒரு விவசாய பருவத்தைத் தேர்ந்தெடுக்கவும்."
            return jsonify({"success": False, "error": msg}), 400
        if not method_id:
            msg = "Please select an irrigation method." if lang == "en" else "தயவுசெய்து ஒரு நீர்ப்பாசன முறையைத் தேர்ந்தெடுக்கவும்."
            return jsonify({"success": False, "error": msg}), 400

        season_name = season_id
        for s in SEASONS:
            if s["id"] == season_id:
                season_name = s["ta"] if lang == "ta" else s["en"]
                break

        method_name = method_id
        for m in IRRIGATION_METHODS:
            if m["id"] == method_id:
                method_name = m["ta"] if lang == "ta" else m["en"]
                break

        from services.ai_service import AIService
        ai = AIService()

        if lang == "ta":
            prompt = (
                f"நீங்கள் தமிழ்நாட்டின் முன்னணி நீர்ப்பாசன திட்டமிடல் நிபுணர். பின்வரும் தகவல்களின் அடிப்படையில் முழுமையான நீர்ப்பாசன திட்டத்தை உருவாக்கவும்.\n\n"
                f"பயிர்: {crop}\n"
                f"மாவட்டம்: {district}\n"
                f"விவசாய பருவம்: {season_name}\n"
                f"நீர்ப்பாசன முறை: {method_name}\n\n"
                f"பின்வரும் பகுதிகளை உள்ளடக்கிய முழுமையான அறிக்கையை உருவாக்கவும். ஒவ்வொரு பகுதியையும் ## தலைப்புடன் தொடங்கவும்:\n\n"
                f"## பயிர் சுருக்கம்\n"
                f"பயிர், மாவட்டம், பருவம், நீர்ப்பாசன முறை, மதிப்பிடப்பட்ட தினசரி நீர் தேவை (லிட்டரில்), வாராந்திர நீர் தேவை, மொத்த பருவகால நீர் தேவை, ஏக்கருக்கு நீர் தேவை ஆகியவற்றைக் காட்டவும். மதிப்புகள் தோராயமானவை மற்றும் வானிலை மற்றும் மண் நிலைகளைப் பொறுத்தது என்பதைக் குறிப்பிடவும்.\n\n"
                f"## நீர்ப்பாசன அட்டவணை\n"
                f"வளர்ச்சி நிலை, அதிர்வெண், கால அளவு, பரிந்துரைக்கப்பட்ட நேரம் ஆகியவற்றைக் கொண்ட அட்டவணையை உருவாக்கவும்.\n\n"
                f"## சிறந்த நீர்ப்பாசன நேரம்\n"
                f"பருவம், வெப்பநிலை மற்றும் நீர் பாதுகாப்பின் அடிப்படையில் சிறந்த நேரத்தை பரிந்துரைக்கவும் (அதிகாலை/மாலை). ஏன் இந்த நேரம் விரும்பப்படுகிறது என்பதை விளக்கவும்.\n\n"
                f"## நீர்ப்பாசன முறை ஆலோசனை\n"
                f"தேர்ந்தெடுக்கப்பட்ட {method_name} முறைக்கு குறிப்பிட்ட பரிந்துரைகளை வழங்கவும்.\n\n"
                f"## நீர் சேமிப்பு குறிப்புகள்\n"
                f"தழைக்கூளம், சொட்டு நீர் பாசனம், மழைநீர் சேகரிப்பு, வயல் சமன்படுத்துதல், நண்பகல் நீர்ப்பாசனத்தை தவிர்த்தல், கால்வாய் பராமரிப்பு போன்ற நடைமுறை பரிந்துரைகளை வழங்கவும்.\n\n"
                f"## பருவகால ஆலோசனை\n"
                f"தேர்ந்தெடுக்கப்பட்ட {season_name} பருவத்தின் அடிப்படையில் மழை எதிர்பார்ப்புகள், நீர்ப்பாசன மாற்றங்கள், நீர் பாதுகாப்பு நடவடிக்கைகள் பற்றி வழங்கவும்.\n\n"
                f"## வறட்சி மேலாண்மை\n"
                f"நீர் கிடைக்கும் தன்மை குறைவாக இருந்தால், குறைக்கப்பட்ட நீர்ப்பாசன அட்டவணை, முன்னுரிமை வளர்ச்சி நிலைகள், அவசர நீர்ப்பாசன நடைமுறைகள், ஈரப்பதம் தக்கவைப்பு நுட்பங்களை பரிந்துரைக்கவும்.\n\n"
                f"## பொதுவான விவசாயி தவறுகள்\n"
                f"அதிக நீர்ப்பாசனம், குறைந்த நீர்ப்பாசனம், நண்பகல் நீர்ப்பாசனம், மோசமான வடிகால், நீர் தேக்கம், மழையை புறக்கணித்தல் போன்றவற்றுக்கு எதிராக எச்சரிக்கவும்.\n\n"
                f"## மதிப்பிடப்பட்ட நீர் பயன்பாடு\n"
                f"மதிப்பிடப்பட்ட லிட்டர்/நாள், லிட்டர்/வாரம், லிட்டர்/பருவம், ஏக்கருக்கு நீர் பயன்பாடு ஆகியவற்றைக் காட்டவும். இவை AI உருவாக்கிய மதிப்பீடுகள் என்பதைக் குறிப்பிடவும்.\n\n"
                f"## AI குறிப்புகள்\n"
                f"நீர்ப்பாசனத்திற்கு முன் மண்ணின் ஈரப்பதத்தை கண்காணிக்கவும், மழைக்குப் பிறகு நீர்ப்பாசனத்தை சரிசெய்யவும், வேர்களைச் சுற்றி தேங்கும் நீரை தவிர்க்கவும், ஆவியாதலை குறைக்க தழைக்கூளம் பயன்படுத்தவும், நீர்ப்பாசன உபகரணங்களை தவறாமல் சரிபார்க்கவும் போன்ற AI பரிந்துரைகளை வழங்கவும்.\n\n"
                f"## நீர் பாதுகாப்பு மதிப்பெண்\n"
                f"தேர்ந்தெடுக்கப்பட்ட பயிர் மற்றும் நீர்ப்பாசன முறைக்கு 100-க்குள் AI உருவாக்கிய மதிப்பெண்ணை வழங்கவும். சுருக்கமான விளக்கத்தையும் சேர்க்கவும்.\n\n"
                f"தமிழ்நாடு விவசாயப் பல்கலைக்கழகம் மற்றும் தமிழ்நாடு வேளாண்மைத் துறை வழிகாட்டுதல்களைப் பின்பற்றவும். தமிழில் மட்டுமே பதிலளிக்கவும். உங்கள் பதிலில் மார்க் டவுன் வடிவமைப்பைப் பயன்படுத்தவும்."
            )
        else:
            prompt = (
                f"You are a leading irrigation planning expert for Tamil Nadu agriculture. Generate a comprehensive irrigation plan based on the following details.\n\n"
                f"Crop: {crop}\n"
                f"District: {district}\n"
                f"Agricultural Season: {season_name}\n"
                f"Irrigation Method: {method_name}\n\n"
                f"Generate a comprehensive report covering the following sections. Start each section with ## heading:\n\n"
                f"## Crop Summary\n"
                f"Display Crop, District, Season, Irrigation Method, Estimated Daily Water Requirement (in litres), Weekly Water Requirement, Total Seasonal Water Requirement, Water Requirement per Acre. Mention that values are approximate and depend on weather and soil conditions.\n\n"
                f"## Irrigation Schedule\n"
                f"Create a table with Growth Stage, Frequency, Duration, Recommended Time of Day.\n\n"
                f"## Best Irrigation Time\n"
                f"Recommend the best time based on season, temperature, and water conservation (Early Morning / Late Evening). Explain why.\n\n"
                f"## Irrigation Method Advice\n"
                f"Provide specific recommendations for the selected {method_name} method.\n\n"
                f"## Water Saving Tips\n"
                f"Provide practical recommendations: mulching, drip irrigation, rainwater harvesting, field leveling, avoiding midday irrigation, canal maintenance.\n\n"
                f"## Seasonal Advice\n"
                f"Based on the selected {season_name} season, provide rainfall expectations, irrigation adjustments, water conservation measures.\n\n"
                f"## Drought Management\n"
                f"If water availability is low, recommend reduced irrigation schedule, priority growth stages, emergency watering practices, moisture retention techniques.\n\n"
                f"## Common Farmer Mistakes\n"
                f"Warn against over-irrigation, under-irrigation, midday watering, poor drainage, waterlogging, ignoring rainfall.\n\n"
                f"## Estimated Water Usage\n"
                f"Display estimated litres per day, litres per week, litres per season, water usage per acre. Mention these are AI-generated estimates.\n\n"
                f"## AI Tips\n"
                f"Provide personalized suggestions: monitor soil moisture before watering, adjust irrigation after rainfall, avoid stagnant water around roots, use mulching to reduce evaporation, inspect irrigation equipment regularly.\n\n"
                f"## Water Conservation Score\n"
                f"Provide an AI-generated score out of 100 indicating how water-efficient the selected irrigation method + crop combination is. Include a brief explanation.\n\n"
                f"Follow Tamil Nadu Agricultural University and Tamil Nadu Agriculture Department guidelines. "
                f"Include specific advice relevant to {district} district, {season_name} season, and {method_name} method. "
                f"Use markdown formatting in your response. Reply only in English."
            )

        response = ai.get_response(prompt, lang)

        return jsonify({
            "success": True,
            "recommendation": response,
            "metadata": {
                "crop": crop,
                "district": district,
                "season": season_name,
                "irrigation_method": method_name,
            }
        })

    except Exception as e:
        print(f"[Irrigation Error] generate: {traceback.format_exc()}")
        try:
            lang = session.get("lang", "en")
        except Exception:
            lang = "en"
        msg = f"Server error: {type(e).__name__}: {str(e)}"
        return jsonify({"success": False, "error": msg}), 500


@irrigation_bp.route("/api/irrigation/save", methods=["POST"])
@login_required
def save():
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"success": False, "error": "Invalid JSON"}), 400

        user_id = session.get("user_id")
        lang = session.get("lang", "en")

        p = Irrigation()
        p.user_id = user_id
        p.crop = data.get("crop", "")
        p.district = data.get("district", "")
        p.season = data.get("season", "")
        p.irrigation_method = data.get("irrigation_method", "")
        p.recommendation = data.get("recommendation", "")
        p.language = data.get("language", lang)
        p.save()

        msg = "Irrigation plan saved successfully!" if lang == "en" else "நீர்ப்பாசன திட்டம் வெற்றிகரமாக சேமிக்கப்பட்டது!"
        return jsonify({"success": True, "message": msg})

    except Exception as e:
        print(f"[Irrigation Error] save: {traceback.format_exc()}")
        return jsonify({"success": False, "error": "Failed to save plan"}), 500


@irrigation_bp.route("/api/irrigation/history", methods=["GET"])
@login_required
def get_history():
    try:
        user_id = session.get("user_id")
        search_q = request.args.get("search", "").strip()
        if search_q:
            items = Irrigation.search_by_user(user_id, search_q)
        else:
            items = Irrigation.find_by_user(user_id)
        return jsonify({"success": True, "history": [h.to_dict() for h in items]})
    except Exception as e:
        print(f"[Irrigation Error] history: {traceback.format_exc()}")
        return jsonify({"success": False, "error": "Failed to load history"}), 500


@irrigation_bp.route("/api/irrigation/<plan_id>", methods=["DELETE"])
@login_required
def delete(plan_id):
    try:
        lang = session.get("lang", "en")
        p = Irrigation.find_by_id(plan_id)
        if not p:
            msg = "Plan not found." if lang == "en" else "திட்டம் கிடைக்கவில்லை."
            return jsonify({"success": False, "error": msg})
        p.delete()
        stats = Irrigation.get_stats(session.get("user_id"))
        msg = "Plan deleted successfully!" if lang == "en" else "திட்டம் வெற்றிகரமாக நீக்கப்பட்டது!"
        return jsonify({"success": True, "message": msg, "stats": stats})
    except Exception as e:
        print(f"[Irrigation Error] delete: {traceback.format_exc()}")
        return jsonify({"success": False, "error": "Failed to delete"}), 500


@irrigation_bp.route("/api/irrigation/export/<plan_id>", methods=["GET"])
@login_required
def export(plan_id):
    try:
        lang = session.get("lang", "en")
        p = Irrigation.find_by_id(plan_id)
        if not p:
            msg = "Plan not found." if lang == "en" else "திட்டம் கிடைக்கவில்லை."
            return jsonify({"success": False, "error": msg})

        fmt = request.args.get("format", "txt")
        username = session.get("username", "Farmer")
        lines = []
        lines.append("=" * 50)
        lines.append("IRRIGATION PLAN REPORT" if lang == "en" else "நீர்ப்பாசன திட்ட அறிக்கை")
        lines.append("=" * 50)
        lines.append(f"Farmer: {username}" if lang == "en" else f"விவசாயி: {username}")
        lines.append(f"Crop: {p.crop}" if lang == "en" else f"பயிர்: {p.crop}")
        lines.append(f"District: {p.district}" if lang == "en" else f"மாவட்டம்: {p.district}")
        lines.append(f"Season: {p.season}" if lang == "en" else f"பருவம்: {p.season}")
        lines.append(f"Irrigation Method: {p.irrigation_method}" if lang == "en" else f"நீர்ப்பாசன முறை: {p.irrigation_method}")
        lines.append(f"Date: {p.created_at.strftime('%Y-%m-%d %H:%M')}" if lang == "en" else f"தேதி: {p.created_at.strftime('%Y-%m-%d %H:%M')}")
        lines.append("")
        lines.append(p.recommendation)

        text_content = "\n".join(lines)

        if fmt == "csv":
            csv_lines = [
                "Field,Value",
                f"Crop,{p.crop}",
                f"District,{p.district}",
                f"Season,{p.season}",
                f"Irrigation Method,{p.irrigation_method}",
                f"Date,{p.created_at.strftime('%Y-%m-%d %H:%M')}",
            ]
            return jsonify({
                "success": True,
                "export": "\n".join(csv_lines),
                "filename": f"irrigation_{plan_id[:8]}.csv",
                "mime": "text/csv",
            })

        if fmt == "pdf":
            from fpdf import FPDF
            from fpdf.enums import XPos, YPos
            pdf = FPDF()
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.add_font("Arial", "", r"C:\Windows\Fonts\arial.ttf")
            pdf.add_font("Arial", "B", r"C:\Windows\Fonts\arialbd.ttf")
            pdf.set_font("Arial", "B", 16)
            title = "Irrigation Plan Report" if lang == "en" else "நீர்ப்பாசன திட்ட அறிக்கை"
            pdf.cell(0, 10, text=title, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
            pdf.set_font("Arial", "", 10)
            for line in text_content.split("\n"):
                pdf.set_x(pdf.l_margin)
                if line.startswith("=") or line.startswith("-"):
                    pdf.set_font("Arial", "", 10)
                elif any(line.startswith(x) for x in ["CROP", "IRRIGATION", "பயிர்", "நீர்ப்பாசன"]):
                    pdf.set_font("Arial", "B", 11)
                else:
                    pdf.set_font("Arial", "", 10)
                w = pdf.get_string_width(line) + 2
                if w > 190:
                    pdf.multi_cell(0, 5, text=line)
                else:
                    pdf.cell(0, 5, text=line, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            import base64
            output = bytes(pdf.output())
            return jsonify({
                "success": True,
                "export": base64.b64encode(output).decode("ascii"),
                "filename": f"irrigation_{plan_id[:8]}.pdf",
                "mime": "application/pdf",
                "encoding": "base64",
            })

        return jsonify({
            "success": True,
            "export": text_content,
            "filename": f"irrigation_{plan_id[:8]}.txt",
            "mime": "text/plain",
        })

    except Exception as e:
        print(f"[Irrigation Error] export: {traceback.format_exc()}")
        return jsonify({"success": False, "error": "Failed to export"}), 500


@irrigation_bp.route("/api/irrigation/stats", methods=["GET"])
@login_required
def get_stats():
    user_id = session.get("user_id")
    stats = Irrigation.get_stats(user_id)
    return jsonify({"success": True, "stats": stats})
