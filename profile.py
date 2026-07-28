from flask import Blueprint, render_template, request, jsonify, session
from utils.auth import login_required
from models.user import User
from utils.helpers import get_districts

profile_bp = Blueprint("profile", __name__)

@profile_bp.route("/profile", methods=["GET"])
@login_required
def index():
    user_id = session.get("user_id")
    user = User.find_by_id(user_id)
    return render_template(
        "profile.html",
        user=user.to_dict() if user else {},
        districts=get_districts(),
        lang=session.get("lang", "en"),
    )

@profile_bp.route("/api/profile", methods=["PUT"])
@login_required
def update_profile():
    data = request.get_json()
    user_id = session.get("user_id")
    lang = session.get("lang", "en")

    user = User.find_by_id(user_id)
    if not user:
        msg = "User not found." if lang == "en" else "பயனர் கிடைக்கவில்லை."
        return jsonify({"success": False, "message": msg})

    update_data = {}
    for field in ["district", "village", "preferred_language", "farm_size", "primary_crops"]:
        if field in data:
            update_data[field] = data[field]

    if "farm_size" in update_data:
        try:
            update_data["farm_size"] = float(update_data["farm_size"])
        except (ValueError, TypeError):
            msg = "Invalid farm size." if lang == "en" else "தவறான பண்ணை அளவு."
            return jsonify({"success": False, "message": msg})

    user.update(update_data)

    if "preferred_language" in update_data:
        session["lang"] = update_data["preferred_language"]

    msg = "Profile updated successfully!" if lang == "en" else "சுயவிவரம் வெற்றிகரமாக புதுப்பிக்கப்பட்டது!"
    return jsonify({"success": True, "message": msg})
