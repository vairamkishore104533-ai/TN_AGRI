from flask import Blueprint, render_template, request, jsonify, session
from utils.auth import login_required
from models.notification import Notification
from services.notification_service import NotificationService
import traceback
from datetime import datetime

notifications_bp = Blueprint("notifications", __name__)


@notifications_bp.route("/notifications")
@login_required
def index():
    return render_template("notifications.html", lang=session.get("lang", "en"))


@notifications_bp.route("/api/notifications")
@login_required
def get_notifications():
    try:
        user_id = session.get("user_id")
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 50))
        category = request.args.get("category", "")
        all_param = request.args.get("all", "0")

        query = {"user_id": user_id}
        if category:
            query["category"] = category

        total = Notification.get_collection().count_documents(query)
        notifs = list(Notification.get_collection().find(query).sort("created_at", -1).skip((page - 1) * per_page).limit(per_page))
        unread = Notification.count_unread(user_id)

        return jsonify({
            "success": True,
            "notifications": [Notification(n).to_dict() for n in notifs],
            "unread_count": unread,
            "total": total,
            "page": page,
        })
    except Exception as e:
        print(f"[Notifications Error] list: {traceback.format_exc()}")
        return jsonify({"success": False, "error": "Failed to load notifications"}), 500


@notifications_bp.route("/api/notifications/generate", methods=["POST"])
@login_required
def generate():
    try:
        user_id = session.get("user_id")
        lang = session.get("lang", "en")
        NotificationService.generate_all(user_id, lang)
        return jsonify({"success": True, "message": "Notifications generated"})
    except Exception as e:
        print(f"[Notifications Error] generate: {traceback.format_exc()}")
        return jsonify({"success": False, "error": "Failed to generate"}), 500


@notifications_bp.route("/api/notifications/read", methods=["POST"])
@login_required
def mark_read():
    try:
        data = request.get_json(silent=True) or {}
        notif_id = data.get("notification_id")
        if notif_id:
            notif = Notification.find_by_id(notif_id)
            if notif:
                notif.mark_read()
        else:
            user_id = session.get("user_id")
            Notification.mark_all_read(user_id)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": "Failed"}), 500


@notifications_bp.route("/api/notifications/clear", methods=["POST"])
@login_required
def clear():
    try:
        data = request.get_json(silent=True) or {}
        user_id = session.get("user_id")
        notif_id = data.get("notification_id")
        if notif_id:
            notif = Notification.find_by_id(notif_id)
            if notif and notif.user_id == user_id:
                Notification.get_collection().delete_one({"_id": notif.id})
        else:
            Notification.clear_all(user_id)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": "Failed"}), 500


@notifications_bp.route("/api/notifications/unread")
@login_required
def unread_count():
    try:
        user_id = session.get("user_id")
        count = Notification.count_unread(user_id)
        return jsonify({"success": True, "count": count})
    except Exception as e:
        return jsonify({"success": False, "error": "Failed"}), 500
