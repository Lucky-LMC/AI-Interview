// AI模拟面试系统v1.0 - 通用 API 和 工具函数
// 作者：刘梦畅

const API_BASE_URL = 'http://localhost:8000/api/interview';
const AUTH_API_URL = 'http://localhost:8000/api/auth';
// const API_BASE_URL = 'http://172.18.174.107:8000/api/interview';
// const AUTH_API_URL = 'http://172.18.174.107:8000/api/auth';


// 通用 API 调用函数
async function callAPI(url, options = {}) {
    try {
        const response = await fetch(url, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        });

        if (!response.ok) {
            // 尝试解析错误信息，如果解析失败则使用状态文本
            let errorMsg = '请求失败';
            try {
                const error = await response.json();
                errorMsg = error.detail || '请求失败';
            } catch (e) {
                // 某些 500 错误可能返回 HTML 或非 JSON
                errorMsg = `请求失败 (${response.status} ${response.statusText})`;
            }
            throw new Error(errorMsg);
        }

        return await response.json();
    } catch (error) {
        if (error.message === 'Failed to fetch') {
            throw new Error('无法连接到后端服务，请确保后端服务已启动');
        }
        throw error;
    }
}

// ============================================
// ========== UI 工具函数 ====================
// ============================================

// 显示/隐藏加载提示
function showLoading(message = '处理中...') {
    const overlay = document.getElementById('loading-overlay');
    const messageEl = document.getElementById('loading-message');
    if (overlay && messageEl) {
        messageEl.textContent = message;
        overlay.classList.remove('hidden');
    }
}

function hideLoading() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.classList.add('hidden');
    }
}

// 显示错误信息 (支持传入 elementId 或者是用 alert/chat 显示)
function showError(target, message) {
    if (typeof target === 'string') {
        const element = document.getElementById(target);
        if (element) {
            element.textContent = message;
            element.classList.add('show');
            setTimeout(() => {
                element.classList.remove('show');
            }, 5000);
        } else {
            // 如果找不到元素，且是在聊天页面，可能需要调用 addMessage（但这里无法直接调用 main.js 的函数）
            // 所以这里只处理基于 elementId 的错误显示，或者 alert
            alert(`错误: ${message}`);
        }
    } else {
        // 在 main.js 里被重写或者调用
        console.error(message);
        alert(message);
    }
}

// 获取认证信息
function getAuth() {
    const authStr = sessionStorage.getItem('auth');
    return authStr ? JSON.parse(authStr) : null;
}

// 保存认证信息
function saveAuth(auth) {
    sessionStorage.setItem('auth', JSON.stringify(auth));
}

// 清除认证信息
function clearAuth() {
    sessionStorage.removeItem('auth');
}
