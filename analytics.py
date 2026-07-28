from flask import Blueprint, render_template, request, jsonify, session
from utils.auth import login_required
from services.analytics_service import AnalyticsService, AnalyticsDataService
from services.ai_service import AIService
import traceback
from datetime import datetime

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.route("/analytics")
@login_required
def index():
    lang = session.get("lang", "en")
    return render_template("analytics.html", lang=lang)


@analytics_bp.route("/api/analytics/overview")
@login_required
def get_overview():
    try:
        user_id = session.get("user_id")
        date_range = request.args.get("date_range", "6m")
        crop = request.args.get("crop", "")
        district = request.args.get("district", "")
        data = AnalyticsService.get_overview(user_id, date_range, crop, district)
        return jsonify({"success": True, **data})
    except Exception as e:
        print(f"[Analytics Error] overview: {traceback.format_exc()}")
        return jsonify({"success": False, "error": "Failed to load overview"}), 500


@analytics_bp.route("/api/analytics/crop-distribution")
@login_required
def get_crop_distribution():
    try:
        user_id = session.get("user_id")
        district = request.args.get("district", "")
        data = AnalyticsService.get_crop_distribution(user_id, district)
        return jsonify({"success": True, "distribution": data})
    except Exception as e:
        return jsonify({"success": False, "error": "Failed to load crop distribution"}), 500


@analytics_bp.route("/api/analytics/finances")
@login_required
def get_finances():
    try:
        user_id = session.get("user_id")
        months = int(request.args.get("months", 6))
        data = AnalyticsService.get_monthly_finances(user_id, months)
        return jsonify({"success": True, "monthly": data})
    except Exception as e:
        return jsonify({"success": False, "error": "Failed to load finances"}), 500


@analytics_bp.route("/api/analytics/activity")
@login_required
def get_activity():
    try:
        user_id = session.get("user_id")
        date_range = request.args.get("date_range", "6m")
        data = AnalyticsService.get_activity_timeline(user_id, date_range)
        return jsonify({"success": True, "activity": data})
    except Exception as e:
        return jsonify({"success": False, "error": "Failed to load activity"}), 500


@analytics_bp.route("/api/analytics/quick-stats")
@login_required
def get_quick_stats():
    try:
        user_id = session.get("user_id")
        data = AnalyticsService.get_quick_stats(user_id)
        return jsonify({"success": True, **data})
    except Exception as e:
        return jsonify({"success": False, "error": "Failed to load quick stats"}), 500


@analytics_bp.route("/api/analytics/insights")
@login_required
def get_insights():
    try:
        user_id = session.get("user_id")
        lang = session.get("lang", "en")
        crop = request.args.get("crop", "")
        district = request.args.get("district", "")
        data = AnalyticsService.get_ai_insights(user_id, lang, crop, district)
        return jsonify({"success": True, **data})
    except Exception as e:
        print(f"[Analytics Error] insights: {traceback.format_exc()}")
        lang = session.get("lang", "en")
        if lang == "ta":
            return jsonify({"success": True, "insights": "பகுப்பாய்வை உருவாக்க முடியவில்லை. பின்னர் மீண்டும் முயற்சிக்கவும்.", "confidence": 0})
        return jsonify({"success": True, "insights": "Unable to generate analysis. Please try again later.", "confidence": 0})


@analytics_bp.route("/api/analytics/options")
@login_required
def get_options():
    try:
        user_id = session.get("user_id")
        crops = AnalyticsDataService.get_crop_options(user_id)
        districts = AnalyticsDataService.get_district_options(user_id)
        return jsonify({"success": True, "crops": crops, "districts": districts})
    except Exception as e:
        return jsonify({"success": False, "error": "Failed to load options"}), 500


@analytics_bp.route("/api/analytics/export/<fmt>")
@login_required
def export_report(fmt):
    try:
        user_id = session.get("user_id")
        date_range = request.args.get("date_range", "6m")
        crop = request.args.get("crop", "")
        district = request.args.get("district", "")
        data, mime, filename = AnalyticsService.export_report(user_id, fmt, date_range, crop, district)
        if data is None:
            return jsonify({"success": False, "error": "Unsupported format"}), 400
        import base64
        if isinstance(data, str):
            data = data.encode()
        return jsonify({
            "success": True,
            "data": base64.b64encode(data).decode("ascii"),
            "filename": filename,
            "mime": mime,
            "encoding": "base64",
        })
    except Exception as e:
        print(f"[Analytics Error] export: {traceback.format_exc()}")
        return jsonify({"success": False, "error": "Failed to export"}), 500
