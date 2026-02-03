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

        // 渲染消息（过滤掉空内容的消息）
        if (data.messages && data.messages.length > 0) {
            data.messages.forEach(msg => {
                // 只渲染有内容的消息
                if (msg.content && msg.content.trim()) {
                    const type = msg.role === 'human' ? 'user' : 'ai';
                    // 传递工具使用信息（如果有）
                    addMessageToUI(type, msg.content, false, msg.tools_used);
                }
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

// ====================================================================
// 旧版本（非流式）- 已注释
// ====================================================================
/*
async function handleSendMessage_OLD() {
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
                thread_id: currentSessionId,
                user_name: auth ? auth.userName : 'User'
            })
        });

        const data = await response.json();
        hideLoading();

        if (data.success) {
            if (data.thread_id) {
                currentSessionId = data.thread_id;
            }

            addMessageToUI('ai', data.reply, true);
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
*/

// ====================================================================
// 新版本（流式输出）- 使用 SSE 接收打字机效果
// ====================================================================
async function handleSendMessage() {
    const message = userInput.value.trim();
    if (!message) return;

    // 1. UI 显示用户消息
    addMessageToUI('user', message, true);
    userInput.value = '';
    userInput.style.height = 'auto';
    checkInputEmpty();

    // 2. 创建 AI 消息占位符（用于流式追加内容）
    const aiMessageDiv = document.createElement('div');
    aiMessageDiv.className = 'message ai-message';

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.style.background = 'linear-gradient(135deg, #11998e 0%, #38ef7d 100%)';
    avatar.textContent = 'AI';

    const contentWrapper = document.createElement('div');
    contentWrapper.className = 'message-content';

    // 状态提示区域（显示"正在搜索..."等）
    const statusDiv = document.createElement('div');
    statusDiv.className = 'tool-status';
    statusDiv.style.cssText = 'font-size: 12px; color: #666; margin-bottom: 5px; font-style: italic;';
    contentWrapper.appendChild(statusDiv);

    // 实际内容区域
    const textDiv = document.createElement('div');
    textDiv.className = 'message-text';
    textDiv.style.whiteSpace = 'pre-wrap';
    contentWrapper.appendChild(textDiv);

    aiMessageDiv.appendChild(avatar);
    aiMessageDiv.appendChild(contentWrapper);
    messagesContainer.appendChild(aiMessageDiv);
    scrollToBottom();

    try {
        const auth = getAuth();

        // 添加超时控制
        const controller = new AbortController();
        const timeoutId = setTimeout(() => {
            controller.abort();
            console.error('请求超时');
        }, 60000); // 60秒超时

        const response = await fetch(`${API_BASE_URL.replace('/api/interview', '/api/customer-service')}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-User-Name': auth ? auth.userName : ''
            },
            body: JSON.stringify({
                message: message,
                thread_id: currentSessionId,
                user_name: auth ? auth.userName : 'User'
            }),
            signal: controller.signal
        });

        if (!response.ok) {
            throw new Error(`请求失败: ${response.status}`);
        }

        // 3. 读取流式数据
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        const detectedTools = new Set(); // 累积记录本轮使用的工具

        while (true) {
            const { done, value } = await reader.read();
            if (done) {
                clearTimeout(timeoutId); // 清除超时
                break;
            }

            // 解码数据块
            buffer += decoder.decode(value, { stream: true });

            // 按行分割（SSE 格式是 "data: ...\n\n"）
            const lines = buffer.split('\n');
            buffer = lines.pop(); // 保留最后不完整的行

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const jsonStr = line.slice(6); // 去掉 "data: "
                        const event = JSON.parse(jsonStr);

                        switch (event.type) {
                            case 'thread_id':
                                // 保存后端返回的 thread_id
                                currentSessionId = event.content;
                                break;

                            case 'token':
                                // 追加文本内容（打字机效果）
                                textDiv.textContent += event.content;

                                // 如果是第一个token，且有检测到工具，立即更新为工具标记
                                if (textDiv.textContent.length === event.content.length && detectedTools.size > 0) {
                                    const labels = [];
                                    if (detectedTools.has('knowledge_base')) labels.push('🔍 知识库搜索');
                                    if (detectedTools.has('tavily_search')) labels.push('🌐 联网搜索');

                                    statusDiv.textContent = labels.join(' + ');
                                    statusDiv.style.cssText = 'font-size: 12px; color: #28a745; margin-bottom: 8px; font-weight: 500;';
                                }

                                scrollToBottom();
                                break;

                            case 'status':
                                // 记录工具使用情况
                                if (event.content) {
                                    if (event.content.includes('知识库')) detectedTools.add('knowledge_base');
                                    if (event.content.includes('联网')) detectedTools.add('tavily_search');
                                }

                                // 显示工具调用状态（只有在还没有开始输出内容时才更新状态文本，避免覆盖已生成的"已使用"标签）
                                if (textDiv.textContent.length === 0) {
                                    statusDiv.textContent = event.content;
                                    statusDiv.style.cssText = 'font-size: 12px; color: #666; margin-bottom: 5px; font-style: italic;';
                                    if (!event.content) {
                                        statusDiv.style.display = 'none';
                                    } else {
                                        statusDiv.style.display = 'block';
                                    }
                                }
                                break;

                            case 'done':
                                // 流式输出完成
                                const toolsUsed = event.tools_used || [];

                                // 如果使用了工具，将临时状态栏改为永久显示的工具标记
                                if (toolsUsed.length > 0) {
                                    statusDiv.style.cssText = 'font-size: 12px; color: #28a745; margin-bottom: 8px; font-weight: 500;';
                                    const toolLabels = toolsUsed.map(tool => {
                                        if (tool === 'knowledge_base') return '🔍 知识库搜索';
                                        if (tool === 'tavily_search') return '🌐 联网搜索';
                                        return `🛠️ ${tool}`;
                                    });
                                    statusDiv.textContent = toolLabels.join(' + ');
                                    statusDiv.style.display = 'block';
                                    // 将工具信息保存到 DOM，方便后续使用
                                    aiMessageDiv.dataset.toolsUsed = JSON.stringify(toolsUsed);
                                } else {
                                    statusDiv.style.display = 'none';
                                }

                                // 检测并渲染 Markdown
                                const fullText = textDiv.textContent;
                                const hasMarkdown = /###|##|\*\*|\n-\s|\n\d+\.\s/.test(fullText);

                                if (hasMarkdown && typeof marked !== 'undefined') {
                                    // 渲染 Markdown
                                    textDiv.innerHTML = marked.parse(fullText);
                                    // 添加 markdown-document 类以应用 GitHub 风格
                                    contentWrapper.classList.add('markdown-document');
                                }

                                // 刷新左侧历史列表
                                renderHistoryList();
                                break;

                            case 'error':
                                // 错误处理
                                textDiv.textContent = `❌ 错误：${event.content}`;
                                statusDiv.style.display = 'none';
                                break;
                        }
                    } catch (parseError) {
                        console.warn('解析 SSE 事件失败:', line, parseError);
                    }
                }
            }
        }

    } catch (error) {
        console.error('流式对话错误:', error);
        if (error.name === 'AbortError') {
            textDiv.textContent = '❌ 请求超时，请重试';
        } else {
            textDiv.textContent = `❌ 网络连接出现问题: ${error.message}`;
        }
        statusDiv.style.display = 'none';
    }
}

// 添加消息到 UI（不再保存到本地存储）
function addMessageToUI(type, content, shouldSave = false, toolsUsed = null) {
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

    // 如果是 AI 消息且有工具使用记录，显示工具标记
    if (type === 'ai' && toolsUsed && toolsUsed.length > 0) {
        const toolBadge = document.createElement('div');
        toolBadge.style.cssText = 'font-size: 12px; color: #28a745; margin-bottom: 8px; font-weight: 500;';
        const toolLabels = toolsUsed.map(tool => {
            if (tool === 'knowledge_base') return '🔍 知识库搜索';
            if (tool === 'tavily_search') return '🌐 联网搜索';
            return `🛠️ ${tool}`;
        });
        toolBadge.textContent = toolLabels.join(' + ');
        messageContent.appendChild(toolBadge);
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
