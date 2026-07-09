const loginForm = document.getElementById("loginForm");
const loginMessage = document.getElementById("loginMessage");
const passwordToggleButton = document.getElementById("passwordToggleButton");

async function apiPostForm(path, formData) {
    const response = await fetch(path, {
        method: "POST",
        body: formData,
    });
    const result = await response.json();
    if (!response.ok) {
        return { success: false, message: result.detail || result.message || "Request failed." };
    }
    return result;
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

function showMessage(text, success = true) {
    loginMessage.textContent = text;
    loginMessage.className = `message ${success ? "success" : "error"}`;
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
