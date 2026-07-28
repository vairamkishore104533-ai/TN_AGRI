from flask import current_app
from datetime import datetime
import re


class Expense:
    def __init__(self, data=None):
        self.id = str(data.get("_id", "")) if data else ""
        self.user_id = data.get("user_id", "") if data else ""
        self.type = data.get("type", "expense") if data else "expense"
        self.category = data.get("category", "") if data else ""
        self.amount = data.get("amount", 0) if data else 0
        self.description = data.get("description", "") if data else ""
        self.date = data.get("date", datetime.utcnow().strftime("%Y-%m-%d")) if data else datetime.utcnow().strftime("%Y-%m-%d")
        self.created_at = data.get("created_at", datetime.utcnow()) if data else datetime.utcnow()

    @staticmethod
    def get_collection():
        return current_app.config["MONGO"]["expenses"]

    @staticmethod
    def find_by_user(user_id):
        data = Expense.get_collection().find({"user_id": user_id}).sort("date", -1)
        return [Expense(e) for e in data]

    @staticmethod
    def find_by_id(expense_id):
        from bson.objectid import ObjectId
        data = Expense.get_collection().find_one({"_id": ObjectId(expense_id)})
        return Expense(data) if data else None

    @staticmethod
    def find_paginated(user_id, page=1, per_page=20, search="", etype="", category="", month="", year="", sort_by="date", sort_order="desc"):
        query = {"user_id": user_id}
        if etype:
            query["type"] = etype
        if category:
            query["category"] = category
        if month and year:
            query["date"] = {"$regex": f"^{year}-{int(month):02d}"}
        elif year:
            query["date"] = {"$regex": f"^{year}"}
        if search:
            pattern = re.compile(re.escape(search), re.IGNORECASE)
            query["$or"] = [{"description": pattern}, {"category": pattern}]
        sort_dir = -1 if sort_order == "desc" else 1
        if sort_by == "amount":
            sort_field = "amount"
        elif sort_by == "date":
            sort_field = "date"
        else:
            sort_field = "date"
        total = Expense.get_collection().count_documents(query)
        data = Expense.get_collection().find(query).sort(sort_field, sort_dir).skip((page - 1) * per_page).limit(per_page)
        return [Expense(e) for e in data], total

    def save(self):
        data = {
            "user_id": self.user_id,
            "type": self.type,
            "category": self.category,
            "amount": self.amount,
            "description": self.description,
            "date": self.date,
            "created_at": self.created_at,
        }
        result = Expense.get_collection().insert_one(data)
        return str(result.inserted_id)

    def update(self, data):
        from bson.objectid import ObjectId
        update = {}
        if "type" in data:
            update["type"] = data["type"]
        if "category" in data:
            update["category"] = data["category"]
        if "amount" in data:
            update["amount"] = float(data["amount"])
        if "description" in data:
            update["description"] = data["description"]
        if "date" in data:
            update["date"] = data["date"]
        if update:
            Expense.get_collection().update_one({"_id": ObjectId(self.id)}, {"$set": update})
            for k, v in update.items():
                setattr(self, k, v)

    def delete(self):
        from bson.objectid import ObjectId
        Expense.get_collection().delete_one({"_id": ObjectId(self.id)})

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
            "amount": self.amount,
            "description": self.description,
            "date": self.date,
            "created_at": created,
        }

    @staticmethod
    def get_summary(user_id):
        pipeline = [
            {"$match": {"user_id": user_id}},
            {"$group": {"_id": "$type", "total": {"$sum": "$amount"}, "count": {"$sum": 1}}}
        ]
        results = list(Expense.get_collection().aggregate(pipeline))
        summary = {"income": 0, "expense": 0, "income_count": 0, "expense_count": 0}
        for r in results:
            t = r["_id"]
            summary[t] = r["total"]
            summary[t + "_count"] = r["count"]
        return summary

    @staticmethod
    def get_stats(user_id):
        pipeline_income = [
            {"$match": {"user_id": user_id, "type": "income"}},
            {"$group": {"_id": None, "max": {"$max": "$amount"}, "min": {"$min": "$amount"}, "avg": {"$avg": "$amount"}, "count": {"$sum": 1}}}
        ]
        pipeline_expense = [
            {"$match": {"user_id": user_id, "type": "expense"}},
            {"$group": {"_id": None, "max": {"$max": "$amount"}, "min": {"$min": "$amount"}, "avg": {"$avg": "$amount"}, "count": {"$sum": 1}}}
        ]
        inc_result = list(Expense.get_collection().aggregate(pipeline_income))
        exp_result = list(Expense.get_collection().aggregate(pipeline_expense))
        inc_max = Expense.get_collection().find_one({"user_id": user_id, "type": "income"}, sort=[("amount", -1)])
        exp_max = Expense.get_collection().find_one({"user_id": user_id, "type": "expense"}, sort=[("amount", -1)])
        return {
            "highest_income": inc_max["amount"] if inc_max else 0,
            "highest_income_cat": inc_max["category"] if inc_max else "",
            "highest_expense": exp_max["amount"] if exp_max else 0,
            "highest_expense_cat": exp_max["category"] if exp_max else "",
            "avg_monthly_income": round(inc_result[0]["avg"], 2) if inc_result else 0,
            "avg_monthly_expense": round(exp_result[0]["avg"], 2) if exp_result else 0,
            "total_transactions": (inc_result[0]["count"] if inc_result else 0) + (exp_result[0]["count"] if exp_result else 0),
        }

    @staticmethod
    def get_category_breakdown(user_id, etype="expense"):
        pipeline = [
            {"$match": {"user_id": user_id, "type": etype}},
            {"$group": {"_id": "$category", "total": {"$sum": "$amount"}, "count": {"$sum": 1}}},
            {"$sort": {"total": -1}}
        ]
        return list(Expense.get_collection().aggregate(pipeline))

    @staticmethod
    def get_monthly_data(user_id, year=None):
        if not year:
            year = datetime.utcnow().year
        pipeline = [
            {"$match": {"user_id": user_id, "date": {"$regex": f"^{year}"}}},
            {"$group": {"_id": {"type": "$type", "month": {"$substr": ["$date", 5, 2]}}, "total": {"$sum": "$amount"}}}
        ]
        results = list(Expense.get_collection().aggregate(pipeline))
        months = {}
        for r in results:
            m = int(r["_id"]["month"])
            t = r["_id"]["type"]
            if m not in months:
                months[m] = {"income": 0, "expense": 0}
            months[m][t] = r["total"]
        return months

    @staticmethod
    def get_recent(user_id, limit=5):
        data = Expense.get_collection().find({"user_id": user_id}).sort("date", -1).limit(limit)
        return [Expense(e) for e in data]

    @staticmethod
    def get_top_categories(user_id, etype="expense", limit=5):
        pipeline = [
            {"$match": {"user_id": user_id, "type": etype}},
            {"$group": {"_id": "$category", "total": {"$sum": "$amount"}}},
            {"$sort": {"total": -1}},
            {"$limit": limit}
        ]
        return list(Expense.get_collection().aggregate(pipeline))
