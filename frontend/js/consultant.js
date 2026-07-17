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

// 在左侧添加临时会话占位项（用于实时反馈）
function addTemporarySessionToSidebar(threadId, userMessage) {
    // 检查是否已存在
    const existing = historyContainer.querySelector(`[data-thread-id="${threadId}"]`);
    if (existing) return;

    // 查找或创建"今天"分组
    let todaySection = null;
    const sections = historyContainer.querySelectorAll('.history-section');
    for (const section of sections) {
        const titleDiv = section.querySelector('.history-title');
        if (titleDiv && titleDiv.textContent === '今天') {
            todaySection = section;
            break;
        }
    }

    if (!todaySection) {
        todaySection = document.createElement('div');
        todaySection.className = 'history-section';
        todaySection.innerHTML = '<div class="history-title">今天</div>';
        historyContainer.insertBefore(todaySection, historyContainer.firstChild);
    }

    // 创建临时占位项
    const tempItem = document.createElement('div');
    tempItem.className = 'chat-item active';
    tempItem.dataset.threadId = threadId;

    // 生成简短标题（取用户消息的前20个字符）
    const title = userMessage.trim().substring(0, 20) + (userMessage.length > 20 ? '...' : '');
    const now = new Date();
    const timeStr = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`;

    tempItem.innerHTML = `
        <div class="chat-item-title">${title}</div>
        <div class="chat-item-time">${timeStr}</div>
    `;

    tempItem.onclick = () => {
        if (currentSessionId !== threadId) {
            loadSessionFromBackend(threadId);
        }
    };

    // 插入到"今天"分组的最前面（标题之后）
    const firstItem = todaySection.querySelector('.chat-item');
    if (firstItem) {
        todaySection.insertBefore(tempItem, firstItem);
    } else {
        todaySection.appendChild(tempItem);
    }
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
// 工具函数：获取工具显示名称
// ====================================================================
function getToolDisplayName(tool) {
    if (tool === 'knowledge_base' || tool === 'search_knowledge_base') return '🔍 知识库搜索';
    if (tool === 'tavily_search') return '🌐 联网搜索';
    return `🛠️ ${tool}`;
}

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
        let fullText = '';  // 累积完整文本用于实时 Markdown 渲染
        let renderTimeout = null;  // 防抖定时器
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
                                // 立即在左侧添加临时占位项（使用用户输入的消息作为标题）
                                addTemporarySessionToSidebar(event.content, message);
                                break;

                            case 'token':
                                // 追加文本内容
                                fullText += event.content;

                                // 实时渲染 Markdown（每个 token 都立即渲染）
                                if (typeof marked !== 'undefined') {
                                    textDiv.innerHTML = marked.parse(fullText);
                                    contentWrapper.classList.add('markdown-chat');
                                } else {
                                    textDiv.textContent = fullText;
                                }

                                // 如果是第一个token，且有检测到工具，立即更新为工具标记
                                if (fullText.length === event.content.length && detectedTools.size > 0) {
                                    const labels = [];
                                    if (detectedTools.has('knowledge_base')) labels.push('🔍 知识库搜索');
                                    if (detectedTools.has('tavily_search')) labels.push('🌐 联网搜索');

                                    statusDiv.textContent = labels.join('\t\t');
                                    statusDiv.style.cssText = 'font-size: 12px; color: #28a745; margin-bottom: 8px; font-weight: 500;';
                                }

                                // 收到第一个 token 时，立即刷新左侧历史列表（让用户看到会话出现）
                                if (fullText.length === event.content.length) {
                                    renderHistoryList();
                                }

                                scrollToBottom();
                                break;

                            case 'status':
                                // 记录工具使用情况
                                if (event.content) {
                                    if (event.content.includes('知识库')) detectedTools.add('knowledge_base');
                                    if (event.content.includes('联网')) detectedTools.add('tavily_search');
                                }

                                // 实时刷新工具标签栏（显示所有已检测到的工具）
                                if (detectedTools.size > 0) {
                                    const labels = [];
                                    // 保持固定的显示顺序
                                    if (detectedTools.has('knowledge_base')) labels.push('🔍 知识库搜索');
                                    if (detectedTools.has('tavily_search')) labels.push('🌐 联网搜索');

                                    // 如果当前是正在搜索的临时状态且不在已检测列表中（不过上面已经添加了），可以在这里处理动画
                                    // 简单起见，我们直接显示累积的静态标签

                                    statusDiv.textContent = labels.join('\t\t');
                                    statusDiv.style.cssText = 'font-size: 12px; color: #28a745; margin-bottom: 8px; font-weight: 500;';
                                    statusDiv.style.display = 'block';
                                } else {
                                    // 如果没有任何工具，但有临时状态文本（比如"正在..."），显示它
                                    statusDiv.textContent = event.content;
                                    statusDiv.style.cssText = 'font-size: 12px; color: #666; margin-bottom: 5px; font-style: italic;';
                                    statusDiv.style.display = 'block';
                                }
                                break;

                            case 'tool_start':
                                detectedTools.add(event.tool === 'search_knowledge_base' ? 'knowledge_base' : event.tool);
                                statusDiv.textContent = `${getToolDisplayName(event.tool)} 执行中...`;
                                statusDiv.style.display = 'block';
                                break;

                            case 'tool_end':
                                statusDiv.textContent = `${getToolDisplayName(event.tool)} 已完成`;
                                statusDiv.style.display = 'block';
                                break;

                            case 'degraded':
                                statusDiv.textContent = '部分外部能力不可用，已自动切换降级路径';
                                statusDiv.style.cssText = 'font-size: 12px; color: #b7791f; margin-bottom: 8px;';
                                statusDiv.style.display = 'block';
                                break;

                            case 'done':
                                // 流式输出完成
                                // 合并后端返回的 tools_used 和前端检测到的 detectedTools
                                const backendTools = event.tools_used || [];
                                const finalTools = [...new Set([...backendTools, ...detectedTools])];

                                // 如果使用了工具，将临时状态栏改为永久显示的工具标记
                                if (finalTools.length > 0) {
                                    statusDiv.style.cssText = 'font-size: 12px; color: #28a745; margin-bottom: 8px; font-weight: 500;';
                                    // 使用提取的 helper 函数
                                    const toolLabels = finalTools.map(getToolDisplayName);
                                    statusDiv.textContent = toolLabels.join('\t');
                                    statusDiv.style.display = 'block';
                                    // 将工具信息保存到 DOM，方便后续使用
                                    aiMessageDiv.dataset.toolsUsed = JSON.stringify(finalTools);
                                } else {
                                    statusDiv.style.display = 'none';
                                }

                                // 最终渲染 Markdown（确保防抖结束后完整渲染）
                                clearTimeout(renderTimeout);
                                if (typeof marked !== 'undefined' && fullText) {
                                    textDiv.innerHTML = marked.parse(fullText);
                                    // 添加 markdown-chat 类以应用紧凑样式
                                    contentWrapper.classList.add('markdown-chat');
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
    // 如果是 AI 消息且包含 Markdown，添加 markdown-chat 类以启用紧凑样式
    const isMarkdown = typeof marked !== 'undefined' && (content.includes('#') || content.includes('*') || content.includes('-'));
    if (type === 'ai' && isMarkdown) {
        messageContent.className = 'message-content markdown-chat';
    } else {
        messageContent.className = 'message-content';
    }

    messageContent.style.boxShadow = 'none';

    // 保留边框样式
    messageContent.style.border = '1px solid #e1e4e8';

    // 如果是 AI 消息且有工具使用记录，显示工具标记
    if (type === 'ai' && toolsUsed && toolsUsed.length > 0) {
        const toolBadge = document.createElement('div');
        toolBadge.style.cssText = 'font-size: 12px; color: #28a745; margin-bottom: 8px; font-weight: 500;';
        // 使用提取的 helper 函数
        const toolLabels = toolsUsed.map(getToolDisplayName);
        toolBadge.textContent = toolLabels.join('\t\t');
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

// 使用 api.js 中的工具函数
// showLoading, hideLoading, scrollToBottom 等已在 api.js 中定义
function scrollToBottom() { messagesContainer.scrollTop = messagesContainer.scrollHeight; }
