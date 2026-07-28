from flask import current_app, session
from datetime import datetime, timedelta
from services.ai_service import AIService
import calendar
import io
import base64
import csv


class AnalyticsService:
    @staticmethod
    def get_overview(user_id, date_range="6m", crop_filter="", district=""):
        db = current_app.config["MONGO"]
        now = datetime.utcnow()
        date_from = AnalyticsService._date_from_range(date_range, now)

        crops_coll = db["crops"]
        expenses_coll = db["expenses"]
        diagnoses_coll = db["diagnoses"]
        fertilizer_coll = db["fertilizer"]
        irrigation_coll = db["irrigation"]
        weather_coll = db["weather_history"]
        market_coll = db["market_history"]
        schemes_coll = db["saved_schemes"]

        crop_query = {"user_id": user_id}
        if crop_filter:
            crop_query["crop_name"] = crop_filter
        if district:
            crop_query["district"] = district

        crops = list(crops_coll.find(crop_query))
        total_crops = len(crops)
        total_area = sum(float(c.get("land_size", 0)) for c in crops)

        expense_query = {"user_id": user_id, "date": {"$gte": date_from.strftime("%Y-%m-%d")}}
        inc_pipe = [{"$match": {**expense_query, "type": "income"}}, {"$group": {"_id": None, "total": {"$sum": "$amount"}}}]
        exp_pipe = [{"$match": {**expense_query, "type": "expense"}}, {"$group": {"_id": None, "total": {"$sum": "$amount"}}}]
        inc_result = list(expenses_coll.aggregate(inc_pipe))
        exp_result = list(expenses_coll.aggregate(exp_pipe))
        total_income = inc_result[0]["total"] if inc_result else 0
        total_expense = exp_result[0]["total"] if exp_result else 0
        net_profit = total_income - total_expense

        diag_query = {"user_id": user_id}
        if crop_filter:
            diag_query["crop"] = crop_filter
        if district:
            diag_query["district"] = district
        diagnoses = list(diagnoses_coll.find(diag_query))

        fert_count = fertilizer_coll.count_documents({"user_id": user_id})
        irr_count = irrigation_coll.count_documents({"user_id": user_id})
        weather_count = weather_coll.count_documents({"user_id": user_id})
        market_count = market_coll.count_documents({"user_id": user_id})
        scheme_count = schemes_coll.count_documents({"user_id": user_id})

        farm_score = AnalyticsService._calc_farm_score(
            total_crops, total_area, total_income, total_expense,
            len(diagnoses), fert_count, irr_count, weather_count, scheme_count
        )

        return {
            "total_crops": total_crops,
            "total_area": round(total_area, 2),
            "total_income": round(total_income, 2),
            "total_expense": round(total_expense, 2),
            "net_profit": round(net_profit, 2),
            "farm_score": farm_score,
            "crop_count": total_crops,
            "diagnosis_count": len(diagnoses),
            "fertilizer_count": fert_count,
            "irrigation_count": irr_count,
        }

    @staticmethod
    def get_crop_distribution(user_id, district=""):
        db = current_app.config["MONGO"]
        query = {"user_id": user_id}
        if district:
            query["district"] = district
        pipe = [{"$match": query}, {"$group": {"_id": "$crop_name", "count": {"$sum": 1}, "area": {"$sum": "$land_size"}}}]
        return list(db["crops"].aggregate(pipe))

    @staticmethod
    def get_monthly_finances(user_id, months=6):
        db = current_app.config["MONGO"]
        now = datetime.utcnow()
        data = []
        for i in range(months - 1, -1, -1):
            dt = datetime(now.year, now.month, 1) - timedelta(days=30 * i)
            y, m = dt.year, dt.month
            month_str = f"{y}-{m:02d}"
            pipe = [
                {"$match": {"user_id": user_id, "date": {"$regex": f"^{month_str}"}}},
                {"$group": {"_id": "$type", "total": {"$sum": "$amount"}}}
            ]
            results = list(db["expenses"].aggregate(pipe))
            inc = 0
            exp = 0
            for r in results:
                if r["_id"] == "income":
                    inc = r["total"]
                elif r["_id"] == "expense":
                    exp = r["total"]
            data.append({
                "month": dt.strftime("%b %Y"),
                "income": round(inc, 2),
                "expense": round(exp, 2),
                "profit": round(inc - exp, 2),
            })
        return data

    @staticmethod
    def get_activity_timeline(user_id, date_range="6m"):
        db = current_app.config["MONGO"]
        now = datetime.utcnow()
        date_from = AnalyticsService._date_from_range(date_range, now)
        date_str = date_from.strftime("%Y-%m-%d")

        crops = list(db["crops"].find({"user_id": user_id, "created_at": {"$gte": date_from}}))
        diagnoses = list(db["diagnoses"].find({"user_id": user_id, "created_at": {"$gte": date_from}}))
        fertilizers = list(db["fertilizer"].find({"user_id": user_id, "created_at": {"$gte": date_from}}))
        irrigations = list(db["irrigation"].find({"user_id": user_id, "created_at": {"$gte": date_from}}))

        timeline = {}
        for item in crops:
            d = item.get("created_at", date_from).strftime("%Y-%m-%d")
            timeline.setdefault(d, {"crops": 0, "diagnoses": 0, "fertilizers": 0, "irrigations": 0})
            timeline[d]["crops"] += 1
        for item in diagnoses:
            d = item.get("created_at", date_from).strftime("%Y-%m-%d")
            timeline.setdefault(d, {"crops": 0, "diagnoses": 0, "fertilizers": 0, "irrigations": 0})
            timeline[d]["diagnoses"] += 1
        for item in fertilizers:
            d = item.get("created_at", date_from).strftime("%Y-%m-%d")
            timeline.setdefault(d, {"crops": 0, "diagnoses": 0, "fertilizers": 0, "irrigations": 0})
            timeline[d]["fertilizers"] += 1
        for item in irrigations:
            d = item.get("created_at", date_from).strftime("%Y-%m-%d")
            timeline.setdefault(d, {"crops": 0, "diagnoses": 0, "fertilizers": 0, "irrigations": 0})
            timeline[d]["irrigations"] += 1

        result = [{"date": k, **v} for k, v in sorted(timeline.items())]
        return result

    @staticmethod
    def get_quick_stats(user_id):
        db = current_app.config["MONGO"]
        result = {}

        crops_coll = db["crops"]
        expenses_coll = db["expenses"]
        diagnoses_coll = db["diagnoses"]
        weather_coll = db["weather_history"]
        market_coll = db["market_history"]
        schemes_coll = db["saved_schemes"]
        irrigation_coll = db["irrigation"]

        crops = list(crops_coll.find({"user_id": user_id}))
        if crops:
            crop_counts = {}
            for c in crops:
                name = c.get("crop_name", "Unknown")
                crop_counts[name] = crop_counts.get(name, 0) + 1
            result["most_cultivated_crop"] = max(crop_counts, key=crop_counts.get)
        else:
            result["most_cultivated_crop"] = None

        inc_pipe = [{"$match": {"user_id": user_id, "type": "income"}}, {"$group": {"_id": None, "total": {"$sum": "$amount"}}}]
        exp_pipe = [{"$match": {"user_id": user_id, "type": "expense"}}, {"$group": {"_id": None, "total": {"$sum": "$amount"}}}]
        inc_result = list(expenses_coll.aggregate(inc_pipe))
        exp_result = list(expenses_coll.aggregate(exp_pipe))
        total_inc = inc_result[0]["total"] if inc_result else 0
        total_exp = exp_result[0]["total"] if exp_result else 0
        result["avg_monthly_profit"] = round((total_inc - total_exp) / max(1, datetime.utcnow().month), 2)

        diag_pipe = [{"$match": {"user_id": user_id}}, {"$group": {"_id": "$disease", "count": {"$sum": 1}}}, {"$sort": {"count": -1}}, {"$limit": 1}]
        diag_result = list(diagnoses_coll.aggregate(diag_pipe))
        result["most_common_disease"] = diag_result[0]["_id"] if diag_result else None

        weather_count = weather_coll.count_documents({"user_id": user_id})
        irrigation_count = irrigation_coll.count_documents({"user_id": user_id})
        total_water = 0
        irr_records = list(irrigation_coll.find({"user_id": user_id}))
        for ir in irr_records:
            rec = ir.get("recommendation", {})
            if isinstance(rec, dict):
                total_water += float(rec.get("water_usage", 0) or 0)
        efficiency = 100
        if irrigation_count > 0 and total_water > 0:
            efficiency = min(100, round((irrigation_count / total_water) * 100))
        result["water_efficiency"] = efficiency

        market_pipe = [{"$match": {"user_id": user_id}}, {"$group": {"_id": "$market", "count": {"$sum": 1}}}, {"$sort": {"count": -1}}, {"$limit": 1}]
        market_result = list(market_coll.aggregate(market_pipe))
        result["favorite_market"] = market_result[0]["_id"] if market_result else None

        result["schemes_saved"] = schemes_coll.count_documents({"user_id": user_id})

        return result

    @staticmethod
    def get_ai_insights(user_id, lang="en", crop="", district=""):
        db = current_app.config["MONGO"]

        crops = list(db["crops"].find({"user_id": user_id}))
        expenses = list(db["expenses"].find({"user_id": user_id}))
        diagnoses = list(db["diagnoses"].find({"user_id": user_id}))
        fertilizers = list(db["fertilizer"].find({"user_id": user_id}))
        irrigations = list(db["irrigation"].find({"user_id": user_id}))
        schemes = list(db["saved_schemes"].find({"user_id": user_id}))
        weather = list(db["weather_history"].find({"user_id": user_id}))

        total_inc = sum(e["amount"] for e in expenses if e.get("type") == "income")
        total_exp = sum(e["amount"] for e in expenses if e.get("type") == "expense")
        net = total_inc - total_exp
        crop_count = len(crops)
        diag_count = len(diagnoses)
        fert_count = len(fertilizers)
        irr_count = len(irrigations)
        scheme_count = len(schemes)
        weather_count = len(weather)

        district_str = f" in {district}" if district else ""
        crop_str = f" growing {crop}" if crop else ""
        area = sum(float(c.get("land_size", 0)) for c in crops)

        if lang == "ta":
            prompt = (
                f"நீங்கள் தமிழ்நாடு விவசாய ஆய்வாளர். {district_str} பகுதியில் உள்ள ஒரு விவசாயியின்{area} ஏக்கர் நிலத்தில் {crop_count} பயிர்கள் பயிரிடப்படுகின்றன.\n\n"
                f"நிதி: மொத்த வருமானம் ₹{total_inc:.0f}, மொத்த செலவு ₹{total_exp:.0f}, நிகர லாபம் ₹{net:.0f}\n"
                f"பயிர்கள்: {crop_count}, பகுதி: {area:.1f} ஏக்கர்\n"
                f"நோய் கண்டறிதல்கள்: {diag_count}, உர பரிந்துரைகள்: {fert_count}, நீர்ப்பாசன திட்டங்கள்: {irr_count}\n"
                f"சேமிக்கப்பட்ட திட்டங்கள்: {scheme_count}, வானிலை தரவுகள்: {weather_count}\n\n"
                f"மேலே உள்ள தரவுகளின் அடிப்படையில் சுருக்கமான 5-7 புள்ளிகள் கொண்ட பகுப்பாய்வை தமிழில் வழங்கவும்:\n"
                f"- ஒட்டுமொத்த பண்ணை செயல்திறன்\n"
                f"- நிதி நிலை\n"
                f"- பயிர் ஆரோக்கியம்\n"
                f"- நீர் மேலாண்மை பரிந்துரை\n"
                f"- ஒரு முன்னேற்ற பரிந்துரை\n"
                f"- ஒரு எச்சரிக்கை (பொருந்தினால்)\n"
                f"- {crop_str}க்கான குறிப்பிட்ட ஆலோசனை\n\n"
                f"சுருக்கமாகவும் பயனுள்ளதாகவும் இருக்க வேண்டும். ஒவ்வொரு புள்ளியும் ஒரு வரியாக இருக்கட்டும்."
            )
        else:
            district_text = f" in {district}" if district else ""
            crop_text = f" growing {crop}" if crop else ""
            prompt = (
                f"You are a Tamil Nadu farm analyst. A farmer{district_str}{crop_text} with {area:.1f} acres growing {crop_count} crops.\n\n"
                f"Financials: Total Income ₹{total_inc:.0f}, Total Expense ₹{total_exp:.0f}, Net Profit ₹{net:.0f}\n"
                f"Crops: {crop_count}, Area: {area:.1f} acres\n"
                f"Diagnoses: {diag_count}, Fertilizer Plans: {fert_count}, Irrigation Plans: {irr_count}\n"
                f"Saved Schemes: {scheme_count}, Weather Records: {weather_count}\n\n"
                f"Based on the above data, provide a concise 5-7 bullet point analysis covering:\n"
                f"- Overall farm performance\n"
                f"- Financial status\n"
                f"- Crop health observations\n"
                f"- Water management suggestion\n"
                f"- One improvement recommendation\n"
                f"- One warning (if applicable)\n"
                f"- Specific advice for {crop or 'the current season'}\n\n"
                f"Keep it brief and actionable. Each point should be one line."
            )

        ai = AIService()
        try:
            insights = ai.get_response(prompt, lang)
            confidence = AnalyticsService._calc_confidence(crop_count, diag_count, fert_count, irr_count, weather_count, scheme_count, total_inc)
        except Exception:
            if lang == "ta":
                insights = "✅ உங்கள் பண்ணை சீராக செயல்படுகிறது. செலவுகளை கண்காணித்து மகசூலை அதிகரிக்க முயற்சிக்கவும்."
            else:
                insights = "✅ Your farm is performing steadily. Monitor expenses and look for ways to increase yield."
            confidence = 60
        return {"insights": insights, "confidence": confidence}

    @staticmethod
    def export_report(user_id, fmt, date_range="6m", crop="", district=""):
        import csv, io, json
        overview = AnalyticsService.get_overview(user_id, date_range, crop, district)
        quick = AnalyticsService.get_quick_stats(user_id)
        monthly = AnalyticsService.get_monthly_finances(user_id)

        if fmt == "csv":
            output = io.StringIO()
            w = csv.writer(output)
            w.writerow(["Metric", "Value"])
            for k, v in overview.items():
                w.writerow([k, v])
            for k, v in quick.items():
                w.writerow([k, v])
            w.writerow([])
            w.writerow(["Month", "Income", "Expense", "Profit"])
            for m in monthly:
                w.writerow([m["month"], m["income"], m["expense"], m["profit"]])
            return output.getvalue(), "text/csv", "analytics_report.csv"
        elif fmt == "json":
            data = {"overview": overview, "quick_stats": quick, "monthly": monthly}
            return json.dumps(data, indent=2), "application/json", "analytics_report.json"
        elif fmt == "pdf":
            html = AnalyticsService._generate_pdf_html(overview, quick, monthly)
            try:
                from weasyprint import HTML
                buf = io.BytesIO()
                HTML(string=html).write_pdf(buf)
                buf.seek(0)
                return buf.read(), "application/pdf", "analytics_report.pdf"
            except ImportError:
                fallback = json.dumps({"overview": overview, "quick_stats": quick, "monthly": monthly})
                return fallback, "application/json", "analytics_report.json"
        return None, None, None

    @staticmethod
    def _generate_pdf_html(overview, quick, monthly):
        html = "<html><head><style>body{font-family:Arial;padding:20px}"
        html += "h1{color:#1a7d36}h2{color:#145a27}table{width:100%;border-collapse:collapse;margin:10px 0}"
        html += "th,td{padding:8px 12px;text-align:left;border-bottom:1px solid #ddd}"
        html += "th{background:#e8f5e9;color:#1a7d36}</style></head><body>"
        html += "<h1>Farm Analytics Report</h1>"
        html += "<h2>Overview</h2><table>"
        labels = {"total_crops": "Total Crops", "total_area": "Farm Area (acres)",
                  "total_income": "Total Income", "total_expense": "Total Expenses",
                  "net_profit": "Net Profit", "farm_score": "AI Farm Score"}
        for k, v in overview.items():
            label = labels.get(k, k)
            html += f"<tr><td>{label}</td><td>{v}</td></tr>"
        html += "</table>"
        html += "<h2>Quick Statistics</h2><table>"
        qlabels = {"most_cultivated_crop": "Most Cultivated Crop", "avg_monthly_profit": "Avg Monthly Profit",
                   "most_common_disease": "Most Common Disease", "water_efficiency": "Water Efficiency (%)",
                   "favorite_market": "Favorite Market", "schemes_saved": "Schemes Saved"}
        for k, v in quick.items():
            label = qlabels.get(k, k)
            html += f"<tr><td>{label}</td><td>{v or 'N/A'}</td></tr>"
        html += "</table>"
        html += "<h2>Monthly Finances</h2><table><tr><th>Month</th><th>Income</th><th>Expense</th><th>Profit</th></tr>"
        for m in monthly:
            html += f"<tr><td>{m['month']}</td><td>₹{m['income']:.0f}</td><td>₹{m['expense']:.0f}</td><td>₹{m['profit']:.0f}</td></tr>"
        html += "</table></body></html>"
        return html

    @staticmethod
    def _date_from_range(date_range, now):
        if date_range == "30d":
            return now - timedelta(days=30)
        elif date_range == "6m":
            return now - timedelta(days=180)
        elif date_range == "1y":
            return now - timedelta(days=365)
        return now - timedelta(days=180)

    @staticmethod
    def _calc_farm_score(crops, area, income, expense, diagnoses, fert, irr, weather, schemes):
        score = 0
        if crops > 0:
            score += min(20, crops * 5)
        if income > 0:
            ratio = income / max(1, income + expense)
            score += min(20, ratio * 20)
        if fert > 0:
            score += min(10, fert * 2)
        if irr > 0:
            score += min(10, irr * 2)
        if weather > 0:
            score += min(10, weather * 2)
        if schemes > 0:
            score += min(10, schemes * 5)
        if diagnoses == 0:
            score += 10
        elif diagnoses <= 2:
            score += 5
        if area > 0:
            score += min(10, (area / 10) * 10)
        return min(100, round(score))

    @staticmethod
    def _calc_confidence(crops, diagnoses, fert, irr, weather, schemes, income):
        total = crops + diagnoses + fert + irr + weather + schemes
        if total == 0 and income == 0:
            return 30
        base = min(95, 40 + total * 3)
        if income > 0:
            base += 5
        return min(98, base)


class AnalyticsDataService:
    @staticmethod
    def get_crop_options(user_id):
        db = current_app.config["MONGO"]
        crops = db["crops"].distinct("crop_name", {"user_id": user_id})
        return sorted(crops)

    @staticmethod
    def get_district_options(user_id):
        db = current_app.config["MONGO"]
        districts = db["crops"].distinct("district", {"user_id": user_id})
        return sorted(districts)
