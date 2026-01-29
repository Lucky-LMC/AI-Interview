// AI模拟面试系统v1.0，作者刘梦畅
// ========== API 请求模块 ==========

// 注册 API
async function registerAPI(username, password) {
    return await callAPI(`${AUTH_API_URL}/register`, {
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

// 显示成功信息
function showSuccess(message) {
    alert(message);
}

// 处理注册
async function handleRegister() {
    const username = document.getElementById('register-username').value.trim();
    const password = document.getElementById('register-password').value;

    if (!username || !password) {
        showError('register-error', '请输入用户名和密码');
        return;
    }

    if (username.length < 3 || password.length < 3) {
        showError('register-error', '用户名和密码至少需要3个字符');
        return;
    }

    showLoading('正在注册...');

    try {
        const result = await registerAPI(username, password);

        hideLoading();
        showSuccess(result.message || '注册成功，请登录');
        setTimeout(() => {
            window.location.href = 'index.html';
        }, 1000);
    } catch (error) {
        hideLoading();
        showError('register-error', `注册失败：${error.message}`);
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

    // 绑定注册表单
    const registerForm = document.getElementById('register-form');
    registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        await handleRegister();
    });

    // 回车键注册
    document.getElementById('register-password').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            registerForm.dispatchEvent(new Event('submit'));
        }
    });
});
