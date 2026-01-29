// 智能面试助手 - 前端交互逻辑
// 适配新版 UI (SideBar Layout)

// DOM 元素
const messagesContainer = document.getElementById('messages-container');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const newChatBtn = document.getElementById('new-agent-chat-btn');
const historyContainer = document.getElementById('agent-chat-history');
const loadingOverlay = document.getElementById('loading-overlay');

// 本地存储 key
const STORAGE_KEY = 'agent_chat_sessions';
let currentSessionId = null;

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    initAuth();
    setupEventListeners();
    createNewSession(false); //如果不强制新建，则加载最近一次会话
    checkInputEmpty(); // 初始化按钮状态
});

// 初始化用户信息
function initAuth() {
    const auth = getAuth();
    if (auth && auth.userName) {
        const userNameDisplay = document.getElementById('user-name-display');
        const userAvatarText = document.getElementById('user-avatar-text');
        if (userNameDisplay) userNameDisplay.textContent = auth.userName;
        if (userAvatarText) userAvatarText.textContent = auth.userName.charAt(0).toUpperCase();
    }
}

// 设置事件监听器
function setupEventListeners() {
    // 发送按钮点击
    sendBtn.addEventListener('click', handleSendMessage);

    // 回车发送
    userInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    });

    // 自动调整高度
    userInput.addEventListener('input', () => {
        userInput.style.height = 'auto';
        userInput.style.height = Math.min(userInput.scrollHeight, 200) + 'px';
        checkInputEmpty();
    });

    // 新建会话
    newChatBtn.addEventListener('click', () => {
        createNewSession(true);
    });
}

function checkInputEmpty() {
    const val = userInput.value.trim();
    if (val) {
        sendBtn.disabled = false;
        sendBtn.style.opacity = '1';
        sendBtn.style.cursor = 'pointer';
    } else {
        sendBtn.disabled = true;
        sendBtn.style.opacity = '0.5';
        sendBtn.style.cursor = 'not-allowed';
    }
}

// 获取所有会话
function getSessions() {
    const json = localStorage.getItem(STORAGE_KEY);
    return json ? JSON.parse(json) : [];
}

// 保存所有会话
function saveSessions(sessions) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions));
}

// 创建新会话
function createNewSession(forceNew = true) {
    let sessions = getSessions();

    // 如果不强制新建，且最近有一个空会话或刚开始的会话，就复用它
    if (!forceNew && sessions.length > 0) {
        loadSession(sessions[0].id);
        return;
    }

    const newSession = {
        id: Date.now().toString(),
        title: '新咨询会话',
        timestamp: new Date().toISOString(),
        messages: [{
            type: 'ai',
            content: '你好！我是您的专业面试顾问。我可以帮您解答面试流程、分享 STAR 法则技巧，或者为您搜寻最新的行业面试题。请问有什么可以帮您？'
        }]
    };

    sessions.unshift(newSession); // 加到最前
    saveSessions(sessions);
    loadSession(newSession.id);
}

// 加载会话
function loadSession(sessionId) {
    currentSessionId = sessionId;
    const sessions = getSessions();
    const session = sessions.find(s => s.id === sessionId);

    if (!session) return;

    // 清空界面
    messagesContainer.innerHTML = '';

    // 渲染消息
    session.messages.forEach(msg => {
        addMessageToUI(msg.type, msg.content, false); // false = 不保存，因为已经保存过了
    });

    // 更新侧边栏高亮
    renderHistoryList();
    scrollToBottom();
}

// 渲染历史列表
function renderHistoryList() {
    const sessions = getSessions();
    historyContainer.innerHTML = '';

    if (sessions.length === 0) return;

    const section = document.createElement('div');
    section.className = 'history-section';
    section.innerHTML = '<div class="history-title">最近咨询</div>';

    sessions.forEach(session => {
        const item = document.createElement('div');
        item.className = `chat-item ${session.id === currentSessionId ? 'active' : ''}`;

        // 格式化时间
        const date = new Date(session.timestamp);
        const timeStr = `${date.getMonth() + 1}/${date.getDate()} ${date.getHours()}:${String(date.getMinutes()).padStart(2, '0')}`;

        item.innerHTML = `
            <div>
                <span class="chat-title">${session.title}</span>
                <button class="chat-menu-btn" title="删除" onclick="deleteSession(event, '${session.id}')">×</button>
            </div>
            <span class="chat-meta">${timeStr}</span>
        `;

        item.addEventListener('click', (e) => {
            // 防止点击删除按钮时触发
            if (!e.target.classList.contains('chat-menu-btn')) {
                loadSession(session.id);
            }
        });

        section.appendChild(item);
    });

    historyContainer.appendChild(section);
}

// 删除会话
window.deleteSession = function (event, sessionId) {
    event.stopPropagation();
    if (!confirm('确定删除这条记录吗？')) return;

    let sessions = getSessions();
    sessions = sessions.filter(s => s.id !== sessionId);
    saveSessions(sessions);

    if (currentSessionId === sessionId) {
        createNewSession(true); // 如果删除了当前会话，新建一个
    } else {
        renderHistoryList(); // 仅刷新列表
    }
};

// 发送消息处理
async function handleSendMessage() {
    const message = userInput.value.trim();
    if (!message) return;

    // 1. UI 显示用户消息
    addMessageToUI('user', message, true);
    userInput.value = '';
    userInput.style.height = 'auto';
    checkInputEmpty();

    // 2. 更新会话标题（如果是第一条用户消息）
    updateSessionTitleIfNeeded(message);

    // 3. 显示加载
    showLoading();

    try {
        const auth = getAuth();
        const response = await fetch(`${API_BASE_URL.replace('/api/interview', '/api/customer-service')}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                user_name: auth ? auth.userName : 'User'
            })
        });

        const data = await response.json();
        hideLoading();

        if (data.success) {
            addMessageToUI('ai', data.reply, true);
        } else {
            addMessageToUI('ai', '抱歉，服务暂时不可用。', true);
        }

    } catch (error) {
        console.error(error);
        hideLoading();
        addMessageToUI('ai', '网络连接出现问题。', true);
    }
}

// 更新标题
function updateSessionTitleIfNeeded(firstUserMessage) {
    const sessions = getSessions();
    const session = sessions.find(s => s.id === currentSessionId);
    if (session && session.title === '新咨询会话') {
        // 截取前 15 个字符作为标题
        session.title = firstUserMessage.substring(0, 15) + (firstUserMessage.length > 15 ? '...' : '');
        saveSessions(sessions);
        renderHistoryList();
    }
}

// 添加消息到 UI 并保存
function addMessageToUI(type, content, shouldSave = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}-message`;

    // 头像
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    if (type === 'ai') {
        avatar.style.background = 'linear-gradient(135deg, #11998e 0%, #38ef7d 100%)'; // AI 绿色
        avatar.textContent = '🤖';
    } else {
        avatar.textContent = getAuth()?.userName?.charAt(0).toUpperCase() || 'U';
    }

    // 内容气泡
    // 内容气泡
    const messageContent = document.createElement('div');
    // 如果是 AI 消息且包含 Markdown，添加 markdown-document 类以启用 GitHub 风格样式
    const isMarkdown = typeof marked !== 'undefined' && (content.includes('#') || content.includes('*') || content.includes('-'));
    if (type === 'ai' && isMarkdown) {
        messageContent.className = 'message-content markdown-document';
    } else {
        messageContent.className = 'message-content';
    }

    messageContent.style.boxShadow = 'none';

    // 如果不是 markdown document，保留边框；markdown document 自带样式
    if (!messageContent.classList.contains('markdown-document')) {
        messageContent.style.border = '1px solid #e1e4e8';
    }

    const messageText = document.createElement('div');
    messageText.className = 'message-text';

    if (isMarkdown) {
        messageText.innerHTML = marked.parse(content);
    } else {
        messageText.innerHTML = content.replace(/\n/g, '<br>');
    }

    messageContent.appendChild(messageText);
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(messageContent);
    messagesContainer.appendChild(messageDiv);

    scrollToBottom();

    if (shouldSave) {
        saveMessageToStorage(type, content);
    }
}

// 保存消息到 Storage
function saveMessageToStorage(type, content) {
    const sessions = getSessions();
    const session = sessions.find(s => s.id === currentSessionId);
    if (session) {
        session.messages.push({ type, content });
        // 更新时间戳
        session.timestamp = new Date().toISOString();
        // 移到最前（最近更新）
        const index = sessions.indexOf(session);
        sessions.splice(index, 1);
        sessions.unshift(session);

        saveSessions(sessions);
        renderHistoryList();
    }
}

function showLoading() { loadingOverlay.classList.remove('hidden'); }
function hideLoading() { loadingOverlay.classList.add('hidden'); }
function scrollToBottom() { messagesContainer.scrollTop = messagesContainer.scrollHeight; }
