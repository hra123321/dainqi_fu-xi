// =============================================
//  共享应用逻辑 — 所有页面共用
// =============================================
// 【作用】
// 1. 主题切换（暗色/亮色模式，自动保存到 localStorage）
// 2. 导航栏激活状态
// 3. 学科选择器初始化
// 4. Toast 通知系统
// 5. 页面加载动画

// ========== 1. 主题切换 ==========
// 【原理】
// - 读取 localStorage 中保存的主题偏好
// - 有则应用，没有则跟随系统设置
// - 切换时同时保存到 localStorage

function initTheme() {
    const savedTheme = localStorage.getItem("theme");
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;

    if (savedTheme === "dark" || (!savedTheme && prefersDark)) {
        document.body.classList.add("dark");
    }

    // 监听系统主题变化
    window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", (e) => {
        if (!localStorage.getItem("theme")) {  // 用户没有手动设置过才跟随系统
            if (e.matches) {
                document.body.classList.add("dark");
            } else {
                document.body.classList.remove("dark");
            }
        }
    });
}

function toggleTheme() {
    document.body.classList.toggle("dark");
    const isDark = document.body.classList.contains("dark");
    localStorage.setItem("theme", isDark ? "dark" : "light");
    
    // 更新按钮图标
    const btn = document.querySelector(".theme-toggle");
    if (btn) {
        btn.textContent = isDark ? "☀️" : "🌙";
    }
}

// ========== 2. 导航栏激活状态 ==========
// 【原理】
// 获取当前页面路径，给对应的导航链接加 active 类

function initNavigation() {
    const currentPath = window.location.pathname;
    document.querySelectorAll(".nav-link").forEach(link => {
        const href = link.getAttribute("href");
        if (href === currentPath || (currentPath === "/" && href === "/")) {
            link.classList.add("active");
        } else if (currentPath.startsWith(href) && href !== "/") {
            link.classList.add("active");
        }
    });
}

// ========== 3. 学科选择器 ==========
// 【原理】
// 找到页面中的学科选择器下拉框，填入学科选项
// 选择学科后保存到 localStorage，所有页面共享

function initSubjectSelector() {
    const select = document.getElementById("subjectSelector");
    if (!select) return;

    // 清空并填充选项
    select.innerHTML = SUBJECTS.map(s => 
        `<option value="${s.id}">${s.icon} ${s.name}</option>`
    ).join("");

    // 恢复上次选择的学科
    const saved = localStorage.getItem("selectedSubject");
    if (saved) {
        select.value = saved;
    }

    // 选择变化时保存
    select.addEventListener("change", (e) => {
        localStorage.setItem("selectedSubject", e.target.value);
        // 触发自定义事件，其他组件可以监听
        document.dispatchEvent(new CustomEvent("subjectChanged", {
            detail: findSubject(e.target.value)
        }));
    });
}

// ========== 4. Toast 通知系统 ==========
// 【原理】
// 在页面右上角显示临时通知消息，几秒后自动消失
// 不需要修改 HTML 结构，JS 动态创建和移除

function showToast(message, type = "info", duration = 3000) {
    // 如果还没创建容器，先创建一个
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

    // 创建 toast 元素
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

    // 根据类型设置颜色
    const colors = {
        success: { bg: "#f0fdf4", text: "#16a34a", border: "#bbf7d0" },
        error: { bg: "#fef2f2", text: "#dc2626", border: "#fecaca" },
        warning: { bg: "#fffbeb", text: "#d97706", border: "#fde68a" },
        info: { bg: "#eff6ff", text: "#2563eb", border: "#bfdbfe" },
    };

    const c = colors[type] || colors.info;
    toast.style.background = c.bg;
    toast.style.color = c.text;
    toast.style.border = `1px solid ${c.border}`;
    toast.textContent = message;

    container.appendChild(toast);

    // 自动移除
    setTimeout(() => {
        toast.style.animation = "fadeIn 0.3s ease reverse";
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

// ========== 5. 页面加载完成后的初始化 ==========
// 【DOMContentLoaded】在页面 HTML 加载完成后执行
// 比 window.onload 更早触发（不用等图片加载完）

document.addEventListener("DOMContentLoaded", () => {
    initTheme();
    initNavigation();
    initSubjectSelector();

    // 添加 fade-in 动画到所有卡片
    document.querySelectorAll(".card").forEach((card, i) => {
        card.style.animation = `fadeIn 0.3s ease ${i * 0.05}s both`;
    });
});

// ========== 6. 加载状态管理 ==========
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
