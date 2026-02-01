// 智能面试助手 - 前端交互逻辑
// 适配新版 UI (SideBar Layout)

// DOM 元素
const messagesContainer = document.getElementById('messages-container');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const newChatBtn = document.getElementById('new-agent-chat-btn');
const historyContainer = document.getElementById('agent-chat-history');
const loadingOverlay = document.getElementById('loading-overlay');

// 当前会话ID
let currentSessionId = null;

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    initAuth();
    setupEventListeners();
    loadMostRecentSession(); // 改为加载最近的会话，如果没有则显示空白
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

// 加载最近的会话（如果有）
async function loadMostRecentSession() {
    // 不自动加载历史会话，始终显示新对话
    // 用户可以通过点击左侧历史记录来加载
    
    // 渲染历史记录列表
    await renderHistoryList();
    
    // 显示欢迎消息（不保存到后端）
    showWelcomeMessage();
}

// 显示欢迎消息（不保存到后端）
function showWelcomeMessage() {
    messagesContainer.innerHTML = '';
    addMessageToUI('ai', '你好！我是您的专业面试顾问。我可以帮您解答面试流程、分享 STAR 法则技巧，或者为您搜寻最新的行业面试题。请问有什么可以帮您？', false);
}

// 创建新会话
function createNewSession(forceNew = true) {
    // 清空当前会话
    currentSessionId = null;
    messagesContainer.innerHTML = '';
    
    // 显示欢迎消息（不保存）
    showWelcomeMessage();
    
    // 刷新历史列表
    renderHistoryList();
}

// 加载会话（已废弃，保留空函数以防报错）
function loadSession(sessionId) {
    console.warn('loadSession is deprecated');
}

// 渲染历史列表
async function renderHistoryList() {
    // 防止重复请求
    if (renderHistoryList.isLoading) return;
    renderHistoryList.isLoading = true;
    
    historyContainer.innerHTML = '';

    try {
        // 从后端获取记录
        const auth = getAuth();
        const response = await fetch(`${API_BASE_URL.replace('/api/interview', '/api/customer-service')}/records`, {
            headers: {
                'X-User-Name': auth ? auth.userName : ''
            }
        });

        if (!response.ok) {
            console.warn('获取顾问记录失败');
            return;
        }

        const data = await response.json();
        const records = data.records || [];

        if (records.length === 0) return;

        // 按时间分组：今天、昨天、前天、7天内、30天内、更早
        const now = new Date();
        const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
        
        const groups = {
            '今天': [],
            '昨天': [],
            '前天': [],
            '7天内': [],
            '30天内': [],
            '更早': []
        };

        records.forEach(record => {
            const recordDate = new Date(record.updated_at || record.created_at);
            const recordDay = new Date(recordDate.getFullYear(), recordDate.getMonth(), recordDate.getDate());
            
            const daysDiff = Math.floor((today - recordDay) / (1000 * 60 * 60 * 24));
            
            if (daysDiff === 0) {
                groups['今天'].push(record);
            } else if (daysDiff === 1) {
                groups['昨天'].push(record);
            } else if (daysDiff === 2) {
                groups['前天'].push(record);
            } else if (daysDiff <= 7) {
                groups['7天内'].push(record);
            } else if (daysDiff <= 30) {
                groups['30天内'].push(record);
            } else {
                groups['更早'].push(record);
            }
        });

        // 按顺序渲染各个分组
        const groupOrder = ['今天', '昨天', '前天', '7天内', '30天内', '更早'];
        groupOrder.forEach(groupName => {
            const groupRecords = groups[groupName];
            if (groupRecords.length > 0) {
                const section = document.createElement('div');
                section.className = 'history-section';
                section.innerHTML = `<div class="history-title">${groupName}</div>`;

                groupRecords.forEach(record => {
                    const item = createRecordItem(record);
                    section.appendChild(item);
                });

                historyContainer.appendChild(section);
            }
        });

    } catch (error) {
        console.error('获取顾问记录失败:', error);
    } finally {
        renderHistoryList.isLoading = false;
    }
}

// 创建记录项
function createRecordItem(record) {
    const item = document.createElement('div');
    item.className = `chat-item ${record.thread_id === currentSessionId ? 'active' : ''}`;

    // 使用后端返回的标题
    const title = record.title || '新咨询会话';

    // 格式化时间
    const timeStr = record.updated_at || record.created_at;
    const date = new Date(timeStr);
    const displayTime = `${date.getMonth() + 1}/${date.getDate()} ${date.getHours()}:${String(date.getMinutes()).padStart(2, '0')}`;

    item.innerHTML = `
        <div>
            <span class="chat-title">${title}</span>
            <button class="chat-menu-btn chat-delete-btn" title="删除">×</button>
        </div>
        <span class="chat-meta">${displayTime}</span>
    `;

    // 点击加载会话
    item.addEventListener('click', (e) => {
        if (!e.target.classList.contains('chat-menu-btn')) {
            loadSessionFromBackend(record.thread_id);
        }
    });

    // 删除按钮
    const deleteBtn = item.querySelector('.chat-delete-btn');
    deleteBtn.addEventListener('click', async (e) => {
        e.stopPropagation();
        await handleDeleteSessionFromBackend(record.thread_id);
    });

    return item;
}

// 从后端加载会话
async function loadSessionFromBackend(threadId) {
    try {
        showLoading();
        const auth = getAuth();
        const response = await fetch(`${API_BASE_URL.replace('/api/interview', '/api/customer-service')}/records/${threadId}`, {
            headers: {
                'X-User-Name': auth ? auth.userName : ''
            }
        });

        if (!response.ok) {
            throw new Error('加载会话失败');
        }

        const data = await response.json();
        currentSessionId = threadId;

        // 清空界面
        messagesContainer.innerHTML = '';

        // 渲染消息
        if (data.messages && data.messages.length > 0) {
            data.messages.forEach(msg => {
                const type = msg.role === 'human' ? 'user' : 'ai';
                addMessageToUI(type, msg.content, false);
            });
        }

        hideLoading();
        renderHistoryList();
        scrollToBottom();

    } catch (error) {
        hideLoading();
        console.error('加载会话失败:', error);
        alert('加载会话失败');
    }
}

// 从后端删除会话
async function handleDeleteSessionFromBackend(threadId) {
    if (!confirm('确定要删除这条记录吗？删除后无法恢复！')) return;

    try {
        showLoading();
        const auth = getAuth();
        const response = await fetch(`${API_BASE_URL.replace('/api/interview', '/api/customer-service')}/records/${threadId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'X-User-Name': auth ? auth.userName : ''
            }
        });

        if (!response.ok) {
            throw new Error('删除失败');
        }

        hideLoading();

        // 如果删除了当前会话，新建一个
        if (currentSessionId === threadId) {
            createNewSession(true);
        } else {
            renderHistoryList();
        }

    } catch (error) {
        hideLoading();
        console.error('删除失败:', error);
        alert(`删除失败：${error.message}`);
    }
}

// 发送消息处理
async function handleSendMessage() {
    const message = userInput.value.trim();
    if (!message) return;

    // 1. UI 显示用户消息
    addMessageToUI('user', message, true);
    userInput.value = '';
    userInput.style.height = 'auto';
    checkInputEmpty();

    // 2. 显示加载
    showLoading();

    try {
        const auth = getAuth();
        const response = await fetch(`${API_BASE_URL.replace('/api/interview', '/api/customer-service')}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-User-Name': auth ? auth.userName : ''
            },
            body: JSON.stringify({
                message: message,
                thread_id: currentSessionId, // 使用当前会话ID（如果是新会话则为null）
                user_name: auth ? auth.userName : 'User'
            })
        });

        const data = await response.json();
        hideLoading();

        if (data.success) {
            // 保存后端返回的 thread_id
            if (data.thread_id) {
                currentSessionId = data.thread_id;
            }

            addMessageToUI('ai', data.reply, true);
            
            // 刷新左侧历史记录列表
            renderHistoryList();
        } else {
            addMessageToUI('ai', '抱歉，服务暂时不可用。', true);
        }

    } catch (error) {
        console.error(error);
        hideLoading();
        addMessageToUI('ai', '网络连接出现问题。', true);
    }
}

// 添加消息到 UI（不再保存到本地存储）
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
    
    // shouldSave 参数已废弃，不再保存到本地存储
}

function showLoading() { loadingOverlay.classList.remove('hidden'); }
function hideLoading() { loadingOverlay.classList.add('hidden'); }
function scrollToBottom() { messagesContainer.scrollTop = messagesContainer.scrollHeight; }
