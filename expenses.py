from flask import Blueprint, render_template, request, jsonify, session, json
from utils.auth import login_required
from models.expense import Expense
from services.expense_service import ExpenseAnalytics, BudgetManager, ExportService
from services.ai_service import AIService
from datetime import datetime
import traceback

expenses_bp = Blueprint("expenses", __name__)

INCOME_CATEGORIES = [
    "Crop Sales", "Vegetable Sales", "Fruit Sales", "Dairy Income",
    "Poultry Income", "Fisheries", "Government Subsidy", "Scheme Benefits",
    "Equipment Rental", "Other Income",
]

INCOME_CATEGORIES_TA = [
    "பயிர் விற்பனை", "காய்கறி விற்பனை", "பழ விற்பனை", "பால் வருமானம்",
    "கோழி வருமானம்", "மீன்வளம்", "அரசு மானியம்", "திட்ட நன்மைகள்",
    "உபகரண வாடகை", "பிற வருமானம்",
]

EXPENSE_CATEGORIES = [
    "Seeds", "Fertilizers", "Pesticides", "Irrigation", "Electricity",
    "Labour", "Machinery", "Fuel", "Transportation", "Equipment Maintenance",
    "Animal Feed", "Loan Repayment", "Miscellaneous",
]

EXPENSE_CATEGORIES_TA = [
    "விதைகள்", "உரங்கள்", "பூச்சிக்கொல்லிகள்", "நீர்ப்பாசனம்", "மின்சாரம்",
    "கூலி", "இயந்திரங்கள்", "எரிபொருள்", "போக்குவரத்து", "உபகரண பராமரிப்பு",
    "கால்நடை தீவனம்", "கடன் திருப்பிச் செலுத்துதல்", "இதர",
]


@expenses_bp.route("/expenses")
@login_required
def index():
    try:
        lang = session.get("lang", "en")
        income_cats = []
        for i, c in enumerate(INCOME_CATEGORIES):
            income_cats.append({"en": c, "ta": INCOME_CATEGORIES_TA[i] if i < len(INCOME_CATEGORIES_TA) else c})
        expense_cats = []
        for i, c in enumerate(EXPENSE_CATEGORIES):
            expense_cats.append({"en": c, "ta": EXPENSE_CATEGORIES_TA[i] if i < len(EXPENSE_CATEGORIES_TA) else c})
        budgets = BudgetManager.get_budgets(session.get("user_id"))
        return render_template(
            "expenses.html",
            lang=lang,
            income_categories=income_cats,
            income_categories_json=json.dumps(income_cats),
            expense_categories=expense_cats,
            expense_categories_json=json.dumps(expense_cats),
            budgets_json=json.dumps(budgets),
            today=datetime.utcnow().strftime("%Y-%m-%d"),
            page_error=None,
        )
    except Exception as e:
        print(f"[Expenses Page Error] {traceback.format_exc()}")
        # Render a minimal fallback page so the user doesn't see a 500
        lang = session.get("lang", "en")
        err_msg = "Failed to load finances. Please try again later." if lang == "en" else "நிதித் தகவல்களை ஏற்ற முடியவில்லை. பின்னர் மீண்டும் முயற்சிக்கவும்."
        return render_template(
            "expenses.html",
            lang=lang,
            income_categories=[],
            income_categories_json="[]",
            expense_categories=[],
            expense_categories_json="[]",
            budgets_json="[]",
            today=datetime.utcnow().strftime("%Y-%m-%d"),
            page_error=err_msg,
        )


@expenses_bp.route("/api/expenses", methods=["GET"])
@login_required
def get_expenses():
    try:
        user_id = session.get("user_id")
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 20))
        search = request.args.get("search", "").strip()
        etype = request.args.get("type", "").strip()
        category = request.args.get("category", "").strip()
        month = request.args.get("month", "").strip()
        year = request.args.get("year", "").strip()
        sort_by = request.args.get("sort_by", "date")
        sort_order = request.args.get("sort_order", "desc")
        results, total = Expense.find_paginated(user_id, page, per_page, search, etype, category, month, year, sort_by, sort_order)
        summary = Expense.get_summary(user_id)
        return jsonify({
            "success": True,
            "expenses": [e.to_dict() for e in results],
            "summary": summary,
            "total": total,
            "page": page,
            "pages": max(1, -(-total // per_page)),
        })
    except Exception as e:
        print(f"[Expenses Error] get: {traceback.format_exc()}")
        return jsonify({"success": False, "error": "Failed to load expenses"}), 500


@expenses_bp.route("/api/expenses", methods=["POST"])
@login_required
def add_expense():
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"success": False, "error": "Invalid JSON"}), 400
        user_id = session.get("user_id")
        lang = session.get("lang", "en")
        etype = (data.get("type") or "").strip()
        category = (data.get("category") or "").strip()
        amount = str(data.get("amount") or "").strip()
        description = (data.get("description") or "").strip()
        date_val = (data.get("date") or "").strip()
        if not etype or not category or not amount:
            msg = "Type, category, and amount are required." if lang == "en" else "வகை, பிரிவு மற்றும் தொகை தேவை."
            return jsonify({"success": False, "error": msg}), 400
        try:
            amount = float(amount)
        except ValueError:
            msg = "Invalid amount." if lang == "en" else "தவறான தொகை."
            return jsonify({"success": False, "error": msg}), 400
        if amount <= 0:
            msg = "Amount must be positive." if lang == "en" else "தொகை நேர்மறையாக இருக்க வேண்டும்."
            return jsonify({"success": False, "error": msg}), 400
        e = Expense()
        e.user_id = user_id
        e.type = etype
        e.category = category
        e.amount = amount
        e.description = description[:500] if description else ""
        e.date = date_val or datetime.utcnow().strftime("%Y-%m-%d")
        e.save()
        msg = "Transaction added successfully!" if lang == "en" else "பரிவர்த்தனை வெற்றிகரமாக சேர்க்கப்பட்டது!"
        return jsonify({"success": True, "message": msg})
    except Exception as e:
        print(f"[Expenses Error] add: {traceback.format_exc()}")
        try:
            lang = session.get("lang", "en")
        except Exception:
            lang = "en"
        msg = f"Failed to add transaction: {str(e)}" if lang == "en" else "பரிவர்த்தனை சேர்க்க முடியவில்லை."
        print(f"[Expenses Error] add detail: {traceback.format_exc()}")
        return jsonify({"success": False, "error": msg}), 500


@expenses_bp.route("/api/expenses/<expense_id>", methods=["PUT"])
@login_required
def update_expense(expense_id):
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"success": False, "error": "Invalid JSON"}), 400
        lang = session.get("lang", "en")
        e = Expense.find_by_id(expense_id)
        if not e:
            msg = "Transaction not found." if lang == "en" else "பரிவர்த்தனை கிடைக்கவில்லை."
            return jsonify({"success": False, "error": msg}), 404
        if "amount" in data and data["amount"]:
            try:
                val = float(data["amount"])
                if val <= 0:
                    raise ValueError
                data["amount"] = val
            except (ValueError, TypeError):
                msg = "Invalid amount." if lang == "en" else "தவறான தொகை."
                return jsonify({"success": False, "error": msg}), 400
        if "description" in data:
            data["description"] = (data.get("description", "") or "")[:500]
        e.update(data)
        msg = "Transaction updated successfully!" if lang == "en" else "பரிவர்த்தனை வெற்றிகரமாக புதுப்பிக்கப்பட்டது!"
        return jsonify({"success": True, "message": msg})
    except Exception as e:
        print(f"[Expenses Error] update: {traceback.format_exc()}")
        return jsonify({"success": False, "error": "Failed to update"}), 500


@expenses_bp.route("/api/expenses/<expense_id>", methods=["DELETE"])
@login_required
def delete_expense(expense_id):
    try:
        lang = session.get("lang", "en")
        e = Expense.find_by_id(expense_id)
        if not e:
            msg = "Transaction not found." if lang == "en" else "பரிவர்த்தனை கிடைக்கவில்லை."
            return jsonify({"success": False, "error": msg}), 404
        e.delete()
        msg = "Transaction deleted successfully!" if lang == "en" else "பரிவர்த்தனை வெற்றிகரமாக நீக்கப்பட்டது!"
        return jsonify({"success": True, "message": msg})
    except Exception as e:
        return jsonify({"success": False, "error": "Failed to delete"}), 500


@expenses_bp.route("/api/expenses/analytics")
@login_required
def get_analytics():
    try:
        user_id = session.get("user_id")
        data = ExpenseAnalytics.get_chart_data(user_id)
        return jsonify({"success": True, "analytics": data})
    except Exception as e:
        print(f"[Expenses Error] analytics: {traceback.format_exc()}")
        return jsonify({"success": False, "error": "Failed to load analytics"}), 500


@expenses_bp.route("/api/expenses/insights")
@login_required
def get_insights():
    try:
        user_id = session.get("user_id")
        lang = session.get("lang", "en")
        text = ExpenseAnalytics.get_ai_insights(user_id, lang)
        return jsonify({"success": True, "insights": text})
    except Exception as e:
        print(f"[Expenses Error] insights: {traceback.format_exc()}")
        return jsonify({"success": False, "error": "Failed to generate insights"}), 500


@expenses_bp.route("/api/expenses/budgets", methods=["GET"])
@login_required
def get_budgets():
    try:
        user_id = session.get("user_id")
        budgets = BudgetManager.get_budgets(user_id)
        alerts = BudgetManager.get_alerts(user_id)
        return jsonify({"success": True, "budgets": budgets, "alerts": alerts})
    except Exception as e:
        return jsonify({"success": False, "error": "Failed to load budgets"}), 500


@expenses_bp.route("/api/expenses/budgets", methods=["POST"])
@login_required
def save_budgets():
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"success": False, "error": "Invalid JSON"}), 400
        user_id = session.get("user_id")
        lang = session.get("lang", "en")
        budgets = data.get("budgets", [])
        BudgetManager.save_budgets(user_id, budgets)
        msg = "Budgets saved successfully!" if lang == "en" else "பட்ஜெட்கள் வெற்றிகரமாக சேமிக்கப்பட்டன!"
        return jsonify({"success": True, "message": msg})
    except Exception as e:
        return jsonify({"success": False, "error": "Failed to save budgets"}), 500


@expenses_bp.route("/api/expenses/export/<fmt>")
@login_required
def export_expenses(fmt):
    try:
        user_id = session.get("user_id")
        lang = session.get("lang", "en")
        if fmt == "csv":
            csv_data = ExportService.export_csv(user_id)
            import base64
            return jsonify({
                "success": True,
                "data": base64.b64encode(csv_data.encode()).decode("ascii"),
                "filename": f"farm_finances_{datetime.utcnow().strftime('%Y%m%d')}.csv",
                "mime": "text/csv",
                "encoding": "base64",
            })
        elif fmt == "pdf":
            buf = ExportService.export_pdf(user_id)
            import base64
            return jsonify({
                "success": True,
                "data": base64.b64encode(buf.read()).decode("ascii"),
                "filename": f"farm_finances_{datetime.utcnow().strftime('%Y%m%d')}.pdf",
                "mime": "application/pdf",
                "encoding": "base64",
            })
        elif fmt == "xlsx":
            buf = ExportService.export_excel(user_id)
            import base64
            return jsonify({
                "success": True,
                "data": base64.b64encode(buf.read()).decode("ascii"),
                "filename": f"farm_finances_{datetime.utcnow().strftime('%Y%m%d')}.xlsx",
                "mime": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "encoding": "base64",
            })
        msg = "Invalid format." if lang == "en" else "தவறான வடிவம்."
        return jsonify({"success": False, "error": msg}), 400
    except Exception as e:
        print(f"[Expenses Error] export: {traceback.format_exc()}")
        return jsonify({"success": False, "error": "Failed to export"}), 500


@expenses_bp.route("/api/expenses/<expense_id>", methods=["GET"])
@login_required
def get_expense(expense_id):
    try:
        user_id = session.get("user_id")
        e = Expense.find_by_id(expense_id)
        if not e or e.user_id != user_id:
            return jsonify({"success": False, "error": "Not found"}), 404
        return jsonify({"success": True, "expense": e.to_dict()})
    except Exception as exc:
        print(f"[Expenses Error] get_one: {traceback.format_exc()}")
        return jsonify({"success": False, "error": "Failed to load expense"}), 500
