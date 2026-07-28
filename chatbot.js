var currentConvId = null;
var isLoading = false;

function initChatbot() {
    var messages = document.getElementById("chat-messages");
    var input = document.getElementById("chat-input");
    var sendBtn = document.getElementById("chat-send");
    var newBtn = document.getElementById("chat-new-btn");
    var exportBtn = document.getElementById("chat-export-btn");

    if (!messages) return;

    updateConvId();
    if (!messages.querySelector(".chat-bubble")) {
        showSuggestions();
    }

    if (sendBtn && input) {
        sendBtn.addEventListener("click", sendMessage);
        input.addEventListener("keydown", function (e) {
            if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    }

    if (newBtn) {
        newBtn.addEventListener("click", newConversation);
    }

    if (exportBtn) {
        exportBtn.addEventListener("click", showExportModal);
    }

    document.querySelectorAll(".chat-suggestion-chip").forEach(function (chip) {
        chip.addEventListener("click", function () {
            if (input) {
                input.value = this.getAttribute("data-text") || this.textContent;
                sendMessage();
            }
        });
    });

    document.querySelectorAll(".chat-conv-item").forEach(function (item) {
        item.addEventListener("click", function (e) {
            if (e.target.closest(".chat-conv-delete")) return;
            loadConversation(this.getAttribute("data-conv-id"));
        });
    });

    document.querySelectorAll(".chat-conv-delete").forEach(function (btn) {
        btn.addEventListener("click", function (e) {
            e.stopPropagation();
            deleteConversation(this.getAttribute("data-conv-id"));
        });
    });

    document.querySelectorAll(".chat-export-option").forEach(function (btn) {
        btn.addEventListener("click", function () {
            exportChat(this.getAttribute("data-format"));
        });
    });

    var cancelBtn = document.querySelector(".chat-export-cancel");
    var overlay = document.querySelector(".chat-export-overlay");
    if (cancelBtn) cancelBtn.addEventListener("click", hideExportModal);
    if (overlay) overlay.addEventListener("click", hideExportModal);

    updateExportBtn();
}

function updateConvId() {
    var active = document.querySelector(".chat-conv-item.active");
    if (active) {
        currentConvId = active.getAttribute("data-conv-id");
    } else {
        var first = document.querySelector(".chat-conv-item");
        if (first) {
            currentConvId = first.getAttribute("data-conv-id");
        } else {
            currentConvId = null;
        }
    }
}

function showSuggestions() {
    var suggestions = document.getElementById("chat-suggestions");
    if (suggestions) {
        suggestions.style.display = "block";
    }
}

function hideSuggestions() {
    var suggestions = document.getElementById("chat-suggestions");
    if (suggestions) {
        suggestions.style.display = "none";
    }
}

function addBubble(text, role) {
    var messages = document.getElementById("chat-messages");
    if (!messages) return;

    var div = document.createElement("div");
    div.className = "chat-bubble " + role;

    var content = document.createElement("div");
    content.className = "chat-bubble-content";
    content.innerHTML = renderMarkdown(text);
    div.appendChild(content);

    var actions = document.createElement("div");
    actions.className = "chat-bubble-actions";
    var copyBtn = document.createElement("button");
    copyBtn.className = "chat-copy-btn";
    copyBtn.title = "Copy";
    copyBtn.innerHTML = '<i class="fas fa-copy"></i>';
    copyBtn.addEventListener("click", function () {
        copyToClipboard(text);
    });
    actions.appendChild(copyBtn);
    div.appendChild(actions);

    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
}

function renderMarkdown(text) {
    if (typeof marked !== "undefined" && typeof DOMPurify !== "undefined") {
        var html = marked.parse(String(text), { breaks: true, gfm: true });
        return DOMPurify.sanitize(html);
    }
    var html = String(text)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
    html = html.replace(/###\s*(.+?)(\n|$)/g, '<h3>$1</h3>');
    html = html.replace(/##\s*(.+?)(\n|$)/g, '<h2>$1</h2>');
    html = html.replace(/#\s*(.+?)(\n|$)/g, '<h1>$1</h1>');
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
    html = html.replace(/^- (.+)$/gm, '<li>$1</li>');
    html = html.replace(/((?:<li>.*?<\/li>\n?)+)/g, '<ul>$1</ul>');
    html = html.replace(/\n/g, '<br>');
    return html;
}

function sendMessage() {
    if (isLoading) return;

    var input = document.getElementById("chat-input");
    var message = input.value.trim();
    if (!message) return;

    hideSuggestions();
    addBubble(message, "user");
    input.value = "";
    setLoading(true);

    var langEl = document.documentElement;
    var language = langEl.getAttribute("data-lang") || "en";
    var districtBadge = document.querySelector(".chat-district-badge");
    var district = districtBadge ? districtBadge.textContent.replace("📍", "").trim() : "";

    fetch("/api/chat/send", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            message: message,
            conversation_id: currentConvId || "",
            language: language,
            district: district,
        }),
    })
    .then(function (resp) {
        if (!resp.ok) {
            return resp.json().then(function (err) {
                throw new Error(err.message || "Server error");
            }).catch(function () {
                throw new Error("Server returned " + resp.status);
            });
        }
        return resp.json();
    })
    .then(function (data) {
        if (data.success) {
            if (data.conversation_id) {
                currentConvId = data.conversation_id;
            }
            addConversationToList(data.conversation_id, data.title);
            simulateTyping(data.reply);
        } else {
            showToast(data.message || "An error occurred", "error");
            setLoading(false);
        }
    })
    .catch(function (err) {
        setLoading(false);
        showToast(err.message || "Unable to contact the AI service at the moment. Please try again later.", "error");
    });
}

function simulateTyping(fullText) {
    var messages = document.getElementById("chat-messages");
    if (!messages) return;

    var div = document.createElement("div");
    div.className = "chat-bubble assistant";

    var content = document.createElement("div");
    content.className = "chat-bubble-content";
    content.id = "typing-content";
    div.appendChild(content);

    var actions = document.createElement("div");
    actions.className = "chat-bubble-actions";
    var copyBtn = document.createElement("button");
    copyBtn.className = "chat-copy-btn";
    copyBtn.innerHTML = '<i class="fas fa-copy"></i>';
    copyBtn.addEventListener("click", function () {
        copyToClipboard(fullText);
    });
    actions.appendChild(copyBtn);
    div.appendChild(actions);

    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;

    var words = fullText.split(" ");
    var index = 0;
    var currentText = "";

    function typeNext() {
        if (index < words.length) {
            currentText += (index > 0 ? " " : "") + words[index];
            content.innerHTML = renderMarkdown(currentText);
            messages.scrollTop = messages.scrollHeight;
            index++;
            var delay = Math.min(50, Math.max(10, 200 / words.length));
            setTimeout(typeNext, delay);
        } else {
            content.id = "";
            setLoading(false);
            updateExportBtn();
        }
    }

    typeNext();
}

function setLoading(loading) {
    isLoading = loading;
    var sendBtn = document.getElementById("chat-send");
    var input = document.getElementById("chat-input");
    var typing = document.getElementById("chat-typing");
    if (sendBtn) sendBtn.disabled = loading;
    if (input) input.disabled = loading;
    if (typing) typing.style.display = loading ? "flex" : "none";
}

function newConversation() {
    fetch("/api/chat/new", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
    })
    .then(function (r) { return r.json(); })
    .then(function (res) {
        if (res.success) {
            window.location.href = "/ai-chat?conv=" + res.conversation.id;
        }
    })
    .catch(function () {
        showToast("Failed to create new conversation", "error");
    });
}

function loadConversation(convId) {
    window.location.href = "/ai-chat?conv=" + convId;
}

function deleteConversation(convId) {
    if (!confirm("Delete this conversation?")) return;
    fetch("/api/chat/conversation/" + convId, { method: "DELETE" })
    .then(function (r) { return r.json(); })
    .then(function (res) {
        if (res.success) {
            var item = document.querySelector('.chat-conv-item[data-conv-id="' + convId + '"]');
            if (item) item.remove();
            if (currentConvId === convId) {
                window.location.href = "/ai-chat";
            }
        } else {
            showToast(res.message || "Failed to delete", "error");
        }
    })
    .catch(function () {
        showToast("Failed to delete conversation", "error");
    });
}

function addConversationToList(convId, title) {
    if (!convId) return;
    var existing = document.querySelector('.chat-conv-item[data-conv-id="' + convId + '"]');
    if (!existing) {
        var list = document.getElementById("chat-conversations");
        if (!list) return;
        var empty = list.querySelector(".chat-conv-empty");
        if (empty) empty.remove();
        var div = document.createElement("div");
        div.className = "chat-conv-item active";
        div.setAttribute("data-conv-id", convId);
        div.innerHTML =
            '<div class="chat-conv-title">' + escapeHtml(title || "New Chat") + '</div>' +
            '<div class="chat-conv-meta"><span>—</span>' +
            '<button class="chat-conv-delete" data-conv-id="' + convId + '"><i class="fas fa-trash"></i></button></div>';
        div.addEventListener("click", function () {
            loadConversation(convId);
        });
        div.querySelector(".chat-conv-delete").addEventListener("click", function (e) {
            e.stopPropagation();
            deleteConversation(convId);
        });
        list.insertBefore(div, list.firstChild);
        document.querySelectorAll(".chat-conv-item").forEach(function (item) {
            item.classList.remove("active");
        });
        div.classList.add("active");
    }
    updateExportBtn();
}

function escapeHtml(text) {
    var d = document.createElement("div");
    d.textContent = text;
    return d.innerHTML;
}

function showExportModal() {
    var modal = document.getElementById("chat-export-modal");
    if (modal) modal.style.display = "block";
}

function hideExportModal() {
    var modal = document.getElementById("chat-export-modal");
    if (modal) modal.style.display = "none";
}

function exportChat(format) {
    if (!currentConvId) return;
    fetch("/api/chat/export", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ conv_id: currentConvId, format: format }),
    })
    .then(function (r) { return r.json(); })
    .then(function (res) {
        if (res.success) {
            var content = res.export;
            var mimeType = res.mime;
            if (res.encoding === "base64") {
                var binary = atob(content);
                var array = new Uint8Array(binary.length);
                for (var i = 0; i < binary.length; i++) {
                    array[i] = binary.charCodeAt(i);
                }
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
            hideExportModal();
            showToast("Exported successfully!", "success");
        } else {
            showToast(res.message || "Export failed", "error");
        }
    })
    .catch(function () {
        showToast("Export failed", "error");
    });
}

function copyToClipboard(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(function () {
            showToast("Copied!", "success");
        }).catch(function () {
            fallbackCopy(text);
        });
    } else {
        fallbackCopy(text);
    }
}

function fallbackCopy(text) {
    var ta = document.createElement("textarea");
    ta.value = text;
    ta.style.position = "fixed";
    ta.style.opacity = "0";
    document.body.appendChild(ta);
    ta.select();
    try {
        document.execCommand("copy");
        showToast("Copied!", "success");
    } catch (e) {}
    document.body.removeChild(ta);
}

function showToast(msg, type) {
    var toast = document.getElementById("chat-toast");
    if (!toast) return;
    toast.textContent = msg;
    toast.className = "chat-toast " + (type || "");
    toast.style.display = "block";
    clearTimeout(toast._hideTimer);
    toast._hideTimer = setTimeout(function () {
        toast.style.display = "none";
    }, 3000);
}

function updateExportBtn() {
    var btn = document.getElementById("chat-export-btn");
    if (!btn) return;
    var bubbles = document.querySelectorAll("#chat-messages .chat-bubble");
    btn.style.display = bubbles.length > 0 ? "flex" : "none";
}

function renderExistingMessages() {
    var contents = document.querySelectorAll("#chat-messages .chat-bubble-content");
    if (typeof marked !== "undefined" && typeof DOMPurify !== "undefined") {
        contents.forEach(function (el) {
            var raw = el.textContent;
            if (raw.indexOf("#") >= 0 || raw.indexOf("**") >= 0 || raw.indexOf("```") >= 0 || raw.indexOf("|") >= 0 || raw.indexOf("- ") >= 0) {
                el.innerHTML = DOMPurify.sanitize(marked.parse(raw, { breaks: true, gfm: true }));
            }
        });
    }
}

document.addEventListener("DOMContentLoaded", function () {
    if (document.getElementById("chat-messages")) {
        initChatbot();
        renderExistingMessages();
    }
});
