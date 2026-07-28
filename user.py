from flask import current_app
from datetime import datetime

class User:
    def __init__(self, data=None):
        self.id = str(data.get("_id", "")) if data else ""
        self.username = data.get("username", "") if data else ""
        self.password = data.get("password", "") if data else ""
        self.district = data.get("district", "") if data else ""
        self.village = data.get("village", "") if data else ""
        self.preferred_language = data.get("preferred_language", "en") if data else "en"
        self.farm_size = data.get("farm_size", 0) if data else 0
        self.primary_crops = data.get("primary_crops", "") if data else ""
        self.is_admin = data.get("is_admin", False) if data else False
        self.created_at = data.get("created_at", datetime.utcnow()) if data else datetime.utcnow()
        self.last_login = data.get("last_login", datetime.utcnow()) if data else datetime.utcnow()

    @staticmethod
    def get_collection():
        return current_app.config["MONGO"]["users"]

    @staticmethod
    def find_by_username(username):
        data = User.get_collection().find_one({"username": username})
        return User(data) if data else None

    @staticmethod
    def find_by_id(user_id):
        from bson.objectid import ObjectId
        data = User.get_collection().find_one({"_id": ObjectId(user_id)})
        return User(data) if data else None

    def save(self):
        data = {
            "username": self.username,
            "password": self.password,
            "district": self.district,
            "village": self.village,
            "preferred_language": self.preferred_language,
            "farm_size": self.farm_size,
            "primary_crops": self.primary_crops,
            "is_admin": self.is_admin,
            "created_at": self.created_at,
            "last_login": self.last_login,
        }
        result = User.get_collection().insert_one(data)
        return str(result.inserted_id)

    def update(self, data):
        from bson.objectid import ObjectId
        User.get_collection().update_one(
            {"_id": ObjectId(self.id)},
            {"$set": data}
        )

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "district": self.district,
            "village": self.village,
            "preferred_language": self.preferred_language,
            "farm_size": self.farm_size,
            "primary_crops": self.primary_crops,
            "is_admin": self.is_admin,
            "created_at": self.created_at,
            "last_login": self.last_login,
        }
