from flask import Blueprint, render_template, request, jsonify, session
from utils.auth import login_required
from models.weather import WeatherHistory, WeatherFavorite
from services.weather_service import WeatherService
from services.ai_service import AIService
from datetime import datetime
import traceback
import json

weather_bp = Blueprint("weather", __name__)
weather_service = WeatherService()

DISTRICTS = [
    "Ariyalur", "Chengalpattu", "Chennai", "Coimbatore", "Cuddalore",
    "Dharmapuri", "Dindigul", "Erode", "Kallakurichi", "Kanchipuram",
    "Kanyakumari", "Karur", "Krishnagiri", "Madurai", "Mayiladuthurai",
    "Nagapattinam", "Namakkal", "Nilgiris", "Perambalur", "Pudukkottai",
    "Ramanathapuram", "Ranipet", "Salem", "Sivaganga", "Tenkasi",
    "Thanjavur", "Theni", "Thoothukudi", "Tiruchirappalli", "Tirunelveli",
    "Tirupathur", "Tiruppur", "Tiruvallur", "Tiruvannamalai", "Tiruvarur",
    "Vellore", "Villupuram", "Virudhunagar",
]

DISTRICTS_TA = [
    "அரியலூர்", "செங்கல்பட்டு", "சென்னை", "கோயம்புத்தூர்", "கடலூர்",
    "தர்மபுரி", "திண்டுக்கல்", "ஈரோடு", "கள்ளக்குறிச்சி", "காஞ்சிபுரம்",
    "கன்னியாகுமரி", "கரூர்", "கிருஷ்ணகிரி", "மதுரை", "மயிலாடுதுறை",
    "நாகப்பட்டினம்", "நாமக்கல்", "நீலகிரி", "பெரம்பலூர்", "புதுக்கோட்டை",
    "இராமநாதபுரம்", "ராணிப்பேட்டை", "சேலம்", "சிவகங்கை", "தென்காசி",
    "தஞ்சாவூர்", "தேனி", "தூத்துக்குடி", "திருச்சிராப்பள்ளி", "திருநெல்வேலி",
    "திருப்பத்தூர்", "திருப்பூர்", "திருவள்ளூர்", "திருவண்ணாமலை", "திருவாரூர்",
    "வேலூர்", "விழுப்புரம்", "விருதுநகர்",
]


@weather_bp.route("/weather", methods=["GET"])
@login_required
def index():
    lang = session.get("lang", "en")
    user_id = session.get("user_id")
    favorites = WeatherFavorite.find_by_user(user_id)
    district_list = []
    for i, d in enumerate(DISTRICTS):
        district_list.append({"en": d, "ta": DISTRICTS_TA[i] if i < len(DISTRICTS_TA) else d})
    return render_template(
        "weather.html",
        districts=district_list,
        districts_json=json.dumps(district_list),
        favorites=[f.to_dict() for f in favorites],
        favorites_json=json.dumps([f.to_dict() for f in favorites]),
        lang=lang,
    )


@weather_bp.route("/api/weather/fetch", methods=["POST"])
@login_required
def fetch_weather():
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"success": False, "error": "Invalid JSON"}), 400
        district = data.get("district", "").strip()
        town = data.get("town", "").strip()
        lang = session.get("lang", "en")

        if not district:
            msg = "Please select a district." if lang == "en" else "தயவுசெய்து ஒரு மாவட்டத்தைத் தேர்ந்தெடுக்கவும்."
            return jsonify({"success": False, "error": msg}), 400
        if not town:
            msg = "Please enter a town or village name." if lang == "en" else "தயவுசெய்து ஒரு நகரம் அல்லது கிராமத்தின் பெயரை உள்ளிடவும்."
            return jsonify({"success": False, "error": msg}), 400

        result = weather_service.fetch_all(district, town)
        if result.get("error"):
            return jsonify({"success": False, "error": result["error"]}), 502

        advice = ""
        current = result.get("current", {})
        if current:
            ai = AIService()
            if lang == "ta":
                ap = (
                    f"நீங்கள் தமிழ்நாட்டின் விவசாய வானிலை ஆலோசகர். பின்வரும் நேரடி வானிலை தரவுகளின் அடிப்படையில் "
                    f"விவசாய ஆலோசனைகளை வழங்கவும்.\n\n"
                    f"வெப்பநிலை: {current.get('temp')}°C\n"
                    f"ஈரப்பதம்: {current.get('humidity')}%\n"
                    f"காற்று வேகம்: {current.get('wind_speed')} km/h\n"
                    f"மழை வாய்ப்பு: {current.get('clouds')}%\n"
                    f"வானிலை: {current.get('condition_raw')}\n\n"
                    f"பின்வரும் பகுதிகளுக்கு சுருக்கமான ஆலோசனைகளை வழங்கவும்:\n"
                    f"1. நீர்ப்பாசனம் (அதிகரிக்க/குறைக்க/தவிர்க்க)\n"
                    f"2. மழை எச்சரிக்கை (கனமழை எதிர்பார்க்கப்பட்டால்)\n"
                    f"3. வெப்பநிலை எச்சரிக்கை (அதிக வெப்பம் அல்லது குளிர்)\n"
                    f"4. காற்று எச்சரிக்கை (தெளிப்பு/உரங்களுக்கு ஏற்றதா)\n"
                    f"5. பயிர் ஆலோசனை (அறுவடை/உரமிடுதல்/தெளிப்புக்கான சிறந்த நேரம்)\n\n"
                    f"தமிழில் மட்டுமே பதிலளிக்கவும். 3-4 வரிகளுக்கு மேல் இருக்க வேண்டாம்."
                )
            else:
                ap = (
                    f"You are a Tamil Nadu agricultural weather advisor. Based on the following live weather data, "
                    f"provide concise farming advice.\n\n"
                    f"Temperature: {current.get('temp')}°C\n"
                    f"Humidity: {current.get('humidity')}%\n"
                    f"Wind Speed: {current.get('wind_speed')} km/h\n"
                    f"Rain Chance: {current.get('clouds')}%\n"
                    f"Condition: {current.get('condition_raw')}\n\n"
                    f"Cover these points briefly:\n"
                    f"1. Irrigation advice (increase/reduce/avoid)\n"
                    f"2. Rain alert if heavy rain expected\n"
                    f"3. Temperature alert (extreme heat/cold)\n"
                    f"4. Wind alert (suitable for spraying/fertilizer)\n"
                    f"5. Crop advisory (best time for harvest/fertilizer/spraying)\n\n"
                    f"Reply in English. Keep it to 3-4 lines."
                )
            try:
                advice = ai.get_response(ap, lang)
            except Exception:
                if lang == "ta":
                    advice = "வானிலை விவசாயத்திற்கு சாதகமாக உள்ளது. வழக்கமான பணிகளை தொடரலாம்."
                else:
                    advice = "Weather conditions are favorable for farming. Continue with regular activities."

        return jsonify({
            "success": True,
            "weather": current,
            "uv": result.get("uv"),
            "daily": result.get("daily", []),
            "hourly": result.get("hourly", []),
            "advice": advice,
        })

    except Exception as e:
        print(f"[Weather Error] fetch: {traceback.format_exc()}")
        try:
            lang = session.get("lang", "en")
        except Exception:
            lang = "en"
        return jsonify({"success": False, "error": f"Server error: {str(e)}"}), 500


@weather_bp.route("/api/weather/save", methods=["POST"])
@login_required
def save():
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"success": False, "error": "Invalid JSON"}), 400
        user_id = session.get("user_id")
        lang = session.get("lang", "en")
        h = WeatherHistory()
        h.user_id = user_id
        h.district = data.get("district", "")
        h.town = data.get("town", "")
        h.weather_data = data.get("weather_data", {})
        h.save()
        msg = "Weather data saved!" if lang == "en" else "வானிலை தரவு சேமிக்கப்பட்டது!"
        return jsonify({"success": True, "message": msg})
    except Exception as e:
        print(f"[Weather Error] save: {traceback.format_exc()}")
        return jsonify({"success": False, "error": "Failed to save"}), 500


@weather_bp.route("/api/weather/history", methods=["GET"])
@login_required
def get_history():
    try:
        user_id = session.get("user_id")
        search_q = request.args.get("search", "").strip()
        if search_q:
            items = WeatherHistory.search_by_user(user_id, search_q)
        else:
            items = WeatherHistory.find_by_user(user_id)
        return jsonify({"success": True, "history": [h.to_dict() for h in items]})
    except Exception as e:
        print(f"[Weather Error] history: {traceback.format_exc()}")
        return jsonify({"success": False, "error": "Failed to load history"}), 500


@weather_bp.route("/api/weather/history/<hid>", methods=["DELETE"])
@login_required
def delete_history(hid):
    try:
        lang = session.get("lang", "en")
        h = WeatherHistory.find_by_id(hid)
        if not h:
            msg = "Record not found." if lang == "en" else "பதிவு கிடைக்கவில்லை."
            return jsonify({"success": False, "error": msg})
        h.delete()
        msg = "Record deleted!" if lang == "en" else "பதிவு நீக்கப்பட்டது!"
        return jsonify({"success": True, "message": msg})
    except Exception as e:
        print(f"[Weather Error] delete: {traceback.format_exc()}")
        return jsonify({"success": False, "error": "Failed to delete"}), 500


@weather_bp.route("/api/weather/favorites", methods=["GET"])
@login_required
def get_favorites():
    try:
        user_id = session.get("user_id")
        items = WeatherFavorite.find_by_user(user_id)
        return jsonify({"success": True, "favorites": [f.to_dict() for f in items]})
    except Exception as e:
        return jsonify({"success": False, "error": "Failed to load favorites"}), 500


@weather_bp.route("/api/weather/favorites/add", methods=["POST"])
@login_required
def add_favorite():
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"success": False, "error": "Invalid JSON"}), 400
        user_id = session.get("user_id")
        district = data.get("district", "").strip()
        town = data.get("town", "").strip()
        lang = session.get("lang", "en")
        if not district or not town:
            msg = "District and town required." if lang == "en" else "மாவட்டம் மற்றும் நகரம் தேவை."
            return jsonify({"success": False, "error": msg}), 400
        existing = WeatherFavorite.find_by_user_and_location(user_id, district, town)
        if existing:
            msg = "Already in favorites!" if lang == "en" else "ஏற்கனவே விருப்பங்களில் உள்ளது!"
            return jsonify({"success": True, "message": msg, "id": str(existing.get("_id", ""))})
        f = WeatherFavorite()
        f.user_id = user_id
        f.district = district
        f.town = town
        fid = f.save()
        msg = "Added to favorites!" if lang == "en" else "விருப்பங்களில் சேர்க்கப்பட்டது!"
        return jsonify({"success": True, "message": msg, "id": fid})
    except Exception as e:
        return jsonify({"success": False, "error": "Failed to add favorite"}), 500


@weather_bp.route("/api/weather/favorites/<fid>", methods=["DELETE"])
@login_required
def remove_favorite(fid):
    try:
        lang = session.get("lang", "en")
        f = WeatherFavorite.find_by_id(fid)
        if not f:
            msg = "Favorite not found." if lang == "en" else "விருப்பம் கிடைக்கவில்லை."
            return jsonify({"success": False, "error": msg})
        f.delete()
        msg = "Removed from favorites!" if lang == "en" else "விருப்பங்களில் இருந்து நீக்கப்பட்டது!"
        return jsonify({"success": True, "message": msg})
    except Exception as e:
        return jsonify({"success": False, "error": "Failed to remove favorite"}), 500


@weather_bp.route("/api/weather/export/<hid>", methods=["GET"])
@login_required
def export(hid):
    try:
        lang = session.get("lang", "en")
        h = WeatherHistory.find_by_id(hid)
        if not h:
            msg = "Record not found." if lang == "en" else "பதிவு கிடைக்கவில்லை."
            return jsonify({"success": False, "error": msg})
        fmt = request.args.get("format", "txt")
        wd = h.weather_data or {}
        lines = []
        lines.append("=" * 50)
        lines.append("WEATHER REPORT" if lang == "en" else "வானிலை அறிக்கை")
        lines.append("=" * 50)
        lines.append(f"District: {h.district}" if lang == "en" else f"மாவட்டம்: {h.district}")
        lines.append(f"Town: {h.town}" if lang == "en" else f"நகரம்: {h.town}")
        lines.append(f"Date: {h.created_at}" if lang == "en" else f"தேதி: {h.created_at}")
        lines.append("")
        if wd.get("temp") is not None:
            lines.append(f"Temperature: {wd['temp']}°C" if lang == "en" else f"வெப்பநிலை: {wd['temp']}°C")
        if wd.get("humidity") is not None:
            lines.append(f"Humidity: {wd['humidity']}%" if lang == "en" else f"ஈரப்பதம்: {wd['humidity']}%")
        if wd.get("wind_speed") is not None:
            lines.append(f"Wind: {wd['wind_speed']} km/h" if lang == "en" else f"காற்று: {wd['wind_speed']} km/h")
        if wd.get("condition_raw"):
            lines.append(f"Condition: {wd['condition_raw']}" if lang == "en" else f"நிலை: {wd['condition_raw']}")

        text_content = "\n".join(lines)

        if fmt == "csv":
            csv_lines = [
                "Field,Value",
                f"District,{h.district}",
                f"Town,{h.town}",
                f"Temperature,{wd.get('temp','')}",
                f"Humidity,{wd.get('humidity','')}",
                f"Wind Speed,{wd.get('wind_speed','')}",
                f"Condition,{wd.get('condition_raw','')}",
                f"Date,{h.created_at}",
            ]
            return jsonify({
                "success": True,
                "export": "\n".join(csv_lines),
                "filename": f"weather_{hid[:8]}.csv",
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
            title = "Weather Report" if lang == "en" else "வானிலை அறிக்கை"
            pdf.cell(0, 10, text=title, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
            pdf.set_font("Arial", "", 10)
            for line in text_content.split("\n"):
                pdf.set_x(pdf.l_margin)
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
                "filename": f"weather_{hid[:8]}.pdf",
                "mime": "application/pdf",
                "encoding": "base64",
            })
        return jsonify({
            "success": True,
            "export": text_content,
            "filename": f"weather_{hid[:8]}.txt",
            "mime": "text/plain",
        })
    except Exception as e:
        print(f"[Weather Error] export: {traceback.format_exc()}")
        return jsonify({"success": False, "error": "Failed to export"}), 500
