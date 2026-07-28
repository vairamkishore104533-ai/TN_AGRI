var anlCharts = {};
var anlLang = document.documentElement.lang || "en";
var anlState = { dateRange: "6m", crop: "", district: "" };

function anlT(en, ta) { return anlLang === "ta" ? ta : en; }

function anlToast(msg, type) {
    var t = document.getElementById("anl-toast");
    if (!t) return;
    t.textContent = msg; t.className = "anl-toast " + type;
    t.classList.add("show");
    clearTimeout(t._hide);
    t._hide = setTimeout(function () { t.classList.remove("show"); }, 3000);
}

/* Boot */
document.addEventListener("DOMContentLoaded", function () {
    anlLoadOptions();
    anlLoadAll();
    anlSetupFilters();
});

function anlSetLanguage() {
    fetch("/set-language/" + (anlLang === "en" ? "ta" : "en"), { method: "POST" })
        .then(function () { location.reload(); });
}

/* Filter Setup */
function anlSetupFilters() {
    var els = ["anl-filter-range", "anl-filter-crop", "anl-filter-district"];
    els.forEach(function (id) {
        var el = document.getElementById(id);
        if (!el) return;
        el.addEventListener("change", function () {
            anlState.dateRange = document.getElementById("anl-filter-range").value;
            anlState.crop = document.getElementById("anl-filter-crop").value;
            anlState.district = document.getElementById("anl-filter-district").value;
            anlReloadAll();
        });
    });
}

function anlLoadOptions() {
    fetch("/api/analytics/options")
        .then(function (r) { return r.json(); })
        .then(function (res) {
            if (!res.success) return;
            var cropSel = document.getElementById("anl-filter-crop");
            var distSel = document.getElementById("anl-filter-district");
            if (cropSel && res.crops) {
                res.crops.forEach(function (c) {
                    var opt = document.createElement("option");
                    opt.value = c; opt.textContent = c;
                    cropSel.appendChild(opt);
                });
            }
            if (distSel && res.districts) {
                res.districts.forEach(function (d) {
                    var opt = document.createElement("option");
                    opt.value = d; opt.textContent = d;
                    distSel.appendChild(opt);
                });
            }
        });
}

function anlReloadAll() {
    anlLoadOverview();
    anlLoadCropDistribution();
    anlLoadFinances();
    anlLoadActivity(anlState.dateRange);
    anlLoadQuickStats();
    anlRefreshInsights();
}

function anlLoadAll() {
    anlLoadOverview();
    anlLoadCropDistribution();
    anlLoadFinances();
    anlLoadActivity("6m");
    anlLoadQuickStats();
    anlRefreshInsights();
}

/* Overview Cards */
function anlLoadOverview() {
    var p = new URLSearchParams();
    p.set("date_range", anlState.dateRange);
    if (anlState.crop) p.set("crop", anlState.crop);
    if (anlState.district) p.set("district", anlState.district);
    fetch("/api/analytics/overview?" + p.toString())
        .then(function (r) { return r.json(); })
        .then(function (res) {
            if (!res.success) return;
            var cards = [
                { icon: "🌾", label: anlT("Total Crops", "மொத்த பயிர்கள்"), value: res.total_crops, sub: anlT("Currently growing", "தற்போது விளைவிக்கப்படுகிறது"), color: "#10b981" },
                { icon: "📐", label: anlT("Farm Area", "பண்ணை பரப்பு"), value: res.total_area + " ac", sub: anlT("Total land", "மொத்த நிலம்"), color: "#3b82f6" },
                { icon: "💰", label: anlT("Total Income", "மொத்த வருமானம்"), value: "₹" + anlFmt(res.total_income), sub: anlT("This period", "இந்த காலம்"), color: "#10b981" },
                { icon: "💸", label: anlT("Total Expenses", "மொத்த செலவுகள்"), value: "₹" + anlFmt(res.total_expense), sub: anlT("This period", "இந்த காலம்"), color: "#ef4444" },
                { icon: "📈", label: anlT("Net Profit", "நிகர லாபம்"), value: "₹" + anlFmt(res.net_profit), sub: res.net_profit >= 0 ? anlT("Profitable", "லாபம்") : anlT("Loss", "நஷ்டம்"), color: res.net_profit >= 0 ? "#10b981" : "#ef4444" },
                { icon: "🏆", label: anlT("AI Farm Score", "AI பண்ணை மதிப்பெண்"), value: res.farm_score + "/100", sub: anlT("Overall health", "ஒட்டுமொத்த ஆரோக்கியம்"), color: "#f59e0b", score: res.farm_score },
            ];
            var grid = document.getElementById("anl-overview");
            if (!grid) return;
            grid.innerHTML = cards.map(function (c) {
                var scoreHtml = "";
                if (c.score !== undefined) {
                    var pct = Math.min(100, c.score);
                    scoreHtml = '<div class="anl-ov-score"><div class="anl-ov-score-bar"><div class="anl-ov-score-fill" style="width:' + pct + '%"></div></div><span class="anl-ov-score-text" style="color:' + c.color + '">' + c.score + '</span></div>';
                }
                return '<div class="anl-ov-card" style="border-left:3px solid ' + c.color + '"><div class="anl-ov-icon">' + c.icon + '</div><div class="anl-ov-label">' + c.label + '</div><div class="anl-ov-value" style="color:' + c.color + '">' + c.value + '</div><div class="anl-ov-sub">' + c.sub + '</div>' + scoreHtml + '</div>';
            }).join("");
            anlAnimateCounters();
        });
}

function anlFmt(n) {
    if (typeof n !== "number") return n || "0";
    return n.toLocaleString("en-IN", { maximumFractionDigits: 0 });
}

function anlAnimateCounters() {
    var els = document.querySelectorAll(".anl-ov-value");
    els.forEach(function (el) {
        var txt = el.textContent;
        var match = txt.match(/([\d,.]+)/);
        if (!match) return;
        var target = parseFloat(match[1].replace(/,/g, ""));
        if (isNaN(target) || target === 0) return;
        var prefix = txt.includes("₹") ? "₹" : "";
        var suffix = txt.includes("ac") ? " ac" : txt.includes("/100") ? "/100" : "";
        var duration = 800, steps = 30, step = 0;
        var inc = target / steps;
        var timer = setInterval(function () {
            step++;
            var val = Math.round(inc * step);
            if (step >= steps) { val = target; clearInterval(timer); }
            el.textContent = prefix + val.toLocaleString("en-IN") + suffix;
        }, duration / steps);
    });
}

/* Crop Distribution Chart */
function anlLoadCropDistribution() {
    var p = new URLSearchParams();
    if (anlState.district) p.set("district", anlState.district);
    fetch("/api/analytics/crop-distribution?" + p.toString())
        .then(function (r) { return r.json(); })
        .then(function (res) {
            var wrap = document.getElementById("anl-chart-crop-dist");
            var empty = document.getElementById("anl-empty-crop-dist");
            if (!res.success || !res.distribution || res.distribution.length === 0) {
                if (wrap) { wrap.style.display = "none"; }
                if (empty) { empty.style.display = "block"; }
                return;
            }
            if (wrap) wrap.style.display = "block";
            if (empty) empty.style.display = "none";
            var labels = res.distribution.map(function (d) { return d._id || "Unknown"; });
            var data = res.distribution.map(function (d) { return d.count; });
            if (anlCharts.cropDist) anlCharts.cropDist.destroy();
            var ctx = document.getElementById("anl-chart-crop-dist");
            if (!ctx) return;
            var colors = ["#1a7d36", "#2e9e4a", "#10b981", "#34d399", "#6ee7b7", "#a7f3d0", "#d1fae5", "#e8f5e9"];
            anlCharts.cropDist = new Chart(ctx, {
                type: "pie",
                data: { labels: labels, datasets: [{ data: data, backgroundColor: colors, borderWidth: 2, borderColor: "#fff" }] },
                options: {
                    responsive: true, maintainAspectRatio: false,
                    plugins: {
                        legend: { position: "right", labels: { font: { size: 11, family: "Inter" }, padding: 12, boxWidth: 12 } },
                        tooltip: { callbacks: { label: function (c) { return c.label + ": " + c.raw + " " + anlT("crops", "பயிர்கள்"); } } }
                    }
                }
            });
        });
}

/* Finances Chart */
function anlLoadFinances() {
    fetch("/api/analytics/finances?months=6")
        .then(function (r) { return r.json(); })
        .then(function (res) {
            var wrap = document.getElementById("anl-chart-finances");
            var empty = document.getElementById("anl-empty-finances");
            if (!res.success || !res.monthly || res.monthly.length === 0) {
                if (wrap) { wrap.style.display = "none"; }
                if (empty) { empty.style.display = "block"; }
                return;
            }
            var hasData = res.monthly.some(function (m) { return m.income > 0 || m.expense > 0; });
            if (!hasData) {
                if (wrap) { wrap.style.display = "none"; }
                if (empty) { empty.style.display = "block"; }
                return;
            }
            if (wrap) wrap.style.display = "block";
            if (empty) empty.style.display = "none";
            var labels = res.monthly.map(function (m) { return m.month; });
            if (anlCharts.finances) anlCharts.finances.destroy();
            var ctx = document.getElementById("anl-chart-finances");
            if (!ctx) return;
            anlCharts.finances = new Chart(ctx, {
                type: "bar",
                data: {
                    labels: labels,
                    datasets: [
                        { label: anlT("Income", "வருமானம்"), data: res.monthly.map(function (m) { return m.income; }), backgroundColor: "rgba(16,185,129,0.7)", borderColor: "#10b981", borderWidth: 1, borderRadius: 4 },
                        { label: anlT("Expense", "செலவு"), data: res.monthly.map(function (m) { return m.expense; }), backgroundColor: "rgba(239,68,68,0.7)", borderColor: "#ef4444", borderWidth: 1, borderRadius: 4 },
                    ]
                },
                options: {
                    responsive: true, maintainAspectRatio: false,
                    interaction: { mode: "index", intersect: false },
                    plugins: {
                        legend: { position: "top", labels: { font: { size: 11, family: "Inter" }, boxWidth: 12, padding: 12 } },
                        tooltip: { callbacks: { label: function (c) { return c.dataset.label + ": ₹" + c.raw.toLocaleString("en-IN"); } } }
                    },
                    scales: {
                        x: { grid: { display: false }, ticks: { font: { size: 10, family: "Inter" } } },
                        y: { grid: { color: "rgba(0,0,0,0.05)" }, ticks: { font: { size: 10, family: "Inter" }, callback: function (v) { return "₹" + v.toLocaleString("en-IN"); } } }
                    }
                }
            });
        });
}

/* Activity Timeline */
function anlSetTimeline(range) {
    anlState.dateRange = range;
    document.getElementById("anl-filter-range").value = range;
    var tabs = document.querySelectorAll(".anl-tab");
    tabs.forEach(function (t) { t.classList.toggle("active", t.dataset.range === range); });
    anlLoadActivity(range);
}

function anlLoadActivity(range) {
    fetch("/api/analytics/activity?date_range=" + range)
        .then(function (r) { return r.json(); })
        .then(function (res) {
            var wrap = document.getElementById("anl-chart-activity");
            var empty = document.getElementById("anl-empty-activity");
            if (!res.success || !res.activity || res.activity.length === 0) {
                if (wrap) { wrap.style.display = "none"; }
                if (empty) { empty.style.display = "block"; }
                return;
            }
            var hasData = res.activity.some(function (a) { return a.crops > 0 || a.diagnoses > 0 || a.fertilizers > 0 || a.irrigations > 0; });
            if (!hasData) {
                if (wrap) { wrap.style.display = "none"; }
                if (empty) { empty.style.display = "block"; }
                return;
            }
            if (wrap) wrap.style.display = "block";
            if (empty) empty.style.display = "none";
            var labels = res.activity.map(function (a) { return a.date.substring(5); });
            if (anlCharts.activity) anlCharts.activity.destroy();
            var ctx = document.getElementById("anl-chart-activity");
            if (!ctx) return;
            anlCharts.activity = new Chart(ctx, {
                type: "line",
                data: {
                    labels: labels,
                    datasets: [
                        { label: anlT("Crops", "பயிர்கள்"), data: res.activity.map(function (a) { return a.crops; }), borderColor: "#10b981", backgroundColor: "rgba(16,185,129,0.1)", fill: true, tension: 0.3, pointRadius: 3, pointHoverRadius: 5 },
                        { label: anlT("Diagnoses", "நோய்கள்"), data: res.activity.map(function (a) { return a.diagnoses; }), borderColor: "#ef4444", backgroundColor: "rgba(239,68,68,0.1)", fill: true, tension: 0.3, pointRadius: 3, pointHoverRadius: 5 },
                        { label: anlT("Fertilizers", "உரங்கள்"), data: res.activity.map(function (a) { return a.fertilizers; }), borderColor: "#f59e0b", backgroundColor: "rgba(245,158,11,0.1)", fill: true, tension: 0.3, pointRadius: 3, pointHoverRadius: 5 },
                        { label: anlT("Irrigation", "நீர்ப்பாசனம்"), data: res.activity.map(function (a) { return a.irrigations; }), borderColor: "#3b82f6", backgroundColor: "rgba(59,130,246,0.1)", fill: true, tension: 0.3, pointRadius: 3, pointHoverRadius: 5 },
                    ]
                },
                options: {
                    responsive: true, maintainAspectRatio: false,
                    interaction: { mode: "index", intersect: false },
                    plugins: {
                        legend: { position: "top", labels: { font: { size: 10, family: "Inter" }, boxWidth: 12, padding: 10 } },
                        tooltip: { mode: "index" }
                    },
                    scales: {
                        x: { grid: { display: false }, ticks: { font: { size: 9, family: "Inter" }, maxTicksLimit: 10 } },
                        y: { grid: { color: "rgba(0,0,0,0.05)" }, ticks: { font: { size: 9, family: "Inter" }, stepSize: 1 } }
                    }
                }
            });
        });
}

/* Quick Stats */
function anlLoadQuickStats() {
    fetch("/api/analytics/quick-stats")
        .then(function (r) { return r.json(); })
        .then(function (res) {
            if (!res.success) return;
            var items = [
                { icon: "🌾", label: anlT("Top Crop", "முக்கிய பயிர்"), value: res.most_cultivated_crop, na: true },
                { icon: "📊", label: anlT("Avg Monthly Profit", "சராசரி மாத லாபம்"), value: "₹" + anlFmt(res.avg_monthly_profit) },
                { icon: "🦠", label: anlT("Common Disease", "பொதுவான நோய்"), value: res.most_common_disease, na: true },
                { icon: "💧", label: anlT("Water Efficiency", "நீர் திறன்"), value: res.water_efficiency + "%" },
                { icon: "🏪", label: anlT("Favorite Market", "விருப்ப சந்தை"), value: res.favorite_market, na: true },
                { icon: "🏛️", label: anlT("Schemes Saved", "சேமித்த திட்டங்கள்"), value: res.schemes_saved },
            ];
            var grid = document.getElementById("anl-quick-grid");
            if (!grid) return;
            grid.innerHTML = items.map(function (item) {
                var val = item.value || (item.na ? anlT("No data", "தரவு இல்லை") : "0");
                var cls = (!item.value && item.na) ? "anl-quick-na" : "";
                return '<div class="anl-quick-item"><div class="anl-quick-icon">' + item.icon + '</div><div class="anl-quick-label">' + item.label + '</div><div class="anl-quick-value ' + cls + '">' + val + '</div></div>';
            }).join("");
        });
}

/* AI Insights */
function anlRefreshInsights() {
    var body = document.getElementById("anl-insights-body");
    var loading = document.getElementById("anl-insights-loading");
    var badge = document.getElementById("anl-confidence-badge");
    if (!body || !loading) return;
    var p = new URLSearchParams();
    if (anlState.crop) p.set("crop", anlState.crop);
    if (anlState.district) p.set("district", anlState.district);
    loading.style.display = "flex";
    body.innerHTML = "";
    fetch("/api/analytics/insights?" + p.toString())
        .then(function (r) { return r.json(); })
        .then(function (res) {
            loading.style.display = "none";
            if (!res.success) return;
            if (badge) badge.textContent = "🎯 " + (res.confidence || 0) + "%";
            if (res.insights) {
                var t = anlEscapeHtml(res.insights);
                t = t.replace(/^(✅|📈|📉|💡|⚠️|🌾|💧|🔬|🧪|🏛️)/gm, "");
                t = t.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
                t = t.replace(/__(.+?)__/g, "<strong>$1</strong>");
                t = t.replace(/\*(.+?)\*/g, "<em>$1</em>");
                var lines = t.split("\n").filter(function (l) { return l.trim(); });
                if (lines.length > 0) {
                    body.innerHTML = "<ul>" + lines.map(function (l) { return "<li>" + l.replace(/^[-*\d.\s]+/, "") + "</li>"; }).join("") + "</ul>";
                } else {
                    body.innerHTML = "<p>" + t + "</p>";
                }
            }
        })
        .catch(function () {
            loading.style.display = "none";
            body.innerHTML = '<p class="anl-insights-placeholder">' + anlT("Could not generate insights", "நுண்ணறிவுகளை உருவாக்க முடியவில்லை") + "</p>";
        });
}

function anlEscapeHtml(s) {
    if (typeof s !== "string") return s || "";
    var d = document.createElement("div");
    d.textContent = s;
    return d.innerHTML;
}

/* Export */
function anlExport() {
    var fmt = "csv";
    var p = new URLSearchParams();
    p.set("date_range", anlState.dateRange);
    if (anlState.crop) p.set("crop", anlState.crop);
    if (anlState.district) p.set("district", anlState.district);

    var menu = document.createElement("div");
    menu.className = "anl-export-menu show";
    menu.style.position = "absolute";
    menu.innerHTML = [
        { f: "csv", l: "📄 CSV" },
        { f: "json", l: "📋 JSON" },
        { f: "pdf", l: "📕 PDF" },
    ].map(function (opt) {
        return '<button class="anl-export-item" data-fmt="' + opt.f + '">' + opt.l + "</button>";
    }).join("");

    var btn = document.querySelector(".anl-btn-primary");
    if (!btn) return;
    var parent = btn.parentElement;
    parent.style.position = "relative";
    parent.appendChild(menu);

    menu.querySelectorAll(".anl-export-item").forEach(function (el) {
        el.addEventListener("click", function () {
            var fmt = this.dataset.fmt;
            menu.remove();
            anlToast(anlT("Exporting " + fmt.toUpperCase() + "...", fmt.toUpperCase() + " ஏற்றுமதி செய்கிறது..."), "info");
            fetch("/api/analytics/export/" + fmt + "?" + p.toString())
                .then(function (r) { return r.json(); })
                .then(function (res) {
                    if (!res.success) {
                        anlToast(res.error || anlT("Export failed", "ஏற்றுமதி தோல்வி"), "error");
                        return;
                    }
                    var binary = atob(res.data);
                    var arr = new Uint8Array(binary.length);
                    for (var i = 0; i < binary.length; i++) arr[i] = binary.charCodeAt(i);
                    var blob = new Blob([arr], { type: res.mime });
                    var url = URL.createObjectURL(blob);
                    var a = document.createElement("a");
                    a.href = url; a.download = res.filename;
                    document.body.appendChild(a); a.click();
                    document.body.removeChild(a);
                    URL.revokeObjectURL(url);
                    anlToast(anlT("Exported successfully", "வெற்றிகரமாக ஏற்றுமதி செய்யப்பட்டது"), "success");
                })
                .catch(function () {
                    anlToast(anlT("Export failed", "ஏற்றுமதி தோல்வி"), "error");
                });
        });
    });

    document.addEventListener("click", function closeMenu(e) {
        if (!menu.contains(e.target) && e.target !== btn) {
            menu.remove();
            document.removeEventListener("click", closeMenu);
        }
    });
}
