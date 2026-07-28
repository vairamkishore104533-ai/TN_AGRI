var mktState = {
    crop: null, cropName: null,
    market: null,
    currentPrice: null,
    sortKey: "market",
    sortDir: 1,
    page: 1,
    pageSize: 10,
    tableData: [],
    isFavorite: false,
    favId: null,
    historyPage: 1,
    historyPageSize: 5,
    historyItems: [],
};

var mktLoadingMessages = [
    t("Connecting to market database...", "சந்தை தரவுத்தளத்துடன் இணைக்கிறது..."),
    t("Fetching live crop prices...", "நேரடி பயிர் விலைகளை பெறுகிறது..."),
    t("Comparing Tamil Nadu markets...", "தமிழ்நாடு சந்தைகளை ஒப்பிடுகிறது..."),
    t("Analyzing price trends...", "விலை போக்குகளை பகுப்பாய்வு செய்கிறது..."),
    t("Preparing AI market insights...", "AI சந்தை நுண்ணறிவுகளை தயாரிக்கிறது..."),
];

function getLang() { return (MKT_DATA && MKT_DATA.lang) || "en"; }
function t(en, ta) { return getLang() === "ta" ? ta : en; }
function escapeHtml(s) { var d = document.createElement("div"); d.textContent = s; return d.innerHTML; }

function mktBoot() {
    if (typeof MKT_DATA === "undefined") { setTimeout(mktBoot, 100); return; }
    var cropInput = document.getElementById("mkt-crop-input");
    var marketInput = document.getElementById("mkt-market-input");
    if (!cropInput || !marketInput) return;
    try { buildMktSearchSelect({
        input: cropInput, items: MKT_DATA.crops,
        labelKey: getLang() === "ta" ? "ta" : "en",
        name: "mkt-crop",
        onSelect: function (item) { mktState.crop = item.en; mktState.cropName = (item.ta && getLang() === "ta") ? item.ta : item.en; }
    }); } catch(e) {}
    try { buildMktSearchSelect({
        input: marketInput, items: MKT_DATA.markets,
        labelKey: getLang() === "ta" ? "ta" : "en",
        name: "mkt-market",
        onSelect: function (item) { mktState.market = item.en; }
    }); } catch(e) {}
    try { renderFavorites(); } catch(e) {}
    loadHistory();
    try { mktRenderTable(); } catch(e) {}
}

function buildMktSearchSelect(config) {
    var input = config.input, items = config.items, labelKey = config.labelKey || "en", onSelect = config.onSelect, portalName = config.name || "mkt-dd";
    var dropdown = document.createElement("div");
    dropdown.className = "mkt-search-dropdown";
    dropdown.setAttribute("data-portal", portalName);
    document.body.appendChild(dropdown);
    function renderOptions(query) {
        var q = (query || "").toLowerCase().trim();
        var html = "";
        for (var i = 0; i < items.length; i++) {
            var item = items[i], label = item[labelKey] || item.en || "";
            if (q && label.toLowerCase().indexOf(q) < 0) continue;
            var display = item.ta && getLang() === "ta" ? item.ta : (item.en || label);
            html += '<div class="mkt-search-option" data-index="' + i + '">' + escapeHtml(display) + "</div>";
        }
        if (!html) html = '<div class="mkt-search-option" style="color:var(--mkt-text-secondary);cursor:default">' + t("No results found", "முடிவுகள் எதுவும் இல்லை") + "</div>";
        dropdown.innerHTML = html;
    }
    function reposition() {
        var rect = input.getBoundingClientRect();
        dropdown.style.left = Math.max(4, rect.left + window.scrollX) + "px";
        dropdown.style.top = (rect.bottom + window.scrollY + 4) + "px";
        dropdown.style.width = Math.min(rect.width, window.innerWidth - 8) + "px";
    }
    function open() { renderOptions(input.value); reposition(); dropdown.classList.add("open"); }
    function close() { dropdown.classList.remove("open"); }
    input.addEventListener("focus", open);
    input.addEventListener("input", function () {
        renderOptions(input.value);
        if (!dropdown.classList.contains("open")) { reposition(); dropdown.classList.add("open"); }
    });
    window.addEventListener("resize", function () { if (dropdown.classList.contains("open")) reposition(); }, { passive: true });
    var oh = function (e) { if (dropdown.classList.contains("open") && !input.contains(e.target) && !dropdown.contains(e.target)) close(); };
    document.addEventListener("click", oh);
    document.addEventListener("touchstart", oh, { passive: true });
    dropdown.addEventListener("click", function (e) {
        var opt = e.target.closest(".mkt-search-option");
        if (!opt || !opt.dataset.index) return;
        var idx = parseInt(opt.dataset.index), item = items[idx];
        var display = item.ta && getLang() === "ta" ? item.ta : (item.en || "");
        input.value = display;
        close();
        if (onSelect) onSelect(item, idx);
    });
}

function mktFetchPrice() {
    var ci = document.getElementById("mkt-crop-input").value.trim();
    var mi = document.getElementById("mkt-market-input").value.trim();
    if (!mktState.crop || !ci) { mktToast(t("Please select a crop.", "தயவுசெய்து ஒரு பயிரைத் தேர்ந்தெடுக்கவும்."), "error"); return; }
    if (!mktState.market || !mi) { mktToast(t("Please select a market.", "தயவுசெய்து ஒரு சந்தையைத் தேர்ந்தெடுக்கவும்."), "error"); return; }
    showLoading();
    var msgIdx = 0, msgInterval = setInterval(function () {
        msgIdx = (msgIdx + 1) % mktLoadingMessages.length;
        document.getElementById("mkt-loading-text").textContent = mktLoadingMessages[msgIdx];
    }, 2000);
    fetch("/api/market/prices?crop=" + encodeURIComponent(mktState.crop) + "&market=" + encodeURIComponent(mktState.market))
        .then(function (r) { return r.json(); })
        .then(function (res) {
            clearInterval(msgInterval); hideLoading();
            if (res.success) {
                mktState.currentPrice = res.price;
                mktDisplayPrice(res.price);
                mktLoadCompareForCrop(mktState.crop);
                mktLoadInsights(res.price);
                mktUpdateTableForCrop(mktState.crop);
            } else {
                mktToast(res.error || t("Failed to fetch price.", "விலையை பெற முடியவில்லை."), "error");
            }
        })
        .catch(function () { clearInterval(msgInterval); hideLoading(); mktToast(t("Network error.", "நெட்வொர்க் பிழை."), "error"); });
}

function mktSaveSearch() {
    var p = mktState.currentPrice;
    if (!p) { mktToast(t("No data to save.", "சேமிக்க தரவு இல்லை."), "error"); return; }
    fetch("/api/market/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ crop: p.crop, market: p.market, price: p.price, unit: p.unit, trend: p.trend, market_data: p })
    })
        .then(function (r) { return r.json(); })
        .then(function (res) {
            if (res.success) {
                mktToast(t("Saved!", "சேமிக்கப்பட்டது!"), "success");
                refreshHistory();
            } else {
                mktToast(res.error || t("Save failed.", "சேமிப்பு தோல்வி."), "error");
            }
        })
        .catch(function () { mktToast(t("Save failed.", "சேமிப்பு தோல்வி."), "error"); });
}

function mktDisplayPrice(p) {
    var section = document.getElementById("mkt-price-section");
    section.style.display = "block";
    section.classList.add("mkt-fade");
    document.getElementById("mkt-price-badge").innerHTML = "🌾 " + escapeHtml(p.crop) + " @ " + escapeHtml(p.market);
    document.getElementById("mkt-price-value").textContent = "₹" + p.price;
    document.getElementById("mkt-price-unit").textContent = "/" + (p.unit || "Quintal");
    var changeEl = document.getElementById("mkt-price-change");
    var pct = p.change_pct || 0;
    if (pct > 0) { changeEl.innerHTML = "⬆ " + t("Increasing", "அதிகரிப்பு") + " <span style='color:#2e7d32'>+" + pct + "%</span>"; }
    else if (pct < 0) { changeEl.innerHTML = "⬇ " + t("Decreasing", "குறைவு") + " <span style='color:#c62828'>" + pct + "%</span>"; }
    else { changeEl.innerHTML = "➡ " + t("Stable", "நிலையானது"); }
    var statusEl = document.getElementById("mkt-price-status");
    if (p.status === "open") { statusEl.innerHTML = "🟢 " + t("Open", "திறந்த"); statusEl.style.background = "#e8f5e9"; statusEl.style.color = "#2e7d32"; }
    else { statusEl.innerHTML = "🔴 " + t("Closed", "மூடப்பட்டது") + " (" + t("Showing latest price", "கடைசி விலை காட்டப்பட்டுள்ளது") + ")"; statusEl.style.background = "#ffebee"; statusEl.style.color = "#c62828"; }
    document.getElementById("mkt-price-updated").textContent = t("Last updated", "கடைசியாக புதுப்பிக்கப்பட்டது") + ": " + (p.updated_at || "--");
    mktCheckFavorite();
}

function mktLoadCompareForCrop(crop) {
    fetch("/api/market/compare?crop=" + encodeURIComponent(crop))
        .then(function (r) { return r.json(); })
        .then(function (res) {
            if (!res.success) return;
            var grid = document.getElementById("mkt-compare-grid");
            var data = res.prices || [];
            if (!data.length) { grid.innerHTML = "<p style='color:var(--mkt-text-secondary);font-size:13px'>" + t("No data", "தரவு இல்லை") + "</p>"; return; }
            var top = data[0].price;
            grid.innerHTML = data.slice(0, 5).map(function (d) {
                var hl = d.market === mktState.market ? " mkt-compare-highlight" : "";
                return '<div class="mkt-compare-row' + hl + '"><span class="mkt-compare-market">' + escapeHtml(d.market) + '</span><span class="mkt-compare-price" style="color:' + (d.price >= top ? '#2e7d32' : '#5a7a5a') + '">₹' + d.price + '</span></div>';
            }).join("");
        });
}

function mktLoadInsights(p) {
    var card = document.getElementById("mkt-insight-card");
    card.style.display = "block";
    document.getElementById("mkt-ins-crop").textContent = p.crop;
    document.getElementById("mkt-ins-market").textContent = p.market;
    document.getElementById("mkt-ins-price").textContent = "₹" + p.price + "/" + (p.unit || "Quintal");
    var trendMap = { up: t("Increasing", "அதிகரிப்பு"), down: t("Decreasing", "குறைவு"), stable: t("Stable", "நிலையானது") };
    document.getElementById("mkt-ins-trend").textContent = trendMap[p.trend] || trendMap.stable;
    var rec = mktGetRecommendation(p.trend, p.change_pct);
    var badge = document.getElementById("mkt-rec-badge");
    badge.textContent = rec.text;
    badge.style.background = rec.bg;
    badge.style.color = rec.color;
    badge.style.display = "inline-block";
    if (p.trend === "up") {
        document.getElementById("mkt-ins-besttime").innerHTML = p.change_pct > 3 ? "🔥 " + t("Today", "இன்று") : "📅 " + t("Next 2 Days", "அடுத்த 2 நாட்கள்");
        document.getElementById("mkt-ins-expected").innerHTML = "📈 " + t("Increasing", "அதிகரிக்கும்");
    } else if (p.trend === "down") {
        document.getElementById("mkt-ins-besttime").innerHTML = "⏳ " + t("Wait - Market may recover", "காத்திருங்கள் - சந்தை மீளலாம்");
        document.getElementById("mkt-ins-expected").innerHTML = "📉 " + t("May decrease further", "மேலும் குறையலாம்");
    } else {
        document.getElementById("mkt-ins-besttime").innerHTML = "✅ " + t("Anytime - Stable market", "எந்த நேரமும் - நிலையான சந்தை");
        document.getElementById("mkt-ins-expected").innerHTML = "➡ " + t("Stable", "நிலையானது");
    }
}

function mktGetRecommendation(trend, pct) {
    if (trend === "up" && pct > 3) return { text: "🟢 " + t("Sell Now", "இப்போது விற்கவும்"), bg: "#2e7d32", color: "white" };
    if (trend === "up") return { text: "🟡 " + t("Wait - Prices Rising", "காத்திருக்கவும் - விலை உயர்கிறது"), bg: "#f9a825", color: "#1a2e1a" };
    if (trend === "down" && pct < -3) return { text: "🔵 " + t("Hold Stock", "பங்குகளை வைத்திருக்கவும்"), bg: "#1565c0", color: "white" };
    if (trend === "down") return { text: "🟣 " + t("Store Safely", "பாதுகாப்பாக சேமிக்கவும்"), bg: "#7b1fa2", color: "white" };
    return { text: "🟢 " + t("Sell Now - Stable", "இப்போது விற்கவும் - நிலையானது"), bg: "#2e7d32", color: "white" };
}

function mktUpdateTableForCrop(crop) {
    fetch("/api/market/compare?crop=" + encodeURIComponent(crop))
        .then(function (r) { return r.json(); })
        .then(function (res) {
            if (!res.success || !res.prices) return;
            mktState.tableData = res.prices || [];
            mktState.page = 1;
            mktRenderTable();
        });
}

function mktSortTable(key) {
    if (mktState.sortKey === key) { mktState.sortDir *= -1; }
    else { mktState.sortKey = key; mktState.sortDir = 1; }
    mktRenderTable();
}

function mktRenderTable() {
    var data = mktState.tableData.slice().sort(function (a, b) {
        var av, bv;
        if (mktState.sortKey === "price") { av = a.price; bv = b.price; }
        else if (mktState.sortKey === "trend") { av = a.trend; bv = b.trend; }
        else { av = a.market; bv = b.market; }
        if (av < bv) return -1 * mktState.sortDir;
        if (av > bv) return 1 * mktState.sortDir;
        return 0;
    });
    var totalPages = Math.max(1, Math.ceil(data.length / mktState.pageSize));
    if (mktState.page > totalPages) mktState.page = totalPages;
    var start = (mktState.page - 1) * mktState.pageSize;
    var pageData = data.slice(start, start + mktState.pageSize);
    var tbody = document.getElementById("mkt-table-body");
    if (!pageData.length) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;color:var(--mkt-text-secondary);padding:30px">' + t("Search for a crop above to compare prices across markets.", "விலைகளை ஒப்பிட மேலே ஒரு பயிரைத் தேடவும்.") + '</td></tr>';
        document.getElementById("mkt-pagination").innerHTML = "";
        return;
    }
    var trendHtml = { up: '<span class="mkt-trend-up">▲ ' + t("Rising", "உயர்வு") + '</span>', down: '<span class="mkt-trend-down">▼ ' + t("Falling", "சரிவு") + '</span>', stable: '<span class="mkt-trend-stable">▬ ' + t("Stable", "நிலையானது") + '</span>' };
    tbody.innerHTML = pageData.map(function (d, i) {
        var hl = d.market === mktState.market ? " mkt-row-highlight" : "";
        var alt = i % 2 === 1 ? " mkt-row-alt" : "";
        return '<tr class="' + hl + alt + '"><td><strong>' + escapeHtml(d.market) + '</strong></td><td><strong>₹' + d.price + '</strong></td><td>' + (d.unit || "Quintal") + '</td><td>' + (trendHtml[d.trend] || trendHtml.stable) + '</td><td>' + (d.updated_at || "--") + '</td></tr>';
    }).join("");
    var pag = document.getElementById("mkt-pagination");
    var phtml = "";
    for (var i = 1; i <= totalPages; i++) {
        phtml += '<button class="mkt-page-btn' + (i === mktState.page ? ' mkt-active' : '') + '" onclick="mktState.page=' + i + ';mktRenderTable();">' + i + '</button>';
    }
    pag.innerHTML = phtml;
}

/* ── Favorites ── */

function mktToggleFavorite() {
    if (!mktState.crop) { mktToast(t("Search a crop first.", "முதலில் பயிரைத் தேடவும்."), "error"); return; }
    if (mktState.isFavorite && mktState.favId) {
        fetch("/api/market/favorites/" + mktState.favId, { method: "DELETE" })
            .then(function (r) { return r.json(); })
            .then(function (res) {
                if (res.success) {
                    mktState.isFavorite = false; mktState.favId = null;
                    mktToast(t("Removed from favorites!", "விருப்பங்களில் இருந்து நீக்கப்பட்டது!"), "success");
                    renderFavorites();
                }
            });
        return;
    }
    fetch("/api/market/favorites/add", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ crop: mktState.crop })
    })
        .then(function (r) { return r.json(); })
        .then(function (res) {
            if (res.success) {
                mktState.isFavorite = true; mktState.favId = res.id;
                mktToast(t("Added to favorites!", "விருப்பங்களில் சேர்க்கப்பட்டது!"), "success");
                renderFavorites();
            } else { mktToast(res.error || t("Failed.", "தோல்வி."), "error"); }
        });
}

function mktCheckFavorite() {
    var favs = MKT_DATA.favorites || [];
    mktState.isFavorite = false; mktState.favId = null;
    for (var i = 0; i < favs.length; i++) {
        if (favs[i].crop === mktState.crop) { mktState.isFavorite = true; mktState.favId = favs[i].id; break; }
    }
}

function renderFavorites() {
    var bar = document.getElementById("mkt-favorites-bar");
    var items = document.getElementById("mkt-fav-items");
    var favs = MKT_DATA.favorites || [];
    if (!favs.length) { bar.style.display = "none"; return; }
    bar.style.display = "flex";
    items.innerHTML = favs.map(function (f) {
        return '<span class="mkt-fav-chip" onclick="mktLoadFavorite(\'' + escapeHtml(f.crop) + '\')">⭐ ' + escapeHtml(f.crop) + '</span>';
    }).join("");
}

function mktLoadFavorite(crop) {
    var ci = document.getElementById("mkt-crop-input");
    ci.value = crop;
    mktState.crop = crop;
    mktFetchPrice();
}

/* ── Export ── */

function mktExportPrice() {
    if (!mktState.currentPrice) { mktToast(t("No data to export.", "ஏற்றுமதி செய்ய தரவு இல்லை."), "error"); return; }
    var p = mktState.currentPrice;
    var lines = [];
    lines.push(t("Crop", "பயிர்") + ": " + p.crop);
    lines.push(t("Market", "சந்தை") + ": " + p.market);
    lines.push(t("Price", "விலை") + ": ₹" + p.price);
    lines.push(t("Unit", "அலகு") + ": " + (p.unit || "Quintal"));
    lines.push(t("Trend", "போக்கு") + ": " + p.trend);
    lines.push(t("Date", "தேதி") + ": " + new Date().toLocaleString());
    var text = lines.join("\n");
    var blob = new Blob([text], { type: "text/plain" });
    var a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "market_" + p.crop + "_" + p.market + ".txt";
    a.click();
    URL.revokeObjectURL(a.href);
    mktToast(t("Exported!", "ஏற்றுமதி செய்யப்பட்டது!"), "success");
}

/* ── History ── */

function renderHistoryList(items) {
    var list = document.getElementById("mkt-history-list");
    if (!items || !items.length) {
        list.innerHTML = '<div style="text-align:center;padding:20px;color:var(--mkt-text-secondary)">' + t("No saved searches. Click Save after fetching a price.", "சேமித்த தேடல்கள் இல்லை. விலையைப் பெற்ற பின் சேமி என்பதைக் கிளிக் செய்யவும்.") + '</div>';
        return;
    }
    var totalPages = Math.max(1, Math.ceil(items.length / mktState.historyPageSize));
    if (mktState.historyPage > totalPages) mktState.historyPage = totalPages;
    var start = (mktState.historyPage - 1) * mktState.historyPageSize;
    var pageItems = items.slice(start, start + mktState.historyPageSize);
    list.innerHTML = pageItems.map(function (h) {
        var date = h.created_at ? h.created_at.slice(0, 10) : "";
        return '<div class="mkt-history-item"><div class="mkt-history-info"><span class="mkt-history-location">📊 ' + escapeHtml(h.crop || "") + ' @ ' + escapeHtml(h.market || "") + ' — ₹' + h.price + '</span><span class="mkt-history-details">' + date + '</span></div><div class="mkt-history-actions" onclick="event.stopPropagation()"><button class="mkt-btn mkt-btn-ghost mkt-btn-sm" onclick="mktViewHistory(\'' + h.id + '\')">👁️ ' + t("View", "பார்க்க") + '</button><button class="mkt-btn mkt-btn-ghost mkt-btn-sm" onclick="mktDeleteHistory(\'' + h.id + '\')">🗑️ ' + t("Delete", "நீக்கு") + '</button></div></div>';
    }).join("");
    if (totalPages > 1) {
        var hp = "";
        for (var i = 1; i <= totalPages; i++) {
            hp += '<button class="mkt-page-btn' + (i === mktState.historyPage ? ' mkt-active' : '') + '" onclick="mktState.historyPage=' + i + ';renderHistoryList(mktState.historyItems);" style="margin:4px 2px;font-size:11px">' + i + '</button>';
        }
        list.innerHTML += '<div style="text-align:center;margin-top:8px">' + hp + '</div>';
    }
}

function loadHistory() {
    mktState.historyItems = (MKT_DATA && MKT_DATA.history) || [];
    renderHistoryList(mktState.historyItems);
}

function refreshHistory() {
    fetch("/api/market/history")
        .then(function (r) { return r.json(); })
        .then(function (res) {
            if (res.success && res.history) {
                mktState.historyItems = res.history;
                renderHistoryList(mktState.historyItems);
            }
        })
        .catch(function () {});
}

function mktViewHistory(id) {
    fetch("/api/market/history")
        .then(function (r) { return r.json(); })
        .then(function (res) {
            if (!res.success) return;
            var items = res.history || [], found = null;
            for (var i = 0; i < items.length; i++) { if (items[i].id === id) { found = items[i]; break; } }
            if (!found) { mktToast(t("Record not found.", "பதிவு கிடைக்கவில்லை."), "error"); return; }
            document.getElementById("mkt-crop-input").value = found.crop;
            document.getElementById("mkt-market-input").value = found.market;
            mktState.crop = found.crop;
            mktState.market = found.market;
            mktState.currentPrice = { crop: found.crop, market: found.market, price: found.price, unit: found.unit, trend: found.trend, updated_at: found.created_at ? found.created_at.slice(11, 16) : "--", status: "closed", change_pct: 0 };
            mktDisplayPrice(mktState.currentPrice);
            mktLoadCompareForCrop(found.crop);
            mktLoadInsights(mktState.currentPrice);
            mktUpdateTableForCrop(found.crop);
        });
}

function mktDeleteHistory(id) {
    if (!confirm(t("Delete this record?", "இந்த பதிவை நீக்கவா?"))) return;
    fetch("/api/market/history/" + id, { method: "DELETE" })
        .then(function (r) { return r.json(); })
        .then(function (res) {
            if (res.success) { mktToast(t("Record deleted!", "பதிவு நீக்கப்பட்டது!"), "success"); refreshHistory(); }
            else { mktToast(res.error || t("Delete failed.", "நீக்கம் தோல்வி."), "error"); }
        });
}

function mktSetLanguage(lang) {
    fetch("/set-language", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ lang: lang })
    })
        .then(function () { location.reload(); });
}

function showLoading() { document.getElementById("mkt-loading-overlay").style.display = "flex"; }
function hideLoading() { document.getElementById("mkt-loading-overlay").style.display = "none"; }

function mktToast(msg, type) {
    var toast = document.getElementById("mkt-toast");
    if (!toast) return;
    toast.textContent = msg;
    toast.className = "mkt-toast mkt-toast-" + (type || "success");
    toast.style.display = "block";
    setTimeout(function () { toast.style.display = "none"; }, 3000);
}

document.addEventListener("DOMContentLoaded", function () {
    if (document.getElementById("mkt-crop-input")) { mktBoot(); }
});
