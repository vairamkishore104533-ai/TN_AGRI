var cropsData = [];
var filteredCrops = [];
var currentPage = 1;
var pageSize = 10;
var searchTimer = null;

document.addEventListener("DOMContentLoaded", function () {
    loadCrops();
    animateCounters();
    initRecDropdown();
});

function loadCrops() {
    fetch("/api/crops")
        .then(function (r) { return r.json(); })
        .then(function (res) {
            if (res.success) {
                cropsData = res.crops;
                filteredCrops = cropsData;
                renderTable();
                updateStats();
                loadActivities();
            }
        });
}

function renderTable() {
    var sortBy = document.getElementById("sort-crops").value;
    var tbody = document.getElementById("crops-table-body");
    if (!tbody) return;

    var sorted = filteredCrops.slice();
    if (sortBy === "name") sorted.sort(function (a, b) { return a.crop_name.localeCompare(b.crop_name); });
    else if (sortBy === "land_size") sorted.sort(function (a, b) { return b.land_size - a.land_size; });
    else if (sortBy === "oldest") sorted.sort(function (a, b) { return new Date(a.created_at) - new Date(b.created_at); });
    else sorted.sort(function (a, b) { return new Date(b.created_at) - new Date(a.created_at); });

    var totalPages = Math.max(1, Math.ceil(sorted.length / pageSize));
    if (currentPage > totalPages) currentPage = totalPages;
    var start = (currentPage - 1) * pageSize;
    var page = sorted.slice(start, start + pageSize);

    if (page.length === 0) {
        tbody.innerHTML = '<tr><td colspan="10"><div class="crops-empty">🌾 No crops found matching your filters.</div></td></tr>';
        document.getElementById("crops-pagination").innerHTML = "";
        return;
    }

    var html = "";
    page.forEach(function (c) {
        var statusClass = c.status.toLowerCase().replace(/ /g, "-");
        var planted = c.planting_date ? c.planting_date.substring(0, 10) : "—";
        var harvest = c.harvest_date ? c.harvest_date.substring(0, 10) : "—";
        html += '<tr data-id="' + c.id + '">';
        html += '<td><span class="crop-name-cell">' + escapeHtml(c.crop_name) + '</span></td>';
        html += '<td>' + escapeHtml(c.village || "—") + '</td>';
        html += '<td>' + escapeHtml(c.district) + '</td>';
        html += '<td>' + c.land_size + '</td>';
        html += '<td>' + escapeHtml(c.soil_type) + '</td>';
        html += '<td>' + escapeHtml(c.season || "—") + '</td>';
        html += '<td>' + planted + '</td>';
        html += '<td>' + harvest + '</td>';
        html += '<td><span class="status-badge status-' + statusClass + '">' + escapeHtml(c.status) + '</span></td>';
        html += '<td><div class="action-btns">';
        html += '<button class="action-btn view" title="View" onclick="viewCrop(\'' + c.id + '\')">👁</button>';
        html += '<button class="action-btn edit" title="Edit" onclick="editCrop(\'' + c.id + '\')">✏️</button>';
        html += '<button class="action-btn delete" title="Delete" onclick="deleteCrop(\'' + c.id + '\')">🗑</button>';
        html += '</div></td></tr>';
    });
    tbody.innerHTML = html;

    var pagHtml = "";
    for (var i = 1; i <= totalPages; i++) {
        pagHtml += '<button class="page-btn' + (i === currentPage ? ' active' : '') + '" onclick="goPage(' + i + ')">' + i + '</button>';
    }
    document.getElementById("crops-pagination").innerHTML = pagHtml;
}

function goPage(p) {
    currentPage = p;
    renderTable();
}

function debounceSearch() {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(applyFilters, 300);
}

function applyFilters() {
    var q = document.getElementById("crop-search").value.trim().toLowerCase();
    var district = document.getElementById("filter-district").value;
    var soil = document.getElementById("filter-soil").value;
    var status = document.getElementById("filter-status").value;
    var season = document.getElementById("filter-season").value;

    filteredCrops = cropsData.filter(function (c) {
        if (q && c.crop_name.toLowerCase().indexOf(q) < 0 && c.village.toLowerCase().indexOf(q) < 0) return false;
        if (district && c.district !== district) return false;
        if (soil && c.soil_type !== soil) return false;
        if (status && c.status !== status) return false;
        if (season && c.season !== season) return false;
        return true;
    });
    currentPage = 1;
    renderTable();
}

function animateCounters() {
    var els = document.querySelectorAll(".stat-value[data-target]");
    els.forEach(function (el) {
        var target = parseFloat(el.getAttribute("data-target"));
        if (isNaN(target) || target === 0) { el.textContent = "0"; return; }
        var current = 0;
        var step = Math.max(1, Math.ceil(target / 30));
        var interval = setInterval(function () {
            current += step;
            if (current >= target) { current = target; clearInterval(interval); }
            el.textContent = Number.isInteger(target) ? Math.round(current) : current.toFixed(1);
        }, 40);
    });
}

function openAddModal() {
    document.getElementById("modal-title").textContent = "Add New Crop";
    document.getElementById("crop-id").value = "";
    document.getElementById("crop-form").reset();
    var btn = document.getElementById("form-submit-btn");
    btn.textContent = "Save Crop";
    btn.disabled = false;
    document.getElementById("crop-modal").style.display = "flex";
}

function closeCropModal() {
    document.getElementById("crop-modal").style.display = "none";
    document.getElementById("view-modal").style.display = "none";
    document.getElementById("export-modal").style.display = "none";
}

document.getElementById("crop-form").addEventListener("submit", function (e) {
    e.preventDefault();
    var id = document.getElementById("crop-id").value;
    var data = {
        crop_name: document.getElementById("crop_name").value,
        village: document.getElementById("village").value,
        district: document.getElementById("district").value,
        land_size: parseFloat(document.getElementById("land_size").value),
        soil_type: document.getElementById("soil_type").value,
        season: document.getElementById("season").value,
        planting_date: document.getElementById("planting_date").value,
        harvest_date: document.getElementById("harvest_date").value,
        status: document.getElementById("status").value,
        notes: document.getElementById("notes").value,
    };
    var url = "/api/crops" + (id ? "/" + id : "");
    var method = id ? "PUT" : "POST";
    var btn = document.getElementById("form-submit-btn");
    btn.textContent = "Saving...";
    btn.disabled = true;

    fetch(url, { method: method, headers: { "Content-Type": "application/json" }, body: JSON.stringify(data) })
        .then(function (r) { return r.json(); })
        .then(function (res) {
            if (res.success) {
                showToast(res.message, "success");
                closeCropModal();
                loadCrops();
                btn.textContent = id ? "Update Crop" : "Save Crop";
                btn.disabled = false;
            } else {
                showToast(res.message || "Failed to save crop", "error");
                btn.textContent = id ? "Update Crop" : "Save Crop";
                btn.disabled = false;
            }
        })
        .catch(function () {
            showToast("Network error", "error");
            btn.textContent = id ? "Update Crop" : "Save Crop";
            btn.disabled = false;
        });
});

function editCrop(id) {
    fetch("/api/crops/" + id)
        .then(function (r) { return r.json(); })
        .then(function (res) {
            if (!res.success) { showToast(res.message, "error"); return; }
            var c = res.crop;
            document.getElementById("modal-title").textContent = "Edit Crop";
            document.getElementById("crop-id").value = c.id;
            document.getElementById("crop_name").value = c.crop_name;
            document.getElementById("village").value = c.village || "";
            document.getElementById("district").value = c.district;
            document.getElementById("land_size").value = c.land_size;
            document.getElementById("soil_type").value = c.soil_type;
            document.getElementById("season").value = c.season || "";
            document.getElementById("status").value = c.status;
            document.getElementById("planting_date").value = c.planting_date ? c.planting_date.substring(0, 10) : "";
            document.getElementById("harvest_date").value = c.harvest_date ? c.harvest_date.substring(0, 10) : "";
            document.getElementById("notes").value = c.notes || "";
            var btn = document.getElementById("form-submit-btn");
            btn.textContent = "Update Crop";
            btn.disabled = false;
            document.getElementById("crop-modal").style.display = "flex";
        });
}

function viewCrop(id) {
    fetch("/api/crops/" + id)
        .then(function (r) { return r.json(); })
        .then(function (res) {
            if (!res.success) { showToast(res.message, "error"); return; }
            var c = res.crop;
            var statusClass = c.status.toLowerCase().replace(/ /g, "-");
            var html = '<div class="view-grid">';
            html += '<div class="view-field"><span class="view-label">Crop Name</span><span class="view-val">' + escapeHtml(c.crop_name) + '</span></div>';
            html += '<div class="view-field"><span class="view-label">Village</span><span class="view-val">' + escapeHtml(c.village || "—") + '</span></div>';
            html += '<div class="view-field"><span class="view-label">District</span><span class="view-val">' + escapeHtml(c.district) + '</span></div>';
            html += '<div class="view-field"><span class="view-label">Land Size</span><span class="view-val">' + c.land_size + ' acres</span></div>';
            html += '<div class="view-field"><span class="view-label">Soil Type</span><span class="view-val">' + escapeHtml(c.soil_type) + '</span></div>';
            html += '<div class="view-field"><span class="view-label">Season</span><span class="view-val">' + escapeHtml(c.season || "—") + '</span></div>';
            html += '<div class="view-field"><span class="view-label">Planted</span><span class="view-val">' + (c.planting_date || "—") + '</span></div>';
            html += '<div class="view-field"><span class="view-label">Harvest</span><span class="view-val">' + (c.harvest_date || "—") + '</span></div>';
            html += '<div class="view-field"><span class="view-label">Status</span><span class="view-val"><span class="status-badge status-' + statusClass + '">' + escapeHtml(c.status) + '</span></span></div>';
            html += '<div class="view-field-full"><span class="view-label">Notes</span><span class="view-val">' + escapeHtml(c.notes || "No notes") + '</span></div>';
            html += '</div>';
            document.getElementById("view-details").innerHTML = html;
            document.getElementById("view-modal").style.display = "flex";
        });
}

function deleteCrop(id) {
    if (!confirm("Delete this crop? This cannot be undone.")) return;
    fetch("/api/crops/" + id, { method: "DELETE" })
        .then(function (r) { return r.json(); })
        .then(function (res) {
            if (res.success) {
                showToast(res.message, "success");
                if (res.stats) updateStatsFromServer(res.stats);
                loadCrops();
            } else {
                showToast(res.message, "error");
            }
        });
}

function updateStats() {
    fetch("/api/crops/stats")
        .then(function (r) { return r.json(); })
        .then(function (res) {
            if (res.success) updateStatsFromServer(res.stats);
        });
}

function updateStatsFromServer(stats) {
    document.querySelector("#stat-total .stat-value").textContent = stats.total_crops;
    document.querySelector("#stat-active .stat-value").textContent = stats.active_crops;
    document.querySelector("#stat-harvest .stat-value").textContent = stats.harvest_ready;
    document.querySelector("#stat-area .stat-value").textContent = stats.total_area;
    document.getElementById("insight-most").textContent = stats.most_cultivated || "—";
    document.getElementById("insight-soil").textContent = stats.most_common_soil || "—";
    document.getElementById("insight-district").textContent = stats.most_common_district || "—";
    var avgEl = document.querySelector("#stat-area .stat-value");
    avgEl.textContent = stats.total_area;
    document.getElementById("insight-growing").textContent = stats.active_crops;
    document.getElementById("insight-harvest-ready").textContent = stats.harvest_ready;
    document.getElementById("insight-total").textContent = stats.total_crops;

    var badge = document.querySelector('.crops-badge:last-child');
    if (badge) {
        var txt = badge.textContent.replace(/[0-9]/g, '').trim();
        badge.innerHTML = '<span class="badge-dot" style="background:#f59e0b"></span>' + stats.total_crops + ' Active';
    }
}

/* ===== Searchable District Dropdown ===== */
function initRecDropdown() {
    var trigger = document.getElementById("rec-select-trigger");
    var dropdown = document.getElementById("rec-dropdown");
    var searchInput = document.getElementById("rec-search-input");
    var label = document.getElementById("rec-selected-label");
    var wrap = document.getElementById("rec-search-wrap");
    var options = dropdown.querySelectorAll(".rec-option");
    var selectedValue = "";

    function toggleDropdown(e) {
        e.stopPropagation();
        var isOpen = wrap.classList.contains("open");
        wrap.classList.toggle("open");
        if (!isOpen) {
            searchInput.value = "";
            searchInput.style.display = "block";
            searchInput.focus();
            filterOptions("");
        } else {
            searchInput.style.display = "none";
        }
    }

    function filterOptions(q) {
        var lower = q.toLowerCase();
        options.forEach(function (opt) {
            var text = opt.textContent.toLowerCase();
            opt.style.display = text.indexOf(lower) >= 0 ? "block" : "none";
        });
    }

    function selectOption(opt) {
        var value = opt.getAttribute("data-value");
        var text = opt.textContent;
        selectedValue = value;
        label.textContent = text;
        wrap.classList.remove("open");
        searchInput.style.display = "none";
        loadRecommendations(value);
    }

    trigger.addEventListener("click", toggleDropdown);

    searchInput.addEventListener("input", function () {
        filterOptions(this.value);
    });

    searchInput.addEventListener("keydown", function (e) {
        if (e.key === "Enter") {
            var visible = Array.from(options).filter(function (o) { return o.style.display !== "none"; });
            if (visible.length > 0) {
                selectOption(visible[0]);
            }
        }
        if (e.key === "Escape") {
            wrap.classList.remove("open");
            searchInput.style.display = "none";
        }
    });

    options.forEach(function (opt) {
        opt.addEventListener("click", function () {
            selectOption(this);
        });
    });

    document.addEventListener("click", function () {
        wrap.classList.remove("open");
        searchInput.style.display = "none";
    });

    // Disable native autofill interfering
    searchInput.setAttribute("autocomplete", "off");
}

function loadRecommendations(district) {
    var container = document.getElementById("rec-crops-list");
    container.innerHTML = '<div class="rec-loading"><div class="rec-spinner"></div><span>Loading recommendations...</span></div>';
    fetch("/api/crops/recommendations?district=" + encodeURIComponent(district))
        .then(function (r) { return r.json(); })
        .then(function (res) {
            if (!res.success) {
                container.innerHTML = '<div class="rec-placeholder"><p>Failed to load recommendations. Please try again.</p></div>';
                return;
            }
            if (!res.recommendations || res.recommendations.length === 0) {
                container.innerHTML = '<div class="rec-placeholder"><p>No recommendations available for this district.</p></div>';
                return;
            }
            var html = "";
            res.recommendations.forEach(function (r) {
                var diffClass = r.difficulty.toLowerCase();
                html += '<div class="rec-card">';
                html += '<div class="rec-card-header"><span class="rec-crop-name">' + escapeHtml(r.crop) + '</span><span class="rec-difficulty diff-' + diffClass + '">' + escapeHtml(r.difficulty) + '</span></div>';
                html += '<p class="rec-reason">' + escapeHtml(r.reason) + '</p>';
                html += '<div class="rec-details">';
                html += '<span><strong>Soil:</strong> ' + escapeHtml(r.soil) + '</span>';
                html += '<span><strong>Season:</strong> ' + escapeHtml(r.season) + '</span>';
                html += '<span><strong>Duration:</strong> ' + escapeHtml(r.duration) + '</span>';
                html += '<span><strong>Water:</strong> ' + escapeHtml(r.water) + '</span>';
                html += '<span><strong>Yield:</strong> ' + escapeHtml(r.yield) + '</span>';
                html += '</div></div>';
            });
            container.innerHTML = html;
        })
        .catch(function () {
            container.innerHTML = '<div class="rec-placeholder"><p>Network error. Please try again.</p></div>';
        });
}



function loadActivities() {
    fetch("/api/crops/activities")
        .then(function (r) { return r.json(); })
        .then(function (res) {
            var list = document.getElementById("activities-list");
            if (!list) return;
            if (!res.success || !res.activities || res.activities.length === 0) {
                list.innerHTML = '<div class="crops-empty">No upcoming activities. Add crops with dates.</div>';
                return;
            }
            var html = "";
            res.activities.forEach(function (a) {
                html += '<div class="activity-item activity-' + a.urgency + '">';
                html += '<div class="activity-icon">' + (a.type === "harvest" ? "🌾" : "💧") + '</div>';
                html += '<div class="activity-info">';
                html += '<span class="activity-action">' + escapeHtml(a.action) + " " + escapeHtml(a.crop) + '</span>';
                html += '<span class="activity-time">' + (a.days === 0 ? "Today" : "In " + a.days + " days") + '</span>';
                html += '</div></div>';
            });
            list.innerHTML = html;
        });
}

function showExportModal() {
    document.getElementById("export-modal").style.display = "flex";
}

function exportCrops(format) {
    var btn = document.querySelector('.export-option');
    fetch("/api/crops/export?format=" + format)
        .then(function (r) { return r.json(); })
        .then(function (res) {
            if (!res.success) { showToast(res.message, "error"); return; }
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
            a.download = res.filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            showToast("Exported successfully!", "success");
            closeModal();
        })
        .catch(function () { showToast("Export failed", "error"); });
}

function escapeHtml(text) {
    if (!text) return "";
    var d = document.createElement("div");
    d.textContent = text;
    return d.innerHTML;
}

function showToast(msg, type) {
    var toast = document.getElementById("crops-toast");
    if (!toast) return;
    toast.textContent = msg;
    toast.className = "crops-toast " + (type || "");
    toast.style.display = "block";
    clearTimeout(toast._timer);
    toast._timer = setTimeout(function () { toast.style.display = "none"; }, 3000);
}
