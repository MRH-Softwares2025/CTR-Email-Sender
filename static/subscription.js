const subscriptionStatus = document.getElementById("subscriptionStatus");
const expiryDate = document.getElementById("expiryDate");
const daysLeft = document.getElementById("daysLeft");
const subscriptionNote = document.getElementById("subscriptionNote");
const payButton = document.getElementById("payButton");
const mpesaPhone = document.getElementById("mpesaPhone");
const subscriptionMessage = document.getElementById("subscriptionMessage");
const sendPageLink = document.getElementById("sendPageLink");
const resetButton = document.getElementById("resetButton");
const plansContainer = document.getElementById("plansContainer");
const selectedPlanInfo = document.getElementById("selectedPlanInfo");
const planName = document.getElementById("planName");
const manualConfirmSection = document.getElementById("manualConfirmSection");
const checkoutRequestIdElement = document.getElementById("checkoutRequestId");
const confirmPaymentButton = document.getElementById("confirmPaymentButton");

let selectedPlan = null;
let plans = [];
let activeCheckoutRequestId = null;

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

function showMessage(text, success = true) {
    subscriptionMessage.textContent = text;
    subscriptionMessage.className = `message ${success ? "success" : "error"}`;
}

function updateSubscriptionUI(data) {
    const isRequired = data.subscription_required !== false;
    if (data.active) {
        subscriptionStatus.textContent = "Active";
        subscriptionStatus.className = "status active";
        subscriptionNote.textContent = "Subscription is active. You can continue to send emails.";
        sendPageLink.style.display = "inline-block";
        if (data.plan) {
            planName.textContent = `${data.plan.name} (KES ${data.plan.price})`;
        }
    } else if (isRequired) {
        subscriptionStatus.textContent = "Inactive";
        subscriptionStatus.className = "status inactive";
        subscriptionNote.textContent = "Subscription is required before sending emails.";
        sendPageLink.style.display = "none";
        planName.textContent = "—";
    } else {
        subscriptionStatus.textContent = "Not required";
        subscriptionStatus.className = "status active";
        subscriptionNote.textContent = "Subscription gating is disabled for development.";
        sendPageLink.style.display = "inline-block";
        planName.textContent = "—";
    }
    expiryDate.textContent = data.expiry || "Not set";
    daysLeft.textContent = data.days_left ?? 0;
}

async function loadPlans() {
    try {
        const result = await apiGet("/api/plans");
        console.log("Plans API result:", result);
        if (result.success !== false && result.plans) {
            plans = result.plans;
            renderPlans();
        } else {
            plansContainer.innerHTML = "<p>Failed to load plans. Please try refreshing the page.</p>";
        }
    } catch (error) {
        console.error("Error loading plans:", error);
        plansContainer.innerHTML = "<p>Error loading plans. Please check your connection.</p>";
    }
}

function renderPlans() {
    if (plans.length === 0) {
        plansContainer.innerHTML = "<p>No plans available</p>";
        return;
    }

    plansContainer.innerHTML = plans.map((plan, index) => {
        const isRecommended = plan.name === "Monthly";
        return `
            <div class="plan-card ${isRecommended ? 'recommended' : ''}" data-plan-id="${plan.id}">
                <div class="plan-name">${plan.name}</div>
                <div class="plan-price">KES ${plan.price}</div>
                <div class="plan-duration">${plan.duration_days} day${plan.duration_days > 1 ? 's' : ''}</div>
                <div class="plan-description">${plan.description}</div>
            </div>
        `;
    }).join("");

    // Add click handlers for plan selection
    document.querySelectorAll('.plan-card').forEach(card => {
        card.addEventListener('click', () => {
            const planId = parseInt(card.dataset.planId);
            selectPlan(planId);
        });
    });
}

function selectPlan(planId) {
    selectedPlan = plans.find(p => p.id === planId);
    
    // Update UI
    document.querySelectorAll('.plan-card').forEach(card => {
        card.classList.remove('selected');
        if (parseInt(card.dataset.planId) === planId) {
            card.classList.add('selected');
        }
    });

    // Enable pay button and show selected plan info
    if (selectedPlan) {
        payButton.disabled = false;
        selectedPlanInfo.textContent = `Selected: ${selectedPlan.name} - KES ${selectedPlan.price} for ${selectedPlan.duration_days} day${selectedPlan.duration_days > 1 ? 's' : ''}`;
    }
}

async function loadSubscriptionState() {
    const subscription = await apiGet("/api/subscription");
    updateSubscriptionUI(subscription);
}

payButton.addEventListener("click", async () => {
    const phoneNumber = mpesaPhone.value.trim();
    if (!phoneNumber) {
        showMessage("Enter a valid MPESA phone number first.", false);
        return;
    }
    if (!selectedPlan) {
        showMessage("Please select a plan first.", false);
        return;
    }
    const result = await apiPost("/api/subscription/pay", { 
        phone_number: phoneNumber,
        plan_id: selectedPlan.id
    });
    if (result.success) {
        activeCheckoutRequestId = result.checkout_request_id || null;
        checkoutRequestIdElement.textContent = activeCheckoutRequestId || "—";
        manualConfirmSection.style.display = "block";
        showMessage(result.message || "Payment initiated. Please check your phone to complete the payment.");
        await loadSubscriptionState();
    } else {
        showMessage(result.message || "Payment initiation failed.", false);
    }
});

if (confirmPaymentButton) {
    confirmPaymentButton.addEventListener("click", async () => {
        if (!activeCheckoutRequestId) {
            showMessage("No pending payment request to confirm.", false);
            return;
        }
        const confirmResult = await apiPost("/api/subscription/confirm", {
            checkout_request_id: activeCheckoutRequestId,
            status: "success",
            message: "Manual confirmation from the app",
        });
        if (confirmResult.success) {
            showMessage(confirmResult.message || "Subscription activated successfully.");
            manualConfirmSection.style.display = "none";
            activeCheckoutRequestId = null;
            await loadSubscriptionState();
        } else {
            showMessage(confirmResult.message || "Payment confirmation failed.", false);
        }
    });
}

if (resetButton) {
    resetButton.addEventListener("click", async () => {
        const result = await apiPost("/api/reset", {});
        if (result.success) {
            window.location.href = "/login";
        } else {
            showMessage(result.message || "Reset failed.", false);
        }
    });
}

const logoutButton = document.getElementById("logoutButton");
if (logoutButton) {
    logoutButton.addEventListener("click", async () => {
        const result = await apiPost("/api/logout", {});
        if (result.success) {
            window.location.href = result.redirect || "/login";
        }
    });
}

loadSubscriptionState();
loadPlans();
