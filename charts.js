let chartInstances = {};

function initCharts() {
    const charts = document.querySelectorAll("[data-chart]");
    charts.forEach((el) => {
        const type = el.dataset.chart;
        if (type === "expense-pie") renderExpensePie(el);
        if (type === "income-bar") renderIncomeBar(el);
        if (type === "monthly") renderMonthlyChart(el);
        if (type === "crop-dist") renderCropDist(el);
        if (type === "analytics") renderAnalyticsCharts();
    });
}

function renderExpensePie(container) {
    fetch("/api/expenses")
        .then((r) => r.json())
        .then((res) => {
            if (!res.success || !res.category_breakdown) return;
            const labels = res.category_breakdown.map((c) => c._id);
            const data = res.category_breakdown.map((c) => c.total);
            const colors = ["#10b981", "#3b82f6", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899"];
            renderPieChart(container, labels, data, colors);
        });
}

function renderIncomeBar(container) {
    fetch("/api/expenses/summary")
        .then((r) => r.json())
        .then((res) => {
            if (!res.success) return;
            const labels = ["Income", "Expenses"];
            const data = [res.summary.income || 0, res.summary.expense || 0];
            const colors = ["#10b981", "#ef4444"];
            renderBarChart(container, labels, data, colors);
        });
}

function renderMonthlyChart(container) {
    fetch("/api/analytics")
        .then((r) => r.json())
        .then((res) => {
            if (!res.success || !res.monthly) return;
            const months = res.monthly.map((m) => m.month);
            const income = res.monthly.map((m) => m.income);
            const expense = res.monthly.map((m) => m.expense);
            renderLineChart(container, months, [
                { label: "Income", data: income, color: "#10b981" },
                { label: "Expenses", data: expense, color: "#ef4444" },
            ]);
        });
}

function renderCropDist(container) {
    fetch("/api/analytics")
        .then((r) => r.json())
        .then((res) => {
            if (!res.success || !res.crop_distribution) return;
            const labels = Object.keys(res.crop_distribution);
            const data = Object.values(res.crop_distribution);
            const colors = ["#10b981", "#3b82f6", "#f59e0b", "#8b5cf6", "#ec4899", "#14b8a6"];
            renderPieChart(container, labels, data, colors);
        });
}

function renderPieChart(container, labels, data, colors) {
    if (!container || !labels.length) return;
    const canvas = document.createElement("canvas");
    container.innerHTML = "";
    container.appendChild(canvas);
    const ctx = canvas.getContext("2d");
    const id = "chart-" + Date.now();
    canvas.id = id;

    if (typeof Chart === "undefined") return;

    if (chartInstances[id]) chartInstances[id].destroy();

    chartInstances[id] = new Chart(ctx, {
        type: "doughnut",
        data: {
            labels,
            datasets: [{ data, backgroundColor: colors, borderWidth: 0 }],
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: "bottom",
                    labels: { padding: 16, usePointStyle: true },
                },
            },
            cutout: "60%",
        },
    });
}

function renderBarChart(container, labels, data, colors) {
    if (!container || !labels.length) return;
    const canvas = document.createElement("canvas");
    container.innerHTML = "";
    container.appendChild(canvas);
    const ctx = canvas.getContext("2d");
    const id = "chart-" + Date.now();
    canvas.id = id;

    if (typeof Chart === "undefined") return;
    if (chartInstances[id]) chartInstances[id].destroy();

    chartInstances[id] = new Chart(ctx, {
        type: "bar",
        data: {
            labels,
            datasets: [
                {
                    data,
                    backgroundColor: colors,
                    borderRadius: 8,
                    borderSkipped: false,
                },
            ],
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: false },
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: "rgba(0,0,0,0.05)" },
                },
            },
        },
    });
}

function renderLineChart(container, labels, datasets) {
    if (!container || !labels.length) return;
    const canvas = document.createElement("canvas");
    container.innerHTML = "";
    container.appendChild(canvas);
    const ctx = canvas.getContext("2d");
    const id = "chart-" + Date.now();
    canvas.id = id;

    if (typeof Chart === "undefined") return;
    if (chartInstances[id]) chartInstances[id].destroy();

    chartInstances[id] = new Chart(ctx, {
        type: "line",
        data: {
            labels,
            datasets: datasets.map((ds) => ({
                label: ds.label,
                data: ds.data,
                borderColor: ds.color,
                backgroundColor: ds.color + "20",
                fill: true,
                tension: 0.4,
                pointRadius: 4,
            })),
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: "bottom" },
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: "rgba(0,0,0,0.05)" },
                },
            },
        },
    });
}

function renderAnalyticsCharts() {
    renderMonthlyChart(document.getElementById("monthly-chart"));
    renderCropDist(document.getElementById("crop-dist-chart"));
}

document.addEventListener("DOMContentLoaded", function () {
    if (typeof Chart !== "undefined" && document.querySelector("[data-chart]")) {
        setTimeout(initCharts, 500);
    }
});
