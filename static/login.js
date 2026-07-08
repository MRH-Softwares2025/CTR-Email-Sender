const loginForm = document.getElementById("loginForm");
const configMessage = document.getElementById("configMessage");
const passwordToggleButton = document.getElementById("passwordToggleButton");

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

if (passwordToggleButton) {
    passwordToggleButton.addEventListener("click", () => {
        const passwordField = document.getElementById("appPassword");
        if (!passwordField) return;
        const isPassword = passwordField.type === "password";
        passwordField.type = isPassword ? "text" : "password";
        passwordToggleButton.setAttribute("aria-label", isPassword ? "Hide password" : "Show password");
    });
}

function showMessage(text, success = true) {
    configMessage.textContent = text;
    configMessage.className = `message ${success ? "success" : "error"}`;
}

loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const defaultsResponse = await apiGet("/api/defaults");
    const defaults = defaultsResponse.success === false ? {} : defaultsResponse;
    const payload = {
        gmail_email: document.getElementById("gmailEmail").value,
        app_password: document.getElementById("appPassword").value,
        email_subject: defaults.email_subject || "Automated Email",
        email_body: defaults.email_body || "This is an automated email.",
        start_hour: defaults.start_hour ?? 9,
        end_hour: defaults.end_hour ?? 17,
        emails_per_hour: defaults.emails_per_hour ?? 125,
        time_variation_seconds: defaults.time_variation_seconds ?? 300,
    };
    const result = await apiPost("/api/config", payload);
    if (result.success) {
        showMessage(result.message || "Saved successfully.");
        // Redirect based on subscription status
        const redirectUrl = result.redirect || "/subscription";
        window.location.href = redirectUrl;
    } else {
        showMessage(result.message || "Could not save settings.", false);
    }
});
