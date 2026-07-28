import os
import sys
import traceback
from dotenv import load_dotenv
from flask import Flask, render_template, session, request, redirect, url_for, jsonify
from datetime import datetime

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")

db = None
try:
    from pymongo import MongoClient
    import certifi
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        raise Exception("MONGO_URI not set in .env")
    print(f"[INFO] Connecting to MongoDB Atlas (10s timeout)...", file=sys.stderr)
    mongo_client = MongoClient(
        mongo_uri,
        serverSelectionTimeoutMS=10000,
        connectTimeoutMS=8000,
        tlsCAFile=certifi.where()
    )
    mongo_client.admin.command("ping")
    db = mongo_client["agriculture_assistant"]
    app.config["MONGO"] = db
    app.config["DB_TYPE"] = "mongodb"
    print("[OK] Connected to MongoDB Atlas - agriculture_assistant database", file=sys.stderr)
    if db["users"].count_documents({"username": "admin"}) == 0:
        from utils.auth import hash_password
        db["users"].insert_one({
            "username": "admin",
            "password": hash_password("admin123"),
            "is_admin": True,
            "preferred_language": "en",
            "created_at": datetime.utcnow(),
            "last_login": datetime.utcnow(),
        })
        print("[INFO] Default admin user created (admin/admin123)", file=sys.stderr)
except Exception as e:
    print(f"[ERROR] MongoDB Atlas connection failed:", file=sys.stderr)
    traceback.print_exc()
    print("[WARN] Attempting direct connection fallback...", file=sys.stderr)
    try:
        mongo_client = MongoClient(
            "mongodb://vk:vkdb@ac-mnzj5ki-shard-00-00.rwxd8tx.mongodb.net:27017,ac-mnzj5ki-shard-00-01.rwxd8tx.mongodb.net:27017,ac-mnzj5ki-shard-00-02.rwxd8tx.mongodb.net:27017/?authSource=admin&replicaSet=atlas-jaoq90-shard-0&tls=true&tlsInsecure=true",
            serverSelectionTimeoutMS=10000,
            connectTimeoutMS=8000,
        )
        mongo_client.admin.command("ping")
        db = mongo_client["agriculture_assistant"]
        app.config["MONGO"] = db
        app.config["DB_TYPE"] = "mongodb"
        print("[OK] Connected via direct connection fallback", file=sys.stderr)
    except Exception as e2:
        print(f"[ERROR] All MongoDB Atlas connection attempts failed.", file=sys.stderr)
        traceback.print_exc()
        print("[ERROR] Starting with limited functionality (database unavailable)", file=sys.stderr)
        from bcrypt import hashpw, gensalt
        import uuid
        _admin_pw = hashpw("admin123".encode(), gensalt()).decode("utf-8")
        class _MiniColl:
            def __init__(self):
                self._docs = {}
                self._id_counter = 0
            def _gen_id(self):
                self._id_counter += 1
                return str(uuid.uuid4()).replace("-","")[:24]
            def _matches(self, doc, query):
                if not query: return True
                for k, v in query.items():
                    if isinstance(v, dict):
                        for op, val in v.items():
                            if op == "$gte" and doc.get(k,-1) < val: return False
                            elif op == "$regex":
                                import re
                                if not re.search(val, str(doc.get(k,""))): return False
                            elif op == "$in":
                                if doc.get(k) not in val: return False
                    elif doc.get(k) != v: return False
                return True
            def find_one(self, query):
                for d in self._docs.values():
                    if self._matches(d, query): return dict(d)
                return None
            def find(self, query=None):
                return [dict(d) for d in self._docs.values() if self._matches(d, query or {})]
            def count_documents(self, query=None):
                return sum(1 for _ in self.find(query))
            def insert_one(self, data):
                d = dict(data); d["_id"] = self._gen_id()
                self._docs[d.get("username") or d.get("_id")] = d
                class _Result:
                    inserted_id = d["_id"]
                return _Result()
            def update_one(self, query, update):
                for d in self._docs.values():
                    if self._matches(d, query):
                        for op, val in update.items():
                            if op == "$set": d.update(val)
                            elif op == "$push":
                                for k, v in val.items():
                                    if k not in d: d[k] = []
                                    d[k].append(v)
                        return
            def delete_one(self, query):
                for key in list(self._docs.keys()):
                    if self._matches(self._docs[key], query):
                        del self._docs[key]; return
            def aggregate(self, pipeline=None): return []
            def __getitem__(self, name): return self
        class _MiniDB:
            def __init__(self):
                self._colls = {}
            def __getitem__(self, name):
                if name not in self._colls:
                    self._colls[name] = _MiniColl()
                return self._colls[name]
            def __getattr__(self, name):
                if name.startswith("_"):
                    return super().__getattribute__(name)
                return self[name]
        db = _MiniDB()
        db["users"].insert_one({
            "username": "admin", "password": _admin_pw,
            "is_admin": True, "preferred_language": "en",
            "created_at": datetime.utcnow(), "last_login": datetime.utcnow(),
        })
        app.config["MONGO"] = db
        app.config["DB_TYPE"] = "mock"
        print("[INFO] Admin user seeded (admin/admin123) for offline mode", file=sys.stderr)

app.config["UPLOAD_FOLDER"] = os.path.join("static", "uploads")

from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.chatbot import chatbot_bp
from routes.crops import crops_bp
from routes.weather import weather_bp
from routes.market import market_bp
from routes.schemes import schemes_bp
from routes.expenses import expenses_bp
from routes.analytics import analytics_bp
from routes.diagnosis import diagnosis_bp
from routes.notifications import notifications_bp
from routes.profile import profile_bp
from routes.admin import admin_bp
from routes.fertilizer import fertilizer_bp
from routes.irrigation import irrigation_bp

app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(chatbot_bp)
app.register_blueprint(crops_bp)
app.register_blueprint(weather_bp)
app.register_blueprint(market_bp)
app.register_blueprint(schemes_bp)
app.register_blueprint(expenses_bp)
app.register_blueprint(analytics_bp)
app.register_blueprint(diagnosis_bp)
app.register_blueprint(notifications_bp)
app.register_blueprint(profile_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(fertilizer_bp)
app.register_blueprint(irrigation_bp)

from utils.translations import TRANSLATIONS
from models.notification import Notification

@app.context_processor
def inject_globals():
    lang = session.get("lang", "en")
    unread_count = 0
    if "user_id" in session:
        unread_count = Notification.count_unread(session["user_id"])
    return {
        "lang": lang,
        "t": lambda key: TRANSLATIONS.get(lang, {}).get(key, TRANSLATIONS["en"].get(key, key)),
        "current_year": datetime.now().year,
        "unread_count": unread_count,
        "username": session.get("username", ""),
        "is_admin": session.get("is_admin", False),
    }

@app.route("/")
def index():
    return render_template("index.html", lang=session.get("lang", "en"))

@app.route("/set-language", methods=["POST"])
def set_language():
    data = request.get_json()
    lang = data.get("lang", "en")
    if lang in ["en", "ta"]:
        session["lang"] = lang
    return jsonify({"success": True})

@app.route("/crops")
def feature_crops():
    return render_template("crops.html", lang=session.get("lang", "en"))

@app.route("/api/contact", methods=["POST"])
def contact():
    data = request.get_json()
    lang = session.get("lang", "en")
    msg = "Message sent successfully! We will get back to you soon." if lang == "en" else "செய்தி வெற்றிகரமாக அனுப்பப்பட்டது! நாங்கள் விரைவில் உங்களை தொடர்பு கொள்வோம்."
    return jsonify({"success": True, "message": msg})

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)
