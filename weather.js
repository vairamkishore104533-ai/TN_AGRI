var wthState = {
    district: null, districtName: null,
    town: null,
    current: null,
    currentId: null,
    autoRefreshInterval: null,
    isFavorite: false,
};

var wthLoadingMessages = [
    t("Connecting to weather service...", "வானிலை சேவையுடன் இணைக்கிறது..."),
    t("Fetching live weather...", "நேரடி வானிலையை பெறுகிறது..."),
    t("Preparing forecast...", "முன்னறிவிப்பை தயாரிக்கிறது..."),
    t("Generating farming insights...", "விவசாய நுண்ணறிவுகளை உருவாக்குகிறது..."),
];

function getLang() { return (window.WTH_DATA && window.WTH_DATA.lang) || "en"; }
function t(en, ta) { return getLang() === "ta" ? ta : en; }
function escapeHtml(s) { var d = document.createElement("div"); d.textContent = s; return d.innerHTML; }

function wthRenderAdvice(text) {
    var s = escapeHtml(text);
    s = s.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
    s = s.replace(/\n/g, "<br>");
    return s;
}

function wthBoot() {
    if (typeof WTH_DATA === "undefined") { setTimeout(wthBoot, 100); return; }
    var input = document.getElementById("wth-district-input");
    if (!input) return;
    buildWthSearchSelect({
        input: input,
        items: WTH_DATA.districts,
        labelKey: getLang() === "ta" ? "ta" : "en",
        name: "wth-district",
        onSelect: function (item) {
            wthState.district = item.en;
            wthState.districtName = item.ta && getLang() === "ta" ? item.ta : item.en;
        }
    });
    renderFavorites();
    var hs = document.getElementById("wth-history-search");
    if (hs) hs.addEventListener("input", function () { wthLoadHistory(); });
    wthLoadHistory();
}

/* ── Searchable Dropdown ── */

function buildWthSearchSelect(config) {
    var input = config.input, items = config.items, labelKey = config.labelKey || "en", onSelect = config.onSelect, portalName = config.name || "wth-dd";
    var dropdown = document.createElement("div");
    dropdown.className = "wth-search-dropdown";
    dropdown.setAttribute("data-portal", portalName);
    document.body.appendChild(dropdown);
    var outsideHandler;

    function renderOptions(query) {
        var q = (query || "").toLowerCase().trim();
        var html = "";
        for (var i = 0; i < items.length; i++) {
            var item = items[i], label = item[labelKey] || item.en || "";
            if (q && label.toLowerCase().indexOf(q) < 0) continue;
            var display = item.ta && getLang() === "ta" ? item.ta : (item.en || label);
            html += '<div class="wth-search-option" data-index="' + i + '">' + escapeHtml(display) + "</div>";
        }
        if (!html) html = '<div class="wth-search-option" style="color:var(--wth-text-secondary);cursor:default">' + t("No results found", "முடிவுகள் எதுவும் இல்லை") + "</div>";
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
    outsideHandler = function (e) {
        if (dropdown.classList.contains("open") && !input.contains(e.target) && !dropdown.contains(e.target)) close();
    };
    document.addEventListener("click", outsideHandler);
    document.addEventListener("touchstart", outsideHandler, { passive: true });
    dropdown.addEventListener("click", function (e) {
        var opt = e.target.closest(".wth-search-option");
        if (!opt || !opt.dataset.index) return;
        var idx = parseInt(opt.dataset.index), item = items[idx];
        var display = item.ta && getLang() === "ta" ? item.ta : (item.en || "");
        input.value = display;
        close();
        if (onSelect) onSelect(item, idx);
    });
}

/* ── Fetch Weather ── */

function wthFetchWeather() {
    var district = document.getElementById("wth-district-input").value.trim();
    var town = document.getElementById("wth-town-input").value.trim();

    if (!wthState.district || !district) {
        wthToast(t("Please select a district.", "தயவுசெய்து ஒரு மாவட்டத்தைத் தேர்ந்தெடுக்கவும்."), "error");
        return;
    }
    if (!town) {
        wthToast(t("Please enter a town or village name.", "தயவுசெய்து ஒரு நகரம் அல்லது கிராமத்தின் பெயரை உள்ளிடவும்."), "error");
        return;
    }

    wthState.town = town;

    var overlay = document.getElementById("wth-loading-overlay");
    var loadingText = document.getElementById("wth-loading-text");
    overlay.style.display = "flex";
    var msgIdx = 0;
    var msgInterval = setInterval(function () {
        msgIdx = (msgIdx + 1) % wthLoadingMessages.length;
        loadingText.textContent = wthLoadingMessages[msgIdx];
    }, 2500);

    fetch("/api/weather/fetch", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ district: wthState.district, town: town })
    })
    .then(function (r) { return r.json(); })
    .then(function (res) {
        clearInterval(msgInterval);
        overlay.style.display = "none";
        if (res.success) {
            wthState.current = res.weather;
            wthDisplayCurrent(res);
            wthLoadHistory();
        } else {
            wthToast(res.error || t("Failed to fetch weather.", "வானிலையை பெற முடியவில்லை."), "error");
        }
    })
    .catch(function () {
        clearInterval(msgInterval);
        overlay.style.display = "none";
        wthToast(t("Network error. Please try again.", "நெட்வொர்க் பிழை. மீண்டும் முயற்சிக்கவும்."), "error");
    });
}

/* ── Display Current Weather ── */

function wthDisplayCurrent(res) {
    var w = res.weather || {};
    var section = document.getElementById("wth-current-section");
    section.style.display = "block";
    section.classList.add("wth-fade");

    var iconMap = {
        "sunny": "☀️", "clear": "☀️", "cloudy": "☁️", "rain": "🌧️",
        "thunderstorm": "⛈️", "snow": "🌨️", "mist": "🌫️", "fog": "🌫️",
        "drizzle": "🌦️", "haze": "🌫️",
    };

    var iconCode = w.icon || "01d";
    var isNight = iconCode.indexOf("n") >= 0;
    var icon = isNight ? "🌙" : (iconMap[w.condition] || "🌤️");

    document.getElementById("wth-location-badge").innerHTML = "📍 " + escapeHtml((wthState.districtName || wthState.district) + ", " + wthState.town);
    document.getElementById("wth-temp-value").textContent = w.temp != null ? w.temp : "--";
    document.getElementById("wth-feels-like").textContent = t("Feels like", "உணரப்படும் வெப்பநிலை") + ": " + (w.feels_like != null ? w.feels_like + "°C" : "--");
    document.getElementById("wth-weather-icon").textContent = icon;
    document.getElementById("wth-condition-text").textContent = w.condition_raw || w.condition || "--";

    var dt = w.dt ? new Date(w.dt * 1000) : new Date();
    document.getElementById("wth-last-updated").textContent = t("Last updated", "கடைசியாக புதுப்பிக்கப்பட்டது") + ": " + dt.toLocaleTimeString();

    document.getElementById("wth-humidity").textContent = (w.humidity != null ? w.humidity : "--") + "%";
    document.getElementById("wth-wind").textContent = (w.wind_speed != null ? w.wind_speed : "--") + " km/h";
    document.getElementById("wth-rain").textContent = (w.clouds != null ? w.clouds : "--") + "%";
    document.getElementById("wth-pressure").textContent = (w.pressure != null ? w.pressure : "--") + " hPa";
    document.getElementById("wth-visibility").textContent = (w.visibility != null ? (w.visibility / 1000).toFixed(1) : "--") + " km";

    /* UV */
    var uvEl = document.getElementById("wth-uv");
    var uvVal = res.uv;
    if (uvVal != null) {
        var uvLabel = "Low";
        var uvColor = "#2e7d32";
        if (uvVal >= 8) { uvLabel = "Very High"; uvColor = "#c62828"; }
        else if (uvVal >= 6) { uvLabel = "High"; uvColor = "#e65100"; }
        else if (uvVal >= 3) { uvLabel = "Moderate"; uvColor = "#f9a825"; }
        uvEl.innerHTML = uvVal + ' <span class="wth-uv-badge" style="padding:2px 8px;border-radius:10px;font-size:10px;font-weight:600;background:' + uvColor + ';color:#fff">' + uvLabel + '</span>';
    } else {
        uvEl.textContent = "--";
    }

    /* Sunrise/Sunset */
    var sunriseEl = document.getElementById("wth-sunrise");
    var sunsetEl = document.getElementById("wth-sunset");
    if (w.sunrise) { var sr = new Date(w.sunrise * 1000); sunriseEl.textContent = sr.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }); }
    if (w.sunset) { var ss = new Date(w.sunset * 1000); sunsetEl.textContent = ss.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }); }

    /* Check favorite status */
    wthCheckFavorite();

    /* Alerts */
    wthRenderAlerts(w);

    /* Advice */
    var adviceCard = document.getElementById("wth-advice-card");
    var adviceText = document.getElementById("wth-advice-text");
    if (res.advice) {
        adviceCard.style.display = "block";
        adviceText.innerHTML = wthRenderAdvice(res.advice);
    } else {
        adviceCard.style.display = "none";
    }

    /* Hourly */
    wthRenderHourly(res.hourly);

    /* Daily */
    wthRenderDaily(res.daily);

    section.scrollIntoView({ behavior: "smooth", block: "start" });
}

/* ── Alerts ── */

function wthRenderAlerts(w) {
    var container = document.getElementById("wth-alerts");
    var alerts = [];

    if (w.condition === "thunderstorm" || w.condition === "rain") {
        var rainIntensity = w.rain_1h || w.rain_3h || 0;
        if (rainIntensity > 5 || w.condition === "thunderstorm") {
            alerts.push({ type: "red", icon: "⛈️", msg: getLang() === "ta" ? "கனமழை / இடியுடன் கூடிய மழை எச்சரிக்கை!" : "Heavy Rain / Thunderstorm Warning!" });
        }
    }
    if (w.temp >= 40) {
        alerts.push({ type: "orange", icon: "🔥", msg: getLang() === "ta" ? "அதிக வெப்ப எச்சரிக்கை! பயிர்களை பாதுகாக்கவும்." : "Heat Wave Warning! Protect your crops." });
    }
    if (w.temp <= 15) {
        alerts.push({ type: "blue", icon: "🥶", msg: getLang() === "ta" ? "குளிர் அலை எச்சரிக்கை!" : "Cold Wave Alert!" });
    }
    if (w.wind_speed >= 30) {
        alerts.push({ type: "purple", icon: "💨", msg: getLang() === "ta" ? "பலத்த காற்று எச்சரிக்கை! தெளிப்பு மற்றும் உரமிடலை தவிர்க்கவும்." : "Strong Wind Alert! Avoid spraying and fertilizer application." });
    } else if (w.wind_speed >= 20) {
        alerts.push({ type: "yellow", icon: "💨", msg: getLang() === "ta" ? "காற்று எச்சரிக்கை: தெளிப்பதற்கு முன் கவனமாக இருங்கள்." : "Wind Alert: Be cautious before spraying." });
    }
    if (w.visibility && w.visibility < 1000) {
        alerts.push({ type: "blue", icon: "🌫️", msg: getLang() === "ta" ? "குறைந்த தெரிவுத்திறன்! வயலில் பணியாற்றும்போது கவனமாக இருங்கள்." : "Low Visibility! Be careful working in fields." });
    }

    if (alerts.length === 0) {
        container.style.display = "none";
        return;
    }
    container.style.display = "flex";
    var map = { red: "wth-alert-red", orange: "wth-alert-orange", yellow: "wth-alert-yellow", blue: "wth-alert-blue", purple: "wth-alert-purple" };
    container.innerHTML = alerts.map(function (a) {
        return '<div class="wth-alert-card ' + (map[a.type] || "wth-alert-yellow") + '"><span>' + a.icon + '</span><span>' + a.msg + '</span></div>';
    }).join("");
}

/* ── Hourly ── */

function wthRenderHourly(data) {
    var container = document.getElementById("wth-hourly-scroll");
    if (!data || !data.length) { container.innerHTML = '<div style="color:var(--wth-text-secondary);padding:16px">' + t("Hourly data not available.", "மணிநேர தரவு கிடைக்கவில்லை.") + '</div>'; return; }
    var iconMap = { "clear": "☀️", "clouds": "☁️", "rain": "🌧️", "thunderstorm": "⛈️", "drizzle": "🌦️", "mist": "🌫️", "fog": "🌫️", "snow": "🌨️", "haze": "🌫️" };
    container.innerHTML = data.map(function (h) {
        var ic = iconMap[h.condition] || "🌤️";
        return '<div class="wth-hourly-item"><div class="wth-hourly-time">' + escapeHtml(h.time) + '</div><div class="wth-hourly-icon">' + ic + '</div><div class="wth-hourly-temp">' + h.temp + '°</div><div class="wth-hourly-rain">🌧️ ' + h.rain + '%</div></div>';
    }).join("");
}

/* ── Daily ── */

function wthRenderDaily(data) {
    var container = document.getElementById("wth-daily-grid");
    if (!data || !data.length) { container.innerHTML = '<div style="color:var(--wth-text-secondary);padding:16px">' + t("Forecast not available.", "முன்னறிவிப்பு கிடைக்கவில்லை.") + '</div>'; return; }
    var iconMap = { "clear": "☀️", "clouds": "☁️", "rain": "🌧️", "thunderstorm": "⛈️", "drizzle": "🌦️", "mist": "🌫️", "fog": "🌫️", "snow": "🌨️", "haze": "🌫️" };
    container.innerHTML = data.map(function (d) {
        var ic = iconMap[d.condition] || "🌤️";
        return '<div class="wth-daily-card"><div class="wth-daily-day">' + escapeHtml(d.day_name) + '</div><div class="wth-daily-date">' + escapeHtml(d.date) + '</div><div class="wth-daily-icon">' + ic + '</div><div class="wth-daily-high">' + d.temp_max + '°</div><div class="wth-daily-low">' + d.temp_min + '°</div><div class="wth-daily-rain">🌧️ ' + d.rain + '%</div></div>';
    }).join("");
}

/* ── Save ── */

function wthSaveWeather() {
    if (!wthState.current) { wthToast(t("No weather data to save.", "சேமிக்க வானிலை தரவு இல்லை."), "error"); return; }
    wthToast(t("Saving...", "சேமிக்கிறது..."), "success");
    fetch("/api/weather/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            district: wthState.district,
            town: wthState.town,
            weather_data: wthState.current,
        })
    })
    .then(function (r) { return r.json(); })
    .then(function (res) {
        if (res.success) {
            wthToast(t("Weather data saved!", "வானிலை தரவு சேமிக்கப்பட்டது!"), "success");
            wthLoadHistory();
        } else {
            wthToast(res.error || t("Save failed.", "சேமிப்பு தோல்வி."), "error");
        }
    })
    .catch(function () { wthToast(t("Save failed.", "சேமிப்பு தோல்வி."), "error"); });
}

/* ── Favorites ── */

function wthToggleFavorite() {
    if (!wthState.district || !wthState.town) { wthToast(t("Search weather first.", "முதலில் வானிலை தேடவும்."), "error"); return; }
    var url = wthState.isFavorite ? "/api/weather/favorites/remove" : "/api/weather/favorites/add";
    var method = wthState.isFavorite ? "DELETE" : "POST";
    var body = wthState.isFavorite ? null : JSON.stringify({ district: wthState.district, town: wthState.town });

    if (wthState.isFavorite && wthState.favId) {
        fetch("/api/weather/favorites/" + wthState.favId, { method: "DELETE" })
        .then(function (r) { return r.json(); })
        .then(function (res) {
            if (res.success) {
                wthState.isFavorite = false;
                wthState.favId = null;
                wthToast(t("Removed from favorites!", "விருப்பங்களில் இருந்து நீக்கப்பட்டது!"), "success");
                renderFavorites();
            }
        });
        return;
    }

    fetch("/api/weather/favorites/add", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ district: wthState.district, town: wthState.town })
    })
    .then(function (r) { return r.json(); })
    .then(function (res) {
        if (res.success) {
            wthState.isFavorite = true;
            wthState.favId = res.id;
            wthToast(t("Added to favorites!", "விருப்பங்களில் சேர்க்கப்பட்டது!"), "success");
            renderFavorites();
        } else {
            wthToast(res.error || t("Failed.", "தோல்வி."), "error");
        }
    });
}

function wthCheckFavorite() {
    var favs = WTH_DATA.favorites || [];
    wthState.isFavorite = false;
    wthState.favId = null;
    for (var i = 0; i < favs.length; i++) {
        if (favs[i].district === wthState.district && favs[i].town === wthState.town) {
            wthState.isFavorite = true;
            wthState.favId = favs[i].id;
            break;
        }
    }
}

function renderFavorites() {
    var bar = document.getElementById("wth-favorites-bar");
    var items = document.getElementById("wth-fav-items");
    var favs = WTH_DATA.favorites || [];
    if (!favs.length) { bar.style.display = "none"; return; }
    bar.style.display = "flex";
    items.innerHTML = favs.map(function (f) {
        return '<span class="wth-fav-chip" onclick="wthLoadFavorite(\'' + escapeHtml(f.district) + '\',\'' + escapeHtml(f.town) + '\')">' + escapeHtml(f.town + ", " + f.district) + '</span>';
    }).join("");
}

function wthLoadFavorite(district, town) {
    var dInput = document.getElementById("wth-district-input");
    var tInput = document.getElementById("wth-town-input");
    dInput.value = district;
    tInput.value = town;
    wthState.district = district;
    wthState.districtName = district;
    wthState.town = town;
    wthFetchWeather();
}

/* ── Auto Refresh ── */

function wthToggleAutoRefresh() {
    var cb = document.getElementById("wth-auto-refresh");
    if (cb.checked) {
        wthState.autoRefreshInterval = setInterval(function () {
            if (wthState.district && wthState.town) {
                wthFetchWeather();
            }
        }, 900000);
    } else {
        if (wthState.autoRefreshInterval) {
            clearInterval(wthState.autoRefreshInterval);
            wthState.autoRefreshInterval = null;
        }
    }
}

/* ── History ── */

function wthLoadHistory() {
    var list = document.getElementById("wth-history-list");
    var search = document.getElementById("wth-history-search");
    var q = search ? search.value : "";
    var url = "/api/weather/history" + (q ? "?search=" + encodeURIComponent(q) : "");

    fetch(url)
    .then(function (r) { return r.json(); })
    .then(function (res) {
        if (!res.success) return;
        var items = res.history || [];
        if (!items.length) {
            list.innerHTML = '<div style="text-align:center;padding:20px;color:var(--wth-text-secondary)">' + t("No weather records found.", "வானிலை பதிவுகள் எதுவும் இல்லை.") + '</div>';
            return;
        }
        list.innerHTML = items.map(function (h) {
            var date = h.created_at ? h.created_at.slice(0, 10) : "";
            return '<div class="wth-history-item" onclick="wthViewHistory(\'' + h.id + '\')">' +
                '<div class="wth-history-info"><span class="wth-history-location">🌤️ ' + escapeHtml(h.district || "") + ' → ' + escapeHtml(h.town || "") + '</span>' +
                '<span class="wth-history-details">' + date + '</span></div>' +
                '<div class="wth-history-actions" onclick="event.stopPropagation()">' +
                '<button class="wth-btn wth-btn-ghost wth-btn-sm" onclick="wthViewHistory(\'' + h.id + '\')">👁️ ' + t("View", "பார்க்க") + '</button>' +
                '<button class="wth-btn wth-btn-ghost wth-btn-sm" onclick="wthDeleteHistory(\'' + h.id + '\')">🗑️ ' + t("Delete", "நீக்கு") + '</button>' +
                '</div></div>';
        }).join("");
    });
}

function wthDeleteHistory(id) {
    if (!confirm(t("Delete this record?", "இந்த பதிவை நீக்கவா?"))) return;
    fetch("/api/weather/history/" + id, { method: "DELETE" })
    .then(function (r) { return r.json(); })
    .then(function (res) {
        if (res.success) { wthToast(t("Record deleted!", "பதிவு நீக்கப்பட்டது!"), "success"); wthLoadHistory(); }
        else { wthToast(res.error || t("Delete failed.", "நீக்கம் தோல்வி."), "error"); }
    })
    .catch(function () { wthToast(t("Delete failed.", "நீக்கம் தோல்வி."), "error"); });
}

function wthViewHistory(id) {
    fetch("/api/weather/history")
    .then(function (r) { return r.json(); })
    .then(function (res) {
        if (!res.success) return;
        var items = res.history || [], found = null;
        for (var i = 0; i < items.length; i++) { if (items[i].id === id) { found = items[i]; break; } }
        if (!found) { wthToast(t("Record not found.", "பதிவு கிடைக்கவில்லை."), "error"); return; }
        var wd = found.weather_data || {};
        document.getElementById("wth-district-input").value = found.district;
        document.getElementById("wth-town-input").value = found.town;
        wthState.district = found.district;
        wthState.districtName = found.district;
        wthState.town = found.town;
        wthState.current = wd;
        wthDisplayCurrent({ weather: wd, uv: null, hourly: [], daily: [], advice: "" });
    });
}

/* ── Toast ── */

function wthToast(msg, type) {
    var toast = document.getElementById("wth-toast");
    if (!toast) return;
    toast.textContent = msg;
    toast.className = "wth-toast wth-toast-" + (type || "success");
    toast.style.display = "block";
    setTimeout(function () { toast.style.display = "none"; }, 3000);
}

/* ── Boot ── */

document.addEventListener("DOMContentLoaded", function () {
    if (document.getElementById("wth-district-input")) {
        wthBoot();
    }
});
