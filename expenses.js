var expChartInstances = {};
var expState = {
    type: "income",
    deleteId: null,
    page: 1,
    totalPages: 1,
    currentMonth: new Date().getMonth() + 1,
    currentYear: new Date().getFullYear(),
};

function expT(en, ta) { return document.documentElement.lang === "ta" ? ta : en; }
function expToast(msg, type) {
    var t = document.getElementById("exp-toast");
    if (!t) return;
    t.textContent = msg;
    t.className = "exp-toast " + type;
    t.classList.add("show");
    clearTimeout(t._hide);
    t._hide = setTimeout(function () { t.classList.remove("show"); }, 3000);
}

/* Boot */
document.addEventListener("DOMContentLoaded", function () {
    expPopulateCategories("income");
    expLoadData();
    expSetupForm();
    expSetupFilters();
    expSetupBudgetForm();
});

function expPopulateCategories(type) {
    var sel = document.getElementById("exp-form-category");
    if (!sel) return;
    sel.innerHTML = "";
    var cats = type === "income" ? INCOME_CATS : EXPENSE_CATS;
    for (var i = 0; i < cats.length; i++) {
        var opt = document.createElement("option");
        opt.value = cats[i].en;
        opt.textContent = expT(cats[i].en, cats[i].ta);
        sel.appendChild(opt);
    }
    var filterSel = document.getElementById("exp-filter-category");
    if (filterSel) {
        var curVal = filterSel.value;
        filterSel.innerHTML = '<option value="">' + expT("All Categories", "அனைத்து பிரிவுகள்") + "</option>";
        for (var j = 0; j < cats.length; j++) {
            var opt2 = document.createElement("option");
            opt2.value = cats[j].en;
            opt2.textContent = expT(cats[j].en, cats[j].ta);
            filterSel.appendChild(opt2);
        }
        filterSel.value = curVal;
    }
}

function expSwitchForm(type) {
    expState.type = type;
    var typeInput = document.getElementById("exp-form-type");
    var typeSelect = document.getElementById("exp-type-select");
    var tabs = document.querySelectorAll(".exp-form-tab");
    if (typeInput) typeInput.value = type;
    if (typeSelect) typeSelect.value = type;
    tabs.forEach(function (t) { t.classList.toggle("active", t.dataset.type === type); });
    expPopulateCategories(type);
    var submit = document.getElementById("exp-form-submit");
    if (submit) submit.textContent = "💾 " + expT("Save Transaction", "பரிவர்த்தனையை சேமிக்க");
}

function expCancelEdit() {
    var editId = document.getElementById("exp-form-edit-id");
    var submit = document.getElementById("exp-form-submit");
    var cancel = document.getElementById("exp-form-cancel");
    var form = document.getElementById("exp-form");
    if (editId) editId.value = "";
    if (submit) submit.textContent = "💾 " + expT("Save Transaction", "பரிவர்த்தனையை சேமிக்க");
    if (cancel) cancel.style.display = "none";
    if (form) form.reset();
    var dateInput = form ? form.querySelector("[name=date]") : null;
    if (dateInput) dateInput.value = new Date().toISOString().split("T")[0];
}

function expSetupForm() {
    var form = document.getElementById("exp-form");
    if (!form) return;
    form.addEventListener("submit", function (e) {
        e.preventDefault();
        var loading = document.getElementById("exp-form-loading");
        var submitBtn = document.getElementById("exp-form-submit");
        var editId = document.getElementById("exp-form-edit-id");
        if (loading) loading.style.display = "flex";
        if (submitBtn) submitBtn.disabled = true;
        var fd = new FormData(form);
        var data = {
            type: fd.get("type") || fd.get("type_select"),
            category: fd.get("category"),
            amount: fd.get("amount"),
            description: fd.get("description"),
            date: fd.get("date"),
        };
        var url = "/api/expenses";
        var method = "POST";
        if (editId && editId.value) {
            url = "/api/expenses/" + editId.value;
            method = "PUT";
        }
        fetch(url, {
            method: method,
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
        })
        .then(function (r) { return r.json(); })
        .then(function (res) {
            if (loading) loading.style.display = "none";
            if (submitBtn) submitBtn.disabled = false;
            if (res.success) {
                expToast(res.message, "success");
                form.reset();
                if (editId) editId.value = "";
                var cancel = document.getElementById("exp-form-cancel");
                if (cancel) cancel.style.display = "none";
                if (submitBtn) submitBtn.textContent = "💾 " + expT("Save Transaction", "பரிவர்த்தனையை சேமிக்க");
                var dateInput = form.querySelector("[name=date]");
                if (dateInput) dateInput.value = new Date().toISOString().split("T")[0];
                expState.page = 1;
                expLoadData();
            } else {
                expToast(res.error || "Error", "error");
            }
        })
        .catch(function () {
            if (loading) loading.style.display = "none";
            if (submitBtn) submitBtn.disabled = false;
            expToast("Network error", "error");
        });
    });
}

/* Data Loading */
function expLoadData() {
    expLoadTable();
    expLoadAnalytics();
}

function expGetFilterParams() {
    var params = new URLSearchParams();
    params.set("page", expState.page);
    params.set("per_page", 20);
    var search = document.getElementById("exp-filter-search");
    var type = document.getElementById("exp-filter-type");
    var category = document.getElementById("exp-filter-category");
    var month = document.getElementById("exp-filter-month");
    var year = document.getElementById("exp-filter-year");
    var sort = document.getElementById("exp-filter-sort");
    if (search && search.value) params.set("search", search.value);
    if (type && type.value) params.set("type", type.value);
    if (category && category.value) params.set("category", category.value);
    if (month && month.value) params.set("month", month.value);
    if (year && year.value) params.set("year", year.value);
    if (sort && sort.value) {
        var parts = sort.value.split("_");
        params.set("sort_by", parts[0]);
        params.set("sort_order", parts[1] || "desc");
    }
    return params;
}

function expLoadTable() {
    var params = expGetFilterParams();
    fetch("/api/expenses?" + params.toString())
        .then(function (r) { return r.json(); })
        .then(function (res) {
            if (!res.success) return;
            expRenderSummary(res.summary);
            expRenderTable(res.expenses);
            expRenderPagination(res.page, res.pages);
            var count = document.getElementById("exp-count");
            if (count) count.textContent = "(" + res.total + ")";
        })
        .catch(function () {});
}

function expLoadAnalytics() {
    fetch("/api/expenses/analytics")
        .then(function (r) { return r.json(); })
        .then(function (res) {
            if (!res.success || !res.analytics) return;
            var a = res.analytics;
            expRenderStats(a);
            expRenderCharts(a);
            expRenderMonthly(a.monthly);
            expRenderActivity(a.recent);
            expRenderBudgets();
            if (a.summary.income > 0 || a.summary.expense > 0) {
                expRenderInsights();
            }
        })
        .catch(function () {});
}

/* Summary */
function expRenderSummary(summary) {
    var inc = document.getElementById("exp-summary-income");
    var exp = document.getElementById("exp-summary-expense");
    var profit = document.getElementById("exp-summary-profit");
    var ti = summary.income || 0;
    var te = summary.expense || 0;
    var np = ti - te;
    if (inc) inc.textContent = "₹" + ti.toLocaleString("en-IN");
    if (exp) exp.textContent = "₹" + te.toLocaleString("en-IN");
    if (profit) {
        profit.textContent = "₹" + np.toLocaleString("en-IN");
        profit.className = "exp-summary-value " + (np >= 0 ? "positive" : "negative");
    }
}

/* Stats */
function expRenderStats(a) {
    var row = document.getElementById("exp-stats-row");
    if (!row) return;
    if (a.stats.total_transactions > 0) {
        row.style.display = "grid";
    } else {
        row.style.display = "none";
        return;
    }
    var s = a.stats;
    var count = document.getElementById("exp-stat-count");
    var hi = document.getElementById("exp-stat-highest-inc");
    var hic = document.getElementById("exp-stat-highest-inc-cat");
    var he = document.getElementById("exp-stat-highest-exp");
    var hec = document.getElementById("exp-stat-highest-exp-cat");
    var margin = document.getElementById("exp-stat-margin");
    var savings = document.getElementById("exp-stat-savings");
    if (count) count.textContent = s.total_transactions;
    if (hi) hi.textContent = "₹" + (s.highest_income || 0).toLocaleString("en-IN");
    if (hic) hic.textContent = s.highest_income_cat || "";
    if (he) he.textContent = "₹" + (s.highest_expense || 0).toLocaleString("en-IN");
    if (hec) hec.textContent = s.highest_expense_cat || "";
    if (margin) margin.textContent = (a.profit_margin || 0) + "%";
    if (savings) savings.textContent = (a.savings_rate || 0) + "%";
}

/* Table */
function expRenderTable(expenses) {
    var tbody = document.getElementById("exp-table-body");
    if (!tbody) return;
    if (!expenses || expenses.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="exp-empty">' +
            expT("No transactions recorded yet.", "இதுவரை பரிவர்த்தனைகள் எதுவும் இல்லை.") +
            "</td></tr>";
        return;
    }
    tbody.innerHTML = expenses.map(function (e) {
        var isIncome = e.type === "income";
        var badge = isIncome ? "exp-badge-income" : "exp-badge-expense";
        var badgeIcon = isIncome ? "📈" : "📉";
        var amtClass = isIncome ? "exp-amount-income" : "exp-amount-expense";
        var note = e.description || "-";
        var noteHtml = note.length > 30
            ? '<span class="exp-note-preview" title="' + expEscapeHtml(note) + '">' + expEscapeHtml(note.substring(0, 30)) + '...</span>'
            : '<span class="exp-note-preview">' + expEscapeHtml(note) + "</span>";
        var dateStr = e.date ? e.date.substring(0, 10) : "-";
        return '<tr>' +
            '<td><span class="exp-badge ' + badge + '">' + badgeIcon + " " + expEscapeHtml(expT(e.type === "income" ? "Income" : "Expense", e.type === "income" ? "வருமானம்" : "செலவு")) + "</span></td>" +
            '<td>' + expEscapeHtml(e.category) + "</td>" +
            "<td>" + noteHtml + "</td>" +
            '<td class="exp-amount ' + amtClass + '">₹' + Number(e.amount).toLocaleString("en-IN") + "</td>" +
            "<td>" + dateStr + "</td>" +
            '<td>' +
            '<button class="exp-action-btn edit" onclick="expEdit(\'' + e.id + '\')" title="Edit">✏️</button> ' +
            '<button class="exp-action-btn delete" onclick="expDelete(\'' + e.id + '\')" title="Delete">🗑️</button>' +
            "</td>" +
            "</tr>";
    }).join("");
}

function expEscapeHtml(s) {
    if (typeof s !== "string") return s;
    var d = document.createElement("div");
    d.textContent = s;
    return d.innerHTML;
}

/* Pagination */
function expRenderPagination(page, pages) {
    var container = document.getElementById("exp-pagination");
    if (!container) return;
    expState.page = page;
    expState.totalPages = pages;
    if (pages <= 1) { container.innerHTML = ""; return; }
    var html = "";
    html += '<button class="exp-page-btn" onclick="expGoPage(1)" ' + (page <= 1 ? "disabled" : "") + ">«</button>";
    html += '<button class="exp-page-btn" onclick="expGoPage(' + (page - 1) + ')" ' + (page <= 1 ? "disabled" : "") + ">‹</button>";
    var start = Math.max(1, page - 2);
    var end = Math.min(pages, page + 2);
    for (var i = start; i <= end; i++) {
        html += '<button class="exp-page-btn' + (i === page ? " active" : "") + '" onclick="expGoPage(' + i + ')">' + i + "</button>";
    }
    html += '<button class="exp-page-btn" onclick="expGoPage(' + (page + 1) + ')" ' + (page >= pages ? "disabled" : "") + ">›</button>";
    html += '<button class="exp-page-btn" onclick="expGoPage(' + pages + ')" ' + (page >= pages ? "disabled" : "") + ">»</button>";
    container.innerHTML = html;
}

function expGoPage(p) {
    expState.page = p;
    expLoadTable();
}

/* Filters */
function expSetupFilters() {
    var inputs = ["exp-filter-search", "exp-filter-type", "exp-filter-category", "exp-filter-month", "exp-filter-year", "exp-filter-sort"];
    inputs.forEach(function (id) {
        var el = document.getElementById(id);
        if (el) {
            el.addEventListener("change", function () { expState.page = 1; expLoadTable(); });
            if (id === "exp-filter-search") {
                el.addEventListener("input", function () {
                    clearTimeout(el._timer);
                    el._timer = setTimeout(function () { expState.page = 1; expLoadTable(); }, 400);
                });
            }
        }
    });
}

/* Edit */
function expEdit(id) {
    fetch("/api/expenses/" + id)
        .then(function (r) { return r.json(); })
        .then(function (res) {
            if (!res.success || !res.expense) { expToast(expT("Expense not found", "செலவு கிடைக்கவில்லை"), "error"); return; }
            var item = res.expense;
            var form = document.getElementById("exp-form");
            var typeInput = document.getElementById("exp-form-type");
            var editId = document.getElementById("exp-form-edit-id");
            var submit = document.getElementById("exp-form-submit");
            var cancel = document.getElementById("exp-form-cancel");
            if (typeInput) typeInput.value = item.type;
            expSwitchForm(item.type);
            if (editId) editId.value = item.id;
            if (submit) submit.textContent = "✏️ " + expT("Update Transaction", "பரிவர்த்தனையை புதுப்பிக்க");
            if (cancel) cancel.style.display = "inline-block";
            if (form) {
                var catSel = form.querySelector("[name=category]");
                var amtInput = form.querySelector("[name=amount]");
                var descInput = form.querySelector("[name=description]");
                var dateInput = form.querySelector("[name=date]");
                if (catSel) catSel.value = item.category;
                if (amtInput) amtInput.value = item.amount;
                if (descInput) descInput.value = item.description || "";
                if (dateInput) dateInput.value = item.date ? item.date.substring(0, 10) : "";
            }
            var tabs = document.querySelector(".exp-form-tabs");
            if (tabs) tabs.scrollIntoView({ behavior: "smooth", block: "start" });
        })
        .catch(function () { expToast("Network error", "error"); });
}

/* Delete */
function expDelete(id) {
    expState.deleteId = id;
    var modal = document.getElementById("exp-delete-modal");
    if (modal) modal.style.display = "flex";
    document.getElementById("exp-delete-confirm").onclick = function () {
        expConfirmDelete();
    };
}

function expCloseDelete() {
    var modal = document.getElementById("exp-delete-modal");
    if (modal) modal.style.display = "none";
    expState.deleteId = null;
}

function expConfirmDelete() {
    if (!expState.deleteId) return;
    fetch("/api/expenses/" + expState.deleteId, { method: "DELETE" })
        .then(function (r) { return r.json(); })
        .then(function (res) {
            expCloseDelete();
            if (res.success) {
                expToast(res.message, "success");
                expLoadData();
            } else {
                expToast(res.error || "Error", "error");
            }
        })
        .catch(function () { expCloseDelete(); expToast("Network error", "error"); });
}

/* Charts */
function expRenderCharts(a) {
    var section = document.getElementById("exp-charts-section");
    if (!section) return;
    var hasData = a.monthly && a.monthly.some(function (m) { return m.income > 0 || m.expense > 0; });
    section.style.display = hasData ? "grid" : "none";
    if (!hasData) return;
    expRenderIncomeExpenseChart(a);
    expRenderExpensePieChart(a);
    expRenderTrendChart("exp-chart-income-trend", a.monthly, "income", "#10b981");
    expRenderTrendChart("exp-chart-expense-trend", a.monthly, "expense", "#ef4444");
    expRenderProfitTrendChart(a);
}

function expGetChartCtx(id) {
    var canvas = document.getElementById(id);
    if (!canvas) return null;
    if (expChartInstances[id]) { expChartInstances[id].destroy(); expChartInstances[id] = null; }
    return canvas.getContext("2d");
}

function expRenderIncomeExpenseChart(a) {
    var ctx = expGetChartCtx("exp-chart-income-expense");
    if (!ctx) return;
    var labels = a.monthly.map(function (m) { return m.month_name; });
    var income = a.monthly.map(function (m) { return m.income; });
    var expense = a.monthly.map(function (m) { return m.expense; });
    expChartInstances["exp-chart-income-expense"] = new Chart(ctx, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [
                { label: expT("Income", "வருமானம்"), data: income, backgroundColor: "rgba(16,185,129,0.7)", borderRadius: 4 },
                { label: expT("Expenses", "செலவுகள்"), data: expense, backgroundColor: "rgba(239,68,68,0.7)", borderRadius: 4 },
            ],
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: { legend: { position: "bottom", labels: { usePointStyle: true } } },
            scales: {
                y: { beginAtZero: true, grid: { color: "rgba(0,0,0,0.05)" } },
                x: { grid: { display: false } },
            },
        },
    });
}

function expRenderExpensePieChart(a) {
    var ctx = expGetChartCtx("exp-chart-expense-pie");
    if (!ctx) return;
    var breakdown = a.expense_breakdown || [];
    var labels = breakdown.map(function (c) { return c._id; });
    var data = breakdown.map(function (c) { return c.total; });
    var colors = ["#10b981", "#3b82f6", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899", "#14b8a6", "#f97316", "#6366f1"];
    if (!labels.length) { labels = [expT("No Data", "தரவு இல்லை")]; data = [1]; colors = ["#e5e7eb"]; }
    expChartInstances["exp-chart-expense-pie"] = new Chart(ctx, {
        type: "doughnut",
        data: { labels: labels, datasets: [{ data: data, backgroundColor: colors, borderWidth: 0 }] },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: { legend: { position: "bottom", labels: { padding: 12, usePointStyle: true, font: { size: 11 } } } },
            cutout: "55%",
        },
    });
}

function expRenderTrendChart(id, monthly, key, color) {
    var ctx = expGetChartCtx(id);
    if (!ctx) return;
    var labels = monthly.map(function (m) { return m.month_name; });
    var data = monthly.map(function (m) { return m[key]; });
    expChartInstances[id] = new Chart(ctx, {
        type: "line",
        data: {
            labels: labels,
            datasets: [{
                label: key === "income" ? expT("Income", "வருமானம்") : expT("Expenses", "செலவுகள்"),
                data: data,
                borderColor: color,
                backgroundColor: color + "20",
                fill: true,
                tension: 0.4,
                pointRadius: 3,
            }],
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                y: { beginAtZero: true, grid: { color: "rgba(0,0,0,0.05)" } },
                x: { grid: { display: false } },
            },
        },
    });
}

function expRenderProfitTrendChart(a) {
    var ctx = expGetChartCtx("exp-chart-profit-trend");
    if (!ctx) return;
    var labels = a.monthly.map(function (m) { return m.month_name; });
    var data = a.monthly.map(function (m) { return m.profit; });
    var colors = data.map(function (v) { return v >= 0 ? "rgba(16,185,129,0.7)" : "rgba(239,68,68,0.7)"; });
    expChartInstances["exp-chart-profit-trend"] = new Chart(ctx, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [{ data: data, backgroundColor: colors, borderRadius: 4 }],
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function (ctx) { return "₹" + ctx.parsed.y.toLocaleString("en-IN"); },
                    },
                },
            },
            scales: {
                y: { beginAtZero: true, grid: { color: "rgba(0,0,0,0.05)" } },
                x: { grid: { display: false } },
            },
        },
    });
}

/* Monthly Summary */
function expRenderMonthly(monthly) {
    var section = document.getElementById("exp-monthly-section");
    var grid = document.getElementById("exp-monthly-grid");
    if (!section || !grid) return;
    var hasData = monthly && monthly.some(function (m) { return m.income > 0 || m.expense > 0; });
    if (!hasData) { section.style.display = "none"; return; }
    section.style.display = "block";
    grid.innerHTML = monthly.filter(function (m) { return m.income > 0 || m.expense > 0; }).map(function (m) {
        return '<div class="exp-monthly-card">' +
            "<h4>" + m.month_name + "</h4>" +
            "<p>📈 " + expT("Income", "வருமானம்") + ": ₹" + m.income.toLocaleString("en-IN") + "</p>" +
            "<p>📉 " + expT("Expense", "செலவு") + ": ₹" + m.expense.toLocaleString("en-IN") + "</p>" +
            "<p><strong>" + expT("Profit", "லாபம்") + ": ₹" + m.profit.toLocaleString("en-IN") + "</strong></p>" +
            "</div>";
    }).join("");
}

/* Activity */
function expRenderActivity(recent) {
    var section = document.getElementById("exp-activity-section");
    var list = document.getElementById("exp-activity-list");
    if (!section || !list) return;
    if (!recent || !recent.length) { section.style.display = "none"; return; }
    section.style.display = "block";
    list.innerHTML = recent.map(function (e) {
        var icon = e.type === "income" ? "📈" : "📉";
        var dateStr = e.date ? e.date.substring(0, 10) : "";
        return '<div class="exp-activity-item">' +
            '<div class="exp-activity-left">' +
            '<span class="exp-activity-type">' + icon + "</span>" +
            '<span class="exp-activity-cat">' + expEscapeHtml(e.category) + "</span>" +
            '<span class="exp-activity-date">' + dateStr + "</span>" +
            "</div>" +
            '<span class="exp-activity-amount" style="color:' + (e.type === "income" ? "var(--exp-green)" : "var(--exp-red)") + '">₹' +
            Number(e.amount).toLocaleString("en-IN") + "</span>" +
            "</div>";
    }).join("");
}

/* AI Insights */
function expRenderInsights() {
    var card = document.getElementById("exp-insights-card");
    if (card) card.style.display = "block";
    expRefreshInsights();
}

function expMarkdownToHtml(text) {
    var t = expEscapeHtml(text);
    t = t.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
    t = t.replace(/__(.+?)__/g, "<strong>$1</strong>");
    t = t.replace(/\*(.+?)\*/g, "<em>$1</em>");
    t = t.replace(/_(.+?)_/g, "<em>$1</em>");
    t = t.replace(/^### (.+)$/gm, "<h4>$1</h4>");
    t = t.replace(/^## (.+)$/gm, "<h3>$1</h3>");
    t = t.replace(/^# (.+)$/gm, "<h2>$1</h2>");
    t = t.replace(/^- (.+)$/gm, "<li>$1</li>");
    t = t.replace(/^\* (.+)$/gm, "<li>$1</li>");
    t = t.replace(/^\d+\. (.+)$/gm, "<li>$1</li>");
    t = t.replace(/(<li>.*<\/li>\n?)+/g, "<ul>$&</ul>");
    t = t.replace(/\n/g, "<br>");
    return t;
}

function expRefreshInsights() {
    var textDiv = document.getElementById("exp-insights-text");
    var loadingDiv = document.getElementById("exp-insights-loading");
    if (!textDiv || !loadingDiv) return;
    loadingDiv.style.display = "flex";
    textDiv.innerHTML = "";
    fetch("/api/expenses/insights")
        .then(function (r) { return r.json(); })
        .then(function (res) {
            loadingDiv.style.display = "none";
            if (res.success) {
                textDiv.innerHTML = expMarkdownToHtml(res.insights);
            } else {
                textDiv.innerHTML = res.error || "";
            }
        })
        .catch(function () {
            loadingDiv.style.display = "none";
            textDiv.innerHTML = "";
        });
}

/* Budgets */
function expSetupBudgetForm() {
    var cats = EXPENSE_CATS || [];
    var fields = document.getElementById("exp-budget-fields");
    if (!fields) return;
    fields.innerHTML = cats.map(function (c) {
        return '<div class="exp-budget-field"><label>' + expEscapeHtml(expT(c.en, c.ta)) + '</label><input type="number" class="exp-budget-input" data-category="' + expEscapeHtml(c.en) + '" min="0" step="100" placeholder="₹ 0"></div>';
    }).join("");
}

function expToggleBudgetForm() {
    var form = document.getElementById("exp-budget-form");
    if (form) form.style.display = form.style.display === "none" ? "block" : "none";
}

function expSaveBudgets() {
    var inputs = document.querySelectorAll(".exp-budget-input");
    var budgets = [];
    inputs.forEach(function (inp) {
        var val = parseFloat(inp.value);
        if (val > 0) {
            budgets.push({ category: inp.dataset.category, limit: val });
        }
    });
    fetch("/api/expenses/budgets", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ budgets: budgets }),
    })
    .then(function (r) { return r.json(); })
    .then(function (res) {
        if (res.success) {
            expToast(res.message, "success");
            expRenderBudgets();
        } else {
            expToast(res.error || "Error", "error");
        }
    })
    .catch(function () { expToast("Network error", "error"); });
}

function expRenderBudgets() {
    fetch("/api/expenses/budgets")
        .then(function (r) { return r.json(); })
        .then(function (res) {
            if (!res.success) return;
            var alertsDiv = document.getElementById("exp-budget-alerts");
            var listDiv = document.getElementById("exp-budget-list");
            if (alertsDiv) {
                if (res.alerts && res.alerts.length) {
                    alertsDiv.innerHTML = res.alerts.map(function (a) {
                        return '<div class="exp-budget-alert">⚠️ ' +
                            expT(a.category + " budget exceeded! Spent ₹" + a.spent + " of ₹" + a.limit + " (" + a.pct + "%)",
                                  a.category + " பட்ஜெட் மீறப்பட்டது! செலவு ₹" + a.spent + ", வரம்பு ₹" + a.limit + " (" + a.pct + "%)") +
                            "</div>";
                    }).join("");
                } else {
                    alertsDiv.innerHTML = "";
                }
            }
            if (listDiv) {
                if (res.budgets && res.budgets.length) {
                    listDiv.innerHTML = res.budgets.map(function (b) {
                        var alert = null;
                        if (res.alerts) {
                            for (var i = 0; i < res.alerts.length; i++) {
                                if (res.alerts[i].category === b.category) { alert = res.alerts[i]; break; }
                            }
                        }
                        var pct = alert ? alert.pct : 0;
                        var barClass = "ok";
                        if (pct > 100) barClass = "over";
                        else if (pct > 80) barClass = "warn";
                        return '<div class="exp-budget-item">' +
                            '<span class="exp-budget-name">' + expEscapeHtml(expT(b.category, b.category)) + "</span>" +
                            '<div class="exp-budget-bar"><div class="exp-budget-bar-fill ' + barClass + '" style="width:' + Math.min(pct, 100) + '%"></div></div>' +
                            '<span>₹' + Number(b.limit).toLocaleString("en-IN") + "</span>" +
                            "</div>";
                    }).join("");
                } else {
                    listDiv.innerHTML = '<div class="exp-empty">' + expT("No budgets set. Click 'Set Budgets' above.", "பட்ஜெட் எதுவும் அமைக்கப்படவில்லை. மேலே 'பட்ஜெட் அமைக்க' என்பதைக் கிளிக் செய்யவும்.") + "</div>";
                }
            }
        })
        .catch(function () {});
}

/* Export */
function expExport(fmt) {
    var btn = event && event.target ? event.target : null;
    if (btn) { btn.textContent = "⏳"; btn.disabled = true; }
    fetch("/api/expenses/export/" + fmt)
        .then(function (r) { return r.json(); })
        .then(function (res) {
            if (btn) { btn.textContent = fmt === "csv" ? "📄" : fmt === "xlsx" ? "📊" : "📕"; btn.disabled = false; }
            if (res.success) {
                var link = document.createElement("a");
                link.download = res.filename;
                if (res.encoding === "base64") {
                    var byteChars = atob(res.data);
                    var byteArr = new Uint8Array(byteChars.length);
                    for (var i = 0; i < byteChars.length; i++) byteArr[i] = byteChars.charCodeAt(i);
                    var blob = new Blob([byteArr], { type: res.mime });
                    link.href = URL.createObjectURL(blob);
                } else {
                    link.href = "data:" + res.mime + ";charset=utf-8," + encodeURIComponent(res.data);
                }
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                expToast(expT("Export successful!", "ஏற்றுமதி வெற்றி!"), "success");
            } else {
                expToast(res.error || "Export failed", "error");
            }
        })
        .catch(function () {
            if (btn) { btn.textContent = fmt === "csv" ? "📄" : fmt === "xlsx" ? "📊" : "📕"; btn.disabled = false; }
            expToast("Network error", "error");
        });
}
