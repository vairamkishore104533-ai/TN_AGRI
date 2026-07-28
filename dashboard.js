function loadPage(url, title) {
    const content = document.getElementById("main-content");
    if (!content) return;
    fetch(url)
        .then((r) => r.text())
        .then((html) => {
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, "text/html");
            const newContent = doc.getElementById("main-content");
            if (newContent) {
                content.innerHTML = newContent.innerHTML;
                document.title = title;
                window.history.pushState({}, title, url);
                reinitPage();
            }
        });
}

function reinitPage() {
    if (typeof initCharts === "function") initCharts();
    if (typeof initWeather === "function") initWeather();
    if (typeof initChatbot === "function") initChatbot();
}

function confirmAndDelete(url, onSuccess) {
    const lang = document.documentElement.lang || "en";
    const msg =
        lang === "ta"
            ? "இதை நிச்சயமாக அழிக்க விரும்புகிறீர்களா?"
            : "Are you sure you want to delete this?";
    if (!confirm(msg)) return;

    fetch(url, { method: "DELETE" })
        .then((r) => r.json())
        .then((res) => {
            if (res.success) {
                showToast(res.message, "success");
                if (onSuccess) onSuccess();
            } else {
                showToast(res.message, "error");
            }
        });
}

function loadTableData(url, tableBodyId, renderFn) {
    const tbody = document.getElementById(tableBodyId);
    if (!tbody) return;
    tbody.innerHTML =
        '<tr><td colspan="10" class="text-center"><div class="loading-spinner" style="margin:20px auto"></div></td></tr>';

    fetch(url)
        .then((r) => r.json())
        .then((res) => {
            if (res.success && res.data) {
                tbody.innerHTML = res.data.length
                    ? res.data.map(renderFn).join("")
                    : '<tr><td colspan="10" class="empty-state"><p>No data available</p></td></tr>';
            }
        });
}

function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.add("active");
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.remove("active");
}

function populateSelect(selectId, options, valueKey, labelKey) {
    const select = document.getElementById(selectId);
    if (!select) return;
    select.innerHTML = options
        .map(
            (opt) =>
                `<option value="${opt[valueKey] || opt}">${opt[labelKey] || opt}</option>`
        )
        .join("");
}

document.addEventListener("click", function (e) {
    if (e.target.classList.contains("modal-overlay")) {
        e.target.classList.remove("active");
    }
});

document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") {
        document.querySelectorAll(".modal-overlay.active").forEach((m) => m.classList.remove("active"));
    }
});
