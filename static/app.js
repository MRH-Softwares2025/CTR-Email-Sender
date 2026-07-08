const subscriptionStatus = document.getElementById("subscriptionStatus");
const expiryDate = document.getElementById("expiryDate");
const daysLeft = document.getElementById("daysLeft");
const payButton = document.getElementById("payButton");
const confirmPaymentButton = document.getElementById("confirmPaymentButton");
const mpesaPhone = document.getElementById("mpesaPhone");
const checkoutInput = document.getElementById("checkoutInput");
const paymentStatus = document.getElementById("paymentStatus");
const subscriptionMessage = document.getElementById("subscriptionMessage");
const subscriptionNote = document.getElementById("subscriptionNote");
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

let subscriptionActive = false;
let lastCheckoutRequestId = null;

async function apiGet(path) {
    try {
        const response = await fetch(path);
        const result = await response.json();
        if (!response.ok) {
            return { success: false, message: result.detail || result.message || 'Request failed.' };
        }
        return result;
    } catch (error) {
        return { success: false, message: error.message || 'Network error while fetching data.' };
    }
}

async function apiPost(path, body = {}) {
    try {
        const response = await fetch(path, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
        });
        const result = await response.json();
        if (!response.ok) {
            return { success: false, message: result.detail || result.message || 'Request failed.' };
        }
        return result;
    } catch (error) {
        return { success: false, message: error.message || 'Network error while sending request.' };
    }
}

function setActionState(enabled) {
    sendSingleButton.disabled = !enabled;
    sendBatchButton.disabled = !enabled;
    sendContinuousButton.disabled = !enabled;
    stopButton.disabled = !enabled;
}

// Always enable send controls for testing/development.
setActionState(true);

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
    subscriptionActive = data.active;
    const isRequired = data.subscription_required !== false;
    if (data.active) {
        subscriptionStatus.textContent = "Active";
        subscriptionStatus.className = "status active";
        subscriptionNote.textContent = isRequired ? "Subscription is active and send controls are enabled." : "Subscription gating is disabled for development.";
    } else if (isRequired) {
        subscriptionStatus.textContent = "Inactive";
        subscriptionStatus.className = "status inactive";
        subscriptionNote.textContent = "Subscription is required to send emails. Activate using MPESA or set DISABLE_SUBSCRIPTION_CHECK=true for development.";
    } else {
        subscriptionStatus.textContent = "Not required";
        subscriptionStatus.className = "status active";
        subscriptionNote.textContent = "Subscription gating is disabled for development or testing.";
    }

    expiryDate.textContent = data.expiry || "Not set";
    daysLeft.textContent = data.days_left ?? 0;
    setActionState(!isRequired || data.active);
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
    checkoutInput.value = lastCheckoutRequestId || "";

    const config = await apiGet("/api/config");
    document.getElementById("gmailEmail").value = config.gmail_email || "";
    document.getElementById("emailSubject").value = config.email_subject || "";
    document.getElementById("emailBody").value = config.email_body || "";
    document.getElementById("startHour").value = config.start_hour || 9;
    document.getElementById("endHour").value = config.end_hour || 17;
    document.getElementById("emailsPerHour").value = config.emails_per_hour || 125;
    document.getElementById("timeVariation").value = config.time_variation_seconds || 300;

    const stats = await apiGet("/api/stats");
    updateStatsUI(stats);

    const logs = await apiGet("/api/logs");
    updateLogsUI(logs.logs || []);
}

settingsForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const payload = {
        gmail_email: document.getElementById("gmailEmail").value,
        app_password: document.getElementById("appPassword").value,
        email_subject: document.getElementById("emailSubject").value,
        email_body: document.getElementById("emailBody").value,
        start_hour: parseInt(document.getElementById("startHour").value, 10),
        end_hour: parseInt(document.getElementById("endHour").value, 10),
        emails_per_hour: parseInt(document.getElementById("emailsPerHour").value, 10),
        time_variation_seconds: parseFloat(document.getElementById("timeVariation").value),
    };
    const result = await apiPost("/api/config", payload);
    showMessage(configMessage, result.message || "Settings saved.");
});

payButton.addEventListener("click", async () => {
    const phoneNumber = mpesaPhone.value.trim();
    if (!phoneNumber) {
        showMessage(subscriptionMessage, "Enter a valid MPESA phone number first.", false);
        return;
    }
    const result = await apiPost("/api/subscription/pay", { phone_number: phoneNumber });
    lastCheckoutRequestId = result.checkout_request_id || null;
    checkoutInput.value = lastCheckoutRequestId || "";
    showMessage(subscriptionMessage, result.message || "Payment started.", result.success !== false);
});

confirmPaymentButton.addEventListener("click", async () => {
    const checkoutRequestId = checkoutInput.value.trim();
    if (!checkoutRequestId) {
        showMessage(subscriptionMessage, "Enter a checkout request ID first.", false);
        return;
    }

    const status = paymentStatus.value;
    const result = await apiPost("/api/subscription/confirm", {
        checkout_request_id: checkoutRequestId,
        status,
    });
    showMessage(subscriptionMessage, result.message || "Payment confirmation submitted.", result.success !== false);
    await loadPageState();
});

sendSingleButton.addEventListener("click", async () => {
    const result = await apiPost("/api/send/single");
    showMessage(controlMessage, result.message || "Sent single email.");
    loadPageState();
});

sendBatchButton.addEventListener("click", async () => {
    const count = parseInt(batchCount.value, 10);
    if (!count || count <= 0) {
        showMessage(controlMessage, "Batch count must be a number greater than 0.", false);
        return;
    }
    const result = await apiPost("/api/send/batch", { count });
    showMessage(controlMessage, result.message || "Batch started.");
    loadPageState();
});

sendContinuousButton.addEventListener("click", async () => {
    const result = await apiPost("/api/send/continuous");
    showMessage(controlMessage, result.message || "Continuous mode started.");
    loadPageState();
});

stopButton.addEventListener("click", async () => {
    const result = await apiPost("/api/send/stop");
    showMessage(controlMessage, result.message || "Stopped.");
    loadPageState();
});

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", loadPageState);
} else {
    loadPageState();
}
