// AI模拟面试系统v1.0，作者刘梦畅
// ========== API 请求模块 ==========

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
        window.location.href = 'interview.html';
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
        window.location.href = 'interview.html';
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
