const subscriptionStatus = document.getElementById("subscriptionStatus");
const expiryDate = document.getElementById("expiryDate");
const daysLeft = document.getElementById("daysLeft");
const planName = document.getElementById("planName");
const settingsForm = document.getElementById("settingsForm");
const configMessage = document.getElementById("configMessage");
const passwordToggleButton = document.getElementById("passwordToggleButton");
const sendSingleButton = document.getElementById("sendSingleButton");
const sendBatchButton = document.getElementById("sendBatchButton");
const sendContinuousButton = document.getElementById("sendContinuousButton");
const stopButton = document.getElementById("stopButton");
const controlMessage = document.getElementById("controlMessage");
const batchCount = document.getElementById("batchCount");
const emailsSentToday = document.getElementById("emailsSentToday");
const emailsSentTotal = document.getElementById("emailsSentTotal");
const failedEmails = document.getElementById("failedEmails");
const dailyLimit = document.getElementById("dailyLimit");
const activityLog = document.getElementById("activityLog");

// Notification elements
const notificationBell = document.getElementById("notificationBell");
const notificationBadge = document.getElementById("notificationBadge");
const notificationDropdown = document.getElementById("notificationDropdown");
const notificationList = document.getElementById("notificationList");
const dismissAllNotifications = document.getElementById("dismissAllNotifications");

async function apiGet(path) {
    const response = await fetch(path);
    const result = await response.json();
    if (!response.ok) {
        return { success: false, message: result.detail || result.message || "Request failed." };
    }
    return result;
}

async function apiPost(path, body = {}) {
    const response = await fetch(path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
    });
    const result = await response.json();
    if (!response.ok) {
        return { success: false, message: result.detail || result.message || "Request failed." };
    }
    return result;
}

function setActionState(enabled) {
    sendSingleButton.disabled = !enabled;
    sendBatchButton.disabled = !enabled;
    sendContinuousButton.disabled = !enabled;
    stopButton.disabled = !enabled;
}

if (passwordToggleButton) {
    passwordToggleButton.addEventListener("click", () => {
        const passwordField = document.getElementById("appPassword");
        if (!passwordField) return;
        const isPassword = passwordField.type === "password";
        passwordField.type = isPassword ? "text" : "password";
        passwordToggleButton.setAttribute("aria-label", isPassword ? "Hide password" : "Show password");
    });
}

function showMessage(container, text, success = true) {
    container.textContent = text;
    container.className = `message ${success ? "success" : "error"}`;
}

function updateSubscriptionUI(data) {
    if (!data) return;
    const isRequired = data.subscription_required !== false;
    if (data.active) {
        subscriptionStatus.textContent = "Active";
        subscriptionStatus.className = "status active";
        subscriptionNote.textContent = "Subscription is active. You may send emails.";
        if (data.plan) {
            planName.textContent = `${data.plan.name} (KES ${data.plan.price})`;
        } else {
            planName.textContent = "—";
        }
    } else if (isRequired) {
        subscriptionStatus.textContent = "Inactive";
        subscriptionStatus.className = "status inactive";
        subscriptionNote.textContent = "Subscription is required to use sending features. Go to subscription page.";
        planName.textContent = "—";
    } else {
        subscriptionStatus.textContent = "Not required";
        subscriptionStatus.className = "status active";
        subscriptionNote.textContent = "Subscription gating is disabled for development.";
        planName.textContent = "—";
    }
    expiryDate.textContent = data.expiry || "Not set";
    daysLeft.textContent = data.days_left ?? 0;
    setActionState(data.active || !isRequired);
}

function updateSettingsUI(data) {
    document.getElementById("gmailEmail").value = data.gmail_email || "";
    document.getElementById("emailSubject").value = data.email_subject || "";
    document.getElementById("emailBody").value = data.email_body || "";
    document.getElementById("startHour").value = data.start_hour || 9;
    document.getElementById("endHour").value = data.end_hour || 17;
    document.getElementById("emailsPerHour").value = data.emails_per_hour || 125;
    document.getElementById("timeVariation").value = data.time_variation_seconds || 300;
}

function updateStatsUI(data) {
    emailsSentToday.textContent = data.emails_sent_today || 0;
    emailsSentTotal.textContent = data.emails_sent_total || 0;
    failedEmails.textContent = data.failed_emails || 0;
    dailyLimit.textContent = data.daily_limit || 0;
}

function updateLogsUI(logs) {
    activityLog.textContent = logs.join("\n");
}

async function loadPageState() {
    const subscription = await apiGet("/api/subscription");
    updateSubscriptionUI(subscription);

    const config = await apiGet("/api/config");
    updateSettingsUI(config);

    const stats = await apiGet("/api/stats");
    updateStatsUI(stats);

    const logs = await apiGet("/api/logs");
    updateLogsUI(logs.logs || []);

    // Load notifications
    loadNotifications();
}

settingsForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const payload = {
        gmail_email: document.getElementById("gmailEmail").value,
        email_subject: document.getElementById("emailSubject").value,
        email_body: document.getElementById("emailBody").value,
        start_hour: parseInt(document.getElementById("startHour").value, 10),
        end_hour: parseInt(document.getElementById("endHour").value, 10),
        emails_per_hour: parseInt(document.getElementById("emailsPerHour").value, 10),
        time_variation_seconds: parseFloat(document.getElementById("timeVariation").value),
    };
    const appPassword = document.getElementById("appPassword").value.trim();
    if (appPassword) {
        payload.app_password = appPassword;
    }
    const result = await apiPost("/api/config", payload);
    showMessage(configMessage, result.message || "Settings saved.", result.success !== false);
    if (result.success) {
        document.getElementById("appPassword").value = "";
        await loadPageState();
    }
});

sendSingleButton.addEventListener("click", async () => {
    const result = await apiPost("/api/send/single");
    showMessage(controlMessage, result.message || "Sent single email.", result.success !== false);
    loadPageState();
});

sendBatchButton.addEventListener("click", async () => {
    const count = parseInt(batchCount.value, 10);
    if (!count || count <= 0) {
        showMessage(controlMessage, "Batch count must be a number greater than 0.", false);
        return;
    }
    const result = await apiPost("/api/send/batch", { count });
    showMessage(controlMessage, result.message || "Batch started.", result.success !== false);
    loadPageState();
});

sendContinuousButton.addEventListener("click", async () => {
    const result = await apiPost("/api/send/continuous");
    showMessage(controlMessage, result.message || "Continuous mode started.", result.success !== false);
    loadPageState();
});

stopButton.addEventListener("click", async () => {
    const result = await apiPost("/api/send/stop");
    showMessage(controlMessage, result.message || "Stopped.", result.success !== false);
    loadPageState();
});

// Notification functions
async function loadNotifications() {
    const result = await apiGet("/api/notifications");
    if (result.success !== false) {
        updateNotificationUI(result);
    }
}

function updateNotificationUI(data) {
    const notifications = data.notifications || [];
    const summary = data.summary || { total_unread: 0 };
    
    // Update badge
    if (summary.total_unread > 0) {
        notificationBadge.textContent = summary.total_unread;
        notificationBadge.classList.remove("hidden");
    } else {
        notificationBadge.classList.add("hidden");
    }
    
    // Update notification list
    if (notifications.length === 0) {
        notificationList.innerHTML = '<p class="no-notifications">No notifications</p>';
    } else {
        notificationList.innerHTML = notifications.map((notification, index) => {
            const priorityClass = `priority-${notification.priority}`;
            const unreadClass = notification.read ? "" : "unread";
            const time = new Date(notification.created_at).toLocaleString();
            
            return `
                <div class="notification-item ${priorityClass} ${unreadClass}" data-index="${index}">
                    <div class="notification-item-title">${notification.title}</div>
                    <div class="notification-item-message">${notification.message}</div>
                    <div class="notification-item-time">${time}</div>
                </div>
            `;
        }).join("");
    }
}

function toggleNotificationDropdown() {
    notificationDropdown.classList.toggle("hidden");
}

function closeNotificationDropdown() {
    notificationDropdown.classList.add("hidden");
}

// Notification event listeners
if (notificationBell) {
    notificationBell.addEventListener("click", (e) => {
        e.stopPropagation();
        toggleNotificationDropdown();
        loadNotifications();
    });
}

if (dismissAllNotifications) {
    dismissAllNotifications.addEventListener("click", async () => {
        await apiPost("/api/notifications/dismiss-all");
        loadNotifications();
    });
}

// Close dropdown when clicking outside
document.addEventListener("click", (e) => {
    if (!notificationDropdown.contains(e.target) && !notificationBell.contains(e.target)) {
        closeNotificationDropdown();
    }
});

// Auto-refresh notifications every 30 seconds
setInterval(loadNotifications, 30000);

// Formatting toolbar functionality
const formatButtons = document.querySelectorAll('.format-btn');
const emailBody = document.getElementById('emailBody');

formatButtons.forEach(button => {
    button.addEventListener('click', () => {
        const format = button.dataset.format;
        applyFormatting(format);
    });
});

function applyFormatting(format) {
    const textarea = emailBody;
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const selectedText = textarea.value.substring(start, end);
    
    let formatting;
    switch(format) {
        case 'bold':
            formatting = { prefix: '**', suffix: '**' };
            break;
        case 'italic':
            formatting = { prefix: '*', suffix: '*' };
            break;
        case 'underline':
            formatting = { prefix: '__', suffix: '__' };
            break;
        default:
            return;
    }
    
    const newText = textarea.value.substring(0, start) + 
                   formatting.prefix + selectedText + formatting.suffix + 
                   textarea.value.substring(end);
    
    textarea.value = newText;
    
    // Set cursor position after the formatting
    const newPosition = selectedText ? end + formatting.prefix.length + formatting.suffix.length : start + formatting.prefix.length;
    textarea.setSelectionRange(newPosition, newPosition);
    textarea.focus();
}

// Keyboard shortcuts for formatting
emailBody.addEventListener('keydown', (e) => {
    if (e.ctrlKey || e.metaKey) {
        switch(e.key.toLowerCase()) {
            case 'b':
                e.preventDefault();
                applyFormatting('bold');
                break;
            case 'i':
                e.preventDefault();
                applyFormatting('italic');
                break;
            case 'u':
                e.preventDefault();
                applyFormatting('underline');
                break;
        }
    }
});

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", loadPageState);
} else {
    loadPageState();
}
