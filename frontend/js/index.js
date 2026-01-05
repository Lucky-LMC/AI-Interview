// AI模拟面试系统v1.0，作者刘梦畅
// ========== API 请求模块 ==========

const AUTH_API_URL = 'http://localhost:8000/api/auth';
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
            const error = await response.json();
            throw new Error(error.detail || '请求失败');
        }
        
        return await response.json();
    } catch (error) {
        if (error.message === 'Failed to fetch') {
            throw new Error('无法连接到后端服务，请确保后端服务已启动');
        }
        throw error;
    }
}

// 登录 API
async function loginAPI(username, password) {
    return await callAPI(`${AUTH_API_URL}/login`, {
        method: 'POST',
        body: JSON.stringify({
            user_name: username,
            password: password
        })
    });
}

// ============================================
// ========== UI 交互和工具函数 ==========
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

// 显示错误信息
function showError(elementId, message) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = message;
        element.classList.add('show');
        setTimeout(() => {
            element.classList.remove('show');
        }, 5000);
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

// 保存记住的用户名和密码
function saveRememberedCredentials(username, password) {
    localStorage.setItem('remembered_username', username);
    localStorage.setItem('remembered_password', password);
}

// 获取记住的用户名和密码
function getRememberedCredentials() {
    const username = localStorage.getItem('remembered_username');
    const password = localStorage.getItem('remembered_password');
    return {
        username: username || '',
        password: password || ''
    };
}

// 清除记住的用户名和密码
function clearRememberedCredentials() {
    localStorage.removeItem('remembered_username');
    localStorage.removeItem('remembered_password');
}

// 处理登录
async function handleLogin() {
    const username = document.getElementById('login-username').value.trim();
    const password = document.getElementById('login-password').value;
    const rememberPassword = document.getElementById('remember-password').checked;
    
    if (!username || !password) {
        showError('login-error', '请输入用户名和密码');
        return;
    }
    
    showLoading('正在登录...');
    
    try {
        const result = await loginAPI(username, password);
        
        // 保存认证信息到 sessionStorage
        saveAuth({
            isAuthenticated: true,
            userName: result.user_name
        });
        
        // 如果勾选了记住密码，保存用户名和密码到输入框
        if (rememberPassword) {
            saveRememberedCredentials(username, password);
        } else {
            // 如果没有勾选，清除之前记住的用户名和密码
            clearRememberedCredentials();
        }
        
        hideLoading();
        window.location.href = 'main.html';
    } catch (error) {
        hideLoading();
        showError('login-error', `登录失败：${error.message}`);
    }
}

// ============================================
// ========== 页面初始化 ==========
// ============================================

document.addEventListener('DOMContentLoaded', () => {
    // 检查是否已登录
    const auth = getAuth();
    if (auth && auth.isAuthenticated) {
        window.location.href = 'main.html';
        return;
    }

    // 加载记住的用户名和密码
    const remembered = getRememberedCredentials();
    if (remembered.username) {
        document.getElementById('login-username').value = remembered.username;
        // 如果记住了密码，自动勾选"记住密码"复选框
        if (remembered.password) {
            document.getElementById('login-password').value = remembered.password;
            document.getElementById('remember-password').checked = true;
        }
    }

    // 绑定登录表单
    const loginForm = document.getElementById('login-form');
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        await handleLogin();
    });

    // 回车键登录
    document.getElementById('login-password').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            loginForm.dispatchEvent(new Event('submit'));
        }
    });
});
