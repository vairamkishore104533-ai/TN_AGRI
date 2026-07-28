from flask import Blueprint, render_template, request, jsonify, session
from utils.auth import login_required
from models.market import MarketRecord, MarketFavorite
from services.market_service import market_service, CROPS, CROPS_TA, MARKETS, MARKETS_TA
from services.ai_service import AIService
from datetime import datetime
import traceback
import json

market_bp = Blueprint("market", __name__)


@market_bp.route("/market", methods=["GET"])
@login_required
def index():
    lang = session.get("lang", "en")
    user_id = session.get("user_id")
    favorites = MarketFavorite.find_by_user(user_id)
    history = MarketRecord.find_by_user(user_id)
    crops_list = []
    for i, c in enumerate(CROPS):
        crops_list.append({"en": c, "ta": CROPS_TA[i] if i < len(CROPS_TA) else c})
    markets_list = []
    for i, m in enumerate(MARKETS):
        markets_list.append({"en": m, "ta": MARKETS_TA[i] if i < len(MARKETS_TA) else m})
    return render_template(
        "market.html",
        lang=lang,
        crops=crops_list,
        crops_json=json.dumps(crops_list),
        markets=markets_list,
        markets_json=json.dumps(markets_list),
        favorites=[f.to_dict() for f in favorites],
        favorites_json=json.dumps([f.to_dict() for f in favorites]),
        history=[h.to_dict() for h in history],
        history_json=json.dumps([h.to_dict() for h in history]),
    )


@market_bp.route("/api/market/prices", methods=["GET"])
@login_required
def get_prices():
    try:
        crop = request.args.get("crop", "").strip()
        market = request.args.get("market", "").strip()
        lang = session.get("lang", "en")
        if not crop or not market:
            msg = "Crop and market are required." if lang == "en" else "பயிர் மற்றும் சந்தை தேவை."
            return jsonify({"success": False, "error": msg}), 400
        result = market_service.fetch_price(crop, market)
        if not result:
            msg = "No price data available." if lang == "en" else "விலை தரவு எதுவும் இல்லை."
            return jsonify({"success": False, "error": msg}), 404
        return jsonify({"success": True, "price": result})
    except Exception as e:
        print(f"[Market Error] prices: {traceback.format_exc()}")
        return jsonify({"success": False, "error": str(e)}), 500


@market_bp.route("/api/market/compare", methods=["GET"])
@login_required
def compare():
    try:
        crop = request.args.get("crop", "").strip()
        lang = session.get("lang", "en")
        if not crop:
            msg = "Crop is required." if lang == "en" else "பயிர் தேவை."
            return jsonify({"success": False, "error": msg}), 400
        results = market_service.compare_markets(crop)
        return jsonify({"success": True, "prices": results})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@market_bp.route("/api/market/top-gainers", methods=["GET"])
@login_required
def top_gainers():
    try:
        data = market_service.top_gainers()
        return jsonify({"success": True, "items": data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@market_bp.route("/api/market/top-losers", methods=["GET"])
@login_required
def top_losers():
    try:
        data = market_service.top_losers()
        return jsonify({"success": True, "items": data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@market_bp.route("/api/market/summary", methods=["GET"])
@login_required
def summary():
    try:
        data = market_service.get_summary()
        return jsonify({"success": True, "summary": data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@market_bp.route("/api/market/insights", methods=["POST"])
@login_required
def insights():
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"success": False, "error": "Invalid JSON"}), 400
        crop = data.get("crop", "").strip()
        market = data.get("market", "").strip()
        price = data.get("price", 0)
        trend = data.get("trend", "stable")
        lang = session.get("lang", "en")
        price_data = data.get("price_data", {})

        ai = AIService()
        if lang == "ta":
            prompt = (
                f"நீங்கள் தமிழ்நாட்டின் விவசாய சந்தை ஆலோசகர். பின்வரும் சந்தை தரவுகளின் அடிப்படையில் "
                f"விவசாயிகளுக்கான சந்தை நுண்ணறிவுகள் மற்றும் விற்பனை பரிந்துரைகளை வழங்கவும்.\n\n"
                f"பயிர்: {crop}\nசந்தை: {market}\nதற்போதைய விலை: ₹{price}\n"
                f"போக்கு: {trend}\n\n"
                f"பின்வரும் பகுதிகளை உள்ளடக்கவும்:\n"
                f"1. சந்தை நுண்ணறிவு (விலை ஏன் மாறுகிறது)\n"
                f"2. விற்பனை பரிந்துரை (இப்போது விற்கவும் / காத்திருக்கவும் / பாதுகாப்பாக சேமிக்கவும்)\n"
                f"3. எதிர்பார்க்கப்படும் விலை நகர்வு\n"
                f"4. தேவை மற்றும் வழங்கல் நிலை\n"
                f"5. பண்டிகை / பருவகால தாக்கம்\n\n"
                f"தமிழில் மட்டுமே பதிலளிக்கவும். 5-6 வரிகளுக்கு மேல் இருக்க வேண்டாம்."
            )
        else:
            prompt = (
                f"You are a Tamil Nadu agricultural market advisor. Based on the following market data, "
                f"provide market insights and selling recommendations for farmers.\n\n"
                f"Crop: {crop}\nMarket: {market}\nCurrent Price: ₹{price}\n"
                f"Trend: {trend}\n\n"
                f"Cover these points:\n"
                f"1. Market insight (why price is moving)\n"
                f"2. Selling recommendation (sell now / wait / store safely)\n"
                f"3. Expected price movement\n"
                f"4. Demand and supply level\n"
                f"5. Festival / seasonal impact\n\n"
                f"Reply in English. Keep it to 5-6 lines."
            )
        try:
            advice = ai.get_response(prompt, lang)
        except Exception:
            if lang == "ta":
                advice = "சந்தை நிலவரம் சாதாரணமாக உள்ளது. தற்போதைய விலையில் விற்ப Souk  பயனடையலாம்."
            else:
                advice = "Market conditions are normal. You can sell at current prices for good returns."
        return jsonify({"success": True, "insights": advice})
    except Exception as e:
        print(f"[Market Error] insights: {traceback.format_exc()}")
        return jsonify({"success": False, "error": str(e)}), 500


@market_bp.route("/api/market/save", methods=["POST"])
@login_required
def save():
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"success": False, "error": "Invalid JSON"}), 400
        user_id = session.get("user_id")
        lang = session.get("lang", "en")
        rec = MarketRecord()
        rec.user_id = user_id
        rec.crop = data.get("crop", "")
        rec.market = data.get("market", "")
        rec.price = data.get("price", 0)
        rec.unit = data.get("unit", "Quintal")
        rec.trend = data.get("trend", "stable")
        rec.market_data = data.get("market_data", {})
        rec.save()
        msg = "Market data saved!" if lang == "en" else "சந்தை தரவு சேமிக்கப்பட்டது!"
        return jsonify({"success": True, "message": msg})
    except Exception as e:
        print(f"[Market Error] save: {traceback.format_exc()}")
        return jsonify({"success": False, "error": "Failed to save"}), 500


@market_bp.route("/api/market/history", methods=["GET"])
@login_required
def get_history():
    try:
        user_id = session.get("user_id")
        search_q = request.args.get("search", "").strip()
        if search_q:
            items = MarketRecord.search_by_user(user_id, search_q)
        else:
            items = MarketRecord.find_by_user(user_id)
        return jsonify({"success": True, "history": [h.to_dict() for h in items]})
    except Exception as e:
        print(f"[Market Error] history: {traceback.format_exc()}")
        return jsonify({"success": False, "error": "Failed to load history"}), 500


@market_bp.route("/api/market/history/<hid>", methods=["DELETE"])
@login_required
def delete_history(hid):
    try:
        lang = session.get("lang", "en")
        h = MarketRecord.find_by_id(hid)
        if not h:
            msg = "Record not found." if lang == "en" else "பதிவு கிடைக்கவில்லை."
            return jsonify({"success": False, "error": msg})
        h.delete()
        msg = "Record deleted!" if lang == "en" else "பதிவு நீக்கப்பட்டது!"
        return jsonify({"success": True, "message": msg})
    except Exception as e:
        print(f"[Market Error] delete: {traceback.format_exc()}")
        return jsonify({"success": False, "error": "Failed to delete"}), 500


@market_bp.route("/api/market/favorites", methods=["GET"])
@login_required
def get_favorites():
    try:
        user_id = session.get("user_id")
        items = MarketFavorite.find_by_user(user_id)
        return jsonify({"success": True, "favorites": [f.to_dict() for f in items]})
    except Exception as e:
        return jsonify({"success": False, "error": "Failed to load favorites"}), 500


@market_bp.route("/api/market/favorites/add", methods=["POST"])
@login_required
def add_favorite():
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"success": False, "error": "Invalid JSON"}), 400
        user_id = session.get("user_id")
        crop = data.get("crop", "").strip()
        lang = session.get("lang", "en")
        if not crop:
            msg = "Crop is required." if lang == "en" else "பயிர் தேவை."
            return jsonify({"success": False, "error": msg}), 400
        existing = MarketFavorite.find_by_user_and_crop(user_id, crop)
        if existing:
            msg = "Already in favorites!" if lang == "en" else "ஏற்கனவே விருப்பங்களில் உள்ளது!"
            return jsonify({"success": True, "message": msg, "id": str(existing.get("_id", ""))})
        f = MarketFavorite()
        f.user_id = user_id
        f.crop = crop
        fid = f.save()
        msg = "Added to favorites!" if lang == "en" else "விருப்பங்களில் சேர்க்கப்பட்டது!"
        return jsonify({"success": True, "message": msg, "id": fid})
    except Exception as e:
        return jsonify({"success": False, "error": "Failed to add favorite"}), 500


@market_bp.route("/api/market/favorites/<fid>", methods=["DELETE"])
@login_required
def remove_favorite(fid):
    try:
        lang = session.get("lang", "en")
        f = MarketFavorite.find_by_id(fid)
        if not f:
            msg = "Favorite not found." if lang == "en" else "விருப்பம் கிடைக்கவில்லை."
            return jsonify({"success": False, "error": msg})
        f.delete()
        msg = "Removed from favorites!" if lang == "en" else "விருப்பங்களில் இருந்து நீக்கப்பட்டது!"
        return jsonify({"success": True, "message": msg})
    except Exception as e:
        return jsonify({"success": False, "error": "Failed to remove favorite"}), 500


@market_bp.route("/api/market/export/<hid>", methods=["GET"])
@login_required
def export(hid):
    try:
        lang = session.get("lang", "en")
        h = MarketRecord.find_by_id(hid)
        if not h:
            msg = "Record not found." if lang == "en" else "பதிவு கிடைக்கவில்லை."
            return jsonify({"success": False, "error": msg})
        fmt = request.args.get("format", "txt")
        md = h.market_data or {}
        lines = []
        lines.append("=" * 50)
        lines.append("MARKET PRICE REPORT" if lang == "en" else "சந்தை விலை அறிக்கை")
        lines.append("=" * 50)
        lines.append(f"Crop: {h.crop}" if lang == "en" else f"பயிர்: {h.crop}")
        lines.append(f"Market: {h.market}" if lang == "en" else f"சந்தை: {h.market}")
        lines.append(f"Price: ₹{h.price}" if lang == "en" else f"விலை: ₹{h.price}")
        lines.append(f"Unit: {h.unit}" if lang == "en" else f"அலகு: {h.unit}")
        lines.append(f"Trend: {h.trend}" if lang == "en" else f"போக்கு: {h.trend}")
        lines.append(f"Date: {h.created_at}" if lang == "en" else f"தேதி: {h.created_at}")
        text_content = "\n".join(lines)

        if fmt == "csv":
            csv_lines = [
                "Field,Value",
                f"Crop,{h.crop}",
                f"Market,{h.market}",
                f"Price,{h.price}",
                f"Unit,{h.unit}",
                f"Trend,{h.trend}",
                f"Date,{h.created_at}",
            ]
            return jsonify({
                "success": True,
                "export": "\n".join(csv_lines),
                "filename": f"market_{hid[:8]}.csv",
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
            title = "Market Price Report" if lang == "en" else "சந்தை விலை அறிக்கை"
            pdf.cell(0, 10, text=title, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
            pdf.set_font("Arial", "", 10)
            for line in text_content.split("\n"):
                pdf.set_x(pdf.l_margin)
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
                "filename": f"market_{hid[:8]}.pdf",
                "mime": "application/pdf",
                "encoding": "base64",
            })
        return jsonify({
            "success": True,
            "export": text_content,
            "filename": f"market_{hid[:8]}.txt",
            "mime": "text/plain",
        })
    except Exception as e:
        print(f"[Market Error] export: {traceback.format_exc()}")
        return jsonify({"success": False, "error": "Failed to export"}), 500
