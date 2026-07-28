from flask import Blueprint, render_template, request, jsonify, session
from utils.auth import admin_required
from models.user import User
from models.crop import Crop
from models.notification import Notification
from services.market_service import MarketService
from services.scheme_service import SchemeService
from datetime import datetime

admin_bp = Blueprint("admin", __name__)
market_service = MarketService()
scheme_service = SchemeService()

@admin_bp.route("/admin")
@admin_required
def index():
    return render_template("admin.html", lang=session.get("lang", "en"))

@admin_bp.route("/api/admin/dashboard")
@admin_required
def dashboard_data():
    total_users = User.get_collection().count_documents({})
    total_crops = Crop.count_all()
    total_schemes = len(scheme_service.get_all_schemes())
    today_active = User.get_collection().count_documents({
        "last_login": {"$gte": datetime.now().strftime("%Y-%m-%d")}
    })

    users = list(User.get_collection().find().sort("created_at", -1).limit(10))
    crops_list = list(Crop.get_collection().find().sort("created_at", -1).limit(10))

    return jsonify({
        "success": True,
        "total_users": total_users,
        "total_crops": total_crops,
        "total_schemes": total_schemes,
        "active_today": today_active,
        "recent_users": [User(u).to_dict() for u in users],
        "recent_crops": [Crop(c).to_dict() for c in crops_list],
    })

@admin_bp.route("/api/admin/users", methods=["GET"])
@admin_required
def get_users():
    users = list(User.get_collection().find().sort("created_at", -1))
    return jsonify({"success": True, "users": [User(u).to_dict() for u in users]})

@admin_bp.route("/api/admin/users/<user_id>", methods=["DELETE"])
@admin_required
def delete_user(user_id):
    lang = session.get("lang", "en")
    from bson.objectid import ObjectId
    result = User.get_collection().delete_one({"_id": ObjectId(user_id)})
    if result.deleted_count:
        msg = "User deleted." if lang == "en" else "பயனர் நீக்கப்பட்டார்."
        return jsonify({"success": True, "message": msg})
    msg = "User not found." if lang == "en" else "பயனர் கிடைக்கவில்லை."
    return jsonify({"success": False, "message": msg})

@admin_bp.route("/api/admin/crops", methods=["GET"])
@admin_required
def get_all_crops():
    crops = list(Crop.get_collection().find().sort("created_at", -1))
    return jsonify({"success": True, "crops": [Crop(c).to_dict() for c in crops]})

@admin_bp.route("/api/admin/schemes", methods=["GET"])
@admin_required
def get_schemes():
    schemes = scheme_service.get_all_schemes()
    return jsonify({"success": True, "schemes": schemes})

@admin_bp.route("/api/admin/notifications", methods=["POST"])
@admin_required
def send_notification():
    data = request.get_json()
    lang = session.get("lang", "en")

    title = data.get("title", "")
    message = data.get("message", "")
    notif_type = data.get("type", "info")

    if not title or not message:
        msg = "Title and message required." if lang == "en" else "தலைப்பு மற்றும் செய்தி தேவை."
        return jsonify({"success": False, "message": msg})

    users = User.get_collection().find({})
    count = 0
    for u in users:
        Notification.create_notification(str(u["_id"]), notif_type, title, message)
        count += 1

    msg = f"Notification sent to {count} users." if lang == "en" else f"{count} பயனர்களுக்கு அறிவிப்பு அனுப்பப்பட்டது."
    return jsonify({"success": True, "message": msg})
