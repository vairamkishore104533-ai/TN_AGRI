var fertState = {
    season: "",
    crop: "",
    growthStage: "",
    irrigation: "",
    recommendation: null,
    seasonName: "",
    cropName: "",
    growthStageName: "",
    irrigationName: "",
};

function getLang() {
    return (window.FERT_DATA && FERT_DATA.lang) || "en";
}

function t(en, ta) {
    return getLang() === "ta" ? ta : en;
}

/* ── Searchable Dropdown Component ── */

function buildSearchSelect(config) {
    var input = config.input;
    var items = config.items;
    var labelKey = config.labelKey || "en";
    var onSelect = config.onSelect;
    var portalName = config.name || "dropdown";

    var dropdown = document.createElement("div");
    dropdown.className = "fert-search-dropdown";
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
            html += '<div class="fert-search-option" data-index="' + i + '">' + escapeHtml(displayText) + "</div>";
        }
        if (!html) {
            html = '<div class="fert-search-option" style="color:var(--fert-text-secondary);cursor:default">' + t("No results found", "முடிவுகள் எதுவும் இல்லை") + "</div>";
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
        var opt = e.target.closest(".fert-search-option");
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

function fertInit() {
    var lang = getLang();

    buildSearchSelect({
        input: document.getElementById("fert-season-input"),
        items: FERT_DATA.seasons,
        labelKey: lang === "ta" ? "ta" : "en",
        name: "season",
        onSelect: function (item) {
            fertState.season = item.id;
            fertState.seasonName = item.en;
            showSeasonInfo(item);
            revealStep("crop");
            updateProgress();
        }
    });

    buildSearchSelect({
        input: document.getElementById("fert-crop-input"),
        items: FERT_DATA.crops,
        labelKey: lang === "ta" ? "ta" : "en",
        name: "crop",
        onSelect: function (item) {
            fertState.crop = item.en;
            fertState.cropName = item.en;
            showCropInfo(item);
            revealStep("stage");
            updateProgress();
        }
    });

    buildSearchSelect({
        input: document.getElementById("fert-stage-input"),
        items: FERT_DATA.stages,
        labelKey: lang === "ta" ? "ta" : "en",
        name: "stage",
        onSelect: function (item) {
            fertState.growthStage = item.id;
            fertState.growthStageName = item.en;
            showStageInfo(item);
            revealStep("irrigation");
            updateProgress();
        }
    });

    buildSearchSelect({
        input: document.getElementById("fert-irrigation-input"),
        items: FERT_DATA.irrigation,
        labelKey: lang === "ta" ? "ta" : "en",
        name: "irrigation",
        onSelect: function (item) {
            fertState.irrigation = item.id;
            fertState.irrigationName = item.en;
            showIrrigationInfo(item);
            revealStep("generate");
            updateProgress();
        }
    });

    /* History listeners */
    var searchInput = document.getElementById("fert-history-search-input");
    if (searchInput) {
        searchInput.addEventListener("input", function () { loadFertHistory(); });
    }
    var seasonFilter = document.getElementById("fert-season-filter");
    if (seasonFilter) {
        seasonFilter.addEventListener("change", function () { loadFertHistory(); });
    }
}

/* ── Progressive Reveal ── */

var stepOrder = ["season", "crop", "stage", "irrigation", "generate"];

function revealStep(step) {
    var idx = stepOrder.indexOf(step);
    var el = document.getElementById("fert-card-" + step);
    if (el && el.style.display !== "none" && el.style.display !== "") return;

    if (el) {
        el.style.display = "block";
        el.classList.remove("fert-fade-slide");
        void el.offsetWidth;
        el.classList.add("fert-fade-slide");
        el.scrollIntoView({ behavior: "smooth", block: "center" });
    }
}

function updateProgress() {
    var bar = document.getElementById("fert-progress-bar");
    var fill = document.getElementById("fert-progress-fill");
    var label = document.getElementById("fert-progress-label");
    var count = 0;
    if (fertState.season) count++;
    if (fertState.crop) count++;
    if (fertState.growthStage) count++;
    if (fertState.irrigation) count++;

    if (!bar || !fill || !label) return;
    bar.style.display = "flex";
    fill.style.width = (count / 4 * 100) + "%";
    label.textContent = count + "/4 " + t("completed", "முடிந்தது");

    /* Enable generate button if all 4 selected */
    var genBtn = document.getElementById("fert-generate-btn");
    if (genBtn) {
        genBtn.disabled = count < 4;
    }

    if (count === 4) {
        revealStep("generate");
    }
}

/* ── Info Cards ── */

function showSeasonInfo(item) {
    var el = document.getElementById("fert-info-season");
    if (!el) return;
    var lang = getLang();
    var months = lang === "ta" ? item.months_ta : item.months_en;
    var rainfall = lang === "ta" ? item.rainfall_ta : item.rainfall_en;
    var crops = lang === "ta" ? item.crops_ta : item.crops_en;
    el.style.display = "block";
    el.innerHTML =
        '<div class="fert-info-grid">' +
            '<div class="fert-info-item"><span class="fert-info-label">' + t("Description", "விளக்கம்") + '</span><span class="fert-info-value">' + escapeHtml(item.desc_en) + '</span></div>' +
            '<div class="fert-info-item"><span class="fert-info-label">' + t("Cultivation Months", "சாகுபடி மாதங்கள்") + '</span><span class="fert-info-value">' + escapeHtml(months) + '</span></div>' +
            '<div class="fert-info-item"><span class="fert-info-label">' + t("Rainfall", "மழைப்பொழிவு") + '</span><span class="fert-info-value">' + escapeHtml(rainfall) + '</span></div>' +
            '<div class="fert-info-item"><span class="fert-info-label">' + t("Common Crops", "பொதுவான பயிர்கள்") + '</span><span class="fert-info-value">' + escapeHtml(crops) + '</span></div>' +
        '</div>';
}

function showCropInfo(item) {
    var el = document.getElementById("fert-info-crop");
    if (!el) return;
    var lang = getLang();
    var duration = lang === "ta" ? (item.duration_ta || "-") : (item.duration_en || "-");
    var districts = lang === "ta" ? (item.districts_ta || "-") : (item.districts_en || "-");
    el.style.display = "block";
    el.innerHTML =
        '<div class="fert-info-grid">' +
            '<div class="fert-info-item"><span class="fert-info-label">' + t("Crop Name", "பயிரின் பெயர்") + '</span><span class="fert-info-value">' + escapeHtml(item.en) + '</span></div>' +
            '<div class="fert-info-item"><span class="fert-info-label">' + t("Scientific Name", "அறிவியல் பெயர்") + '</span><span class="fert-info-value">' + escapeHtml(item.sci || "-") + '</span></div>' +
            '<div class="fert-info-item"><span class="fert-info-label">' + t("Average Duration", "சராசரி காலம்") + '</span><span class="fert-info-value">' + escapeHtml(duration) + '</span></div>' +
            '<div class="fert-info-item"><span class="fert-info-label">' + t("Major Districts", "முக்கிய மாவட்டங்கள்") + '</span><span class="fert-info-value">' + escapeHtml(districts) + '</span></div>' +
        '</div>';
}

function showStageInfo(item) {
    var el = document.getElementById("fert-info-stage");
    if (!el) return;
    var lang = getLang();
    var nutrient = lang === "ta" ? (item.nutrient_ta || "") : (item.nutrient_en || "");
    el.style.display = "block";
    el.innerHTML =
        '<div class="fert-info-grid">' +
            '<div class="fert-info-item"><span class="fert-info-label">' + t("Stage", "நிலை") + '</span><span class="fert-info-value">' + escapeHtml(item.en) + '</span></div>' +
            '<div class="fert-info-item" style="grid-column:1/-1"><span class="fert-info-label">' + t("Nutrient Needs", "ஊட்டச்சத்து தேவைகள்") + '</span><span class="fert-info-value">' + escapeHtml(nutrient) + '</span></div>' +
        '</div>';
}

function showIrrigationInfo(item) {
    var el = document.getElementById("fert-info-irrigation");
    if (!el) return;
    var lang = getLang();
    var water = lang === "ta" ? (item.water_ta || "") : (item.water_en || "");
    var fert = lang === "ta" ? (item.fert_ta || "") : (item.fert_en || "");
    el.style.display = "block";
    el.innerHTML =
        '<div class="fert-info-grid">' +
            '<div class="fert-info-item"><span class="fert-info-label">' + t("Method", "முறை") + '</span><span class="fert-info-value">' + escapeHtml(item.en) + '</span></div>' +
            '<div class="fert-info-item"><span class="fert-info-label">' + t("Water Requirement", "நீர் தேவை") + '</span><span class="fert-info-value">' + escapeHtml(water) + '</span></div>' +
            '<div class="fert-info-item" style="grid-column:1/-1"><span class="fert-info-label">' + t("Fertilizer Application", "உர பயன்பாடு") + '</span><span class="fert-info-value">' + escapeHtml(fert) + '</span></div>' +
        '</div>';
}

/* ── Generate ── */

function generateFertilizer() {
    if (!fertState.season || !fertState.crop || !fertState.growthStage || !fertState.irrigation) {
        showFertToast(t("Please complete all fields first.", "தயவுசெய்து முதலில் அனைத்து புலங்களையும் நிரப்பவும்."), "error");
        return;
    }

    var btn = document.getElementById("fert-generate-btn");
    var resultSection = document.getElementById("fert-result-section");
    if (btn) { btn.disabled = true; btn.innerHTML = '<span class="fert-spinner"></span> ' + t("Generating...", "உருவாக்குகிறது..."); }
    if (resultSection) resultSection.style.display = "none";

    var payload = {
        season: fertState.season,
        crop: fertState.crop,
        growth_stage: fertState.growthStage,
        irrigation: fertState.irrigation,
    };

    fetch("/api/fertilizer/recommend", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    })
    .then(function (r) {
        if (!r.ok) {
            return r.text().then(function (text) {
                try { var j = JSON.parse(text); throw new Error(j.error || t("Server error", "சேவையக பிழை")); }
                catch (e) { throw new Error(t("Server error", "சேவையக பிழை") + " (" + r.status + ")"); }
            });
        }
        return r.json();
    })
    .then(function (res) {
        if (btn) { btn.disabled = false; btn.innerHTML = t("Generate AI Fertilizer Recommendation", "AI உர பரிந்துரையை உருவாக்கவும்"); }
        if (!res.success) {
            showFertToast(res.error || t("Failed to generate.", "உருவாக்க முடியவில்லை."), "error");
            return;
        }
        fertState.recommendation = res;
        displayFertResult(res);
        autoSaveFertilizer(res);
    })
    .catch(function (err) {
        if (btn) { btn.disabled = false; btn.innerHTML = t("Generate AI Fertilizer Recommendation", "AI உர பரிந்துரையை உருவாக்கவும்"); }
        showFertToast(t("Error", "பிழை") + ": " + (err.message || t("Something went wrong", "ஏதோ தவறு ஏற்பட்டது")), "error");
    });
}

/* ── Display Result ── */

function displayFertResult(res) {
    var section = document.getElementById("fert-result-section");
    if (!section) return;
    section.style.display = "block";

    var meta = res.metadata || {};
    setFertText("fert-result-crop", meta.crop || fertState.cropName || fertState.crop);
    setFertText("fert-result-season", meta.season || fertState.seasonName || fertState.season);
    setFertText("fert-result-stage", meta.growth_stage || fertState.growthStageName || fertState.growthStage);
    setFertText("fert-result-irrigation", meta.irrigation || fertState.irrigationName || fertState.irrigation);

    var body = document.getElementById("fert-result-body");
    if (body) {
        body.innerHTML = '<div class="fert-markdown fert-fade-in">' + renderFertMarkdown(res.recommendation) + "</div>";
    }

    var saveBtn = document.getElementById("fert-save-btn");
    if (saveBtn) saveBtn.style.display = "inline-flex";
    var exportGroup = document.getElementById("fert-export-group");
    if (exportGroup) exportGroup.style.display = "inline-flex";

    section.scrollIntoView({ behavior: "smooth", block: "start" });
}

function setFertText(id, val) {
    var el = document.getElementById(id);
    if (el) el.textContent = val || "-";
}

/* ── Auto Save ── */

function autoSaveFertilizer(res) {
    var payload = {
        season: fertState.season,
        crop: fertState.crop,
        growth_stage: fertState.growthStage,
        irrigation_method: fertState.irrigation,
        recommendation: res.recommendation,
        language: document.documentElement.getAttribute("data-lang") || "en",
    };

    fetch("/api/fertilizer/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    })
    .then(function (r) { return r.json(); })
    .then(function (res) {
        if (res.success) {
            showFertToast(t("Recommendation saved!", "பரிந்துரை சேமிக்கப்பட்டது!"), "success");
            loadFertHistory();
            updateFertStats();
        }
    })
    .catch(function () {});
}

/* ── Manual Save ── */

function saveFertilizer() {
    if (!fertState.recommendation) {
        showFertToast(t("No recommendation to save.", "சேமிக்க பரிந்துரை இல்லை."), "error");
        return;
    }
    var btn = document.getElementById("fert-save-btn");
    if (btn) { btn.disabled = true; btn.textContent = t("Saving...", "சேமிக்கிறது..."); }

    var payload = {
        season: fertState.season,
        crop: fertState.crop,
        growth_stage: fertState.growthStage,
        irrigation_method: fertState.irrigation,
        recommendation: fertState.recommendation.recommendation,
        language: document.documentElement.getAttribute("data-lang") || "en",
    };

    fetch("/api/fertilizer/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    })
    .then(function (r) { return r.json(); })
    .then(function (res) {
        if (btn) { btn.disabled = false; btn.innerHTML = t("Save", "சேமி"); }
        if (res.success) {
            showFertToast(t("Recommendation saved!", "பரிந்துரை சேமிக்கப்பட்டது!"), "success");
            loadFertHistory();
            updateFertStats();
        } else {
            showFertToast(res.error || t("Failed to save.", "சேமிக்க முடியவில்லை."), "error");
        }
    })
    .catch(function () {
        if (btn) { btn.disabled = false; btn.innerHTML = t("Save", "சேமி"); }
        showFertToast(t("Save failed.", "சேமிப்பு தோல்வி."), "error");
    });
}

/* ── History ── */

function loadFertHistory() {
    var q = "";
    var searchInput = document.getElementById("fert-history-search-input");
    if (searchInput) q = searchInput.value.trim();

    var seasonFilter = document.getElementById("fert-season-filter");
    var seasonVal = seasonFilter ? seasonFilter.value : "";

    var url = "/api/fertilizer/history?";
    var params = [];
    if (q) params.push("search=" + encodeURIComponent(q));
    else if (seasonVal) params.push("season=" + encodeURIComponent(seasonVal));
    url += params.join("&");

    fetch(url)
    .then(function (r) { return r.json(); })
    .then(function (res) {
        var list = document.getElementById("fert-history-list");
        if (!list) return;
        if (!res.success || !res.history || res.history.length === 0) {
            list.innerHTML = '<div class="fert-empty">' + t("No recommendations yet.", "இதுவரை பரிந்துரைகள் இல்லை.") + '</div>';
            return;
        }
        var html = "";
        for (var i = 0; i < res.history.length; i++) {
            var h = res.history[i];
            var dateStr = h.created_at ? h.created_at.substring(0, 10) : "";
            html += '<div class="fert-history-item" data-id="' + h.id + '">';
            html += '<div class="fert-history-left">';
            html += '<span class="fert-history-crop">' + escapeHtml(h.crop) + "</span>";
            html += '<div class="fert-history-meta"><span>' + escapeHtml(h.season || "") + "</span><span>" + escapeHtml(h.growth_stage || "") + "</span><span>" + escapeHtml(h.irrigation_method || "") + "</span></div>";
            html += '<span class="fert-history-date">' + dateStr + "</span></div>";
            html += '<div class="fert-history-right">';
            html += '<button class="fert-btn-icon" title="' + t("View", "பார்") + '" onclick="viewFertHistory(\'' + h.id + '\')">👁</button>';
            html += '<div class="fert-export-dropdown" style="position:relative;display:inline-block">';
            html += '<button class="fert-btn-icon" title="' + t("Export", "ஏற்றுமதி") + '" onclick="toggleExportMenu(this)">📄</button>';
            html += '<div class="fert-export-menu" style="display:none;position:absolute;right:0;top:100%;background:var(--fert-card-bg);border:1px solid var(--fert-border);border-radius:8px;box-shadow:0 4px 12px rgba(0,0,0,0.1);z-index:100;min-width:90px;overflow:hidden">';
            html += '<button class="fert-export-option" style="display:block;width:100%;padding:8px 14px;border:none;background:transparent;cursor:pointer;font-size:0.8rem;text-align:left;font-family:inherit" onclick="exportFertilizer(\'' + h.id + "','txt');fertCloseMenus()\">TXT</button>";
            html += '<button class="fert-export-option" style="display:block;width:100%;padding:8px 14px;border:none;background:transparent;cursor:pointer;font-size:0.8rem;text-align:left;font-family:inherit" onclick="exportFertilizer(\'' + h.id + "','pdf');fertCloseMenus()\">PDF</button>";
            html += '<button class="fert-export-option" style="display:block;width:100%;padding:8px 14px;border:none;background:transparent;cursor:pointer;font-size:0.8rem;text-align:left;font-family:inherit" onclick="exportFertilizer(\'' + h.id + "','csv');fertCloseMenus()\">CSV</button>";
            html += "</div></div>";
            html += '<button class="fert-btn-icon" title="' + t("Delete", "நீக்கு") + '" onclick="deleteFertilizer(\'' + h.id + '\')">🗑</button>';
            html += "</div></div>";
        }
        list.innerHTML = html;
    });
}

function toggleExportMenu(btn) {
    fertCloseMenus();
    var menu = btn.nextElementSibling;
    if (menu) menu.style.display = menu.style.display === "block" ? "none" : "block";
}

function fertCloseMenus() {
    document.querySelectorAll(".fert-export-menu").forEach(function (m) { m.style.display = "none"; });
}

document.addEventListener("click", function (e) {
    if (!e.target.closest(".fert-export-dropdown")) {
        document.querySelectorAll(".fert-export-menu").forEach(function (m) { m.style.display = "none"; });
    }
});

function viewFertHistory(id) {
    fetch("/api/fertilizer/history")
    .then(function (r) { return r.json(); })
    .then(function (res) {
        var found = null;
        if (res.history) {
            for (var i = 0; i < res.history.length; i++) {
                if (res.history[i].id === id) { found = res.history[i]; break; }
            }
        }
        if (!found) { showFertToast(t("Recommendation not found.", "பரிந்துரை கிடைக்கவில்லை."), "error"); return; }
        var body = document.getElementById("fert-view-modal-body");
        if (!body) return;
        var html =
            '<div class="fert-view-field"><span class="fert-view-label">' + t("Crop", "பயிர்") + '</span><span class="fert-view-val">' + escapeHtml(found.crop) + "</span></div>" +
            '<div class="fert-view-field"><span class="fert-view-label">' + t("Season", "பருவம்") + '</span><span class="fert-view-val">' + escapeHtml(found.season) + "</span></div>" +
            '<div class="fert-view-field"><span class="fert-view-label">' + t("Growth Stage", "வளர்ச்சி நிலை") + '</span><span class="fert-view-val">' + escapeHtml(found.growth_stage) + "</span></div>" +
            '<div class="fert-view-field"><span class="fert-view-label">' + t("Irrigation", "நீர்ப்பாசனம்") + '</span><span class="fert-view-val">' + escapeHtml(found.irrigation_method) + "</span></div>" +
            '<div class="fert-view-field"><span class="fert-view-label">' + t("Date", "தேதி") + '</span><span class="fert-view-val">' + (found.created_at ? found.created_at.substring(0, 10) : "") + "</span></div>";
        if (found.recommendation) {
            html += '<div class="fert-view-field" style="margin-top:12px"><span class="fert-view-label">' + t("Recommendation", "பரிந்துரை") + '</span><div class="fert-markdown" style="font-size:0.85rem;line-height:1.6;margin-top:4px">' + renderFertMarkdown(found.recommendation) + "</div></div>";
        }
        body.innerHTML = html;
        document.getElementById("fert-view-modal").style.display = "flex";
    });
}

function closeFertViewModal() {
    document.getElementById("fert-view-modal").style.display = "none";
}

function deleteFertilizer(id) {
    if (!confirm(t("Delete this recommendation?", "இந்த பரிந்துரையை நீக்கவா?"))) return;
    fetch("/api/fertilizer/" + id, { method: "DELETE" })
    .then(function (r) { return r.json(); })
    .then(function (res) {
        if (res.success) {
            showFertToast(t("Recommendation deleted!", "பரிந்துரை நீக்கப்பட்டது!"), "success");
            loadFertHistory();
            if (res.stats) updateFertStatsFromServer(res.stats);
        } else {
            showFertToast(res.error || t("Failed to delete.", "நீக்க முடியவில்லை."), "error");
        }
    });
}

/* ── Export ── */

function exportFertilizer(id, fmt) {
    fetch("/api/fertilizer/export/" + id + "?format=" + fmt)
    .then(function (r) { return r.json(); })
    .then(function (res) {
        if (res.success) { downloadFertFile(res); }
        else { showFertToast(res.error || t("Export failed.", "ஏற்றுமதி தோல்வி."), "error"); }
    });
}

function downloadFertFile(res) {
    var content = res.export;
    var mimeType = res.mime;
    if (res.encoding === "base64") {
        var binary = atob(content);
        var array = new Uint8Array(binary.length);
        for (var i = 0; i < binary.length; i++) { array[i] = binary.charCodeAt(i); }
        content = array;
    }
    var blob = new Blob([content], { type: mimeType });
    var url = URL.createObjectURL(blob);
    var a = document.createElement("a");
    a.href = url;
    a.download = res.filename || "fertilizer_export.txt";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    showFertToast(t("Exported!", "ஏற்றுமதி செய்யப்பட்டது!"), "success");
}

function exportCurrentResult(fmt) {
    if (!fertState.recommendation) {
        showFertToast(t("No result to export.", "ஏற்றுமதி செய்ய முடிவு இல்லை."), "error");
        return;
    }
    var lines = [];
    lines.push("FERTILIZER RECOMMENDATION REPORT");
    lines.push("=".repeat(50));
    lines.push("Crop: " + (fertState.cropName || fertState.crop));
    lines.push("Season: " + (fertState.seasonName || fertState.season));
    lines.push("Growth Stage: " + (fertState.growthStageName || fertState.growthStage));
    lines.push("Irrigation: " + (fertState.irrigationName || fertState.irrigation));
    lines.push("");
    lines.push(fertState.recommendation.recommendation);

    if (fmt === "csv") {
        var csv = "Field,Value\n";
        csv += "Crop," + (fertState.cropName || fertState.crop) + "\n";
        csv += "Season," + (fertState.seasonName || fertState.season) + "\n";
        csv += "Growth Stage," + (fertState.growthStageName || fertState.growthStage) + "\n";
        csv += "Irrigation," + (fertState.irrigationName || fertState.irrigation) + "\n";
        downloadFertBlob(csv, "text/csv", "fertilizer_current.csv");
    } else {
        downloadFertBlob(lines.join("\n"), "text/plain", "fertilizer_current.txt");
    }
}

function downloadFertBlob(content, mime, filename) {
    var blob = new Blob([content], { type: mime });
    var url = URL.createObjectURL(blob);
    var a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    showFertToast(t("Exported!", "ஏற்றுமதி செய்யப்பட்டது!"), "success");
}

/* ── Stats ── */

function updateFertStats() {
    fetch("/api/fertilizer/stats")
    .then(function (r) { return r.json(); })
    .then(function (res) {
        if (res.success) updateFertStatsFromServer(res.stats);
    });
}

function updateFertStatsFromServer(stats) {
    var el = document.getElementById("fert-stat-total");
    if (el) el.textContent = stats.total || 0;
}

/* ── Markdown ── */

function renderFertMarkdown(text) {
    if (!text) return "";
    var html = text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    html = html.replace(/^### (.+)$/gm, "<h3>$1</h3>");
    html = html.replace(/^## (.+)$/gm, "<h2>$1</h2>");
    html = html.replace(/^# (.+)$/gm, "<h1>$1</h1>");
    html = html.replace(/^-\s\*\*(.+?)\*\*:\s*(.+)$/gm, "<li><strong>$1</strong>: $2</li>");
    html = html.replace(/^-\s(.+)$/gm, "<li>$1</li>");
    html = html.replace(/(<li>.*<\/li>\n?)+/g, "<ul>$&</ul>");
    html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
    html = html.replace(/`([^`]+)`/g, "<code>$1</code>");
    html = html.replace(/(\d+\.\s+)(.+)/gm, function (m, num, text) {
        return "<li>" + num + text + "</li>";
    });
    html = html.replace(/\n\n/g, "</p><p>");
    html = "<p>" + html + "</p>";
    html = html.replace(/<\/ul><p><ul>/g, "");
    html = html.replace(/<\/p>\n?<li>/g, "<li>");
    html = html.replace(/<\/li>\n?<\/p>/g, "</li>");
    html = html.replace(/<p><ul>/g, "<ul>");
    html = html.replace(/<\/ul><\/p>/g, "</ul>");
    return html;
}

function escapeHtml(str) {
    if (!str) return "";
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

/* ── Toast ── */

function showFertToast(msg, type) {
    var toast = document.getElementById("fert-toast");
    if (!toast) { alert(msg); return; }
    toast.textContent = msg;
    toast.className = "fert-toast " + (type || "");
    toast.style.display = "block";
    clearTimeout(toast._timer);
    toast._timer = setTimeout(function () { toast.style.display = "none"; }, 3000);
}

/* ── Boot ── */

window.generateFertilizer = generateFertilizer;
window.saveFertilizer = saveFertilizer;
window.toggleExportMenu = toggleExportMenu;
window.fertCloseMenus = fertCloseMenus;
window.exportCurrentResult = exportCurrentResult;
window.viewFertHistory = viewFertHistory;
window.exportFertilizer = exportFertilizer;
window.deleteFertilizer = deleteFertilizer;
window.closeFertViewModal = closeFertViewModal;
window.downloadFertFile = downloadFertFile;
window.showFertToast = showFertToast;

function fertBoot() {
    try { fertInit(); } catch (e) { console.error("fertInit error:", e); }
    try { loadFertHistory(); } catch (e) { console.error("loadFertHistory error:", e); }
    try { updateFertStats(); } catch (e) { console.error("updateFertStats error:", e); }
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", fertBoot);
} else {
    fertBoot();
}
