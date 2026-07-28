var notifLang = document.documentElement.lang || "en";
var notifFilterCat = "";
var notifAutoTimer = null;

function notifT(en, ta) { return notifLang === "ta" ? ta : en; }

function notifToast(msg, type) {
    var t = document.getElementById("notif-toast");
    if (!t) return;
    t.textContent = msg; t.className = "notif-toast " + type;
    t.classList.add("show");
    clearTimeout(t._hide);
    t._hide = setTimeout(function () { t.classList.remove("show"); }, 3000);
}

function notifSetLanguage() {
    fetch("/set-language/" + (notifLang === "en" ? "ta" : "en"), { method: "POST" })
        .then(function () { location.reload(); });
}

/* Boot */
document.addEventListener("DOMContentLoaded", function () {
    notifGenerate();
    notifAutoTimer = setInterval(notifLoadList, 120000);
});

/* Generate notifications from user data */
function notifGenerate() {
    fetch("/api/notifications/generate", { method: "POST" })
        .then(function (r) { return r.json(); })
        .then(function (res) {
            notifLoadList();
        })
        .catch(function () {});
}

/* Load notification list */
function notifLoadList() {
    var p = new URLSearchParams();
    if (notifFilterCat) p.set("category", notifFilterCat);
    p.set("all", "1");
    fetch("/api/notifications?" + p.toString())
        .then(function (r) { return r.json(); })
        .then(function (res) {
            if (!res.success) return;
            notifRenderList(res.notifications);
            document.getElementById("notif-total-count").textContent = res.total || 0;
            document.getElementById("notif-unread-count").textContent = res.unread_count || 0;
        })
        .catch(function () {});
}

/* Filter by category */
function notifFilter(cat) {
    notifFilterCat = cat;
    var tabs = document.querySelectorAll(".notif-cat-tab");
    tabs.forEach(function (t) { t.classList.toggle("active", t.dataset.cat === cat); });
    notifLoadList();
}

/* Render notification cards */
function notifRenderList(notifications) {
    var list = document.getElementById("notif-list");
    if (!list) return;
    if (!notifications || notifications.length === 0) {
        list.innerHTML =
            '<div class="notif-empty">' +
            '<div class="notif-empty-icon">🔔</div>' +
            '<h3>' + notifT("You're all caught up!", "நீங்கள் அனைத்தையும் பார்த்துவிட்டீர்கள்!") + "</h3>" +
            '<p>' + notifT("New farming notifications will appear here.", "புதிய விவசாய அறிவிப்புகள் இங்கே தோன்றும்.") + "</p>" +
            '<a href="/dashboard" class="notif-btn notif-btn-primary">📊 ' + notifT("Go to Dashboard", "டாஷ்போர்டுக்கு செல்ல") + "</a>" +
            "</div>";
        return;
    }
    list.innerHTML = notifications.map(function (n) {
        var icons = {
            scheme: "🏛️", scheme_update: "🔄", price_up: "📈", price_down: "📉",
            irrigation: "💧", fertilizer: "🧪", info: "ℹ️",
        };
        var icon = icons[n.type] || "ℹ️";
        var catBadge = notifCatBadge(n.category);
        var priBadge = notifPriorityBadge(n.priority);
        var timeStr = notifTimeAgo(n.created_at);
        var unreadCls = n.is_read ? "" : " unread";
        var readBtn = n.is_read ? "" :
            '<button class="notif-action-btn" onclick="notifMarkRead(\'' + n.id + '\')">✅ ' + notifT("Read", "படித்தது") + "</button>";
        return '<div class="notif-card' + unreadCls + '">' +
            '<div class="notif-card-icon">' + icon + "</div>" +
            '<div class="notif-card-body">' +
            '<div class="notif-card-title">' + notifEscape(n.title) + "</div>" +
            '<div class="notif-card-msg">' + notifEscape(n.message) + "</div>" +
            '<div class="notif-card-footer">' +
            catBadge + priBadge +
            '<span class="notif-time">' + timeStr + "</span>" +
            "</div></div>" +
            '<div class="notif-card-actions">' +
            readBtn +
            '<button class="notif-action-btn danger" onclick="notifClear(\'' + n.id + '\')">✕</button>' +
            "</div></div>";
    }).join("");
}

function notifCatBadge(cat) {
    var labels = {
        scheme: notifT("Scheme", "திட்டம்"),
        market: notifT("Market", "சந்தை"),
        irrigation: notifT("Irrigation", "நீர்ப்பாசனம்"),
        fertilizer: notifT("Fertilizer", "உரம்"),
    };
    var cls = "notif-badge-" + (cat || "info");
    return '<span class="notif-badge ' + cls + '">' + (labels[cat] || notifT("Info", "தகவல்")) + "</span>";
}

function notifPriorityBadge(pri) {
    var labels = {
        high: notifT("High", "அதிக"),
        medium: notifT("Medium", "நடுத்தர"),
        low: notifT("Low", "குறைந்த"),
    };
    return '<span class="notif-priority notif-priority-' + pri + '">' + (labels[pri] || pri) + "</span>";
}

function notifTimeAgo(dateStr) {
    if (!dateStr) return "";
    var now = new Date();
    var d = new Date(dateStr);
    if (isNaN(d.getTime())) return dateStr;
    var diff = Math.floor((now - d) / 1000);
    if (diff < 60) return notifT("Just now", "இப்போது");
    if (diff < 3600) return Math.floor(diff / 60) + "m";
    if (diff < 86400) return Math.floor(diff / 3600) + "h";
    if (diff < 172800) return notifT("Yesterday", "நேற்று");
    if (diff < 604800) return Math.floor(diff / 86400) + "d";
    return d.toLocaleDateString();
}

function notifEscape(s) {
    if (typeof s !== "string") return s || "";
    var d = document.createElement("div");
    d.textContent = s;
    return d.innerHTML;
}

/* Mark single as read */
function notifMarkRead(id) {
    fetch("/api/notifications/read", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ notification_id: id }),
    })
        .then(function (r) { return r.json(); })
        .then(function (res) {
            if (res.success) notifLoadList();
        });
}

/* Mark all read */
function notifMarkAllRead() {
    fetch("/api/notifications/read", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
    })
        .then(function (r) { return r.json(); })
        .then(function (res) {
            if (res.success) {
                notifLoadList();
                notifToast(notifT("All marked as read", "அனைத்தும் படித்ததாக குறிக்கப்பட்டது"), "success");
            }
        });
}

/* Clear single */
function notifClear(id) {
    fetch("/api/notifications/clear", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ notification_id: id }),
    })
        .then(function (r) { return r.json(); })
        .then(function (res) {
            if (res.success) notifLoadList();
        });
}

/* Clear all */
function notifClearAll() {
    if (!confirm(notifT("Clear all notifications?", "அனைத்து அறிவிப்புகளையும் அழிக்கவா?"))) return;
    fetch("/api/notifications/clear", { method: "POST" })
        .then(function (r) { return r.json(); })
        .then(function (res) {
            if (res.success) {
                notifLoadList();
                notifToast(notifT("All notifications cleared", "அனைத்து அறிவிப்புகளும் அழிக்கப்பட்டன"), "success");
            }
        });
}
