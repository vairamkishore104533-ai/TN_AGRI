const TRANSLATIONS = {};

function showToast(message, type = "success") {
    const container =
        document.querySelector(".toast-container") ||
        (() => {
            const c = document.createElement("div");
            c.className = "toast-container";
            document.body.appendChild(c);
            return c;
        })();

    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    toast.innerHTML = message;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transform = "translateX(100%)";
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function setLanguage(lang) {
    var isDashboard = !!document.querySelector('.dashboard-wrapper');
    fetch("/set-language", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ lang }),
    })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            if (data.success) {
                if (isDashboard) {
                    document.documentElement.setAttribute('data-lang', lang);
                    document.documentElement.lang = lang;
                    var btn = document.querySelector('.lang-toggle span');
                    if (btn) btn.textContent = lang === 'ta' ? 'English' : 'தமிழ்';
                    var toggleBtn = document.querySelector('.lang-toggle');
                    if (toggleBtn) toggleBtn.setAttribute('onclick', "setLanguage('" + (lang === 'ta' ? 'en' : 'ta') + "')");
                    updateDistrictSearchPlaceholder(lang);
                } else {
                    location.reload();
                }
            }
        });
}

function updateDistrictSearchPlaceholder(lang) {
    var input = document.getElementById('districtSearch');
    if (!input) return;
    input.placeholder = lang === 'ta' ? 'மாவட்டத்தைத் தேடுக...' : 'Search district...';
}

function toggleTheme() {
    const html = document.documentElement;
    const current = html.getAttribute("data-theme");
    const next = current === "dark" ? "light" : "dark";
    html.setAttribute("data-theme", next);
    localStorage.setItem("theme", next);
}

function initTheme() {
    const saved = localStorage.getItem("theme") || "light";
    document.documentElement.setAttribute("data-theme", saved);
}

function toggleMobileNav() {
    document.querySelector(".nav-links")?.classList.toggle("open");
    document.querySelector(".tierris-nav-links")?.classList.toggle("open");
}

function toggleSidebar() {
    document.querySelector(".sidebar")?.classList.toggle("open");
}

function initCounters() {
    document.querySelectorAll(".count-up").forEach((el) => {
        const target = parseInt(el.dataset.count) || 0;
        const duration = 2000;
        const step = Math.max(1, Math.floor(target / 60));
        let current = 0;
        const increment = () => {
            current += step;
            if (current >= target) {
                el.textContent = target.toLocaleString() + "+";
                return;
            }
            el.textContent = current.toLocaleString() + "+";
            requestAnimationFrame(increment);
        };
        increment();
    });
}

function initReveal() {
    const observer = new IntersectionObserver(
        (entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    entry.target.classList.add("visible");
                }
            });
        },
        { threshold: 0.1 }
    );

    document.querySelectorAll(".reveal, .fade-in").forEach((el) => observer.observe(el));
}

function initFAQ() {
    document.querySelectorAll(".faq-question").forEach((q) => {
        q.addEventListener("click", () => {
            const item = q.closest(".faq-item");
            item.classList.toggle("active");
        });
    });
}

function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
        anchor.addEventListener("click", function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute("href"));
            if (target) {
                target.scrollIntoView({ behavior: "smooth", block: "start" });
            }
        });
    });
}

function handleFormSubmit(formId, endpoint, onSuccess) {
    const form = document.getElementById(formId);
    if (!form) return;

    form.addEventListener("submit", function (e) {
        e.preventDefault();
        const formData = new FormData(this);
        const data = Object.fromEntries(formData);
        const submitBtn = this.querySelector('[type="submit"]');
        submitBtn.disabled = true;
        submitBtn.classList.add("btn-loading");

        fetch(endpoint, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
        })
            .then((r) => r.json())
            .then((res) => {
                submitBtn.disabled = false;
                submitBtn.classList.remove("btn-loading");
                if (res.success) {
                    if (onSuccess) onSuccess(res);
                    else if (res.redirect) window.location.href = res.redirect;
                } else {
                    showToast(res.message || "Error occurred", "error");
                }
            })
            .catch(() => {
                submitBtn.disabled = false;
                submitBtn.classList.remove("btn-loading");
                showToast("An error occurred. Please try again.", "error");
            });
    });
}

document.addEventListener("DOMContentLoaded", function () {
    initTheme();
    if (document.querySelector(".count-up")) initCounters();
    if (document.querySelector(".reveal")) initReveal();
    if (document.querySelector(".faq-item")) initFAQ();
    initSmoothScroll();
});
