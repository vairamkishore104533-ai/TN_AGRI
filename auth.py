import jwt
import datetime
import bcrypt
import os
from functools import wraps
from flask import request, jsonify, redirect, url_for, session

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")

def hash_password(password):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def check_password(password, hashed):
    if isinstance(hashed, bytes):
        hashed = hashed.decode("utf-8")
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))

def generate_token(user_id):
    payload = {
        "user_id": str(user_id),
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7),
        "iat": datetime.datetime.utcnow(),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def verify_token(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = session.get("token")
        if not token:
            return redirect(url_for("auth.login"))
        payload = verify_token(token)
        if not payload:
            session.clear()
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = session.get("token")
        if not token:
            return redirect(url_for("auth.login"))
        payload = verify_token(token)
        if not payload:
            session.clear()
            return redirect(url_for("auth.login"))
        if not session.get("is_admin"):
            return redirect(url_for("dashboard.index"))
        return f(*args, **kwargs)
    return decorated_function
