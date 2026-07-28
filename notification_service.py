from flask import current_app
from datetime import datetime, timedelta
from models.notification import Notification
from services.scheme_service import SchemeService
from services.ai_service import AIService


class NotificationService:
    @staticmethod
    def generate_all(user_id, lang="en"):
        NotificationService._generate_scheme_notifications(user_id, lang)
        NotificationService._generate_market_notifications(user_id, lang)
        NotificationService._generate_irrigation_notifications(user_id, lang)
        NotificationService._generate_fertilizer_notifications(user_id, lang)

    @staticmethod
    def _exists(user_id, notif_type, title, hours=24):
        since = datetime.utcnow() - timedelta(hours=hours)
        existing = Notification.get_collection().find_one({
            "user_id": user_id, "type": notif_type, "title": title,
            "created_at": {"$gte": since}
        })
        return existing is not None

    @staticmethod
    def _generate_scheme_notifications(user_id, lang):
        db = current_app.config["MONGO"]
        crops = list(db["crops"].find({"user_id": user_id}))
        if not crops:
            return
        user_districts = list(set(c.get("district", "") for c in crops if c.get("district")))
        schemes = SchemeService.get_all_schemes(lang)[:5]
        for s in schemes:
            title = s.get("title_en" if lang == "en" else "title_ta", "")
            if not title:
                continue
            if NotificationService._exists(user_id, "scheme", title, 168):
                continue
            if lang == "ta":
                msg = f"{title} திட்டம் உங்கள் மாவட்டத்திற்கு கிடைக்கிறது. விவரங்களைப் பார்க்கவும்."
            else:
                msg = f"{title} scheme is available. Check details."
            Notification.create_notification(
                user_id=user_id, notif_type="scheme",
                title=title if lang == "en" else s.get("title_ta", title),
                message=msg, category="scheme", priority="medium",
                related_id=s.get("id", ""),
            )

        saved = list(db["saved_schemes"].find({"user_id": user_id}))
        for s in saved:
            sd = s.get("scheme_data", {})
            title = sd.get("title_en" if lang == "en" else "title_ta", "") or sd.get("title", "")
            if not title:
                continue
            key = f"update_{title}"
            if NotificationService._exists(user_id, "scheme_update", key, 168):
                continue
            if lang == "ta":
                msg = f"நீங்கள் சேமித்த {title} திட்டத்தில் புதிய புதுப்பிப்பு உள்ளது."
            else:
                msg = f"New update available for your saved scheme: {title}"
            Notification.create_notification(
                user_id=user_id, notif_type="scheme_update",
                title=title, message=msg,
                category="scheme", priority="medium",
                related_id=str(s.get("_id", "")),
            )

    @staticmethod
    def _generate_market_notifications(user_id, lang):
        db = current_app.config["MONGO"]
        crops = list(db["crops"].find({"user_id": user_id}))
        if not crops:
            return
        user_crops = list(set(c.get("crop_name", "").lower() for c in crops if c.get("crop_name")))
        market_history = list(db["market_history"].find({"user_id": user_id}).sort("created_at", -1).limit(50))
        for crop_name in user_crops:
            crop_records = [m for m in market_history if m.get("crop", "").lower() == crop_name]
            if len(crop_records) < 2:
                continue
            latest = crop_records[0]
            prev = crop_records[1]
            try:
                curr_price = float(latest.get("price", 0))
                prev_price = float(prev.get("price", 1))
                pct_change = ((curr_price - prev_price) / prev_price) * 100
            except (ValueError, TypeError):
                continue
            market_name = latest.get("market", "local")
            crop_display = crop_name.title()

            if abs(pct_change) < 5:
                continue

            if pct_change > 0:
                key = f"price_up_{crop_name}_{market_name}"
                if NotificationService._exists(user_id, "price_up", key, 72):
                    continue
                if lang == "ta":
                    title = f"{crop_display} விலை அதிகரிப்பு"
                    msg = f"{crop_display} விலை {market_name} சந்தையில் {pct_change:.0f}% அதிகரித்துள்ளது. விற்பனை செய்ய ஏற்ற நேரம்."
                else:
                    title = f"{crop_display} Price Up"
                    msg = f"{crop_display} price increased by {pct_change:.0f}% in {market_name}. Good time to sell."
                Notification.create_notification(
                    user_id=user_id, notif_type="price_up",
                    title=title, message=msg,
                    category="market", priority="high" if pct_change > 15 else "medium",
                    related_crop=crop_display,
                )
            else:
                key = f"price_down_{crop_name}_{market_name}"
                if NotificationService._exists(user_id, "price_down", key, 72):
                    continue
                if lang == "ta":
                    title = f"{crop_display} விலை குறைவு"
                    msg = f"{crop_display} விலை {market_name} சந்தையில் {abs(pct_change):.0f}% குறைந்துள்ளது."
                else:
                    title = f"{crop_display} Price Drop"
                    msg = f"{crop_display} price dropped by {abs(pct_change):.0f}% in {market_name}."
                Notification.create_notification(
                    user_id=user_id, notif_type="price_down",
                    title=title, message=msg,
                    category="market", priority="high" if abs(pct_change) > 15 else "medium",
                    related_crop=crop_display,
                )

    @staticmethod
    def _generate_irrigation_notifications(user_id, lang):
        db = current_app.config["MONGO"]
        crops = list(db["crops"].find({"user_id": user_id}))
        for c in crops:
            crop_name = c.get("crop_name", "")
            status = c.get("status", "").lower()
            if not crop_name or status in ("harvested", "planning"):
                continue
            key = f"irr_{crop_name}_{user_id[:8]}"
            if NotificationService._exists(user_id, "irrigation", key, 48):
                continue
            if lang == "ta":
                title = f"{crop_name} நீர்ப்பாசன நினைவூட்டல்"
                msg = f"{crop_name} பயிருக்கு நீர்ப்பாசனம் தேவைப்படலாம். வானிலை மற்றும் மண்ணின் ஈரப்பதத்தை சரிபார்க்கவும்."
            else:
                title = f"{crop_name} Irrigation Reminder"
                msg = f"{crop_name} may need irrigation soon. Check weather and soil moisture."
            Notification.create_notification(
                user_id=user_id, notif_type="irrigation",
                title=title, message=msg,
                category="irrigation", priority="medium",
                related_crop=crop_name,
            )

    @staticmethod
    def _generate_fertilizer_notifications(user_id, lang):
        db = current_app.config["MONGO"]
        crops = list(db["crops"].find({"user_id": user_id}))
        for c in crops:
            crop_name = c.get("crop_name", "")
            status = c.get("status", "").lower()
            if not crop_name or status in ("harvested", "planning"):
                continue
            fert_records = list(db["fertilizer"].find({"user_id": user_id, "crop": crop_name}).sort("created_at", -1).limit(1))
            if not fert_records:
                continue
            key = f"fert_{crop_name}_{user_id[:8]}"
            if NotificationService._exists(user_id, "fertilizer", key, 72):
                continue
            if lang == "ta":
                title = f"{crop_name} உர நினைவூட்டல்"
                msg = f"{crop_name} பயிருக்கு உரம் இட வேண்டிய நேரம். உங்கள் உர பரிந்துரையை பார்க்கவும்."
            else:
                title = f"{crop_name} Fertilizer Reminder"
                msg = f"Time to apply fertilizer for {crop_name}. Check your fertilizer recommendation."
            Notification.create_notification(
                user_id=user_id, notif_type="fertilizer",
                title=title, message=msg,
                category="fertilizer", priority="low",
                related_crop=crop_name,
            )
