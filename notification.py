from flask import current_app
from datetime import datetime

class Notification:
    def __init__(self, data=None):
        self.id = str(data.get("_id", "")) if data else ""
        self.user_id = data.get("user_id", "") if data else ""
        self.type = data.get("type", "info") if data else "info"
        self.category = data.get("category", "info") if data else "info"
        self.title = data.get("title", "") if data else ""
        self.message = data.get("message", "") if data else ""
        self.priority = data.get("priority", "low") if data else "low"
        self.related_crop = data.get("related_crop", "") if data else ""
        self.related_id = data.get("related_id", "") if data else ""
        self.is_read = data.get("is_read", False) if data else False
        self.created_at = data.get("created_at", datetime.utcnow()) if data else datetime.utcnow()

    @staticmethod
    def get_collection():
        return current_app.config["MONGO"]["notifications"]

    @staticmethod
    def find_by_user(user_id, limit=20):
        notif_data = Notification.get_collection().find(
            {"user_id": user_id}
        ).sort("created_at", -1).limit(limit)
        return [Notification(n) for n in notif_data]

    @staticmethod
    def count_unread(user_id):
        return Notification.get_collection().count_documents({
            "user_id": user_id,
            "is_read": False
        })

    def save(self):
        data = {
            "user_id": self.user_id,
            "type": self.type,
            "category": self.category,
            "title": self.title,
            "message": self.message,
            "priority": self.priority,
            "related_crop": self.related_crop,
            "related_id": self.related_id,
            "is_read": self.is_read,
            "created_at": self.created_at,
        }
        result = Notification.get_collection().insert_one(data)
        return str(result.inserted_id)

    def mark_read(self):
        from bson.objectid import ObjectId
        Notification.get_collection().update_one(
            {"_id": ObjectId(self.id)},
            {"$set": {"is_read": True}}
        )

    @staticmethod
    def find_by_id(notif_id):
        from bson.objectid import ObjectId
        data = Notification.get_collection().find_one({"_id": ObjectId(notif_id)})
        return Notification(data) if data else None

    @staticmethod
    def mark_all_read(user_id):
        Notification.get_collection().update_many(
            {"user_id": user_id, "is_read": False},
            {"$set": {"is_read": True}}
        )

    @staticmethod
    def clear_all(user_id):
        Notification.get_collection().delete_many({"user_id": user_id})

    @staticmethod
    def create_notification(user_id, notif_type, title, message, category="info", priority="low", related_crop="", related_id=""):
        notif = Notification()
        notif.user_id = user_id
        notif.type = notif_type
        notif.category = category
        notif.title = title
        notif.message = message
        notif.priority = priority
        notif.related_crop = related_crop
        notif.related_id = related_id
        notif.created_at = datetime.utcnow()
        return notif.save()

    def to_dict(self):
        created = self.created_at
        if hasattr(created, "isoformat"):
            created = created.isoformat()
        else:
            created = str(created)
        return {
            "id": self.id,
            "user_id": self.user_id,
            "type": self.type,
            "category": self.category,
            "title": self.title,
            "message": self.message,
            "priority": self.priority,
            "related_crop": self.related_crop,
            "related_id": self.related_id,
            "is_read": self.is_read,
            "created_at": created,
        }
