from flask import current_app
from datetime import datetime
from bson.objectid import ObjectId

class ChatConversation:
    def __init__(self, data=None):
        self.id = str(data.get("_id", "")) if data else ""
        self.user_id = data.get("user_id", "") if data else ""
        self.title = data.get("title", "New Chat") if data else ""
        self.district = data.get("district", "") if data else ""
        self.messages = data.get("messages", []) if data else []
        self.created_at = data.get("created_at", datetime.utcnow()) if data else datetime.utcnow()
        self.updated_at = data.get("updated_at", datetime.utcnow()) if data else datetime.utcnow()

    @staticmethod
    def get_collection():
        return current_app.config["MONGO"]["chat_conversations"]

    @staticmethod
    def find_by_id(conv_id):
        try:
            oid = ObjectId(conv_id) if isinstance(conv_id, str) else conv_id
            data = ChatConversation.get_collection().find_one({"_id": oid})
            if data:
                return ChatConversation(data)
        except Exception:
            pass
        try:
            data = ChatConversation.get_collection().find_one({"_id": str(conv_id)})
            if data:
                return ChatConversation(data)
        except Exception:
            pass
        return None

    @staticmethod
    def find_by_user(user_id, limit=20):
        result = ChatConversation.get_collection().find({"user_id": user_id})
        if isinstance(result, list):
            result.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
            result = result[:limit]
        else:
            result = result.sort("updated_at", -1).limit(limit)
        return [ChatConversation(d) for d in result]

    def save(self):
        data = {
            "user_id": self.user_id,
            "title": self.title,
            "district": self.district,
            "messages": self.messages,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        result = ChatConversation.get_collection().insert_one(data)
        rid = result.inserted_id
        self.id = str(rid) if not isinstance(rid, str) else rid
        return self.id

    def _object_id(self):
        try:
            return ObjectId(self.id) if self.id else None
        except Exception:
            return None

    def update(self, data):
        oid = self._object_id()
        if not oid:
            return
        ChatConversation.get_collection().update_one(
            {"_id": oid},
            {"$set": data}
        )

    def add_message(self, role, content):
        oid = self._object_id()
        if not oid:
            return
        msg = {"role": role, "content": content, "timestamp": datetime.utcnow().isoformat()}
        self.messages.append(msg)
        self.updated_at = datetime.utcnow()
        ChatConversation.get_collection().update_one(
            {"_id": oid},
            {"$set": {"messages": self.messages, "updated_at": self.updated_at}}
        )

    @staticmethod
    def delete_by_id(conv_id):
        try:
            oid = ObjectId(conv_id) if isinstance(conv_id, str) else conv_id
            ChatConversation.get_collection().delete_one({"_id": oid})
        except Exception:
            try:
                ChatConversation.get_collection().delete_one({"_id": str(conv_id)})
            except Exception:
                pass

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "district": self.district,
            "messages": [
                {"role": m["role"], "content": m["content"]}
                for m in self.messages
            ],
            "created_at": self.created_at.isoformat() if hasattr(self.created_at, "isoformat") else str(self.created_at),
            "updated_at": self.updated_at.isoformat() if hasattr(self.updated_at, "isoformat") else str(self.updated_at),
        }
