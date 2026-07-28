from flask import Blueprint, render_template, request, jsonify, session
from utils.auth import login_required
from models.fertilizer import Fertilizer
from utils.helpers import get_districts
from datetime import datetime
import traceback
import json

fertilizer_bp = Blueprint("fertilizer", __name__)

SEASONS = [
    {"id": "kuruvai", "en": "Kuruvai", "ta": "குறுவை", "desc_en": "June–September. Short-term paddy cultivation.", "desc_ta": "ஜூன்–செப்டம்பர். குறுகிய கால நெல் சாகுபடி.", "months_en": "June to September", "months_ta": "ஜூன் முதல் செப்டம்பர் வரை", "rainfall_en": "South-West Monsoon (400–600 mm)", "rainfall_ta": "தென்மேற்கு பருவமழை (400–600 மிமீ)", "crops_en": "Paddy, Black Gram, Green Gram", "crops_ta": "நெல், உளுந்து, பச்சைப்பயறு"},
    {"id": "samba", "en": "Samba", "ta": "சம்பா", "desc_en": "August–January. Long-duration paddy season.", "desc_ta": "ஆகஸ்ட்–ஜனவரி. நீண்ட கால நெல் பருவம்.", "months_en": "August to January", "months_ta": "ஆகஸ்ட் முதல் ஜனவரி வரை", "rainfall_en": "North-East Monsoon (500–800 mm)", "rainfall_ta": "வடகிழக்கு பருவமழை (500–800 மிமீ)", "crops_en": "Paddy (long-duration varieties), Sugarcane, Banana", "crops_ta": "நெல் (நீண்டகால ரகங்கள்), கரும்பு, வாழை"},
    {"id": "thaladi", "en": "Thaladi", "ta": "தாளடி", "desc_en": "September–February. Late paddy season.", "desc_ta": "செப்டம்பர்–பிப்ரவரி. தாமதமான நெல் பருவம்.", "months_en": "September to February", "months_ta": "செப்டம்பர் முதல் பிப்ரவரி வரை", "rainfall_en": "Post-monsoon (300–500 mm)", "rainfall_ta": "பருவமழைக்குப் பின் (300–500 மிமீ)", "crops_en": "Paddy (short-duration), Pulses", "crops_ta": "நெல் (குறுகியகாலம்), பயறு வகைகள்"},
    {"id": "navarai", "en": "Navarai", "ta": "நவரை", "desc_en": "December–March. Summer paddy season.", "desc_ta": "டிசம்பர்–மார்ச். கோடை நெல் பருவம்.", "months_en": "December to March", "months_ta": "டிசம்பர் முதல் மார்ச் வரை", "rainfall_en": "Dry season, irrigation-dependent", "rainfall_ta": "வறண்ட காலம், பாசனம் சார்ந்தது", "crops_en": "Paddy, Groundnut, Millets", "crops_ta": "நெல், வேர்க்கடலை, சிறுதானியங்கள்"},
    {"id": "summer", "en": "Summer", "ta": "கோடை", "desc_en": "March–June. Suitable for vegetables and pulses.", "desc_ta": "மார்ச்–ஜூன். காய்கறிகள் மற்றும் பயறு வகைகளுக்கு ஏற்றது.", "months_en": "March to June", "months_ta": "மார்ச் முதல் ஜூன் வரை", "rainfall_en": "Dry, hot season (<200 mm)", "rainfall_ta": "வறண்ட, வெப்பமான காலம் (<200 மிமீ)", "crops_en": "Vegetables (Tomato, Brinjal, Chilli), Pulses, Cotton, Maize", "crops_ta": "காய்கறிகள் (தக்காளி, கத்திரி, மிளகாய்), பயறுகள், பருத்தி, சோளம்"},
    {"id": "rainy", "en": "Rainy Season", "ta": "மழைக்காலம்", "desc_en": "October–December. North-east monsoon period.", "desc_ta": "அக்டோபர்–டிசம்பர். வடகிழக்கு பருவமழை காலம்.", "months_en": "October to December", "months_ta": "அக்டோபர் முதல் டிசம்பர் வரை", "rainfall_en": "Heavy rainfall (800–1200 mm)", "rainfall_ta": "அதிக மழைப்பொழிவு (800–1200 மிமீ)", "crops_en": "Paddy, Sugarcane, Banana, Tapioca", "crops_ta": "நெல், கரும்பு, வாழை, மரவள்ளி"},
    {"id": "winter", "en": "Winter", "ta": "குளிர்காலம்", "desc_en": "January–February. Suitable for cool-season crops.", "desc_ta": "ஜனவரி–பிப்ரவரி. குளிர்கால பயிர்களுக்கு ஏற்றது.", "months_en": "January to February", "months_ta": "ஜனவரி முதல் பிப்ரவரி வரை", "rainfall_en": "Low rainfall (100–200 mm)", "rainfall_ta": "குறைந்த மழைப்பொழிவு (100–200 மிமீ)", "crops_en": "Cabbage, Cauliflower, Carrot, Beans, Onion", "crops_ta": "முட்டைகோஸ், காலிஃபிளவர், கேரட், பீன்ஸ், வெங்காயம்"},
    {"id": "custom", "en": "Custom Season", "ta": "தனிப்பயன் பருவம்", "desc_en": "Specify your own season.", "desc_ta": "உங்கள் சொந்த பருவத்தைக் குறிப்பிடவும்.", "months_en": "As specified", "months_ta": "குறிப்பிட்டபடி", "rainfall_en": "Varies by region", "rainfall_ta": "பகுதிக்கு ஏற்ப மாறுபடும்", "crops_en": "Any suitable crop", "crops_ta": "ஏதேனும் பொருத்தமான பயிர்"},
]

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

CROP_INFO = {
    "Paddy": {"sci": "Oryza sativa", "duration_en": "120–150 days", "duration_ta": "120–150 நாட்கள்", "districts_en": "Thanjavur, Tiruvallur, Cuddalore, Nagapattinam", "districts_ta": "தஞ்சாவூர், திருவள்ளூர், கடலூர், நாகப்பட்டினம்"},
    "Banana": {"sci": "Musa paradisiaca", "duration_en": "10–12 months", "duration_ta": "10–12 மாதங்கள்", "districts_en": "Tiruchirappalli, Theni, Thoothukudi", "districts_ta": "திருச்சி, தேனி, தூத்துக்குடி"},
    "Sugarcane": {"sci": "Saccharum officinarum", "duration_en": "10–12 months", "duration_ta": "10–12 மாதங்கள்", "districts_en": "Vellore, Dharmapuri, Salem, Erode", "districts_ta": "வேலூர், தர்மபுரி, சேலம், ஈரோடு"},
    "Cotton": {"sci": "Gossypium hirsutum", "duration_en": "150–180 days", "duration_ta": "150–180 நாட்கள்", "districts_en": "Coimbatore, Salem, Virudhunagar, Ramanathapuram", "districts_ta": "கோயம்புத்தூர், சேலம், விருதுநகர், இராமநாதபுரம்"},
    "Groundnut": {"sci": "Arachis hypogaea", "duration_en": "90–120 days", "duration_ta": "90–120 நாட்கள்", "districts_en": "Tiruvannamalai, Vellore, Cuddalore", "districts_ta": "திருவண்ணாமலை, வேலூர், கடலூர்"},
    "Coconut": {"sci": "Cocos nucifera", "duration_en": "Year-round (perennial)", "duration_ta": "ஆண்டு முழுவதும் (பல ஆண்டு)", "districts_en": "Kanyakumari, Thanjavur, Tiruppur, Pollachi", "districts_ta": "கன்னியாகுமரி, தஞ்சாவூர், திருப்பூர், பொள்ளாச்சி"},
    "Turmeric": {"sci": "Curcuma longa", "duration_en": "7–9 months", "duration_ta": "7–9 மாதங்கள்", "districts_en": "Erode, Salem, Namakkal", "districts_ta": "ஈரோடு, சேலம், நாமக்கல்"},
    "Maize": {"sci": "Zea mays", "duration_en": "90–110 days", "duration_ta": "90–110 நாட்கள்", "districts_en": "Perambalur, Tiruchi, Dindigul", "districts_ta": "பெரம்பலூர், திருச்சி, திண்டுக்கல்"},
    "Tomato": {"sci": "Solanum lycopersicum", "duration_en": "70–90 days", "duration_ta": "70–90 நாட்கள்", "districts_en": "Krishnagiri, Dharmapuri, Madurai, Theni", "districts_ta": "கிருஷ்ணகிரி, தர்மபுரி, மதுரை, தேனி"},
    "Brinjal": {"sci": "Solanum melongena", "duration_en": "100–120 days", "duration_ta": "100–120 நாட்கள்", "districts_en": "Coimbatore, Dindigul, Theni", "districts_ta": "கோயம்புத்தூர், திண்டுக்கல், தேனி"},
    "Chilli": {"sci": "Capsicum annuum", "duration_en": "90–120 days", "duration_ta": "90–120 நாட்கள்", "districts_en": "Virudhunagar, Tuticorin, Ramanathapuram", "districts_ta": "விருதுநகர், தூத்துக்குடி, இராமநாதபுரம்"},
    "Onion": {"sci": "Allium cepa", "duration_en": "90–120 days", "duration_ta": "90–120 நாட்கள்", "districts_en": "Tiruchirappalli, Perambalur, Dindigul", "districts_ta": "திருச்சி, பெரம்பலூர், திண்டுக்கல்"},
    "Millets": {"sci": "Multiple species", "duration_en": "75–120 days", "duration_ta": "75–120 நாட்கள்", "districts_en": "Dharmapuri, Krishnagiri, Salem", "districts_ta": "தர்மபுரி, கிருஷ்ணகிரி, சேலம்"},
    "Black Gram": {"sci": "Vigna mungo", "duration_en": "70–90 days", "duration_ta": "70–90 நாட்கள்", "districts_en": "Thanjavur, Tiruvallur, Cuddalore", "districts_ta": "தஞ்சாவூர், திருவள்ளூர், கடலூர்"},
    "Green Gram": {"sci": "Vigna radiata", "duration_en": "60–75 days", "duration_ta": "60–75 நாட்கள்", "districts_en": "Tiruvannamalai, Vellore, Salem", "districts_ta": "திருவண்ணாமலை, வேலூர், சேலம்"},
    "Mango": {"sci": "Mangifera indica", "duration_en": "4–5 months (seasonal)", "duration_ta": "4–5 மாதங்கள் (பருவகாலம்)", "districts_en": "Krishnagiri, Dharmapuri, Theni", "districts_ta": "கிருஷ்ணகிரி, தர்மபுரி, தேனி"},
    "Tapioca": {"sci": "Manihot esculenta", "duration_en": "8–10 months", "duration_ta": "8–10 மாதங்கள்", "districts_en": "Salem, Namakkal, Erode, Villupuram", "districts_ta": "சேலம், நாமக்கல், ஈரோடு, விழுப்புரம்"},
    "Sunflower": {"sci": "Helianthus annuus", "duration_en": "80–100 days", "duration_ta": "80–100 நாட்கள்", "districts_en": "Villupuram, Cuddalore, Tiruvannamalai", "districts_ta": "விழுப்புரம், கடலூர், திருவண்ணாமலை"},
    "Sesame": {"sci": "Sesamum indicum", "duration_en": "75–90 days", "duration_ta": "75–90 நாட்கள்", "districts_en": "Ramanathapuram, Virudhunagar, Sivaganga", "districts_ta": "இராமநாதபுரம், விருதுநகர், சிவகங்கை"},
    "Horse Gram": {"sci": "Macrotyloma uniflorum", "duration_en": "90–120 days", "duration_ta": "90–120 நாட்கள்", "districts_en": "Dharmapuri, Krishnagiri, Tiruvannamalai", "districts_ta": "தர்மபுரி, கிருஷ்ணகிரி, திருவண்ணாமலை"},
    "Red Gram": {"sci": "Cajanus cajan", "duration_en": "120–180 days", "duration_ta": "120–180 நாட்கள்", "districts_en": "Villupuram, Cuddalore, Tiruvannamalai", "districts_ta": "விழுப்புரம், கடலூர், திருவண்ணாமலை"},
    "Cashew": {"sci": "Anacardium occidentale", "duration_en": "Year-round (perennial)", "duration_ta": "ஆண்டு முழுவதும் (பல ஆண்டு)", "districts_en": "Cuddalore, Villupuram, Kanyakumari", "districts_ta": "கடலூர், விழுப்புரம், கன்னியாகுமரி"},
    "Papaya": {"sci": "Carica papaya", "duration_en": "8–10 months", "duration_ta": "8–10 மாதங்கள்", "districts_en": "Coimbatore, Madurai, Theni", "districts_ta": "கோயம்புத்தூர், மதுரை, தேனி"},
    "Guava": {"sci": "Psidium guajava", "duration_en": "Year-round (perennial)", "duration_ta": "ஆண்டு முழுவதும் (பல ஆண்டு)", "districts_en": "Tiruchirappalli, Madurai, Theni", "districts_ta": "திருச்சி, மதுரை, தேனி"},
    "Okra": {"sci": "Abelmoschus esculentus", "duration_en": "50–70 days", "duration_ta": "50–70 நாட்கள்", "districts_en": "Erode, Salem, Coimbatore", "districts_ta": "ஈரோடு, சேலம், கோயம்புத்தூர்"},
    "Cabbage": {"sci": "Brassica oleracea", "duration_en": "70–100 days", "duration_ta": "70–100 நாட்கள்", "districts_en": "Krishnagiri, Dharmapuri, Nilgiris", "districts_ta": "கிருஷ்ணகிரி, தர்மபுரி, நீலகிரி"},
    "Cauliflower": {"sci": "Brassica oleracea botrytis", "duration_en": "70–120 days", "duration_ta": "70–120 நாட்கள்", "districts_en": "Krishnagiri, Dharmapuri, Nilgiris", "districts_ta": "கிருஷ்ணகிரி, தர்மபுரி, நீலகிரி"},
    "Carrot": {"sci": "Daucus carota", "duration_en": "60–80 days", "duration_ta": "60–80 நாட்கள்", "districts_en": "Krishnagiri, Nilgiris, Dindigul", "districts_ta": "கிருஷ்ணகிரி, நீலகிரி, திண்டுக்கல்"},
    "Beans": {"sci": "Phaseolus vulgaris", "duration_en": "50–70 days", "duration_ta": "50–70 நாட்கள்", "districts_en": "Krishnagiri, Dharmapuri, Theni", "districts_ta": "கிருஷ்ணகிரி, தர்மபுரி, தேனி"},
    "Drumstick": {"sci": "Moringa oleifera", "duration_en": "Year-round (perennial)", "duration_ta": "ஆண்டு முழுவதும் (பல ஆண்டு)", "districts_en": "Virudhunagar, Ramanathapuram, Thoothukudi", "districts_ta": "விருதுநகர், இராமநாதபுரம், தூத்துக்குடி"},
    "Watermelon": {"sci": "Citrullus lanatus", "duration_en": "75–90 days", "duration_ta": "75–90 நாட்கள்", "districts_en": "Thanjavur, Tiruvallur, Cuddalore", "districts_ta": "தஞ்சாவூர், திருவள்ளூர், கடலூர்"},
    "Pumpkin": {"sci": "Cucurbita moschata", "duration_en": "90–120 days", "duration_ta": "90–120 நாட்கள்", "districts_en": "Dindigul, Theni, Madurai", "districts_ta": "திண்டுக்கல், தேனி, மதுரை"},
    "Other": {"sci": "—", "duration_en": "Varies", "duration_ta": "மாறுபடும்", "districts_en": "Varies by crop", "districts_ta": "பயிருக்கு ஏற்ப மாறுபடும்"},
}

GROWTH_STAGES = [
    {"id": "land_prep", "en": "Land Preparation", "ta": "நிலம் தயாரிப்பு", "nutrient_en": "Basal application of NPK. Incorporate organic manure (10–15 tons/acre) during ploughing.", "nutrient_ta": "அடிப்படை NPK உர பயன்பாடு. உழவின் போது கரிம எருவை (ஏக்கருக்கு 10–15 டன்) சேர்த்தல்."},
    {"id": "seed_treatment", "en": "Seed Treatment", "ta": "விதை நேர்த்தி", "nutrient_en": "Treat seeds with biofertilizers (Azospirillum, Phosphobacteria) and fungicides before sowing.", "nutrient_ta": "விதைப்பதற்கு முன் உயிர் உரங்கள் (அசோஸ்பைரில்லம், பாஸ்போபாக்டீரியா) மற்றும் பூஞ்சைக் கொல்லிகளால் விதை நேர்த்தி செய்யவும்."},
    {"id": "nursery", "en": "Nursery Stage", "ta": "நாற்றங்கால் நிலை", "nutrient_en": "Apply FYM and recommended NPK in nursery beds. Ensure adequate moisture for seedling growth.", "nutrient_ta": "நாற்றங்கால் பாத்திகளில் தொழுவுரம் மற்றும் பரிந்துரைக்கப்பட்ட NPK இடவும். நாற்று வளர்ச்சிக்கு போதுமான ஈரப்பதத்தை உறுதி செய்யவும்."},
    {"id": "germination", "en": "Germination", "ta": "முளைப்பு", "nutrient_en": "Light irrigation needed. No direct fertilizer application during germination stage. Starter solution may help.", "nutrient_ta": "மெல்லிய நீர்ப்பாசனம் தேவை. முளைப்பு கட்டத்தில் நேரடி உர பயன்பாடு தேவையில்லை. தொடக்கக் கரைசல் உதவலாம்."},
    {"id": "seedling", "en": "Seedling", "ta": "நாற்று நிலை", "nutrient_en": "Apply 1/4 of recommended nitrogen as top dressing. Ensure phosphorus for root development.", "nutrient_ta": "பரிந்துரைக்கப்பட்ட நைட்ரஜனில் 1/4 பகுதியை மேலுரமாக இடவும். வேர் வளர்ச்சிக்கு பாஸ்பரஸை உறுதி செய்யவும்."},
    {"id": "vegetative", "en": "Vegetative Stage", "ta": "தாவர வளர்ச்சி நிலை", "nutrient_en": "Heavy nitrogen requirement. Apply 50% of recommended N. Incorporate potash for stem strength.", "nutrient_ta": "அதிக நைட்ரஜன் தேவை. பரிந்துரைக்கப்பட்ட N-இல் 50% இடவும். தண்டு வலுவுக்கு பொட்டாஷ் சேர்க்கவும்."},
    {"id": "tillering", "en": "Tillering", "ta": "தூர்க்கும் நிலை", "nutrient_en": "Critical stage for nitrogen. Apply remaining N. Zinc sulfate (25 kg/ha) recommended for paddy.", "nutrient_ta": "நைட்ரஜனுக்கு முக்கியமான நிலை. மீதமுள்ள N இடவும். நெல்லுக்கு துத்தநாக சல்பேட் (ஹெக்டேருக்கு 25 கிகி) பரிந்துரைக்கப்படுகிறது."},
    {"id": "flowering", "en": "Flowering", "ta": "பூக்கும் நிலை", "nutrient_en": "Apply phosphorus and potash. Avoid excess nitrogen. Boron and micronutrient spray beneficial.", "nutrient_ta": "பாஸ்பரஸ் மற்றும் பொட்டாஷ் இடவும். அதிக நைட்ரஜனை தவிர்க்கவும். போரான் மற்றும் நுண்ணூட்ட தெளிப்பு பயனுள்ளது."},
    {"id": "fruiting", "en": "Fruiting", "ta": "காய்க்கும் நிலை", "nutrient_en": "Potash-heavy fertilization. Apply potassium nitrate for fruit quality. Maintain consistent irrigation.", "nutrient_ta": "பொட்டாஷ் அதிகமான உரமிடுதல். பழ தரத்திற்கு பொட்டாசியம் நைட்ரேட் இடவும். நிலையான நீர்ப்பாசனத்தை பராமரிக்கவும்."},
    {"id": "grain_filling", "en": "Grain Filling", "ta": "தானிய நிரப்பும் நிலை", "nutrient_en": "Apply potash for grain development. Foliar spray of DAP (2%) recommended. Avoid nitrogen at this stage.", "nutrient_ta": "தானிய வளர்ச்சிக்கு பொட்டாஷ் இடவும். DAP (2%) இலைவழி தெளிப்பு பரிந்துரைக்கப்படுகிறது. இந்த கட்டத்தில் நைட்ரஜனை தவிர்க்கவும்."},
    {"id": "maturity", "en": "Maturity", "ta": "முதிர்ச்சி நிலை", "nutrient_en": "Stop fertilizer application. Reduce irrigation gradually. Monitor for pest attacks.", "nutrient_ta": "உர பயன்பாட்டை நிறுத்தவும். படிப்படியாக நீர்ப்பாசனத்தை குறைக்கவும். பூச்சி தாக்குதலை கண்காணிக்கவும்."},
    {"id": "harvest", "en": "Harvest Stage", "ta": "அறுவடை நிலை", "nutrient_en": "No fertilization required. Harvest at correct moisture content. Store in dry conditions.", "nutrient_ta": "உரமிடுதல் தேவையில்லை. சரியான ஈரப்பதத்தில் அறுவடை செய்யவும். உலர்ந்த நிலையில் சேமிக்கவும்."},
]

IRRIGATION_METHODS = [
    {"id": "drip", "en": "Drip Irrigation", "ta": "சொட்டு நீர் பாசனம்", "water_en": "Low water requirement (2–4 L/hr). 60–80% efficiency.", "water_ta": "குறைந்த நீர் தேவை (2–4 லி/மணி). 60–80% திறன்.", "fert_en": "Fertigation recommended. Water-soluble fertilizers injected directly to root zone. Reduces wastage by 30–40%.", "fert_ta": "உர நீர்ப்பாசனம் பரிந்துரைக்கப்படுகிறது. நீரில் கரையக்கூடிய உரங்கள் நேரடியாக வேர் பகுதிக்கு செலுத்தப்படுகின்றன. 30–40% வீணாவதை குறைக்கிறது."},
    {"id": "flood", "en": "Flood Irrigation", "ta": "வெள்ளப் பாசனம்", "water_en": "High water requirement. 40–50% efficiency. Common for paddy.", "water_ta": "அதிக நீர் தேவை. 40–50% திறன். நெல்லுக்கு பொதுவானது.", "fert_en": "Apply fertilizer in split doses. Ensure standing water during urea application. Use neem-coated urea to reduce loss.", "fert_ta": "தவணை முறையில் உரமிடவும். யூரியா பயன்பாட்டின் போது நீர் தேக்கத்தை உறுதி செய்யவும். இழப்பை குறைக்க வேப்பம்பூச்சு யூரியாவைப் பயன்படுத்தவும்."},
    {"id": "sprinkler", "en": "Sprinkler Irrigation", "ta": "தெளிப்பு பாசனம்", "water_en": "Moderate water requirement. 60–70% efficiency. Suitable for vegetables.", "water_ta": "மிதமான நீர் தேவை. 60–70% திறன். காய்கறிகளுக்கு ஏற்றது.", "fert_en": "Foliar feeding effective. Apply water-soluble fertilizers through sprinkler. Avoid urea in hard water.", "fert_ta": "இலைவழி உரமிடுதல் பயனுள்ளது. தெளிப்பான் வழியாக நீரில் கரையும் உரங்களை இடவும். கடின நீரில் யூரியாவை தவிர்க்கவும்."},
    {"id": "rainfed", "en": "Rainfed Farming", "ta": "மழை சார்ந்த விவசாயம்", "water_en": "Rainfall-dependent. No irrigation infrastructure needed.", "water_ta": "மழையை சார்ந்தது. நீர்ப்பாசன கட்டமைப்பு தேவையில்லை.", "fert_en": "Apply fertilizers just before expected rainfall. Use slow-release and organic fertilizers. Split application recommended.", "fert_ta": "எதிர்பார்க்கப்படும் மழைக்கு முன் உரங்களை இடவும். மெதுவாக வெளியிடும் மற்றும் கரிம உரங்களைப் பயன்படுத்தவும். தவணை முறை பரிந்துரைக்கப்படுகிறது."},
    {"id": "furrow", "en": "Furrow Irrigation", "ta": "சால் பாசனம்", "water_en": "Moderate water use. 50–60% efficiency. Good for row crops.", "water_ta": "மிதமான நீர் பயன்பாடு. 50–60% திறன். வரிசை பயிர்களுக்கு ஏற்றது.", "fert_en": "Place fertilizer in furrows before irrigation. Band placement improves uptake. Use ammonium-based fertilizers.", "fert_ta": "நீர்ப்பாசனத்திற்கு முன் சால்களில் உரமிடவும். பட்டை முறை உரமிடுதல் உறிஞ்சுதலை மேம்படுத்துகிறது. அம்மோனியம் அடிப்படையிலான உரங்களைப் பயன்படுத்தவும்."},
    {"id": "basin", "en": "Basin Irrigation", "ta": "குட்டை பாசனம்", "water_en": "High water use. 40–50% efficiency. Common for orchards.", "water_ta": "அதிக நீர் பயன்பாடு. 40–50% திறன். பழத்தோட்டங்களுக்கு பொதுவானது.", "fert_en": "Apply fertilizers evenly within the basin. Use controlled-release fertilizers. Incorporate organic matter.", "fert_ta": "குட்டைக்குள் சீரான உர பயன்பாடு. கட்டுப்படுத்தப்பட்ட வெளியீட்டு உரங்களைப் பயன்படுத்தவும். கரிமப் பொருட்களை சேர்க்கவும்."},
    {"id": "manual", "en": "Manual Irrigation", "ta": "கைமுறை பாசனம்", "water_en": "Low volume. Labor-intensive. Suitable for small plots.", "water_ta": "குறைந்த அளவு. உழைப்பு மிகுந்தது. சிறிய நிலங்களுக்கு ஏற்றது.", "fert_en": "Apply liquid fertilizers manually. Use fertigation cans. Precise placement reduces waste.", "fert_ta": "திரவ உரங்களை கைமுறையாக இடவும். உர நீர்ப்பாசன கேன்களைப் பயன்படுத்தவும். துல்லியமான இடம் வீணாவதை குறைக்கிறது."},
    {"id": "other", "en": "Other", "ta": "மற்றவை", "water_en": "Varies by method.", "water_ta": "முறைக்கு ஏற்ப மாறுபடும்.", "fert_en": "Consult local agricultural officer for method-specific fertilizer recommendations.", "fert_ta": "முறை சார்ந்த உர பரிந்துரைகளுக்கு உள்ளூர் வேளாண் அலுவலரை அணுகவும்."},
]

@fertilizer_bp.route("/fertilizer", methods=["GET"])
@login_required
def index():
    lang = session.get("lang", "en")
    user_id = session.get("user_id")
    stats = Fertilizer.get_stats(user_id)
    history = Fertilizer.find_by_user(user_id)
    crop_list = []
    for i, c in enumerate(CROPS):
        info = CROP_INFO.get(c, {"sci": "", "duration_en": "", "duration_ta": "", "districts_en": "", "districts_ta": ""})
        crop_list.append({"en": c, "ta": CROPS_TA[i] if i < len(CROPS_TA) else c, **info})
    return render_template(
        "fertilizer.html",
        seasons=SEASONS,
        crops=crop_list,
        growth_stages=GROWTH_STAGES,
        irrigation_methods=IRRIGATION_METHODS,
        seasons_json=json.dumps(SEASONS),
        crops_json=json.dumps(crop_list),
        stages_json=json.dumps(GROWTH_STAGES),
        irrigation_json=json.dumps(IRRIGATION_METHODS),
        districts=get_districts(),
        stats=stats,
        history=[h.to_dict() for h in history],
        lang=lang,
    )

@fertilizer_bp.route("/api/fertilizer/seasons", methods=["GET"])
@login_required
def get_seasons():
    return jsonify({"success": True, "seasons": SEASONS})

@fertilizer_bp.route("/api/fertilizer/crops", methods=["GET"])
@login_required
def get_crops():
    lang = session.get("lang", "en")
    crop_list = []
    for i, c in enumerate(CROPS):
        info = CROP_INFO.get(c, {"sci": "", "duration_en": "", "duration_ta": "", "districts_en": "", "districts_ta": ""})
        crop_list.append({"en": c, "ta": CROPS_TA[i] if i < len(CROPS_TA) else c, **info})
    return jsonify({"success": True, "crops": crop_list})

@fertilizer_bp.route("/api/fertilizer/growth-stages", methods=["GET"])
@login_required
def get_growth_stages():
    return jsonify({"success": True, "stages": GROWTH_STAGES})

@fertilizer_bp.route("/api/fertilizer/irrigation-methods", methods=["GET"])
@login_required
def get_irrigation_methods():
    return jsonify({"success": True, "methods": IRRIGATION_METHODS})

@fertilizer_bp.route("/api/fertilizer/recommend", methods=["POST"])
@login_required
def recommend():
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"success": False, "error": "Invalid JSON in request body"}), 400

        season_id = data.get("season", "").strip()
        crop = data.get("crop", "").strip()
        growth_stage_id = data.get("growth_stage", "").strip()
        irrigation_id = data.get("irrigation", "").strip()
        lang = session.get("lang", "en")

        print("Recommendation request received")
        print("Request data:", {k: v for k, v in data.items()})
        print("Calling Groq...")

        if not season_id:
            msg = "Please select an agricultural season." if lang == "en" else "தயவுசெய்து ஒரு விவசாய பருவத்தைத் தேர்ந்தெடுக்கவும்."
            return jsonify({"success": False, "error": msg}), 400
        if not crop:
            msg = "Please select a crop." if lang == "en" else "தயவுசெய்து ஒரு பயிரைத் தேர்ந்தெடுக்கவும்."
            return jsonify({"success": False, "error": msg}), 400
        if not growth_stage_id:
            msg = "Please select a growth stage." if lang == "en" else "தயவுசெய்து ஒரு வளர்ச்சி நிலையைத் தேர்ந்தெடுக்கவும்."
            return jsonify({"success": False, "error": msg}), 400
        if not irrigation_id:
            msg = "Please select an irrigation method." if lang == "en" else "தயவுசெய்து ஒரு நீர்ப்பாசன முறையைத் தேர்ந்தெடுக்கவும்."
            return jsonify({"success": False, "error": msg}), 400

        season_name = season_id
        for s in SEASONS:
            if s["id"] == season_id:
                season_name = s["ta"] if lang == "ta" else s["en"]
                break

        stage_name = growth_stage_id
        for s in GROWTH_STAGES:
            if s["id"] == growth_stage_id:
                stage_name = s["ta"] if lang == "ta" else s["en"]
                break

        irrigation_name = irrigation_id
        for m in IRRIGATION_METHODS:
            if m["id"] == irrigation_id:
                irrigation_name = m["ta"] if lang == "ta" else m["en"]
                break

        district = session.get("district", "")
        print(f"[Fertilizer] Calling AI with: {crop}, {season_name}, {stage_name}, {irrigation_name}")

        from services.ai_service import AIService
        ai = AIService()

        if lang == "ta":
            prompt = (
                f"நீங்கள் தமிழ்நாட்டின் முன்னணி உர பரிந்துரை நிபுணர். பின்வரும் தகவல்களின் அடிப்படையில் முழுமையான உர பரிந்துரையை வழங்கவும்.\n\n"
                f"பயிர்: {crop}\n"
                f"விவசாய பருவம்: {season_name}\n"
                f"வளர்ச்சி நிலை: {stage_name}\n"
                f"நீர்ப்பாசன முறை: {irrigation_name}\n"
                f"மாவட்டம்: {district}\n\n"
                f"பின்வரும் பகுதிகளை உள்ளடக்கிய முழுமையான அறிக்கையை உருவாக்கவும். ஒவ்வொரு பகுதியையும் ## தலைப்புடன் தொடங்கவும்:\n\n"
                f"## பயிர் சுருக்கம்\n"
                f"## பரிந்துரைக்கப்பட்ட உரங்கள்\n"
                f"## உர அட்டவணை\n"
                f"## பயன்பாட்டு முறை\n"
                f"## ஊட்டச்சத்து தேவைகள்\n"
                f"## நீர்ப்பாசன அடிப்படையிலான பரிந்துரைகள்\n"
                f"## பருவகால ஆலோசனைகள்\n"
                f"## கரிம மாற்றுகள்\n"
                f"## பொதுவான விவசாயி தவறுகள்\n"
                f"## செலவு மதிப்பீடு\n"
                f"## பாதுகாப்பு வழிகாட்டுதல்கள்\n"
                f"## அரசு பரிந்துரைகள்\n\n"
                f"தமிழ்நாடு விவசாயப் பல்கலைக்கழகம் மற்றும் தமிழ்நாடு வேளாண்மைத் துறை வழிகாட்டுதல்களைப் பின்பற்றவும். தமிழில் மட்டுமே பதிலளிக்கவும்."
            )
        else:
            prompt = (
                f"You are a leading fertilizer recommendation expert for Tamil Nadu agriculture. Generate a complete fertilizer recommendation based on the following details.\n\n"
                f"Crop: {crop}\n"
                f"Agricultural Season: {season_name}\n"
                f"Growth Stage: {stage_name}\n"
                f"Irrigation Method: {irrigation_name}\n"
                f"District: {district}\n\n"
                f"Generate a comprehensive report covering the following sections. Start each section with ## heading:\n\n"
                f"## Crop Summary\n"
                f"## Recommended Fertilizers\n"
                f"## Fertilizer Schedule\n"
                f"## Application Method\n"
                f"## Nutrient Requirements\n"
                f"## Irrigation-Based Recommendations\n"
                f"## Seasonal Advice\n"
                f"## Organic Alternatives\n"
                f"## Common Farmer Mistakes\n"
                f"## Cost Estimation\n"
                f"## Safety Guidelines\n"
                f"## Government Recommendations\n\n"
                f"Follow Tamil Nadu Agricultural University and Tamil Nadu Agriculture Department guidelines. "
                f"Include specific fertilizer names, quantities per acre, timing, and application methods. "
                f"Reply only in English."
            )

        print(f"[Fertilizer] Prompt ({len(prompt)} chars): {prompt[:200]}...")
        response = ai.get_response(prompt, lang)
        print("Recommendation generated")
        print(f"[Fertilizer] AI response ({len(response)} chars): {response[:200]}...")

        return jsonify({
            "success": True,
            "recommendation": response,
            "metadata": {
                "season": season_name,
                "crop": crop,
                "growth_stage": stage_name,
                "irrigation": irrigation_name,
            }
        })

    except Exception as e:
        print(f"[Fertilizer Error] recommend: {traceback.format_exc()}")
        try:
            lang = session.get("lang", "en")
        except Exception:
            lang = "en"
        msg = f"Server error: {type(e).__name__}: {str(e)}"
        return jsonify({"success": False, "error": msg}), 500

@fertilizer_bp.route("/api/fertilizer/save", methods=["POST"])
@login_required
def save():
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"success": False, "error": "Invalid JSON"}), 400

        user_id = session.get("user_id")
        lang = session.get("lang", "en")

        f = Fertilizer()
        f.user_id = user_id
        f.season = data.get("season", "")
        f.crop = data.get("crop", "")
        f.growth_stage = data.get("growth_stage", "")
        f.irrigation_method = data.get("irrigation_method", "")
        f.recommendation = data.get("recommendation", "")
        f.language = data.get("language", lang)
        f.district = data.get("district", session.get("district", ""))
        f.save()

        print("Saved to MongoDB")
        msg = "Recommendation saved successfully!" if lang == "en" else "பரிந்துரை வெற்றிகரமாக சேமிக்கப்பட்டது!"
        return jsonify({"success": True, "message": msg})

    except Exception as e:
        print(f"[Fertilizer Error] save: {traceback.format_exc()}")
        return jsonify({"success": False, "error": "Failed to save recommendation"}), 500

@fertilizer_bp.route("/api/fertilizer/history", methods=["GET"])
@login_required
def get_history():
    try:
        user_id = session.get("user_id")
        search_q = request.args.get("search", "").strip()
        season_filter = request.args.get("season", "").strip()
        if search_q:
            items = Fertilizer.search_by_user(user_id, search_q)
        elif season_filter:
            items = Fertilizer.find_by_season(user_id, season_filter)
        else:
            items = Fertilizer.find_by_user(user_id)
        return jsonify({"success": True, "history": [h.to_dict() for h in items]})
    except Exception as e:
        print(f"[Fertilizer Error] history: {traceback.format_exc()}")
        return jsonify({"success": False, "error": "Failed to load history"}), 500

@fertilizer_bp.route("/api/fertilizer/<rec_id>", methods=["DELETE"])
@login_required
def delete(rec_id):
    try:
        lang = session.get("lang", "en")
        f = Fertilizer.find_by_id(rec_id)
        if not f:
            msg = "Recommendation not found." if lang == "en" else "பரிந்துரை கிடைக்கவில்லை."
            return jsonify({"success": False, "error": msg})
        f.delete()
        stats = Fertilizer.get_stats(session.get("user_id"))
        msg = "Recommendation deleted successfully!" if lang == "en" else "பரிந்துரை வெற்றிகரமாக நீக்கப்பட்டது!"
        return jsonify({"success": True, "message": msg, "stats": stats})
    except Exception as e:
        print(f"[Fertilizer Error] delete: {traceback.format_exc()}")
        return jsonify({"success": False, "error": "Failed to delete"}), 500

@fertilizer_bp.route("/api/fertilizer/stats", methods=["GET"])
@login_required
def get_stats():
    user_id = session.get("user_id")
    stats = Fertilizer.get_stats(user_id)
    return jsonify({"success": True, "stats": stats})

@fertilizer_bp.route("/api/fertilizer/export/<rec_id>", methods=["GET"])
@login_required
def export(rec_id):
    try:
        lang = session.get("lang", "en")
        f = Fertilizer.find_by_id(rec_id)
        if not f:
            msg = "Recommendation not found." if lang == "en" else "பரிந்துரை கிடைக்கவில்லை."
            return jsonify({"success": False, "error": msg})

        fmt = request.args.get("format", "txt")
        username = session.get("username", "Farmer")
        lines = []
        lines.append("=" * 50)
        lines.append("FERTILIZER RECOMMENDATION REPORT" if lang == "en" else "உர பரிந்துரை அறிக்கை")
        lines.append("=" * 50)
        lines.append(f"Farmer: {username}" if lang == "en" else f"விவசாயி: {username}")
        lines.append(f"Crop: {f.crop}" if lang == "en" else f"பயிர்: {f.crop}")
        lines.append(f"Season: {f.season}" if lang == "en" else f"பருவம்: {f.season}")
        lines.append(f"Growth Stage: {f.growth_stage}" if lang == "en" else f"வளர்ச்சி நிலை: {f.growth_stage}")
        lines.append(f"Irrigation: {f.irrigation_method}" if lang == "en" else f"நீர்ப்பாசனம்: {f.irrigation_method}")
        lines.append(f"Date: {f.created_at.strftime('%Y-%m-%d %H:%M')}" if lang == "en" else f"தேதி: {f.created_at.strftime('%Y-%m-%d %H:%M')}")
        lines.append("")
        lines.append(f.recommendation)

        text_content = "\n".join(lines)

        if fmt == "csv":
            csv_lines = [
                "Field,Value",
                f"Crop,{f.crop}",
                f"Season,{f.season}",
                f"Growth Stage,{f.growth_stage}",
                f"Irrigation Method,{f.irrigation_method}",
                f"Date,{f.created_at.strftime('%Y-%m-%d %H:%M')}",
            ]
            return jsonify({
                "success": True,
                "export": "\n".join(csv_lines),
                "filename": f"fertilizer_{rec_id[:8]}.csv",
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
            title = "Fertilizer Recommendation Report" if lang == "en" else "உர பரிந்துரை அறிக்கை"
            pdf.cell(0, 10, text=title, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
            pdf.set_font("Arial", "", 10)
            for line in text_content.split("\n"):
                pdf.set_x(pdf.l_margin)
                if line.startswith("=") or line.startswith("-"):
                    pdf.set_font("Arial", "", 10)
                elif any(line.startswith(x) for x in ["CROP", "FERTILIZER", "பயிர்", "உர"]):
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
                "filename": f"fertilizer_{rec_id[:8]}.pdf",
                "mime": "application/pdf",
                "encoding": "base64",
            })

        return jsonify({
            "success": True,
            "export": text_content,
            "filename": f"fertilizer_{rec_id[:8]}.txt",
            "mime": "text/plain",
        })

    except Exception as e:
        print(f"[Fertilizer Error] export: {traceback.format_exc()}")
        return jsonify({"success": False, "error": "Failed to export"}), 500
