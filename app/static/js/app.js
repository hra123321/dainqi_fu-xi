function initTheme() {
    const savedTheme = localStorage.getItem("theme");
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;

    if (savedTheme === "dark" || (!savedTheme && prefersDark)) {
        document.body.classList.add("dark");
    }

    window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", (event) => {
        if (!localStorage.getItem("theme")) {
            document.body.classList.toggle("dark", event.matches);
        }
    });
}

function toggleTheme() {
    document.body.classList.toggle("dark");
    const isDark = document.body.classList.contains("dark");
    localStorage.setItem("theme", isDark ? "dark" : "light");

    const button = document.querySelector(".theme-toggle");
    if (button) {
        button.textContent = isDark ? "☀️" : "🌙";
    }
}

function initNavigation() {
    const currentPath = window.location.pathname;
    document.querySelectorAll(".nav-link").forEach((link) => {
        const href = link.getAttribute("href");
        if (href === currentPath || (currentPath === "/" && href === "/")) {
            link.classList.add("active");
        } else if (href !== "/" && currentPath.startsWith(href)) {
            link.classList.add("active");
        }
    });
}

function initSubjectSelector() {
    const select = document.getElementById("subjectSelector");
    if (!select) return;

    select.innerHTML = SUBJECTS.map((subject) =>
        `<option value="${subject.id}">${subject.icon} ${subject.name}</option>`
    ).join("");

    const saved = localStorage.getItem("selectedSubject");
    if (saved) {
        select.value = saved;
    } else if (SUBJECTS.length > 0) {
        select.value = SUBJECTS[0].id;
        localStorage.setItem("selectedSubject", SUBJECTS[0].id);
    }

    select.addEventListener("change", (event) => {
        localStorage.setItem("selectedSubject", event.target.value);
        document.dispatchEvent(new CustomEvent("subjectChanged", {
            detail: findSubject(event.target.value)
        }));
    });
}

function showToast(message, type = "info", duration = 3000) {
    let container = document.getElementById("toastContainer");
    if (!container) {
        container = document.createElement("div");
        container.id = "toastContainer";
        container.style.cssText = `
            position: fixed;
            top: 80px;
            right: 20px;
            z-index: 9999;
            display: flex;
            flex-direction: column;
            gap: 8px;
        `;
        document.body.appendChild(container);
    }

    const toast = document.createElement("div");
    toast.style.cssText = `
        padding: 12px 20px;
        border-radius: 10px;
        font-size: 14px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        animation: fadeIn 0.3s ease;
        max-width: 360px;
        display: flex;
        align-items: center;
        gap: 8px;
    `;

    const colors = {
        success: { bg: "#f0fdf4", text: "#16a34a", border: "#bbf7d0" },
        error: { bg: "#fef2f2", text: "#dc2626", border: "#fecaca" },
        warning: { bg: "#fffbeb", text: "#d97706", border: "#fde68a" },
        info: { bg: "#eff6ff", text: "#2563eb", border: "#bfdbfe" },
    };

    const color = colors[type] || colors.info;
    toast.style.background = color.bg;
    toast.style.color = color.text;
    toast.style.border = `1px solid ${color.border}`;
    toast.textContent = message;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = "fadeIn 0.3s ease reverse";
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

function showLoading(containerId, text = "加载中...") {
    const container = document.getElementById(containerId);
    if (!container) return;
    container.innerHTML = `
        <div class="flex-center" style="padding: 40px;">
            <div class="spinner"></div>
            <span style="margin-left: 12px; color: var(--text-muted);">${text}</span>
        </div>
    `;
}

function hideLoading(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    container.innerHTML = "";
}

document.addEventListener("DOMContentLoaded", () => {
    initTheme();
    initNavigation();
    initSubjectSelector();

    document.querySelectorAll(".card").forEach((card, index) => {
        card.style.animation = `fadeIn 0.3s ease ${index * 0.05}s both`;
    });
});
