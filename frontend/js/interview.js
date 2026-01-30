// AI模拟面试系统v1.0，作者刘梦畅
// ========== API 请求模块 ==========

// 开始面试 API
async function startInterviewAPI(file, maxRounds) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('max_rounds', maxRounds);

    const auth = getAuth();

    const response = await fetch(`${API_BASE_URL}/start`, {
        method: 'POST',
        headers: {
            'X-User-Name': auth ? auth.userName : ''
        },
        body: formData
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || '开始面试失败');
    }

    return await response.json();
}

// 提交答案 API（非流式版本）
async function submitAnswerAPI(threadId, answer) {
    // 获取当前登录用户
    const auth = getAuth();
    const requestBody = {
        thread_id: threadId,
        answer: answer,
        user_name: auth.userName
    };

    return await callAPI(`${API_BASE_URL}/submit`, {
        method: 'POST',
        body: JSON.stringify(requestBody)
    });
}

// 获取面试记录列表 API
async function getInterviewRecordsAPI() {
    const auth = getAuth();
    if (!auth || !auth.userName) {
        throw new Error('需要登录');
    }

    return await callAPI(`${API_BASE_URL}/records`, {
        method: 'GET',
        headers: {
            'X-User-Name': auth.userName
        }
    });
}

// 获取面试记录详情 API
async function getInterviewRecordDetailAPI(threadId) {
    const auth = getAuth();
    if (!auth || !auth.userName) {
        throw new Error('需要登录');
    }

    return await callAPI(`${API_BASE_URL}/records/${threadId}`, {
        method: 'GET',
        headers: {
            'X-User-Name': auth.userName
        }
    });
}

// 删除面试记录 API
async function deleteInterviewRecordAPI(threadId) {
    const auth = getAuth();
    if (!auth || !auth.userName) {
        throw new Error('需要登录');
    }

    return await callAPI(`${API_BASE_URL}/records/${threadId}`, {
        method: 'DELETE',
        headers: {
            'X-User-Name': auth.userName
        }
    });
}

// ============================================
// ========== UI 交互和工具函数 ==========
// ============================================

// 面试状态
let interviewState = getInterviewState();

// 当前待发送的文件（前端上传时暂存，点击发送时才真正发送）
let pendingFile = null;

// 显示错误信息 (覆盖 api.js 的通用方法，使用聊天气泡显示)
function showError(message) {
    addMessage('ai', `❌ 错误：${message}`, true);
}

// 显示成功信息
function showSuccess(message) {
    addMessage('ai', `✅ ${message}`, true);
}

// 获取面试状态

// 获取面试状态
function getInterviewState() {
    const stateStr = localStorage.getItem('interviewState');
    const defaultState = {
        threadId: null,
        currentQuestion: null,
        currentRound: 1,
        maxRounds: 3,
        resumeText: '',
        resumeFileUrl: null,
        lastFeedback: null,
        finalReport: null,
        isReadOnly: false
    };
    if (stateStr) {
        const parsed = JSON.parse(stateStr);
        // 确保 isReadOnly 字段存在
        if (parsed.isReadOnly === undefined) {
            parsed.isReadOnly = false;
        }
        return parsed;
    }
    return defaultState;
}

// 保存面试状态
function saveInterviewState(state) {
    localStorage.setItem('interviewState', JSON.stringify(state));
}

// 清除面试状态
function clearInterviewState() {
    localStorage.removeItem('interviewState');
}

// 添加消息到聊天区域
function addMessage(type, content, isError = false, isHtml = false, isDocument = false) {
    const messagesContainer = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}-message`;

    // 获取用户头像（用户名第一个字符）
    let avatar = '';
    if (type === 'ai') {
        avatar = '🤖';
    } else if (type === 'user') {
        const auth = getAuth();
        const userName = auth ? (auth.userName || 'U') : 'U';
        avatar = userName.charAt(0).toUpperCase();
    }

    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';

    // 如果是文件卡片，添加特殊类以去除气泡样式
    if (isHtml && content.includes('class="file-card"')) {
        messageContent.classList.add('is-file');
    }

    // 如果是文档模式，添加 markdown-document 类
    if (isDocument) {
        messageContent.classList.add('markdown-document');
    }

    if (isError) {
        messageContent.style.borderLeft = '4px solid var(--error-color)';
    }


    const messageText = document.createElement('div');
    messageText.className = 'message-text';

    if (isHtml) {
        // 如果是 HTML 内容，直接设置 innerHTML
        // 注意：调用方必须确保 content 是安全的（已转义）
        messageText.innerHTML = content.replace(/\n/g, '<br>');
    } else {
        // 检测是否包含 Markdown 标记（###, **, -, 等）
        const hasMarkdown = /###|##|\*\*|\n-\s|\n\d+\.\s/.test(content);

        if (hasMarkdown && typeof marked !== 'undefined') {
            // 使用 marked.js 渲染 Markdown
            messageText.innerHTML = marked.parse(content);
            // 只有在非文档模式下才添加 markdown-content 类，避免样式冲突
            if (!isDocument) {
                messageText.classList.add('markdown-content');
            }
        } else {
            // 处理纯文本多行
            const lines = content.split('\n');
            lines.forEach(line => {
                const p = document.createElement('p');
                p.textContent = line;
                messageText.appendChild(p);
            });
        }
    }


    messageContent.appendChild(messageText);

    // 创建头像元素
    const avatarDiv = document.createElement('div');
    avatarDiv.className = 'message-avatar';
    avatarDiv.textContent = avatar;

    messageDiv.appendChild(avatarDiv);
    messageDiv.appendChild(messageContent);

    messagesContainer.appendChild(messageDiv);

    // 滚动到容器最底部（使用 requestAnimationFrame 确保 DOM 已更新）
    requestAnimationFrame(() => {
        requestAnimationFrame(() => {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        });
    });

    return messageDiv;
}

// 添加加载消息（思考中动画）
function addLoadingMessage() {
    // 使用纯 CSS 动画的加载指示器
    const loadingHtml = `
        <div class="typing-indicator">
            <span></span>
            <span></span>
            <span></span>
        </div>
    `;
    const messageDiv = addMessage('ai', loadingHtml, false, true);

    // 给思考消息的气泡添加特殊class
    const messageContent = messageDiv.querySelector('.message-content');
    if (messageContent) {
        messageContent.classList.add('loading-bubble');
    }

    return messageDiv;
}

// 移除加载消息
function removeLoadingMessage(messageDiv) {
    if (messageDiv && messageDiv.parentNode) {
        messageDiv.parentNode.removeChild(messageDiv);
    }
}

// 处理上传简历（显示文件预览，不发送请求）
function handleUploadResume(file) {
    if (!file) {
        showError('请选择文件');
        return;
    }

    // 检查文件类型（只支持 PDF）
    if (file.type !== 'application/pdf') {
        showError('只支持 PDF 格式');
        return;
    }

    // 保存文件到待发送列表
    pendingFile = file;

    // 显示文件预览
    const filePreview = document.getElementById('file-preview');
    const previewFileName = document.getElementById('preview-file-name');
    if (filePreview && previewFileName) {
        previewFileName.textContent = file.name;
        filePreview.classList.remove('hidden');
    }

    // 在聊天中提示
    addMessage('ai', '📄 文件已选择，点击发送按钮开始解析并开始面试。');

    if (window.triggerCheckSendButton) window.triggerCheckSendButton();
}

// 处理开始面试（合并文件上传和工作流启动）
async function handleStartInterview() {
    if (!pendingFile) {
        showError('请先上传简历文件');
        return;
    }

    // 保存文件名（在清除 pendingFile 之前）
    const fileName = pendingFile.name;

    // 立即在聊天中显示文件卡片（用户消息）- 先显示PDF
    const fileCardHtml = `<div class="file-card"><span class="file-card-icon">📄</span><div class="file-card-info"><span class="file-card-name">${fileName}</span></div></div>`;
    addMessage('user', fileCardHtml, false, true);

    // 立即清除待发送文件和隐藏文件预览（在发送请求之前）
    const fileToSend = pendingFile;
    pendingFile = null;
    const filePreview = document.getElementById('file-preview');
    if (filePreview) {
        filePreview.classList.add('hidden');
    }

    // 显示加载消息
    const loadingMsg = addLoadingMessage();

    try {
        // 调用非流式 /start 接口
        const result = await startInterviewAPI(fileToSend, interviewState.maxRounds);

        // 移除加载消息
        removeLoadingMessage(loadingMsg);

        // 更新面试状态
        interviewState.threadId = result.thread_id;
        interviewState.resumeText = result.resume_text;
        interviewState.resumeFileUrl = result.resume_file_url;  // 保存PDF文件URL
        interviewState.currentQuestion = result.question;
        interviewState.currentRound = result.round;
        interviewState.isReadOnly = false;

        // 更新当前查看的ID
        currentViewingThreadId = result.thread_id;

        saveInterviewState(interviewState);

        // 重新加载记录列表以更新高亮
        renderInterviewRecords();

        // 初始化右侧仪表盘
        updateDashboard(result);

        // 更新已显示的文件卡片，添加点击功能
        if (result.resume_text) {
            const escapedText = result.resume_text.replace(/"/g, '&quot;');
            const pdfUrl = result.resume_file_url || '';

            // 找到刚才添加的文件卡片，添加 data 属性
            const messages = document.getElementById('chat-messages');
            const lastFileCard = messages.querySelector('.file-card:last-of-type');
            if (lastFileCard) {
                lastFileCard.setAttribute('data-resume', escapedText);
                lastFileCard.setAttribute('data-pdf-url', pdfUrl);
            }

            addMessage('ai', '✅ 文件解析成功！');
        }

        // 显示目标岗位信息
        const targetPosition = result.target_position || '未识别';
        // 使用文档模式显示简历分析结果，使其看起来像一份正式的文档
        addMessage('ai', `# 🎯 简历分析报告\n\n**识别到的目标岗位**：${targetPosition}\n\n---\n\n${result.resume_text}`, false, false, true);

        // 显示第一个问题
        addMessage('ai', `# 📊 第 ${result.round} 轮面试\n\n### ❓ 问题：\n\n${result.question}`, false, false, true);
    } catch (error) {
        removeLoadingMessage(loadingMsg);
        showError(`开始面试失败：${error.message}`);
    }
}

// 显示简历模态框
function showResumeModal(content) {
    const modal = document.getElementById('resume-modal');
    const modalBody = document.getElementById('resume-modal-body');
    if (modal && modalBody) {
        modalBody.textContent = content; // 使用 textContent 自动处理换行
        modal.classList.remove('hidden');
    }
}

// 隐藏简历模态框
function hideResumeModal() {
    const modal = document.getElementById('resume-modal');
    if (modal) {
        modal.classList.add('hidden');
    }
}

// 初始化模态框事件
document.addEventListener('DOMContentLoaded', () => {
    // 关闭按钮
    const closeBtn = document.getElementById('close-resume-modal');
    if (closeBtn) {
        closeBtn.addEventListener('click', hideResumeModal);
    }

    // 点击模态框背景关闭
    const modal = document.getElementById('resume-modal');
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                hideResumeModal();
            }
        });
    }

    // 移除文件按钮
    const removeFileBtn = document.getElementById('remove-file-btn');
    if (removeFileBtn) {
        removeFileBtn.addEventListener('click', () => {
            pendingFile = null;
            const filePreview = document.getElementById('file-preview');
            if (filePreview) {
                filePreview.classList.add('hidden');
            }
            if (window.triggerCheckSendButton) window.triggerCheckSendButton();
        });
    }

    // 委托点击事件处理简历链接和文件卡片
    document.addEventListener('click', (e) => {
        // 处理简历链接
        if (e.target.classList.contains('resume-link')) {
            const content = e.target.getAttribute('data-resume');
            if (content) {
                showResumeModal(content);
            }
        }

        // 处理文件卡片点击 - 优先打开PDF预览
        const fileCard = e.target.closest('.file-card');
        if (fileCard) {
            const pdfUrl = fileCard.getAttribute('data-pdf-url');
            if (pdfUrl) {
                // 有PDF URL时，在新窗口打开PDF预览
                window.open(pdfUrl, '_blank');
            } else {
                // 没有PDF URL时，回退到显示纯文本
                const content = fileCard.getAttribute('data-resume');
                if (content) {
                    showResumeModal(content);
                }
            }
        }
    });
});


// 处理提交答案（非流式版本）
async function handleSubmitAnswer(answer) {
    if (!answer.trim()) {
        showError('请先输入您的回答');
        return;
    }

    if (!interviewState.threadId) {
        showError('面试未开始，请先上传简历并开始面试');
        return;
    }

    addMessage('user', answer);
    // showLoading('🤖 AI 正在生成反馈...');
    const loadingMsg = addLoadingMessage();

    try {
        const result = await submitAnswerAPI(interviewState.threadId, answer);

        // 移除加载消息
        removeLoadingMessage(loadingMsg);

        // 显示反馈结果
        if (result.feedback) {
            addMessage('ai', `📊 反馈结果：\n\n${result.feedback}`);
            interviewState.lastFeedback = result.feedback;
        }

        if (result.is_finished) {
            // 面试完成
            interviewState.finalReport = result.report || '';
            interviewState.currentQuestion = null;
            interviewState.currentRound = result.round;
            interviewState.isReadOnly = false;

            saveInterviewState(interviewState);
            // hideLoading();

            addMessage('ai', `# 🎉 面试最终报告\n\n${result.report || '暂无报告'}`, false, false, true);

            // 重新加载记录列表（面试完成后会新增一条记录）
            renderInterviewRecords();
        } else {
            // 继续下一轮
            interviewState.currentQuestion = result.question || '';
            interviewState.currentRound = result.round;
            interviewState.isReadOnly = false;

            saveInterviewState(interviewState);
            // hideLoading();

            addMessage('ai', `# 📊 第 ${result.round} 轮面试\n\n### ❓ 问题：\n\n${result.question || ''}`, false, false, true);
        }
    } catch (error) {
        // hideLoading();
        removeLoadingMessage(loadingMsg);
        showError(`提交失败：${error.message}`);
    }
}

// 自动调整输入框高度
function autoResizeTextarea(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px';
}

// 当前查看的记录ID（用于高亮显示）
let currentViewingThreadId = null;

// 渲染面试记录列表到侧边栏
async function renderInterviewRecords() {
    try {
        const response = await getInterviewRecordsAPI();
        const records = response.records || [];

        const chatHistory = document.querySelector('.chat-history');
        if (!chatHistory) return;

        // 清空现有内容（保留结构）
        chatHistory.innerHTML = '';

        // 如果有记录，按日期分组
        if (records.length > 0) {
            // 今天和最近的分组
            const today = new Date();
            today.setHours(0, 0, 0, 0);

            const todayRecords = [];
            const recentRecords = [];

            records.forEach(record => {
                const recordDate = new Date(record.created_at);
                recordDate.setHours(0, 0, 0, 0);

                if (recordDate.getTime() === today.getTime()) {
                    todayRecords.push(record);
                } else {
                    recentRecords.push(record);
                }
            });

            // 渲染今天的记录
            if (todayRecords.length > 0) {
                const todaySection = document.createElement('div');
                todaySection.className = 'history-section';
                todaySection.innerHTML = '<div class="history-title">今天</div>';

                todayRecords.forEach(record => {
                    const item = createRecordItem(record);
                    todaySection.appendChild(item);
                });

                chatHistory.appendChild(todaySection);
            }

            // 渲染最近的记录
            if (recentRecords.length > 0) {
                const recentSection = document.createElement('div');
                recentSection.className = 'history-section';
                recentSection.innerHTML = '<div class="history-title">最近</div>';

                recentRecords.forEach(record => {
                    const item = createRecordItem(record);
                    recentSection.appendChild(item);
                });

                chatHistory.appendChild(recentSection);
            }
        } else {
            // 没有记录时显示提示
            const emptySection = document.createElement('div');
            emptySection.className = 'history-section';
            emptySection.innerHTML = '<div class="history-title">暂无面试记录</div>';
            chatHistory.appendChild(emptySection);
        }

        // 绑定点击事件
        chatHistory.querySelectorAll('.chat-item').forEach(item => {
            const threadId = item.getAttribute('data-thread-id');
            if (threadId && threadId !== 'current') {
                // 点击记录加载详情
                item.addEventListener('click', (e) => {
                    // 如果点击的是删除按钮，不触发加载
                    if (e.target.classList.contains('chat-delete-btn')) {
                        return;
                    }
                    loadInterviewRecord(threadId);
                });
            }
        });

        // 绑定删除按钮事件
        chatHistory.querySelectorAll('.chat-delete-btn').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                e.stopPropagation(); // 阻止事件冒泡
                const threadId = btn.getAttribute('data-thread-id');

                if (confirm('确定要删除这条面试记录吗？删除后无法恢复！')) {
                    try {
                        showLoading('正在删除...');
                        await deleteInterviewRecordAPI(threadId);
                        hideLoading();

                        // 如果删除的是当前查看的记录，清空聊天区域和状态
                        if (currentViewingThreadId === threadId) {
                            const chatMessages = document.getElementById('chat-messages');
                            chatMessages.innerHTML = '';
                            addMessage('ai', '面试记录已删除');
                            currentViewingThreadId = null;

                            // 清空面试状态
                            interviewState = {
                                threadId: null,
                                resumeText: '',
                                resumeFileUrl: null,
                                currentQuestion: '',
                                currentRound: 0,
                                maxRounds: 3,
                                isFinished: false,
                                isReadOnly: false
                            };

                            // 清除localStorage
                            localStorage.removeItem('interviewState');
                        }

                        // 如果删除的是localStorage中保存的会话，也要清除
                        const savedStateStr = localStorage.getItem('interviewState');
                        if (savedStateStr) {
                            try {
                                const savedState = JSON.parse(savedStateStr);
                                if (savedState && savedState.threadId === threadId) {
                                    localStorage.removeItem('interviewState');
                                    interviewState = {
                                        threadId: null,
                                        resumeText: '',
                                        resumeFileUrl: null,
                                        currentQuestion: '',
                                        currentRound: 0,
                                        maxRounds: 3,
                                        isFinished: false,
                                        isReadOnly: false
                                    };
                                }
                            } catch (e) {
                                console.error('解析localStorage失败:', e);
                            }
                        }

                        // 重新加载列表
                        renderInterviewRecords();

                        // 清空聊天区域，显示欢迎界面
                        const chatMessages = document.getElementById('chat-messages');
                        chatMessages.innerHTML = '';

                        // 显示删除成功的消息和欢迎提示
                        addMessage('ai', '✅ **面试记录已成功删除**\n\n您可以：\n\n1️⃣ **在此对话下继续**：直接点击下方的“上传简历”按钮，在当前对话中开始新的面试\n\n2️⃣ **新开一个面试**：点击左上角的“➕ 开始面试”按钮，创建全新的面试记录', false, false, true);

                        // 重置右侧面试看板
                        resetDashboard();
                    } catch (error) {
                        hideLoading();
                        showError(`删除失败：${error.message}`);
                    }
                }
            });
        });

    } catch (error) {
        console.error('加载面试记录列表失败:', error);
    }
}

// 创建记录项元素
function createRecordItem(record) {
    const item = document.createElement('div');
    item.className = 'chat-item';
    if (currentViewingThreadId === record.thread_id) {
        item.classList.add('active');
    }
    item.setAttribute('data-thread-id', record.thread_id);

    // 显示"面试记录"加上会话ID（截取前8位）和创建时间（日期+时分）
    const threadIdShort = record.thread_id.substring(0, 8);
    // 后端返回的是本地时间，格式：2025-11-30 13:59:42，直接提取日期和时分
    const dateTimeParts = record.created_at.split(' ');
    const dateStr = dateTimeParts[0]; // 日期部分
    const timeStr = dateTimeParts[1] ? dateTimeParts[1].substring(0, 5) : ''; // 时分部分（前5个字符）
    const dateTimeStr = timeStr ? `${dateStr} ${timeStr}` : dateStr;

    item.innerHTML = `
        <div>
            <span class="chat-title">面试记录 ${threadIdShort}</span>
            <button class="chat-delete-btn" data-thread-id="${record.thread_id}" title="删除记录">×</button>
        </div>
        <span class="chat-meta">${dateTimeStr}</span>
    `;

    return item;
}

// 加载面试记录详情
async function loadInterviewRecord(threadId) {
    try {
        showLoading('正在加载面试记录...');

        const record = await getInterviewRecordDetailAPI(threadId);

        // 更新当前查看的ID
        currentViewingThreadId = threadId;

        // 更新侧边栏高亮
        document.querySelectorAll('.chat-item').forEach(item => {
            item.classList.remove('active');
            if (item.getAttribute('data-thread-id') === threadId) {
                item.classList.add('active');
            }
        });

        // 清空聊天区域
        const chatMessages = document.getElementById('chat-messages');
        chatMessages.innerHTML = '';

        // 更新右侧面试看板
        updateDashboard(record);

        // 【新增】显示简历PDF文件卡片（如果有的话）
        if (record.resume_file_url) {
            const escapedText = record.resume_text ? record.resume_text.replace(/"/g, '&quot;') : '';
            const pdfUrl = record.resume_file_url || '';
            const fileName = record.resume_file_name || '简历文件.pdf';  // 使用真实文件名，如果没有则用默认名称

            // 创建文件卡片HTML
            const fileCardHtml = `<div class="file-card" data-resume="${escapedText}" data-pdf-url="${pdfUrl}"><span class="file-card-icon">📄</span><div class="file-card-info"><span class="file-card-name">${fileName}</span></div></div>`;
            addMessage('user', fileCardHtml, false, true);
        }

        // 显示简历内容
        if (record.resume_text) {
            addMessage('ai', `# 📄 简历内容\n\n${record.resume_text}`, false, false, true);
        }

        // 显示面试历史
        if (record.history && record.history.length > 0) {
            record.history.forEach((item, index) => {
                // 显示问题
                if (item.question) {
                    addMessage('ai', `# 📊 第 ${index + 1} 轮面试\n\n### ❓ 问题：\n\n${item.question}`, false, false, true);
                }

                // 显示回答
                if (item.answer) {
                    addMessage('user', item.answer);
                }

                // 显示反馈
                if (item.feedback) {
                    addMessage('ai', `📊 反馈：\n\n${item.feedback}`);
                }
            });
        }

        // 显示最终报告
        if (record.report) {
            addMessage('ai', `# 🎉 面试最终报告\n\n${record.report}`, false, false, true);
        }

        // 设置 input area 的显示状态
        const inputArea = document.querySelector('.chat-input-area');
        if (record.is_finished) {
            // 已完成：只读模式，隐藏输入框
            interviewState = {
                threadId: record.thread_id,
                currentQuestion: null,
                currentRound: record.history ? record.history.length : 0,
                maxRounds: record.history ? record.history.length : 0,
                resumeText: record.resume_text,
                resumeFileUrl: record.resume_file_url || null,
                lastFeedback: null,
                finalReport: record.report,
                isReadOnly: true
            };
            if (inputArea) inputArea.style.display = 'none';
        } else {
            // 进行中：恢复模式，显示输入框
            // 找到最后一个问题，作为 currentQuestion
            let lastQuestion = '';
            // 逻辑修正：如果 history 最后一项有 question 但没 answer，那就是当前待回答的问题
            // 如果都有，那可能是正在生成中或者异常，这里简化处理，取最后一个 question
            if (record.history && record.history.length > 0) {
                const lastEntry = record.history[record.history.length - 1];
                if (lastEntry.question && !lastEntry.answer) {
                    lastQuestion = lastEntry.question;
                }
            }

            interviewState = {
                threadId: record.thread_id,
                currentQuestion: lastQuestion, // 恢复当前问题
                currentRound: record.history ? record.history.length : 0, // 轮次
                maxRounds: 3, // 这里后端没存 max_rounds，暂时默认 3，或者得从后端取
                resumeText: record.resume_text,
                resumeFileUrl: record.resume_file_url || null,
                lastFeedback: null,
                finalReport: null,
                isReadOnly: false
            };

            if (inputArea) inputArea.style.display = 'flex';

        }

        saveInterviewState(interviewState);
        hideLoading();

    } catch (error) {
        hideLoading();
        showError(`加载面试记录失败：${error.message}`);
    }
}

// ============================================
// ========== 页面初始化 ==========
// ============================================

// 初始化主页面
function initMainPage() {
    // 检查认证
    const auth = getAuth();
    if (!auth || !auth.isAuthenticated) {
        window.location.href = 'index.html';
        return;
    }

    // 显示用户名
    const userNameDisplay = document.getElementById('user-name-display');
    const userAvatarText = document.getElementById('user-avatar-text');
    if (userNameDisplay) {
        userNameDisplay.textContent = auth.userName || '用户';
    }
    if (userAvatarText) {
        userAvatarText.textContent = (auth.userName || 'U').charAt(0).toUpperCase();
    }

    // 页面刷新默认为新对话状态
    // 清除本地缓存的状态，或者重置为默认状态，不自动恢复对话
    // interviewState = getInterviewState(); // 不再从 localStorage 恢复
    interviewState = {
        threadId: null,
        currentQuestion: null,
        currentRound: 1,
        maxRounds: 3,
        resumeText: '',
        resumeFileUrl: null,
        lastFeedback: null,
        finalReport: null,
        isReadOnly: false
    };
    saveInterviewState(interviewState); // 更新 localStorage 为初始状态

    // 清除待发送文件（页面刷新后重新开始）
    pendingFile = null;

    // 不再自动显示进行中的面试问题
    // if (interviewState.currentQuestion && !interviewState.isReadOnly) { ... }

    // 加载面试记录列表
    renderInterviewRecords();

    // 显示默认欢迎消息
    addMessage('ai', '欢迎使用 AI 模拟面试系统！\n请先上传您的简历，然后点击发送开始面试。');

    // 设置事件监听器
    setupEventListeners();
}

// 设置事件监听器
function setupEventListeners() {
    // 退出登录
    const userSettingsBtn = document.getElementById('user-settings-btn');
    if (userSettingsBtn) {
        userSettingsBtn.addEventListener('click', () => {
            if (confirm('确定要退出登录吗？')) {
                clearAuth();
                clearInterviewState();
                window.location.href = 'index.html';
            }
        });
    }

    // 新建对话
    const newChatBtn = document.getElementById('new-chat-btn');
    if (newChatBtn) {
        newChatBtn.addEventListener('click', () => {
            if (confirm('确定要开始新的面试吗？这将清除当前进度。')) {
                interviewState = {
                    threadId: null,
                    currentQuestion: null,
                    currentRound: 1,
                    maxRounds: 3,
                    resumeText: '',
                    lastFeedback: null,
                    finalReport: null,
                    isReadOnly: false
                };

                // 恢复输入框显示
                const inputArea = document.querySelector('.chat-input-area');
                if (inputArea) inputArea.style.display = 'flex';

                pendingFile = null;
                currentViewingThreadId = null;
                saveInterviewState(interviewState);
                document.getElementById('chat-messages').innerHTML = '';
                addMessage('ai', '欢迎使用 AI 模拟面试系统！\n请先上传您的简历，然后点击发送开始面试。');

                // 重新加载记录列表以更新高亮
                renderInterviewRecords();
            }
        });
    }

    // 智能面试助手按钮
    const interviewAgentBtn = document.getElementById('interview-agent-btn');
    if (interviewAgentBtn) {
        interviewAgentBtn.addEventListener('click', () => {
            window.location.href = 'interview-agent.html';
        });
    }

    // 上传简历按钮
    const attachFileBtn = document.getElementById('attach-file-btn');
    const resumeFileInput = document.getElementById('resume-file-input');

    if (attachFileBtn) {
        attachFileBtn.addEventListener('click', () => {
            resumeFileInput?.click();
        });
    }

    if (resumeFileInput) {
        resumeFileInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                handleUploadResume(file);
            }
        });
    }

    // 发送按钮
    const sendBtn = document.getElementById('send-btn');
    const chatInput = document.getElementById('chat-input');

    if (sendBtn && chatInput) {
        // 检查发送按钮状态
        function checkSendButtonState() {
            const text = chatInput.value.trim();
            const hasFile = !!pendingFile;

            if (text || hasFile) {
                sendBtn.disabled = false;
                sendBtn.style.opacity = '1';
                sendBtn.style.cursor = 'pointer';
            } else {
                sendBtn.disabled = true;
                sendBtn.style.opacity = '0.5';
                sendBtn.style.cursor = 'not-allowed';
            }
        }

        // 初始化状态
        checkSendButtonState();

        sendBtn.addEventListener('click', () => {
            const text = chatInput.value.trim();

            // 如果是只读模式（查看历史记录），不允许开始新面试
            if (interviewState.isReadOnly) {
                addMessage('ai', '当前正在查看历史记录，无法开始新面试。请点击"开启新对话"开始新的面试。');
                chatInput.value = '';
                autoResizeTextarea(chatInput);
                checkSendButtonState(); // 重置状态
                return;
            }

            // 如果有待发送的文件，优先处理文件上传和开始面试
            if (pendingFile) {
                handleStartInterview();
                chatInput.value = '';
                autoResizeTextarea(chatInput);
                checkSendButtonState(); // 重置状态
                return;
            }

            // 如果有文本输入
            if (text) {
                // 如果是只读模式（查看历史记录），不允许提交
                if (interviewState.isReadOnly) {
                    addMessage('ai', '当前正在查看历史记录，无法提交新的回答。请点击"开启新对话"开始新的面试。');
                    chatInput.value = '';
                    autoResizeTextarea(chatInput);
                    return;
                }

                if (interviewState.currentQuestion) {
                    // 提交答案（使用非流式版本）
                    handleSubmitAnswer(text);
                } else if (interviewState.threadId) {
                    // 如果已有 threadId 但没有问题，可能是异常情况
                    addMessage('ai', '面试已结束或出现异常，请重新开始。');
                } else {
                    // 没有上传文件，提示用户
                    addMessage('ai', '请先上传简历文件，然后点击发送开始面试。');
                }
                chatInput.value = '';
                autoResizeTextarea(chatInput);
                checkSendButtonState(); // 重置状态
            } else if (!pendingFile) {
                // 理论上按钮disabled了进不来，但保留兜底
                // addMessage('ai', '请先上传简历文件或输入内容。');
            }
        });

        // 回车发送（Shift+Enter换行）
        chatInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                if (!sendBtn.disabled) {
                    sendBtn.click();
                }
            }
        });

        // 自动调整高度并检查按钮
        chatInput.addEventListener('input', () => {
            autoResizeTextarea(chatInput);
            checkSendButtonState();
        });
    }

    // 暴露 checkSendButtonState 给其他函数使用（如果有需要，或者通过事件机制）
    // 为了简单，我们把 checkSendButtonState 挂载到 window 或者在 handleUploadResume 里触发 input 事件来间接触发检查
    // 更优雅的方式是在 handleUploadResume 里手动调用，但因为作用域问题，
    // 我们可以在 handleUploadResume 里模拟触发一下 chatInput 的 input 事件
    window.triggerCheckSendButton = function () {
        const chatInput = document.getElementById('chat-input');
        if (chatInput) {
            // 手动触发 input 事件监听器
            const event = new Event('input');
            chatInput.dispatchEvent(event);
        }
    };

}

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', () => {
    initMainPage();

    // 隐藏首屏加载动画
    const loader = document.getElementById('initial-loading');
    if (loader) {
        //稍微延迟一点以确保渲染完成
        setTimeout(() => {
            loader.style.opacity = '0';
            setTimeout(() => loader.remove(), 500);
        }, 300);
    }
});

// 更新右侧面试看板
function updateDashboard(data) {
    const dashboardContainer = document.getElementById('dashboard-container');
    if (!dashboardContainer) return;

    // 清空空状态提示
    dashboardContainer.innerHTML = '';

    // 如果没有数据，显示默认状态（处理数据异常或初始状态）
    if (!data || (!data.thread_id && !data.id && !data.history && !data.round)) {
        dashboardContainer.innerHTML = `
            <div class="dashboard-empty">
                <div class="empty-icon">📊</div>
                <p>暂无进行中的面试</p>
                <p class="empty-sub">开始面试后，此处将显示实时进度和档案。</p>
            </div>`;
        return;
    }

    const isFinished = data.is_finished;
    const statusClass = isFinished ? 'status-finished' : 'status-active';
    const statusText = isFinished ? '已完成' : '进行中';
    const shortId = (data.thread_id || data.id || '').substring(0, 8);
    const userName = data.user_name || getAuth()?.userName || 'User';

    // 时间处理
    let timeStr = data.created_at || new Date().toLocaleString();

    // 估算进度
    const maxRounds = 3;
    let progressPercent = 0;
    let progressText = "0%";
    let progressSub = "准备就绪";

    // 计算轮次
    let currentRound = 1;

    if (data.history) {
        const roundsCount = data.history.length;
        if (roundsCount > 0) {
            const lastItem = data.history[roundsCount - 1];
            if (lastItem.question && !lastItem.answer) {
                currentRound = roundsCount;
            } else {
                currentRound = roundsCount + 1;
            }
        }
    } else if (data.round) {
        // 如果数据中直接包含了round (来自API返回)，直接使用
        currentRound = data.round;
    }

    if (isFinished) {
        progressPercent = 100;
        progressText = "100%";
        progressSub = "全部完成";
    } else {
        // 计算进度条
        let completedRounds = currentRound - 1;
        progressPercent = Math.min(Math.round((completedRounds / maxRounds) * 100) + 10, 95);

        progressText = `R${currentRound}`;
        progressSub = `第 ${currentRound} / ${maxRounds} 轮`;
    }

    const metaCardHtml = `
        <div class="record-meta-container">
            <div class="record-meta-card">
                <div class="meta-watermark">
                     <svg width="1em" height="1em" viewBox="0 0 24 24" fill="currentColor"><path d="M19,3H14.82C14.4,1.84 13.3,1 12,1C10.7,1 9.6,1.84 9.18,3H5A2,2 0 0,0 3,5V19A2,2 0 0,0 5,21H19A2,2 0 0,0 21,19V5A2,2 0 0,0 19,3M12,3A1,1 0 0,1 13,3H11A1,1 0 0,1 12,3M7,7H17V5H19V19H5V5H7V7M7.5,13.5L9,12L11,14L15.5,9.5L17,11L11,17L7.5,13.5Z" /></svg>
                </div>
                <div class="card-content">
                    <div class="meta-header">
                        <div class="meta-title">
                            <span class="meta-icon">
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
                            </span> 
                            面试档案
                        </div>
                        <span class="status-badge ${statusClass}">${statusText}</span>
                    </div>
                    
                    <div class="meta-body">
                        <div class="meta-info-col">
                            <div class="meta-item">
                                <span class="meta-label">ID</span>
                                <span class="meta-value">${shortId}</span>
                            </div>
                            <div class="meta-item">
                                <span class="meta-label">用户</span>
                                <span class="meta-value">${userName}</span>
                            </div>
                            <div class="meta-item">
                                <span class="meta-label">时间</span>
                                <span class="meta-value long">${timeStr}</span>
                            </div>
                        </div>
                        
                        <div class="meta-progress-col">
                            <div class="progress-label">面试进度</div>
                            <div class="progress-text">${progressText}</div>
                            <div class="progress-track">
                                <div class="progress-fill" style="width: ${progressPercent}%"></div>
                            </div>
                            <div class="progress-sub">${progressSub}</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    dashboardContainer.innerHTML = metaCardHtml;
}

// 重置面试看板
function resetDashboard() {
    const dashboardContainer = document.getElementById('dashboard-container');
    if (!dashboardContainer) return;

    dashboardContainer.innerHTML = '<div style="text-align: center; color: #9ca3af; padding: 40px 0;">暂无面试进行中</div>';
}
