from flask import current_app
from datetime import datetime


class SavedScheme:
    def __init__(self, data=None):
        self.id = str(data.get("_id", "")) if data else ""
        self.user_id = data.get("user_id", "") if data else ""
        self.scheme_id = data.get("scheme_id", "") if data else ""
        self.scheme_data = data.get("scheme_data", {}) if data else {}
        self.created_at = data.get("created_at", datetime.utcnow()) if data else datetime.utcnow()

    @staticmethod
    def get_collection():
        return current_app.config["MONGO"]["saved_schemes"]

    @staticmethod
    def find_by_user(user_id):
        data = SavedScheme.get_collection().find({"user_id": user_id}).sort("created_at", -1)
        return [SavedScheme(d) for d in data]

    @staticmethod
    def find_by_id(rid):
        from bson.objectid import ObjectId
        data = SavedScheme.get_collection().find_one({"_id": ObjectId(rid)})
        return SavedScheme(data) if data else None

    @staticmethod
    def find_by_user_and_scheme(user_id, scheme_id):
        data = SavedScheme.get_collection().find_one({"user_id": user_id, "scheme_id": scheme_id})
        return SavedScheme(data) if data else None

    def save(self):
        data = {
            "user_id": self.user_id,
            "scheme_id": self.scheme_id,
            "scheme_data": self.scheme_data,
            "created_at": self.created_at,
        }
        result = SavedScheme.get_collection().insert_one(data)
        return str(result.inserted_id)

    def delete(self):
        from bson.objectid import ObjectId
        SavedScheme.get_collection().delete_one({"_id": ObjectId(self.id)})

    def to_dict(self):
        created = self.created_at
        if hasattr(created, "isoformat"):
            created = created.isoformat()
        else:
            created = str(created)
        return {
            "id": self.id,
            "user_id": self.user_id,
            "scheme_id": self.scheme_id,
            "scheme_data": self.scheme_data,
            "created_at": created,
        }


class RecentlyViewed:
    def __init__(self, data=None):
        self.id = str(data.get("_id", "")) if data else ""
        self.user_id = data.get("user_id", "") if data else ""
        self.scheme_id = data.get("scheme_id", "") if data else ""
        self.scheme_data = data.get("scheme_data", {}) if data else {}
        self.viewed_at = data.get("viewed_at", datetime.utcnow()) if data else datetime.utcnow()

    @staticmethod
    def get_collection():
        return current_app.config["MONGO"]["recently_viewed"]

    @staticmethod
    def find_by_user(user_id, limit=10):
        data = RecentlyViewed.get_collection().find({"user_id": user_id}).sort("viewed_at", -1).limit(limit)
        return [RecentlyViewed(d) for d in data]

    @staticmethod
    def find_by_user_and_scheme(user_id, scheme_id):
        data = RecentlyViewed.get_collection().find_one({"user_id": user_id, "scheme_id": scheme_id})
        return RecentlyViewed(data) if data else None

    def save(self):
        data = {
            "user_id": self.user_id,
            "scheme_id": self.scheme_id,
            "scheme_data": self.scheme_data,
            "viewed_at": self.viewed_at,
        }
        result = RecentlyViewed.get_collection().insert_one(data)
        return str(result.inserted_id)

    def update_viewed_at(self):
        from bson.objectid import ObjectId
        RecentlyViewed.get_collection().update_one(
            {"_id": ObjectId(self.id)},
            {"$set": {"viewed_at": datetime.utcnow()}}
        )

    def delete(self):
        from bson.objectid import ObjectId
        RecentlyViewed.get_collection().delete_one({"_id": ObjectId(self.id)})

    def to_dict(self):
        viewed = self.viewed_at
        if hasattr(viewed, "isoformat"):
            viewed = viewed.isoformat()
        else:
            viewed = str(viewed)
        return {
            "id": self.id,
            "user_id": self.user_id,
            "scheme_id": self.scheme_id,
            "scheme_data": self.scheme_data,
            "viewed_at": viewed,
        }


class SchemeNotification:
    def __init__(self, data=None):
        self.id = str(data.get("_id", "")) if data else ""
        self.user_id = data.get("user_id", "") if data else ""
        self.scheme_id = data.get("scheme_id", "") if data else ""
        self.enabled = data.get("enabled", True) if data else True
        self.created_at = data.get("created_at", datetime.utcnow()) if data else datetime.utcnow()

    @staticmethod
    def get_collection():
        return current_app.config["MONGO"]["scheme_notifications"]

    @staticmethod
    def find_by_user(user_id):
        data = SchemeNotification.get_collection().find({"user_id": user_id})
        return [SchemeNotification(d) for d in data]

    @staticmethod
    def find_by_user_and_scheme(user_id, scheme_id):
        data = SchemeNotification.get_collection().find_one({"user_id": user_id, "scheme_id": scheme_id})
        return SchemeNotification(data) if data else None

    def save(self):
        from bson.objectid import ObjectId
        existing = SchemeNotification.find_by_user_and_scheme(self.user_id, self.scheme_id)
        if existing:
            SchemeNotification.get_collection().update_one(
                {"_id": ObjectId(existing.id)},
                {"$set": {"enabled": self.enabled}}
            )
            return existing.id
        data = {
            "user_id": self.user_id,
            "scheme_id": self.scheme_id,
            "enabled": self.enabled,
            "created_at": self.created_at,
        }
        result = SchemeNotification.get_collection().insert_one(data)
        return str(result.inserted_id)

    def delete(self):
        from bson.objectid import ObjectId
        SchemeNotification.get_collection().delete_one({"_id": ObjectId(self.id)})

    def to_dict(self):
        created = self.created_at
        if hasattr(created, "isoformat"):
            created = created.isoformat()
        else:
            created = str(created)
        return {
            "id": self.id,
            "user_id": self.user_id,
            "scheme_id": self.scheme_id,
            "enabled": self.enabled,
            "created_at": created,
        }
