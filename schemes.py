from flask import Blueprint, render_template, request, jsonify, session
from utils.auth import login_required
from services.scheme_service import SchemeService
from services.ai_service import AIService
from models.scheme import SavedScheme, RecentlyViewed, SchemeNotification
from datetime import datetime
import traceback
import json

schemes_bp = Blueprint("schemes", __name__)
scheme_service = SchemeService()


@schemes_bp.route("/schemes")
@login_required
def index():
    lang = session.get("lang", "en")
    user_id = session.get("user_id")
    saved = SavedScheme.find_by_user(user_id)
    recent = RecentlyViewed.find_by_user(user_id)
    notifications = SchemeNotification.find_by_user(user_id)
    featured = scheme_service.get_featured()
    categories = scheme_service.get_categories()
    faqs = scheme_service.get_faqs()
    return render_template(
        "schemes.html",
        lang=lang,
        saved=[s.to_dict() for s in saved],
        saved_json=json.dumps([s.to_dict() for s in saved]),
        recent=[r.to_dict() for r in recent],
        recent_json=json.dumps([r.to_dict() for r in recent]),
        notifications_json=json.dumps({n.scheme_id: n.enabled for n in notifications}),
        featured=featured,
        featured_json=json.dumps(featured),
        categories=categories,
        categories_json=json.dumps(categories),
        faqs=faqs,
        faqs_json=json.dumps(faqs),
        all_schemes_json=json.dumps(scheme_service.get_all_schemes()),
    )


@schemes_bp.route("/api/schemes")
@login_required
def get_schemes():
    try:
        search_q = request.args.get("search", "").strip()
        category = request.args.get("category", "").strip()
        featured_only = request.args.get("featured", "").strip()

        if featured_only == "true":
            schemes = scheme_service.get_featured()
        elif search_q:
            schemes = scheme_service.search(search_q)
        elif category:
            schemes = scheme_service.get_by_category(category)
        else:
            schemes = scheme_service.get_all_schemes()

        return jsonify({"success": True, "schemes": schemes})
    except Exception as e:
        print(f"[Schemes Error] get_schemes: {traceback.format_exc()}")
        return jsonify({"success": False, "error": "Failed to load schemes"}), 500


@schemes_bp.route("/api/schemes/<scheme_id>")
@login_required
def get_scheme_detail(scheme_id):
    try:
        scheme = scheme_service.get_by_id(scheme_id)
        if not scheme:
            lang = session.get("lang", "en")
            msg = "Scheme not found." if lang == "en" else "திட்டம் கிடைக்கவில்லை."
            return jsonify({"success": False, "error": msg}), 404
        return jsonify({"success": True, "scheme": scheme})
    except Exception as e:
        print(f"[Schemes Error] detail: {traceback.format_exc()}")
        return jsonify({"success": False, "error": "Failed to load scheme details"}), 500


@schemes_bp.route("/api/schemes/categories")
@login_required
def get_categories():
    try:
        return jsonify({"success": True, "categories": scheme_service.get_categories()})
    except Exception as e:
        return jsonify({"success": False, "error": "Failed to load categories"}), 500


@schemes_bp.route("/api/schemes/recommend", methods=["POST"])
@login_required
def recommend():
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"success": False, "error": "Invalid JSON"}), 400
        user_id = session.get("user_id")
        lang = session.get("lang", "en")
        district = session.get("district", "")
        crops = data.get("crops", "")
        farm_size = data.get("farm_size", "")
        soil_type = data.get("soil_type", "")
        interests = data.get("interests", "")

        scheme_list = scheme_service.get_all_schemes()
        scheme_names = "\n".join([f"- {s['name']} ({s['category_en']}): {s['benefits'][:100]}" for s in scheme_list])

        if lang == "ta":
            prompt = (
                f"நீங்கள் தமிழ்நாடு விவசாய அரசு திட்ட ஆலோசகர். பின்வரும் விவசாயி விவரங்களின் அடிப்படையில் "
                f"மிகவும் பொருத்தமான 3-5 அரசு திட்டங்களை பரிந்துரைக்கவும்.\n\n"
                f"விவசாயி விவரங்கள்:\n"
                f"மாவட்டம்: {district}\n"
                f"பயிர்கள்: {crops}\n"
                f"நில அளவு: {farm_size} ஏக்கர்\n"
                f"மண் வகை: {soil_type}\n"
                f"ஆர்வங்கள்: {interests}\n\n"
                f"கிடைக்கும் திட்டங்கள்:\n{scheme_names}\n\n"
                f"ஒவ்வொரு பரிந்துரைக்கும் காரணத்துடன் தமிழில் பதில் அளிக்கவும். "
                f"3-4 வரிகளுக்கு மேல் இருக்க வேண்டாம். திட்டத்தின் பெயர் மற்றும் விண்ணப்ப இணைப்பை சேர்க்கவும்."
            )
        else:
            prompt = (
                f"You are a Tamil Nadu government scheme advisor. Based on the following farmer profile, "
                f"recommend the 3-5 most suitable government schemes.\n\n"
                f"Farmer Details:\n"
                f"District: {district}\n"
                f"Crops: {crops}\n"
                f"Farm Size: {farm_size} acres\n"
                f"Soil Type: {soil_type}\n"
                f"Interests: {interests}\n\n"
                f"Available Schemes:\n{scheme_names}\n\n"
                f"Provide the recommendation with reasons. Keep it brief (3-4 lines). "
                f"Include scheme name and application link."
            )

        ai = AIService()
        try:
            recommendation = ai.get_response(prompt, lang)
        except Exception:
            if lang == "ta":
                recommendation = "உங்கள் விவரங்களின் அடிப்படையில், PM-KISAN, மண் ஆரோக்கிய அட்டை, மற்றும் தமிழ்நாடு சிறு நீர்ப்பாசன திட்டங்கள் உங்களுக்கு பொருத்தமானவை. மேலும் தகவலுக்கு உங்கள் மாவட்ட வேளாண் அலுவலகத்தை அணுகவும்."
            else:
                recommendation = "Based on your profile, PM-KISAN, Soil Health Card, and TN Micro Irrigation Scheme may be suitable for you. Visit your district agriculture office for more details."

        return jsonify({"success": True, "recommendation": recommendation})
    except Exception as e:
        print(f"[Schemes Error] recommend: {traceback.format_exc()}")
        try:
            lang = session.get("lang", "en")
        except Exception:
            lang = "en"
        msg = "Failed to generate recommendation." if lang == "en" else "பரிந்துரையை உருவாக்க முடியவில்லை."
        return jsonify({"success": False, "error": msg}), 500


@schemes_bp.route("/api/schemes/save", methods=["POST"])
@login_required
def save_scheme():
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"success": False, "error": "Invalid JSON"}), 400
        user_id = session.get("user_id")
        scheme_id = data.get("scheme_id", "")
        lang = session.get("lang", "en")

        if not scheme_id:
            msg = "Scheme ID required." if lang == "en" else "திட்ட ID தேவை."
            return jsonify({"success": False, "error": msg}), 400

        existing = SavedScheme.find_by_user_and_scheme(user_id, scheme_id)
        if existing:
            msg = "Already saved!" if lang == "en" else "ஏற்கனவே சேமிக்கப்பட்டது!"
            return jsonify({"success": True, "message": msg, "id": existing.id})

        scheme_data = scheme_service.get_by_id(scheme_id)
        if not scheme_data:
            msg = "Scheme not found." if lang == "en" else "திட்டம் கிடைக்கவில்லை."
            return jsonify({"success": False, "error": msg}), 404

        s = SavedScheme()
        s.user_id = user_id
        s.scheme_id = scheme_id
        s.scheme_data = scheme_data
        sid = s.save()

        msg = "Scheme saved!" if lang == "en" else "திட்டம் சேமிக்கப்பட்டது!"
        return jsonify({"success": True, "message": msg, "id": sid})
    except Exception as e:
        print(f"[Schemes Error] save: {traceback.format_exc()}")
        return jsonify({"success": False, "error": "Failed to save scheme"}), 500


@schemes_bp.route("/api/schemes/saved", methods=["GET"])
@login_required
def get_saved():
    try:
        user_id = session.get("user_id")
        items = SavedScheme.find_by_user(user_id)
        return jsonify({"success": True, "saved": [s.to_dict() for s in items]})
    except Exception as e:
        return jsonify({"success": False, "error": "Failed to load saved schemes"}), 500


@schemes_bp.route("/api/schemes/saved/<sid>", methods=["DELETE"])
@login_required
def delete_saved(sid):
    try:
        lang = session.get("lang", "en")
        s = SavedScheme.find_by_id(sid)
        if not s:
            msg = "Saved scheme not found." if lang == "en" else "சேமித்த திட்டம் கிடைக்கவில்லை."
            return jsonify({"success": False, "error": msg}), 404
        s.delete()
        msg = "Removed from saved!" if lang == "en" else "சேமிப்பிலிருந்து நீக்கப்பட்டது!"
        return jsonify({"success": True, "message": msg})
    except Exception as e:
        return jsonify({"success": False, "error": "Failed to delete"}), 500


@schemes_bp.route("/api/schemes/viewed", methods=["POST"])
@login_required
def log_viewed():
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"success": False, "error": "Invalid JSON"}), 400
        user_id = session.get("user_id")
        scheme_id = data.get("scheme_id", "")

        if not scheme_id:
            return jsonify({"success": True})

        scheme_data = scheme_service.get_by_id(scheme_id)
        if not scheme_data:
            return jsonify({"success": True})

        existing = RecentlyViewed.find_by_user_and_scheme(user_id, scheme_id)
        if existing:
            existing.update_viewed_at()
        else:
            r = RecentlyViewed()
            r.user_id = user_id
            r.scheme_id = scheme_id
            r.scheme_data = scheme_data
            r.save()

        recent_items = RecentlyViewed.find_by_user(user_id, 20)
        if len(recent_items) > 20:
            for item in recent_items[20:]:
                item.delete()

        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": True})


@schemes_bp.route("/api/schemes/recent", methods=["GET"])
@login_required
def get_recent():
    try:
        user_id = session.get("user_id")
        items = RecentlyViewed.find_by_user(user_id)
        return jsonify({"success": True, "recent": [r.to_dict() for r in items]})
    except Exception as e:
        return jsonify({"success": False, "error": "Failed to load recent views"}), 500


@schemes_bp.route("/api/schemes/notifications/toggle", methods=["POST"])
@login_required
def toggle_notification():
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"success": False, "error": "Invalid JSON"}), 400
        user_id = session.get("user_id")
        scheme_id = data.get("scheme_id", "")
        enabled = data.get("enabled", True)
        lang = session.get("lang", "en")

        if not scheme_id:
            msg = "Scheme ID required." if lang == "en" else "திட்ட ID தேவை."
            return jsonify({"success": False, "error": msg}), 400

        n = SchemeNotification()
        n.user_id = user_id
        n.scheme_id = scheme_id
        n.enabled = enabled
        nid = n.save()

        msg = "Notification settings updated!" if lang == "en" else "அறிவிப்பு அமைப்புகள் புதுப்பிக்கப்பட்டன!"
        return jsonify({"success": True, "message": msg, "id": nid, "enabled": enabled})
    except Exception as e:
        return jsonify({"success": False, "error": "Failed to update notification settings"}), 500


@schemes_bp.route("/api/schemes/notifications/status", methods=["GET"])
@login_required
def get_notification_status():
    try:
        user_id = session.get("user_id")
        items = SchemeNotification.find_by_user(user_id)
        status = {n.scheme_id: n.enabled for n in items}
        return jsonify({"success": True, "status": status})
    except Exception as e:
        return jsonify({"success": False, "error": "Failed to load notification status"}), 500


@schemes_bp.route("/api/schemes/eligibility/check", methods=["POST"])
@login_required
def check_eligibility():
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"success": False, "error": "Invalid JSON"}), 400
        lang = session.get("lang", "en")
        scheme_id = data.get("scheme_id", "")
        farm_size = data.get("farm_size", "").strip()
        crop_type = data.get("crop_type", "").strip()
        is_women = data.get("is_women", False)
        district = data.get("district", "").strip()

        scheme = scheme_service.get_by_id(scheme_id)
        if not scheme:
            msg = "Scheme not found." if lang == "en" else "திட்டம் கிடைக்கவில்லை."
            return jsonify({"success": False, "error": msg}), 404

        reasons = []
        eligible = True

        if scheme_id in ("pm-kisan", "pm-kmy"):
            try:
                fsize = float(farm_size) if farm_size else 0
            except ValueError:
                fsize = 0
            if fsize <= 0:
                eligible = False
                m = "Land ownership records needed for this scheme." if lang == "en" else "இந்த திட்டத்திற்கு நில உரிமை பதிவுகள் தேவை."
                reasons.append(m)

        if scheme_id in ("tn-women-farmer",):
            if not is_women:
                eligible = False
                m = "This scheme is specifically for women farmers." if lang == "en" else "இந்த திட்டம் குறிப்பாக பெண் விவசாயிகளுக்கானது."
                reasons.append(m)

        if scheme_id in ("tn-micro-irrigation", "tn-mechanization", "tn-free-seeds"):
            try:
                fsize2 = float(farm_size) if farm_size else 0
            except ValueError:
                fsize2 = 0
            if fsize2 > 5:
                m = "Priority for small and marginal farmers (up to 5 acres)." if lang == "en" else "சிறு மற்றும் குறு விவசாயிகளுக்கு முன்னுரிமை (5 ஏக்கர் வரை)."
                reasons.append(m)

        if scheme_id in ("tn-organic", "pkvy"):
            if not crop_type or "organic" not in crop_type.lower():
                m = "Organic farming interest or plan recommended." if lang == "en" else "இயற்கை விவசாய ஆர்வம் அல்லது திட்டம் பரிந்துரைக்கப்படுகிறது."
                reasons.append(m)

        if scheme_id in ("midh",):
            horticulture = ["vegetables", "fruits", "spices", "flowers", "कாய்கறிகள்", "पழங்கள்", "मசலாக்கள்"]
            if not any(h in crop_type.lower() for h in horticulture):
                m = "This scheme is for horticulture crops." if lang == "en" else "இந்த திட்டம் தோட்டக்கலை பயிர்களுக்கானது."
                reasons.append(m)

        m = "You are likely eligible for this scheme." if lang == "en" else "இந்த திட்டத்திற்கு நீங்கள் தகுதியானவர்."
        result_msg = m if eligible else ("You may face eligibility challenges for this scheme." if lang == "en" else "இந்த திட்டத்திற்கு நீங்கள் தகுதி சவால்களை சந்திக்க நேரிடலாம்.")

        return jsonify({
            "success": True,
            "eligible": eligible,
            "message": result_msg,
            "reasons": reasons,
        })
    except Exception as e:
        print(f"[Schemes Error] eligibility: {traceback.format_exc()}")
        msg = "Failed to check eligibility." if lang == "en" else "தகுதியை சரிபார்க்க முடியவில்லை."
        return jsonify({"success": False, "error": msg}), 500
