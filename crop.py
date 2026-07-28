from flask import current_app
from datetime import datetime

class Crop:
    def __init__(self, data=None):
        self.id = str(data.get("_id", "")) if data else ""
        self.user_id = data.get("user_id", "") if data else ""
        self.crop_name = data.get("crop_name", "") if data else ""
        self.village = data.get("village", "") if data else ""
        self.district = data.get("district", "") if data else ""
        self.land_size = data.get("land_size", 0) if data else 0
        self.soil_type = data.get("soil_type", "") if data else ""
        self.season = data.get("season", "") if data else ""
        self.planting_date = data.get("planting_date", "") if data else ""
        self.harvest_date = data.get("harvest_date", "") if data else ""
        self.status = data.get("status", "Planned") if data else "Planned"
        self.notes = data.get("notes", "") if data else ""
        self.created_at = data.get("created_at", datetime.utcnow()) if data else datetime.utcnow()
        self.updated_at = data.get("updated_at", datetime.utcnow()) if data else datetime.utcnow()

    @staticmethod
    def get_collection():
        return current_app.config["MONGO"]["crops"]

    @staticmethod
    def find_by_user(user_id):
        crops_data = Crop.get_collection().find({"user_id": user_id}).sort("created_at", -1)
        return [Crop(c) for c in crops_data]

    @staticmethod
    def find_by_id(crop_id):
        from bson.objectid import ObjectId
        data = Crop.get_collection().find_one({"_id": ObjectId(crop_id)})
        return Crop(data) if data else None

    @staticmethod
    def count_by_user(user_id):
        return Crop.get_collection().count_documents({"user_id": user_id})

    @staticmethod
    def search_crops(user_id, query=""):
        import re
        pattern = re.compile(re.escape(query), re.IGNORECASE)
        crops_data = Crop.get_collection().find({
            "user_id": user_id,
            "$or": [
                {"crop_name": pattern},
                {"village": pattern},
                {"district": pattern},
                {"soil_type": pattern},
                {"season": pattern},
                {"status": pattern},
            ]
        }).sort("created_at", -1)
        return [Crop(c) for c in crops_data]

    @staticmethod
    def filter_crops(user_id, filters=None):
        query = {"user_id": user_id}
        if filters:
            for key in ["district", "soil_type", "status", "season"]:
                val = filters.get(key)
                if val:
                    query[key] = val
        crops_data = Crop.get_collection().find(query).sort("created_at", -1)
        return [Crop(c) for c in crops_data]

    @staticmethod
    def get_stats(user_id):
        pipeline = [
            {"$match": {"user_id": user_id}},
            {
                "$group": {
                    "_id": None,
                    "total": {"$sum": 1},
                    "total_area": {"$sum": "$land_size"},
                    "avg_land_size": {"$avg": "$land_size"},
                    "crop_names": {"$push": "$crop_name"},
                    "soil_types": {"$push": "$soil_type"},
                    "statuses": {"$push": "$status"},
                    "districts": {"$push": "$district"},
                }
            }
        ]
        result = list(Crop.get_collection().aggregate(pipeline))
        if not result:
            return {
                "total_crops": 0, "active_crops": 0, "harvest_ready": 0,
                "total_area": 0, "avg_land_size": 0, "most_cultivated": "",
                "most_common_soil": "", "most_common_district": "",
            }
        r = result[0]
        from collections import Counter
        crop_counts = Counter(r["crop_names"])
        soil_counts = Counter(r["soil_types"])
        district_counts = Counter(r["districts"])
        status_counts = Counter(r["statuses"])
        return {
            "total_crops": r["total"],
            "active_crops": status_counts.get("Growing", 0) + status_counts.get("Seeded", 0) + status_counts.get("Flowering", 0) + status_counts.get("Planned", 0),
            "harvest_ready": status_counts.get("Harvest Ready", 0),
            "total_area": round(r["total_area"], 2),
            "avg_land_size": round(r["avg_land_size"], 2),
            "most_cultivated": crop_counts.most_common(1)[0][0] if crop_counts else "",
            "most_common_soil": soil_counts.most_common(1)[0][0] if soil_counts else "",
            "most_common_district": district_counts.most_common(1)[0][0] if district_counts else "",
        }

    @staticmethod
    def get_upcoming_activities(user_id):
        from datetime import timedelta
        crops = Crop.find_by_user(user_id)
        activities = []
        today = datetime.utcnow().date()
        for c in crops:
            if c.status == "Growing" or c.status == "Flowering":
                activities.append({
                    "type": "irrigate",
                    "crop": c.crop_name,
                    "action": "Irrigate",
                    "days": 0,
                    "urgency": "today",
                })
            if c.harvest_date:
                try:
                    hd = datetime.strptime(c.harvest_date, "%Y-%m-%d").date()
                    diff = (hd - today).days
                    if 0 <= diff <= 30:
                        activities.append({
                            "type": "harvest",
                            "crop": c.crop_name,
                            "action": "Harvest",
                            "days": diff,
                            "urgency": "soon" if diff > 7 else "imminent",
                        })
                except ValueError:
                    pass
        activities.sort(key=lambda a: a["days"])
        return activities[:10]

    def save(self):
        now = datetime.utcnow()
        data = {
            "user_id": self.user_id,
            "crop_name": self.crop_name,
            "village": self.village,
            "district": self.district,
            "land_size": self.land_size,
            "soil_type": self.soil_type,
            "season": self.season,
            "planting_date": self.planting_date,
            "harvest_date": self.harvest_date,
            "status": self.status,
            "notes": self.notes,
            "created_at": self.created_at if self.created_at else now,
            "updated_at": now,
        }
        result = Crop.get_collection().insert_one(data)
        return str(result.inserted_id)

    def update(self, data):
        from bson.objectid import ObjectId
        now = datetime.utcnow()
        data["updated_at"] = now
        Crop.get_collection().update_one(
            {"_id": ObjectId(self.id)},
            {"$set": data}
        )

    def delete(self):
        from bson.objectid import ObjectId
        Crop.get_collection().delete_one({"_id": ObjectId(self.id)})

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "crop_name": self.crop_name,
            "village": self.village,
            "district": self.district,
            "land_size": self.land_size,
            "soil_type": self.soil_type,
            "season": self.season,
            "planting_date": self.planting_date,
            "harvest_date": self.harvest_date,
            "status": self.status,
            "notes": self.notes,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
