var scmState = {
    currentScheme: null,
    savedSchemes: [],
    recentSchemes: [],
    notificationStatus: {},
    searchTimeout: null,
};

function scmGetLang() { return (window.SCM_DATA && SCM_DATA.lang) || "en"; }
function scmT(en, ta) { return scmGetLang() === "ta" ? ta : en; }
function scmEscapeHtml(s) { var d = document.createElement("div"); d.textContent = s; return d.innerHTML; }

function scmToast(msg, type) {
    var t = document.getElementById("scm-toast");
    t.textContent = msg;
    t.className = "scm-toast " + type;
    t.classList.add("show");
    clearTimeout(t._hide);
    t._hide = setTimeout(function () { t.classList.remove("show"); }, 3000);
}

function scmBoot() {
    if (typeof SCM_DATA === "undefined") { setTimeout(scmBoot, 100); return; }
    scmState.savedSchemes = SCM_DATA.saved || [];
    scmState.recentSchemes = SCM_DATA.recent || [];
    scmState.notificationStatus = SCM_DATA.notifications || {};
    scmRenderStrip();
    scmRenderFeatured();
    scmRenderCategories();
    scmRenderFaqs();
    scmPopulateEligibilitySelect();
    scmRenderSchemeList(SCM_DATA.allSchemes || []);
    var searchInput = document.getElementById("scm-search-input");
    if (searchInput) {
        searchInput.addEventListener("input", function () {
            clearTimeout(scmState.searchTimeout);
            scmState.searchTimeout = setTimeout(scmSearch, 400);
        });
    }
    var catSelect = document.getElementById("scm-category-select");
    if (catSelect) {
        catSelect.addEventListener("change", scmSearch);
    }
}

/* Render Strip: Saved + Recent */
function scmRenderStrip() {
    var strip = document.getElementById("scm-strip");
    if (!strip) return;
    var savedSection = document.getElementById("scm-strip-saved");
    var recentSection = document.getElementById("scm-strip-recent");
    var savedItems = document.getElementById("scm-strip-saved-items");
    var recentItems = document.getElementById("scm-strip-recent-items");
    if (!savedItems || !recentItems) return;

    if (scmState.savedSchemes.length > 0) {
        savedItems.innerHTML = scmState.savedSchemes.map(function (s) {
            var sd = s.scheme_data || {};
            return '<span class="scm-strip-chip" onclick="scmOpenModal(\'' + scmEscapeHtml(sd.id || s.scheme_id) + '\')">' + scmEscapeHtml(sd.icon || "🏛️") + " " + scmEscapeHtml(sd.name || s.scheme_id) + "</span>";
        }).join("");
        savedSection.style.display = "flex";
    } else {
        savedSection.style.display = "none";
    }

    if (scmState.recentSchemes.length > 0) {
        recentItems.innerHTML = scmState.recentSchemes.slice(0, 8).map(function (r) {
            var sd = r.scheme_data || {};
            return '<span class="scm-strip-chip" onclick="scmOpenModal(\'' + scmEscapeHtml(sd.id || r.scheme_id) + '\')">' + scmEscapeHtml(sd.icon || "🕐") + " " + scmEscapeHtml(sd.name || r.scheme_id) + "</span>";
        }).join("");
        recentSection.style.display = "flex";
    } else {
        recentSection.style.display = "none";
    }

    strip.style.display = (scmState.savedSchemes.length > 0 || scmState.recentSchemes.length > 0) ? "flex" : "none";
}

/* Featured */
function scmRenderFeatured() {
    var container = document.getElementById("scm-featured-scroll");
    if (!container) return;
    var schemes = SCM_DATA.featured || [];
    if (!schemes.length) {
        container.innerHTML = '<div class="scm-featured-empty">' + scmT("No featured schemes available", "முக்கிய திட்டங்கள் எதுவும் இல்லை") + "</div>";
        return;
    }
    container.innerHTML = schemes.map(function (s) {
        return '<div class="scm-featured-card" onclick="scmOpenModal(\'' + scmEscapeHtml(s.id) + '\')">' +
            '<div class="scm-featured-icon">' + (s.icon || "🏛️") + "</div>" +
            '<div class="scm-featured-name">' + scmEscapeHtml(scmGetLang() === "ta" ? s.name_ta : s.name) + "</div>" +
            '<div class="scm-featured-dept">' + scmEscapeHtml(scmGetLang() === "ta" ? s.department_ta : s.department) + "</div>" +
            '<div class="scm-featured-desc">' + scmEscapeHtml(scmGetLang() === "ta" ? s.benefits_ta : s.benefits) + "</div>" +
            '<a href="' + scmEscapeHtml(s.link) + '" target="_blank" class="scm-featured-link" onclick="event.stopPropagation()">' +
            scmT("Apply Now →", "இப்போது விண்ணப்பிக்கவும் →") + "</a>" +
            "</div>";
    }).join("");
}

/* Categories */
function scmRenderCategories() {
    var container = document.getElementById("scm-category-grid");
    if (!container) return;
    var cats = SCM_DATA.categories || [];
    container.innerHTML = cats.map(function (c) {
        return '<div class="scm-category-card" onclick="scmFilterByCategory(\'' + scmEscapeHtml(c.id) + '\')">' +
            '<div class="scm-category-icon">' + (c.icon || "📂") + "</div>" +
            '<div class="scm-category-name">' + scmEscapeHtml(scmGetLang() === "ta" ? c.ta : c.en) + "</div>" +
            "</div>";
    }).join("");
}

function scmFilterByCategory(catId) {
    var sel = document.getElementById("scm-category-select");
    if (sel) sel.value = catId;
    scmSearch();
    document.getElementById("scm-schemes-section").scrollIntoView({ behavior: "smooth" });
}

/* Search */
function scmSearch() {
    var query = document.getElementById("scm-search-input") ? document.getElementById("scm-search-input").value : "";
    var category = document.getElementById("scm-category-select") ? document.getElementById("scm-category-select").value : "";
    var params = new URLSearchParams();
    if (query) params.set("search", query);
    if (category) params.set("category", category);
    var url = "/api/schemes?" + params.toString();
    var list = document.getElementById("scm-scheme-list");
    if (list) list.innerHTML = '<div style="text-align:center;padding:30px"><div class="scm-spinner" style="margin:0 auto"></div></div>';
    fetch(url)
        .then(function (r) { return r.json(); })
        .then(function (res) {
            if (res.success) {
                scmRenderSchemeList(res.schemes);
            } else {
                scmRenderSchemeList([]);
                scmToast(res.error || "Error", "error");
            }
        })
        .catch(function () { scmRenderSchemeList([]); scmToast("Network error", "error"); });
}

/* Scheme List */
function scmRenderSchemeList(schemes) {
    var list = document.getElementById("scm-scheme-list");
    var count = document.getElementById("scm-count");
    if (!list) return;
    if (count) count.textContent = "(" + schemes.length + ")";
    if (!schemes.length) {
        list.innerHTML = '<div class="scm-scheme-empty">' + scmT("No schemes found", "திட்டங்கள் எதுவும் கிடைக்கவில்லை") + "</div>";
        return;
    }
    list.innerHTML = schemes.map(function (s) {
        var isSaved = scmState.savedSchemes.some(function (sv) { return sv.scheme_id === s.id; });
        var notifOn = scmState.notificationStatus[s.id];
        return '<div class="scm-scheme-item" onclick="scmOpenModal(\'' + scmEscapeHtml(s.id) + '\')">' +
            '<div class="scm-scheme-item-top">' +
            '<div class="scm-scheme-item-info">' +
            '<div class="scm-scheme-item-name"><span class="scm-scheme-item-icon">' + (s.icon || "🏛️") + "</span> " +
            scmEscapeHtml(scmGetLang() === "ta" ? s.name_ta : s.name) + "</div>" +
            '<div class="scm-scheme-item-dept">' + scmEscapeHtml(scmGetLang() === "ta" ? s.department_ta : s.department) + "</div>" +
            '<div class="scm-scheme-item-desc">' + scmEscapeHtml(scmGetLang() === "ta" ? s.benefits_ta : s.benefits) + "</div>" +
            "</div>" +
            '<div class="scm-scheme-item-actions">' +
            (isSaved ? '<button class="scm-btn scm-btn-sm scm-btn-danger" onclick="event.stopPropagation();scmUnsaveScheme(\'' + scmEscapeHtml(s.id) + '\')">' + scmT("Unsave", "நீக்க") + "</button>" :
            '<button class="scm-btn scm-btn-sm scm-btn-primary" onclick="event.stopPropagation();scmSaveScheme(\'' + scmEscapeHtml(s.id) + '\')">📌 ' + scmT("Save", "சேமிக்க") + "</button>") +
            (notifOn === undefined || notifOn === null ? '<button class="scm-btn scm-btn-sm scm-btn-ghost" onclick="event.stopPropagation();scmToggleNotif(\'' + scmEscapeHtml(s.id) + '\')">🔔 ' + scmT("Notify", "அறிவிப்பு") + "</button>" :
            '<button class="scm-btn scm-btn-sm ' + (notifOn ? 'scm-btn-primary' : 'scm-btn-ghost') + '" onclick="event.stopPropagation();scmToggleNotif(\'' + scmEscapeHtml(s.id) + '\')">' +
            (notifOn ? "🔔 " + scmT("On", "இயக்கத்தில்") : "🔕 " + scmT("Off", "முடக்கத்தில்")) + "</button>") +
            "</div>" +
            "</div>" +
            "</div>";
    }).join("");
}

/* Modal */
function scmOpenModal(schemeId) {
    if (!schemeId) return;
    scmLogViewed(schemeId);
    var scheme = null;
    if (SCM_DATA.allSchemes) {
        for (var i = 0; i < SCM_DATA.allSchemes.length; i++) {
            if (SCM_DATA.allSchemes[i].id === schemeId) { scheme = SCM_DATA.allSchemes[i]; break; }
        }
    }
    if (!scheme) {
        fetch("/api/schemes/" + encodeURIComponent(schemeId))
            .then(function (r) { return r.json(); })
            .then(function (res) {
                if (res.success && res.scheme) scmShowModal(res.scheme);
                else scmToast(scmT("Scheme not found", "திட்டம் கிடைக்கவில்லை"), "error");
            })
            .catch(function () { scmToast("Network error", "error"); });
        return;
    }
    scmShowModal(scheme);
}

function scmShowModal(scheme) {
    var overlay = document.getElementById("scm-modal");
    var titleEl = document.getElementById("scm-modal-title");
    var bodyEl = document.getElementById("scm-modal-body");
    if (!overlay || !titleEl || !bodyEl) return;
    var lang = scmGetLang();
    var isSaved = scmState.savedSchemes.some(function (s) { return s.scheme_id === scheme.id; });
    var notifOn = scmState.notificationStatus[scheme.id];

    titleEl.innerHTML = (scheme.icon || "🏛️") + " " + scmEscapeHtml(lang === "ta" ? scheme.name_ta : scheme.name);
    bodyEl.innerHTML =
        '<div class="scm-modal-icon" style="text-align:center">' + (scheme.icon || "🏛️") + "</div>" +
        '<div class="scm-modal-field"><div class="scm-modal-label">' + scmT("Department", "துறை") + "</div>" +
        '<div class="scm-modal-value">' + scmEscapeHtml(lang === "ta" ? scheme.department_ta : scheme.department) + "</div></div>" +
        '<div class="scm-modal-field"><div class="scm-modal-label">' + scmT("Category", "வகை") + "</div>" +
        '<div class="scm-modal-value">' + scmEscapeHtml(lang === "ta" ? scheme.category_ta : scheme.category_en) + "</div></div>" +
        (scheme.deadline ? '<div class="scm-modal-field"><div class="scm-modal-label">' + scmT("Deadline", "கடைசி தேதி") + '</div><div class="scm-modal-value">' + scmEscapeHtml(scheme.deadline) + "</div></div>" : "") +
        '<div class="scm-modal-field"><div class="scm-modal-label">' + scmT("Benefits", "நன்மைகள்") + "</div>" +
        '<div class="scm-modal-value">' + scmEscapeHtml(lang === "ta" ? scheme.benefits_ta : scheme.benefits) + "</div></div>" +
        '<div class="scm-modal-field"><div class="scm-modal-label">' + scmT("Eligibility", "தகுதி") + "</div>" +
        '<div class="scm-modal-value">' + scmEscapeHtml(lang === "ta" ? scheme.eligibility_ta : scheme.eligibility) + "</div></div>" +
        '<div class="scm-modal-field"><div class="scm-modal-label">' + scmT("Required Documents", "தேவையான ஆவணங்கள்") + "</div>" +
        '<div class="scm-modal-value">' + scmEscapeHtml(lang === "ta" ? scheme.documents_ta : scheme.documents) + "</div></div>" +
        '<div class="scm-modal-actions">' +
        '<a href="' + scmEscapeHtml(scheme.link) + '" target="_blank" class="scm-btn scm-btn-primary">' + scmT("Apply Now →", "இப்போது விண்ணப்பிக்கவும் →") + "</a>" +
        (isSaved ? '<button class="scm-btn scm-btn-danger" onclick="scmUnsaveScheme(\'' + scmEscapeHtml(scheme.id) + '\');scmCloseModal()">' + scmT("Unsave", "சேமிப்பிலிருந்து நீக்க") + "</button>" :
        '<button class="scm-btn scm-btn-primary" onclick="scmSaveScheme(\'' + scmEscapeHtml(scheme.id) + '\')">📌 ' + scmT("Save Scheme", "திட்டத்தை சேமிக்க") + "</button>") +
        (notifOn === undefined || notifOn === null ? '<button class="scm-btn scm-btn-ghost" onclick="scmToggleNotif(\'' + scmEscapeHtml(scheme.id) + '\')">🔔 ' + scmT("Get Notifications", "அறிவிப்புகளைப் பெற") + "</button>" :
        '<button class="scm-btn ' + (notifOn ? 'scm-btn-primary' : 'scm-btn-ghost') + '" onclick="scmToggleNotif(\'' + scmEscapeHtml(scheme.id) + '\')">' +
        (notifOn ? "🔔 " + scmT("Notifications On", "அறிவிப்பு இயக்கத்தில்") : "🔕 " + scmT("Notifications Off", "அறிவிப்பு முடக்கத்தில்")) + "</button>") +
        "</div>";
    overlay.style.display = "flex";
}

function scmCloseModal() {
    var overlay = document.getElementById("scm-modal");
    if (overlay) overlay.style.display = "none";
}

/* Log Viewed */
function scmLogViewed(schemeId) {
    fetch("/api/schemes/viewed", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ scheme_id: schemeId })
    }).then(function () {}).catch(function () {});
}

/* Save/Unsave */
function scmSaveScheme(schemeId) {
    fetch("/api/schemes/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ scheme_id: schemeId })
    })
    .then(function (r) { return r.json(); })
    .then(function (res) {
        if (res.success) {
            scmToast(res.message, "success");
            scmRefreshSaved();
        } else {
            scmToast(res.error || "Error", "error");
        }
    })
    .catch(function () { scmToast("Network error", "error"); });
}

function scmUnsaveScheme(schemeId) {
    var item = null;
    for (var i = 0; i < scmState.savedSchemes.length; i++) {
        if (scmState.savedSchemes[i].scheme_id === schemeId) { item = scmState.savedSchemes[i]; break; }
    }
    if (!item) return;
    fetch("/api/schemes/saved/" + encodeURIComponent(item.id), { method: "DELETE" })
        .then(function (r) { return r.json(); })
        .then(function (res) {
            if (res.success) {
                scmToast(res.message, "success");
                scmRefreshSaved();
            } else {
                scmToast(res.error || "Error", "error");
            }
        })
        .catch(function () { scmToast("Network error", "error"); });
}

function scmRefreshSaved() {
    fetch("/api/schemes/saved")
        .then(function (r) { return r.json(); })
        .then(function (res) {
            if (res.success) {
                scmState.savedSchemes = res.saved || [];
                scmRenderStrip();
                scmSearch();
            }
        })
        .catch(function () {});
}

/* Notifications */
function scmToggleNotif(schemeId) {
    var current = scmState.notificationStatus[schemeId];
    var newVal = current === undefined || current === null ? true : !current;
    fetch("/api/schemes/notifications/toggle", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ scheme_id: schemeId, enabled: newVal })
    })
    .then(function (r) { return r.json(); })
    .then(function (res) {
        if (res.success) {
            scmState.notificationStatus[schemeId] = res.enabled;
            scmToast(res.message, "success");
            scmSearch();
        } else {
            scmToast(res.error || "Error", "error");
        }
    })
    .catch(function () { scmToast("Network error", "error"); });
}

/* AI Recommendation */
function scmToggleAIForm() {
    var form = document.getElementById("scm-ai-form");
    if (form) form.style.display = form.style.display === "none" ? "grid" : "none";
}

function scmGetAIRecommendation() {
    var crops = document.getElementById("scm-ai-crops");
    var farmSize = document.getElementById("scm-ai-farm-size");
    var soil = document.getElementById("scm-ai-soil");
    var interests = document.getElementById("scm-ai-interests");
    var resultDiv = document.getElementById("scm-ai-result");
    var loadingDiv = document.getElementById("scm-ai-loading");
    var textDiv = document.getElementById("scm-ai-text");
    if (!resultDiv || !loadingDiv || !textDiv) return;

    loadingDiv.style.display = "flex";
    textDiv.innerHTML = "";
    resultDiv.style.display = "block";

    var aiCard = document.getElementById("scm-ai-card");
    if (aiCard) aiCard.style.display = "block";
    var form = document.getElementById("scm-ai-form");
    if (form) form.style.display = "none";

    fetch("/api/schemes/recommend", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            crops: crops ? crops.value : "",
            farm_size: farmSize ? farmSize.value : "",
            soil_type: soil ? soil.value : "",
            interests: interests ? interests.value : "",
        })
    })
    .then(function (r) { return r.json(); })
    .then(function (res) {
        loadingDiv.style.display = "none";
        if (res.success) {
            var text = scmEscapeHtml(res.recommendation);
            text = text.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
            text = text.replace(/\n/g, "<br>");
            textDiv.innerHTML = text;
        } else {
            textDiv.innerHTML = res.error || scmT("Failed to get recommendation", "பரிந்துரையைப் பெற முடியவில்லை");
        }
    })
    .catch(function () {
        loadingDiv.style.display = "none";
        textDiv.innerHTML = scmT("Network error", "நெட்வொர்க் பிழை");
    });
}

/* Eligibility Checker */
function scmPopulateEligibilitySelect() {
    var sel = document.getElementById("scm-elig-scheme");
    if (!sel || !SCM_DATA.allSchemes) return;
    sel.innerHTML = '<option value="">' + scmT("Select a scheme", "திட்டத்தைத் தேர்ந்தெடுக்கவும்") + "</option>" +
        SCM_DATA.allSchemes.map(function (s) {
            return '<option value="' + scmEscapeHtml(s.id) + '">' + scmEscapeHtml(s.name) + "</option>";
        }).join("");
}

function scmCheckEligibility() {
    var schemeEl = document.getElementById("scm-elig-scheme");
    var farmSizeEl = document.getElementById("scm-elig-farm-size");
    var cropEl = document.getElementById("scm-elig-crop");
    var districtEl = document.getElementById("scm-elig-district");
    var womenEl = document.getElementById("scm-elig-women");
    var resultDiv = document.getElementById("scm-elig-result");
    if (!schemeEl || !resultDiv) return;

    var schemeId = schemeEl.value;
    if (!schemeId) {
        resultDiv.className = "scm-elig-result not-eligible";
        resultDiv.innerHTML = scmT("Please select a scheme", "தயவுசெய்து ஒரு திட்டத்தைத் தேர்ந்தெடுக்கவும்");
        resultDiv.style.display = "block";
        return;
    }

    resultDiv.style.display = "block";
    resultDiv.innerHTML = '<div style="text-align:center;padding:10px"><div class="scm-spinner" style="margin:0 auto"></div></div>';

    fetch("/api/schemes/eligibility/check", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            scheme_id: schemeId,
            farm_size: farmSizeEl ? farmSizeEl.value : "",
            crop_type: cropEl ? cropEl.value : "",
            district: districtEl ? districtEl.value : "",
            is_women: womenEl ? womenEl.checked : false,
        })
    })
    .then(function (r) { return r.json(); })
    .then(function (res) {
        if (res.success) {
            resultDiv.className = "scm-elig-result " + (res.eligible ? "eligible" : "not-eligible");
            var html = "<strong>" + scmEscapeHtml(res.message) + "</strong>";
            if (res.reasons && res.reasons.length) {
                html += "<ul>" + res.reasons.map(function (r) { return "<li>" + scmEscapeHtml(r) + "</li>"; }).join("") + "</ul>";
            }
            resultDiv.innerHTML = html;
        } else {
            resultDiv.className = "scm-elig-result not-eligible";
            resultDiv.innerHTML = res.error || scmT("Error checking eligibility", "தகுதி சரிபார்ப்பில் பிழை");
        }
    })
    .catch(function () {
        resultDiv.className = "scm-elig-result not-eligible";
        resultDiv.innerHTML = scmT("Network error", "நெட்வொர்க் பிழை");
    });
}

/* FAQs */
function scmRenderFaqs() {
    var container = document.getElementById("scm-faq-list");
    if (!container) return;
    var faqs = SCM_DATA.faqs || [];
    if (!faqs.length) {
        container.innerHTML = '<div class="scm-scheme-empty">' + scmT("No FAQs available", "கேள்விகள் எதுவும் இல்லை") + "</div>";
        return;
    }
    container.innerHTML = faqs.map(function (f, i) {
        return '<div class="scm-faq-item">' +
            '<div class="scm-faq-q" onclick="scmToggleFaq(this)">' +
            '<span>' + scmEscapeHtml(scmGetLang() === "ta" ? f.q_ta : f.q) + "</span>" +
            '<span class="scm-faq-arrow">▼</span></div>' +
            '<div class="scm-faq-a">' + scmEscapeHtml(scmGetLang() === "ta" ? f.a_ta : f.a) + "</div>" +
            "</div>";
    }).join("");
}

function scmToggleFaq(el) {
    var answer = el.nextElementSibling;
    if (!answer) return;
    var isOpen = answer.classList.contains("open");
    document.querySelectorAll(".scm-faq-a.open").forEach(function (a) { a.classList.remove("open"); });
    document.querySelectorAll(".scm-faq-q.open").forEach(function (q) { q.classList.remove("open"); });
    if (!isOpen) {
        answer.classList.add("open");
        el.classList.add("open");
    }
}

/* Boot */
document.addEventListener("DOMContentLoaded", scmBoot);
