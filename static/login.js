const loginForm = document.getElementById("loginForm");
const loginMessage = document.getElementById("loginMessage");
const passwordToggleButton = document.getElementById("passwordToggleButton");

// --- Forgot password elements ---
const forgotPasswordLink = document.getElementById("forgotPasswordLink");
const backToLoginLink = document.getElementById("backToLoginLink");
const resendCodeLink = document.getElementById("resendCodeLink");
const forgotPanel = document.getElementById("forgotPanel");
const loginCard = loginForm?.closest(".card");
const forgotStep1 = document.getElementById("forgotStep1");
const forgotStep2 = document.getElementById("forgotStep2");
const forgotForm = document.getElementById("forgotForm");
const resetForm = document.getElementById("resetForm");
const forgotMessage = document.getElementById("forgotMessage");
const resetMessage = document.getElementById("resetMessage");
const resetPasswordToggle = document.getElementById("resetPasswordToggle");

let _forgotEmail = "";

async function apiPostForm(path, formData) {
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 30000);
        const response = await fetch(path, {
            method: "POST",
            body: formData,
            signal: controller.signal,
        });
        clearTimeout(timeoutId);

        let result = {};
        try {
            result = await response.json();
        } catch {
            result = {};
        }

        if (!response.ok) {
            return {
                success: false,
                message: result.detail || result.message || `Request failed (${response.status}).`,
            };
        }

        return {
            success: Boolean(result.success ?? true),
            message: result.message || "Request completed.",
            ...result,
        };
    } catch (error) {
        const timedOut = error && error.name === "AbortError";
        return {
            success: false,
            message: timedOut
                ? "Request timed out. Please try again."
                : "Could not reach the server. Check that the app is running, then try again.",
        };
    }
}

if (passwordToggleButton) {
    passwordToggleButton.addEventListener("click", () => {
        const passwordField = document.getElementById("loginPassword");
        if (!passwordField) return;
        const isPassword = passwordField.type === "password";
        passwordField.type = isPassword ? "text" : "password";
        passwordToggleButton.setAttribute("aria-label", isPassword ? "Hide password" : "Show password");
    });
}

if (resetPasswordToggle) {
    resetPasswordToggle.addEventListener("click", () => {
        const field = document.getElementById("resetNewPassword");
        if (!field) return;
        const isPassword = field.type === "password";
        field.type = isPassword ? "text" : "password";
        resetPasswordToggle.setAttribute("aria-label", isPassword ? "Hide password" : "Show password");
    });
}

function showMessage(text, success = true) {
    loginMessage.textContent = text;
    loginMessage.className = `message ${success ? "success" : "error"}`;
}

function showForgotMessage(el, text, success = true) {
    el.textContent = text;
    el.className = `message ${success ? "success" : "error"}`;
}

function showForgotPanel() {
    if (loginCard) loginCard.style.display = "none";
    forgotPanel.style.display = "";
    forgotStep1.style.display = "";
    forgotStep2.style.display = "none";
    forgotMessage.textContent = "";
    resetMessage.textContent = "";
}

function showLoginPanel() {
    forgotPanel.style.display = "none";
    if (loginCard) loginCard.style.display = "";
}

if (forgotPasswordLink) {
    forgotPasswordLink.addEventListener("click", (e) => {
        e.preventDefault();
        showForgotPanel();
    });
}

if (backToLoginLink) {
    backToLoginLink.addEventListener("click", (e) => {
        e.preventDefault();
        showLoginPanel();
    });
}

async function sendResetCode(email) {
    const fd = new FormData();
    fd.append("gmail_email", email);
    return apiPostForm("/api/forgot-password", fd);
}

if (forgotForm) {
    forgotForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const email = document.getElementById("forgotEmail").value.trim();
        if (!email) {
            showForgotMessage(forgotMessage, "Enter your Gmail address.", false);
            return;
        }
        showForgotMessage(forgotMessage, "Sending code…");
        const result = await sendResetCode(email);
        if (result.success) {
            _forgotEmail = email;
            showForgotMessage(forgotMessage, result.message, true);
            forgotStep1.style.display = "none";
            forgotStep2.style.display = "";
        } else {
            showForgotMessage(forgotMessage, result.message, false);
        }
    });
}

if (resendCodeLink) {
    resendCodeLink.addEventListener("click", async (e) => {
        e.preventDefault();
        if (!_forgotEmail) return;
        showForgotMessage(resetMessage, "Resending…");
        const result = await sendResetCode(_forgotEmail);
        showForgotMessage(resetMessage, result.message, result.success);
    });
}

if (resetForm) {
    resetForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        if (!_forgotEmail) {
            showForgotMessage(resetMessage, "Enter your email and request a code first.", false);
            return;
        }
        const otp = document.getElementById("resetOtp").value.trim();
        const newPassword = document.getElementById("resetNewPassword").value;
        const fd = new FormData();
        fd.append("gmail_email", _forgotEmail);
        fd.append("otp", otp);
        fd.append("new_password", newPassword);
        showForgotMessage(resetMessage, "Resetting…");
        const result = await apiPostForm("/api/reset-password", fd);
        showForgotMessage(resetMessage, result.message, result.success);
        if (result.success) {
            setTimeout(() => showLoginPanel(), 2000);
        }
    });
}

loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    
    const formData = new FormData();
    formData.append("gmail_email", document.getElementById("gmailEmail").value);
    formData.append("password", document.getElementById("loginPassword").value);
    
    const result = await apiPostForm("/api/login", formData);
    if (result.success) {
        showMessage(result.message || "Login successful.");
        // Redirect based on subscription status
        const redirectUrl = result.redirect || "/subscription";
        setTimeout(() => {
            window.location.href = redirectUrl;
        }, 1000);
    } else {
        showMessage(result.message || "Login failed.", false);
    }
});
