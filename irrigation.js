var irrState = {
    crop: null, cropName: null, cropObj: null,
    district: null, districtName: null, districtObj: null,
    season: null, seasonName: null, seasonObj: null,
    method: null, methodName: null, methodObj: null,
    recommendation: null,
    currentId: null,
};

var irrLoadingMessages = [
    t("Analyzing crop water requirements...", "பயிர் நீர் தேவைகளை பகுப்பாய்வு செய்கிறது..."),
    t("Studying district climate...", "மாவட்ட காலநிலையை ஆய்வு செய்கிறது..."),
    t("Evaluating seasonal conditions...", "பருவகால நிலைமைகளை மதிப்பிடுகிறது..."),
    t("Optimizing irrigation schedule...", "நீர்ப்பாசன அட்டவணையை மேம்படுத்துகிறது..."),
    t("Preparing AI irrigation plan...", "AI நீர்ப்பாசன திட்டத்தை தயாரிக்கிறது..."),
];

function getLang() {
    return window.IRR_DATA && window.IRR_DATA.lang || "en";
}

function t(en, ta) {
    return getLang() === "ta" ? ta : en;
}

function escapeHtml(str) {
    var div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
}

/* ── Searchable Dropdown Component ── */

function buildIrrSearchSelect(config) {
    var input = config.input;
    var items = config.items;
    var labelKey = config.labelKey || "en";
    var onSelect = config.onSelect;
    var portalName = config.name || "irr-dropdown";

    var dropdown = document.createElement("div");
    dropdown.className = "irr-search-dropdown";
    dropdown.setAttribute("data-portal", portalName);
    document.body.appendChild(dropdown);

    var outsideHandler;

    function renderOptions(query) {
        var q = (query || "").toLowerCase().trim();
        var html = "";
        for (var i = 0; i < items.length; i++) {
            var item = items[i];
            var label = item[labelKey] || item.en || item.id || "";
            if (q && label.toLowerCase().indexOf(q) < 0) continue;
            var displayText = item.ta && getLang() === "ta" ? item.ta : (item.en || label);
            html += '<div class="irr-search-option" data-index="' + i + '">' + escapeHtml(displayText) + "</div>";
        }
        if (!html) {
            html = '<div class="irr-search-option" style="color:var(--irr-text-secondary);cursor:default">' + t("No results found", "முடிவுகள் எதுவும் இல்லை") + "</div>";
        }
        dropdown.innerHTML = html;
    }

    function positionDropdown() {
        var rect = input.getBoundingClientRect();
        var top = rect.bottom + window.scrollY + 4;
        var left = rect.left + window.scrollX;
        dropdown.style.left = Math.max(4, left) + "px";
        dropdown.style.top = top + "px";
        dropdown.style.width = Math.min(rect.width, window.innerWidth - 8) + "px";
    }

    function openDropdown() {
        renderOptions(input.value);
        positionDropdown();
        dropdown.classList.add("open");
    }

    function closeDropdown() {
        dropdown.classList.remove("open");
    }

    input.addEventListener("focus", openDropdown);

    input.addEventListener("input", function () {
        renderOptions(input.value);
        if (!dropdown.classList.contains("open")) {
            positionDropdown();
            dropdown.classList.add("open");
        }
    });

    window.addEventListener("resize", function () {
        if (dropdown.classList.contains("open")) {
            positionDropdown();
        }
    }, { passive: true });

    outsideHandler = function (e) {
        if (dropdown.classList.contains("open") &&
            !input.contains(e.target) &&
            !dropdown.contains(e.target)) {
            closeDropdown();
        }
    };
    document.addEventListener("click", outsideHandler);
    document.addEventListener("touchstart", outsideHandler, { passive: true });

    dropdown.addEventListener("click", function (e) {
        var opt = e.target.closest(".irr-search-option");
        if (!opt || !opt.dataset.index) return;
        var idx = parseInt(opt.dataset.index);
        var item = items[idx];
        var displayText = item.ta && getLang() === "ta" ? item.ta : (item.en || item.id || "");
        input.value = displayText;
        closeDropdown();
        if (onSelect) onSelect(item, idx);
    });
}

/* ── Init ── */

function irrInit() {
    var lang = getLang();

    buildIrrSearchSelect({
        input: document.getElementById("irr-crop-input"),
        items: IRR_DATA.crops,
        labelKey: lang === "ta" ? "ta" : "en",
        name: "irr-crop",
        onSelect: function (item) {
            irrState.crop = item.en;
            irrState.cropName = item.ta && lang === "ta" ? item.ta : item.en;
            irrState.cropObj = item;
            showIrrCropInfo(item);
            revealIrrStep("district");
            updateIrrProgress();
        }
    });

    buildIrrSearchSelect({
        input: document.getElementById("irr-district-input"),
        items: IRR_DATA.districts,
        labelKey: lang === "ta" ? "ta" : "en",
        name: "irr-district",
        onSelect: function (item) {
            irrState.district = item.en;
            irrState.districtName = item.ta && lang === "ta" ? item.ta : item.en;
            irrState.districtObj = item;
            showIrrDistrictInfo(item);
            revealIrrStep("season");
            updateIrrProgress();
        }
    });

    buildIrrSearchSelect({
        input: document.getElementById("irr-season-input"),
        items: IRR_DATA.seasons,
        labelKey: lang === "ta" ? "ta" : "en",
        name: "irr-season",
        onSelect: function (item) {
            irrState.season = item.id;
            irrState.seasonName = item.ta && lang === "ta" ? item.ta : item.en;
            irrState.seasonObj = item;
            showIrrSeasonInfo(item);
            revealIrrStep("method");
            updateIrrProgress();
        }
    });

    buildIrrSearchSelect({
        input: document.getElementById("irr-method-input"),
        items: IRR_DATA.methods,
        labelKey: lang === "ta" ? "ta" : "en",
        name: "irr-method",
        onSelect: function (item) {
            irrState.method = item.id;
            irrState.methodName = item.ta && lang === "ta" ? item.ta : item.en;
            irrState.methodObj = item;
            showIrrMethodInfo(item);
            revealIrrStep("generate");
            updateIrrProgress();
        }
    });

    var searchInput = document.getElementById("irr-history-search");
    if (searchInput) {
        searchInput.addEventListener("input", function () { loadIrrHistory(); });
    }
}

/* ── Progressive Reveal ── */

var irrStepOrder = ["crop", "district", "season", "method", "generate"];

function revealIrrStep(step) {
    var idx = irrStepOrder.indexOf(step);
    var el = document.getElementById("irr-card-" + step);
    if (el && el.style.display !== "none" && el.style.display !== "") return;
    if (el) {
        el.style.display = "block";
        el.classList.remove("irr-fade-slide");
        void el.offsetWidth;
        el.classList.add("irr-fade-slide");
        el.scrollIntoView({ behavior: "smooth", block: "center" });
    }
}

function updateIrrProgress() {
    var fill = document.getElementById("irr-progress-fill");
    var label = document.getElementById("irr-progress-label");
    var count = 0;
    if (irrState.crop) count++;
    if (irrState.district) count++;
    if (irrState.season) count++;
    if (irrState.method) count++;
    var pct = (count / 4) * 100;
    if (fill) fill.style.width = pct + "%";
    if (label) label.textContent = count + "/4 " + t("Completed", "முடிந்தது");
    var btn = document.getElementById("irr-generate-btn");
    if (btn) btn.disabled = count < 4;
}

/* ── Info Cards ── */

function showIrrCropInfo(item) {
    var el = document.getElementById("irr-info-crop");
    if (!el) return;
    var lang = getLang();
    var wKey = lang === "ta" ? "water_ta" : "water_en";
    var dKey = lang === "ta" ? "duration_ta" : "duration_en";
    var distKey = lang === "ta" ? "districts_ta" : "districts_en";
    var name = lang === "ta" ? item.ta : item.en;
    el.style.display = "block";
    el.innerHTML =
        '<div><span class="irr-info-label">' + t("Crop", "பயிர்") + ':</span> <span class="irr-info-value">' + escapeHtml(name) + '</span></div>' +
        '<div><span class="irr-info-label">' + t("Duration", "கால அளவு") + ':</span> <span class="irr-info-value">' + escapeHtml(item[dKey] || "") + '</span></div>' +
        '<div><span class="irr-info-label">' + t("Water Requirement", "நீர் தேவை") + ':</span> <span class="irr-info-value">' + escapeHtml(item[wKey] || "") + '</span></div>' +
        '<div><span class="irr-info-label">' + t("Major Districts", "முக்கிய மாவட்டங்கள்") + ':</span> <span class="irr-info-value">' + escapeHtml(item[distKey] || "") + '</span></div>';
}

function showIrrDistrictInfo(item) {
    var el = document.getElementById("irr-info-district");
    if (!el) return;
    var lang = getLang();
    var cKey = lang === "ta" ? "climate_ta" : "climate_en";
    var wKey = lang === "ta" ? "water_ta" : "water_en";
    var crKey = lang === "ta" ? "crops_ta" : "crops_en";
    var name = lang === "ta" ? item.ta : item.en;
    el.style.display = "block";
    el.innerHTML =
        '<div><span class="irr-info-label">' + t("District", "மாவட்டம்") + ':</span> <span class="irr-info-value">' + escapeHtml(name) + '</span></div>' +
        '<div><span class="irr-info-label">' + t("Climate", "காலநிலை") + ':</span> <span class="irr-info-value">' + escapeHtml(item[cKey] || "") + '</span></div>' +
        '<div><span class="irr-info-label">' + t("Average Rainfall", "சராசரி மழைப்பொழிவு") + ':</span> <span class="irr-info-value">' + escapeHtml(item.rainfall || "") + '</span></div>' +
        '<div><span class="irr-info-label">' + t("Major Crops", "முக்கிய பயிர்கள்") + ':</span> <span class="irr-info-value">' + escapeHtml(item[crKey] || "") + '</span></div>' +
        '<div><span class="irr-info-label">' + t("Water Availability", "நீர் கிடைக்கும் தன்மை") + ':</span> <span class="irr-info-value">' + escapeHtml(item[wKey] || "") + '</span></div>';
}

function showIrrSeasonInfo(item) {
    var el = document.getElementById("irr-info-season");
    if (!el) return;
    var lang = getLang();
    var mKey = lang === "ta" ? "months_ta" : "months_en";
    var rKey = lang === "ta" ? "rainfall_ta" : "rainfall_en";
    var wKey = lang === "ta" ? "water_ta" : "water_en";
    var name = lang === "ta" ? item.ta : item.en;
    el.style.display = "block";
    el.innerHTML =
        '<div><span class="irr-info-label">' + t("Season", "பருவம்") + ':</span> <span class="irr-info-value">' + escapeHtml(name) + '</span></div>' +
        '<div><span class="irr-info-label">' + t("Cultivation Months", "சாகுபடி மாதங்கள்") + ':</span> <span class="irr-info-value">' + escapeHtml(item[mKey] || "") + '</span></div>' +
        '<div><span class="irr-info-label">' + t("Typical Rainfall", "வழக்கமான மழை") + ':</span> <span class="irr-info-value">' + escapeHtml(item[rKey] || "") + '</span></div>' +
        '<div><span class="irr-info-label">' + t("Water Availability", "நீர் கிடைக்கும் தன்மை") + ':</span> <span class="irr-info-value">' + escapeHtml(item[wKey] || "") + '</span></div>';
}

function showIrrMethodInfo(item) {
    var el = document.getElementById("irr-info-method");
    if (!el) return;
    var lang = getLang();
    var eKey = lang === "ta" ? "explanation_ta" : "explanation_en";
    var name = lang === "ta" ? item.ta : item.en;
    el.style.display = "block";
    el.innerHTML =
        '<div><span class="irr-info-label">' + t("Method", "முறை") + ':</span> <span class="irr-info-value">' + escapeHtml(name) + '</span></div>' +
        '<div style="grid-column:1/-1"><span class="irr-info-label">' + t("Explanation", "விளக்கம்") + ':</span> <span class="irr-info-value">' + escapeHtml(item[eKey] || "") + '</span></div>';
}

/* ── Generate ── */

function generateIrrigation() {
    if (!irrState.crop || !irrState.district || !irrState.season || !irrState.method) {
        showIrrToast(t("Please fill in all fields first.", "முதலில் அனைத்து புலங்களையும் நிரப்பவும்."), "error");
        return;
    }

    var overlay = document.getElementById("irr-loading-overlay");
    var loadingText = document.getElementById("irr-loading-text");
    overlay.style.display = "flex";

    var msgIdx = 0;
    var msgInterval = setInterval(function () {
        msgIdx = (msgIdx + 1) % irrLoadingMessages.length;
        loadingText.textContent = irrLoadingMessages[msgIdx];
    }, 2500);

    fetch("/api/irrigation/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            crop: irrState.crop,
            district: irrState.district,
            season: irrState.season,
            irrigation_method: irrState.method,
        })
    })
    .then(function (r) { return r.json(); })
    .then(function (res) {
        clearInterval(msgInterval);
        overlay.style.display = "none";
        if (res.success) {
            irrState.recommendation = res.recommendation;
            displayIrrResult(res);
        } else {
            var msg = res.error || t("Failed to generate plan", "திட்டத்தை உருவாக்க முடியவில்லை");
            showIrrToast(msg, "error");
        }
    })
    .catch(function (err) {
        clearInterval(msgInterval);
        overlay.style.display = "none";
        showIrrToast(t("Network error. Please try again.", "நெட்வொர்க் பிழை. மீண்டும் முயற்சிக்கவும்."), "error");
    });
}

/* ── Display Result ── */

function displayIrrResult(res) {
    var section = document.getElementById("irr-result-section");
    var meta = document.getElementById("irr-result-meta");
    var body = document.getElementById("irr-result-body");

    section.style.display = "block";
    var m = res.metadata || {};
    meta.innerHTML =
        '<span class="irr-meta-badge">🌾 ' + escapeHtml(m.crop || "") + '</span>' +
        '<span class="irr-meta-badge">📍 ' + escapeHtml(m.district || "") + '</span>' +
        '<span class="irr-meta-badge">📅 ' + escapeHtml(m.season || "") + '</span>' +
        '<span class="irr-meta-badge">💧 ' + escapeHtml(m.irrigation_method || "") + '</span>';

    body.innerHTML = renderIrrMarkdown(res.recommendation);
    section.scrollIntoView({ behavior: "smooth", block: "start" });
}

function renderIrrMarkdown(text) {
    if (!text) return "";
    var lines = escapeHtml(text).split("\n");
    var out = [];
    var inTable = false;
    var listType = null;

    function closeList() {
        if (listType) { out.push("</" + listType + ">"); listType = null; }
    }

    function openList(type) {
        if (listType === type) return;
        closeList();
        out.push("<" + type + ">");
        listType = type;
    }

    for (var i = 0; i < lines.length; i++) {
        var raw = lines[i];
        var line = raw.trim();

        if (!line) {
            closeList();
            if (inTable) { out.push("</table>"); inTable = false; }
            out.push("</p><p>");
            continue;
        }

        var h = line.match(/^(#{1,4})\s+(.+)/);
        if (h) {
            closeList();
            if (inTable) { out.push("</table>"); inTable = false; }
            var lv = Math.min(h[1].length, 4);
            out.push("<h" + lv + ">" + h[2] + "</h" + lv + ">");
            continue;
        }

        var t = line.match(/^\|(.+)\|$/);
        if (t) {
            closeList();
            var cells = t[1].split("|").map(function (c) { return c.trim(); });
            if (cells.every(function (c) { return /^[- ]+$/.test(c); })) continue;
            if (!inTable) {
                inTable = true;
                out.push("<table><thead><tr><td>" + cells.join("</td><td>") + "</td></tr></thead>");
            } else {
                out.push("<tr><td>" + cells.join("</td><td>") + "</td></tr>");
            }
            continue;
        }

        var bolded = raw.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");

        if (/^[\-*]\s/.test(line)) {
            openList("ul");
            out.push("<li>" + bolded.replace(/^[\-*]\s+/, "") + "</li>");
            continue;
        }

        if (/^\d+\.\s/.test(line)) {
            openList("ol");
            out.push("<li>" + bolded.replace(/^\d+\.\s+/, "") + "</li>");
            continue;
        }

        closeList();
        if (inTable) { out.push("</table>"); inTable = false; }
        out.push(bolded);
    }

    closeList();
    if (inTable) out.push("</table>");

    var html = out.join("\n");
    html = html.replace(/<br>\s*<\/(h[234]|li)>/g, "</$1>");
    html = html.replace(/<\/li>\s*<br>/g, "</li>");
    html = html.replace(/<p><\/p>/g, "");
    html = html.replace(/<table>\s*<\/table>/g, "");
    html = html.replace(/<\/table>\s*<br>/g, "</table>");
    html = "<p>" + html + "</p>";
    html = html.replace(/<p>\s*<(h[234]|table|ul|ol)/g, "<$1");
    html = html.replace(/(<\/(h[234]|table|ul|ol)>)\s*<\/p>/g, "$1");
    return html;
}

/* ── Save ── */

function autoSaveIrrPlan(res) {
    fetch("/api/irrigation/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            crop: irrState.crop,
            district: irrState.district,
            season: irrState.season,
            irrigation_method: irrState.method,
            recommendation: irrState.recommendation,
            language: getLang(),
        })
    })
    .then(function (r) { return r.json(); })
    .then(function (res) {
        if (res.success) {
            showIrrToast(t("Plan saved!", "திட்டம் சேமிக்கப்பட்டது!"), "success");
            loadIrrHistory();
            updateIrrStats();
        }
    })
    .catch(function () {});
}

function saveIrrigation() {
    if (!irrState.recommendation) {
        showIrrToast(t("No plan to save.", "சேமிக்க திட்டம் இல்லை."), "error");
        return;
    }
    fetch("/api/irrigation/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            crop: irrState.crop,
            district: irrState.district,
            season: irrState.season,
            irrigation_method: irrState.method,
            recommendation: irrState.recommendation,
            language: getLang(),
        })
    })
    .then(function (r) { return r.json(); })
    .then(function (res) {
        if (res.success) {
            showIrrToast(t("Plan saved!", "திட்டம் சேமிக்கப்பட்டது!"), "success");
            loadIrrHistory();
            updateIrrStats();
        } else {
            showIrrToast(res.error || t("Save failed", "சேமிப்பு தோல்வி"), "error");
        }
    })
    .catch(function () {
        showIrrToast(t("Save failed", "சேமிப்பு தோல்வி"), "error");
    });
}

/* ── History ── */

function loadIrrHistory() {
    var list = document.getElementById("irr-history-list");
    var search = document.getElementById("irr-history-search");
    var q = search ? search.value : "";
    var url = "/api/irrigation/history";
    if (q) url += "?search=" + encodeURIComponent(q);

    fetch(url)
    .then(function (r) { return r.json(); })
    .then(function (res) {
        if (!res.success) return;
        var items = res.history || [];
        if (!items.length) {
            list.innerHTML = '<div style="text-align:center;padding:20px;color:var(--irr-text-secondary)">' +
                t("No irrigation plans found.", "நீர்ப்பாசன திட்டங்கள் எதுவும் இல்லை.") + '</div>';
            return;
        }
        var html = "";
        for (var i = 0; i < items.length; i++) {
            var h = items[i];
            var date = h.created_at ? h.created_at.slice(0, 10) : "";
            html += '<div class="irr-history-item" onclick="viewIrrPlan(\'' + h.id + '\')">' +
                '<div class="irr-history-info">' +
                '<span class="irr-history-crop">💧 ' + escapeHtml(h.crop || "") + ' — ' + escapeHtml(h.district || "") + '</span>' +
                '<span class="irr-history-details">' + escapeHtml(h.season || "") + ' · ' + escapeHtml(h.irrigation_method || "") + ' · ' + date + '</span>' +
                '</div>' +
                '<div class="irr-history-actions" onclick="event.stopPropagation()">' +
                '<button class="irr-btn irr-btn-secondary irr-btn-sm" onclick="viewIrrPlan(\'' + h.id + '\')">👁️ ' + t("View", "பார்க்க") + '</button>' +
                '<button class="irr-btn irr-btn-secondary irr-btn-sm" onclick="deleteIrrPlan(\'' + h.id + '\')">🗑️ ' + t("Delete", "நீக்கு") + '</button>' +
                '</div></div>';
        }
        list.innerHTML = html;
    })
    .catch(function () {});
}

function deleteIrrPlan(id) {
    if (!confirm(t("Delete this plan?", "இந்த திட்டத்தை நீக்கவா?"))) return;
    fetch("/api/irrigation/" + id, { method: "DELETE" })
    .then(function (r) { return r.json(); })
    .then(function (res) {
        if (res.success) {
            showIrrToast(t("Plan deleted!", "திட்டம் நீக்கப்பட்டது!"), "success");
            loadIrrHistory();
            updateIrrStats();
        } else {
            showIrrToast(res.error || t("Delete failed", "நீக்கம் தோல்வி"), "error");
        }
    })
    .catch(function () {
        showIrrToast(t("Delete failed", "நீக்கம் தோல்வி"), "error");
    });
}

function viewIrrPlan(id) {
    fetch("/api/irrigation/history")
    .then(function (r) { return r.json(); })
    .then(function (res) {
        if (!res.success) return;
        var items = res.history || [];
        var found = null;
        for (var i = 0; i < items.length; i++) {
            if (items[i].id === id) { found = items[i]; break; }
        }
        if (!found) {
            showIrrToast(t("Plan not found.", "திட்டம் கிடைக்கவில்லை."), "error");
            return;
        }
        var overlay = document.getElementById("irr-modal-overlay");
        var body = document.getElementById("irr-modal-body");
        var lang = getLang();

        body.innerHTML =
            '<div style="margin-bottom:16px;display:flex;flex-wrap:wrap;gap:8px">' +
            '<span class="irr-meta-badge">🌾 ' + escapeHtml(found.crop || "") + '</span>' +
            '<span class="irr-meta-badge">📍 ' + escapeHtml(found.district || "") + '</span>' +
            '<span class="irr-meta-badge">📅 ' + escapeHtml(found.season || "") + '</span>' +
            '<span class="irr-meta-badge">💧 ' + escapeHtml(found.irrigation_method || "") + '</span>' +
            '<span class="irr-meta-badge">📆 ' + (found.created_at ? found.created_at.slice(0, 10) : "") + '</span>' +
            '</div>' +
            renderIrrMarkdown(found.recommendation || "");

        overlay.style.display = "flex";
    })
    .catch(function () {
        showIrrToast(t("Failed to load plan.", "திட்டத்தை ஏற்ற முடியவில்லை."), "error");
    });
}

function irrCloseModal(e) {
    if (e && e.target !== document.getElementById("irr-modal-overlay") && e.target.closest) {
        if (e.target.closest(".irr-modal")) return;
    }
    document.getElementById("irr-modal-overlay").style.display = "none";
}

/* ── Export ── */

var irrCurrentExportId = null;

function irrToggleExport(e) {
    e.stopPropagation();
    var menus = document.querySelectorAll(".irr-export-menu");
    menus.forEach(function (m) {
        if (m === e.currentTarget.nextElementSibling) {
            m.style.display = m.style.display === "block" ? "none" : "block";
        } else {
            m.style.display = "none";
        }
    });
}

document.addEventListener("click", function () {
    document.querySelectorAll(".irr-export-menu").forEach(function (m) { m.style.display = "none"; });
});

function irrExportResult(fmt) {
    if (!irrState.recommendation) {
        showIrrToast(t("No plan to export.", "ஏற்றுமதி செய்ய திட்டம் இல்லை."), "error");
        return;
    }
    var text = "IRRIGATION PLAN REPORT\n";
    text += "=======================\n";
    text += "Crop: " + (irrState.crop || "") + "\n";
    text += "District: " + (irrState.district || "") + "\n";
    text += "Season: " + (irrState.seasonName || "") + "\n";
    text += "Irrigation Method: " + (irrState.methodName || "") + "\n";
    text += "Date: " + new Date().toISOString().slice(0, 10) + "\n\n";
    text += irrState.recommendation;

    var mime = "text/plain";
    var ext = "txt";
    if (fmt === "csv") {
        text = "Field,Value\nCrop," + (irrState.crop || "") + "\nDistrict," + (irrState.district || "") + "\nSeason," + (irrState.seasonName || "") + "\nMethod," + (irrState.methodName || "") + "\nDate," + new Date().toISOString().slice(0, 10) + "\n";
        mime = "text/csv";
        ext = "csv";
    } else if (fmt === "pdf") {
        fetch("/api/irrigation/history")
        .then(function (r) { return r.json(); })
        .then(function (res) {
            var items = res.history || [];
            var found = null;
            for (var i = 0; i < items.length; i++) {
                if (items[i].crop === irrState.crop && items[i].district === irrState.district) {
                    found = items[i]; break;
                }
            }
            if (found) {
                var url = "/api/irrigation/export/" + found.id + "?format=pdf";
                fetch(url).then(function (r) { return r.json(); }).then(function (res) {
                    if (res.success && res.encoding === "base64") {
                        var binary = atob(res.export);
                        var arr = new Uint8Array(binary.length);
                        for (var i2 = 0; i2 < binary.length; i2++) arr[i2] = binary.charCodeAt(i2);
                        var blob = new Blob([arr], { type: "application/pdf" });
                        var link = document.createElement("a");
                        link.href = URL.createObjectURL(blob);
                        link.download = res.filename || "irrigation_plan.pdf";
                        link.click();
                    } else {
                        showIrrToast(t("Export failed.", "ஏற்றுமதி தோல்வி."), "error");
                    }
                });
            } else {
                showIrrToast(t("Save the plan first, then export PDF.", "முதலில் திட்டத்தை சேமிக்கவும், பின்னர் PDF ஏற்றுமதி செய்யவும்."), "error");
            }
        });
        return;
    }

    var blob = new Blob([text], { type: mime });
    var link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = "irrigation_plan." + ext;
    link.click();
}

/* ── Stats ── */

function updateIrrStats() {
    fetch("/api/irrigation/stats")
    .then(function (r) { return r.json(); })
    .then(function (res) {
        if (res.success && res.stats) {
            var el = document.getElementById("irr-total-plans");
            if (el) el.textContent = res.stats.total || 0;
        }
    })
    .catch(function () {});
}

/* ── Toast ── */

function showIrrToast(msg, type) {
    var toast = document.getElementById("irr-toast");
    if (!toast) return;
    toast.textContent = msg;
    toast.className = "irr-toast irr-toast-" + (type || "success");
    toast.style.display = "block";
    setTimeout(function () { toast.style.display = "none"; }, 3000);
}

/* ── Boot ── */

function irrBoot() {
    if (typeof IRR_DATA === "undefined") {
        setTimeout(irrBoot, 100);
        return;
    }
    irrInit();
    loadIrrHistory();
}

document.addEventListener("DOMContentLoaded", irrBoot);
