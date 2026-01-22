// AI模拟面试系统v1.0，作者刘梦畅
// ========== API 请求模块 ==========

const API_BASE_URL = 'http://localhost:8000/api/interview';
// const API_BASE_URL = 'http://172.18.174.107:8000/api/interview';


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

// 开始面试 API
async function startInterviewAPI(file, maxRounds) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('max_rounds', maxRounds);

    const response = await fetch(`${API_BASE_URL}/start`, {
        method: 'POST',
        body: formData
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || '开始面试失败');
    }

    return await response.json();
}

// 提交答案 API（非流式版本 - 已弃用，保留作为备用）
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

// 健康检查 API（未使用 - 保留作为备用）
// async function checkBackendAPI() {
//     try {
//         const response = await fetch('http://localhost:8000/health');
//         return response.ok;
//     } catch (error) {
//         return false;
//     }
// }

// ============================================
// ========== UI 交互和工具函数 ==========
// ============================================

// 面试状态
let interviewState = getInterviewState();

// 当前待发送的文件（前端上传时暂存，点击发送时才真正发送）
let pendingFile = null;

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
function showError(message) {
    addMessage('ai', `❌ 错误：${message}`, true);
}

// 显示成功信息
function showSuccess(message) {
    addMessage('ai', `✅ ${message}`, true);
}

// 获取认证信息
function getAuth() {
    const authStr = sessionStorage.getItem('auth');
    return authStr ? JSON.parse(authStr) : null;
}

// 清除认证信息
function clearAuth() {
    sessionStorage.removeItem('auth');
}

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
function addMessage(type, content, isError = false, isHtml = false) {
    const messagesContainer = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}-message`;

    // 获取用户头像（用户名第一个字符）
    let avatar;
    if (type === 'ai') {
        avatar = '🤖';
    } else {
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
            messageText.classList.add('markdown-content');
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
    if (type === 'user') {
        avatarDiv.textContent = avatar;
    } else {
        avatarDiv.textContent = avatar;
    }

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

// 添加加载消息（打字机动画）
// 添加加载消息（思考中动画）
function addLoadingMessage() {
    const loadingHtml = `
        <span class="thinking-text">正在思考</span><span class="thinking-dots"></span>
    `;
    const messageDiv = addMessage('ai', loadingHtml, false, true);
    
    // 给思考消息的气泡添加特殊class，让宽度自适应
    const messageContent = messageDiv.querySelector('.message-content');
    if (messageContent) {
        messageContent.classList.add('thinking-bubble');
    }
    
    return messageDiv;
}

// 移除加载消息
function removeLoadingMessage(messageDiv) {
    if (messageDiv && messageDiv.parentNode) {
        messageDiv.parentNode.removeChild(messageDiv);
    }
}

/**
 * 【流式消息 - 创建】添加一个流式消息到聊天区域
 * 
 * 用途：在开始接收流式数据时，先创建一个空的消息框
 * 返回：消息的 DOM 元素，供后续更新使用
 * 
 * @param {string} type - 消息类型（'ai' 或 'user'）
 * @param {string} initialContent - 初始内容（通常是标题，如 "📊 反馈结果："）
 * @returns {HTMLElement} 消息的 DOM 元素
 */
function addStreamingMessage(type, initialContent) {
    const messagesContainer = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}-message`;

    // 获取用户头像
    let avatar = type === 'ai' ? '🤖' : 'U';

    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';

    // 创建消息文本容器（用于后续更新）
    const messageText = document.createElement('div');
    messageText.className = 'message-text';
    messageText.textContent = initialContent;  // 设置初始内容

    messageContent.appendChild(messageText);

    // 创建头像元素
    const avatarDiv = document.createElement('div');
    avatarDiv.className = 'message-avatar';
    avatarDiv.textContent = avatar;

    messageDiv.appendChild(avatarDiv);
    messageDiv.appendChild(messageContent);

    // 添加到聊天区域
    messagesContainer.appendChild(messageDiv);

    // 滚动到容器最底部（使用 requestAnimationFrame 确保 DOM 已更新）
    requestAnimationFrame(() => {
        requestAnimationFrame(() => {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        });
    });

    // 返回消息元素，供后续更新使用
    return messageDiv;
}

/**
 * 【流式消息 - 更新】更新流式消息的内容（打字机效果）
 * 
 * 用途：在接收到新的流式数据时，更新消息内容
 * 原理：直接替换 textContent，浏览器会自动重新渲染
 * 
 * @param {HTMLElement} messageDiv - 消息的 DOM 元素（由 addStreamingMessage 返回）
 * @param {string} content - 新的内容（累加后的完整内容）
 */
function updateStreamingMessage(messageDiv, content) {
    if (!messageDiv) return;

    // 找到消息文本容器
    const messageText = messageDiv.querySelector('.message-text');
    if (messageText) {
        // 更新文本内容（浏览器会自动重新渲染，形成打字机效果）
        messageText.textContent = content;

        // 立即滚动到底部（确保用户能看到最新内容）
        const messagesContainer = document.getElementById('chat-messages');
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
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
        addMessage('ai', `🎯 **识别到的目标岗位**：${targetPosition}\n\n📋 **简历关键信息**：\n${result.resume_text}`);

        // 显示第一个问题
        addMessage('ai', `📊 面试开始！\n\n当前轮次：${result.round} / ${interviewState.maxRounds}\n\n❓ 问题：\n${result.question}`);
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

// ============================================
// ========== 流式输出处理函数 ==========
// ============================================

/**
 * 【流式输出】处理提交答案（使用 Fetch API + ReadableStream）
 * 
 * 核心技术：
 * 1. Fetch API：发送 HTTP 请求
 * 2. ReadableStream：接收服务器推送的数据流
 * 3. TextDecoder：将二进制数据解码为文本
 * 4. SSE 协议解析：解析 "data: {...}\n\n" 格式的消息
 * 5. 打字机效果：逐字符累加并更新 UI
 * 
 * 流程：
 * 1. 发送 POST 请求到 /submit/stream
 * 2. 获取响应的 ReadableStream
 * 3. 逐块读取数据流（每块可能包含多条 SSE 消息）
 * 4. 解析 SSE 消息（提取 JSON 数据）
 * 5. 根据消息类型更新 UI（打字机效果）
 */
// async function handleSubmitAnswerStream(answer) {
//     // ========== 步骤1：输入验证 ==========
//     if (!answer.trim()) {
//         showError('请先输入您的回答');
//         return;
//     }
// 
//     if (!interviewState.threadId) {
//         showError('面试未开始，请先上传简历并开始面试');
//         return;
//     }
// 
//     // 在聊天区域显示用户的回答
//     addMessage('user', answer);
// 
//     try {
//         // ========== 步骤2：准备请求数据 ==========
//         // 获取认证信息（用户名）
//         const auth = getAuth();
//         const requestBody = {
//             thread_id: interviewState.threadId,  // 会话 ID
//             answer: answer,  // 用户的回答
//             user_name: auth.userName  // 用户名
//         };
// 
//         // ========== 步骤3：发送 HTTP POST 请求 ==========
//         // 使用 Fetch API 发送请求到流式接口
//         const response = await fetch(`${API_BASE_URL}/submit/stream`, {
//             method: 'POST',
//             headers: {
//                 'Content-Type': 'application/json'  // 请求体是 JSON 格式
//             },
//             body: JSON.stringify(requestBody)  // 将 JS 对象转换为 JSON 字符串
//         });
// 
//         // 检查响应状态
//         if (!response.ok) {
//             throw new Error('流式请求失败');
//         }
// 
//         // ========== 步骤4：获取 ReadableStream 并准备读取 ==========
//         // response.body 是一个 ReadableStream，可以逐块读取数据
//         const reader = response.body.getReader();
//         // TextDecoder 用于将二进制数据（Uint8Array）解码为文本（UTF-8）
//         const decoder = new TextDecoder();
// 
//         // ========== 步骤5：初始化累加变量 ==========
//         // 用于累加 LLM 逐字符输出的内容（打字机效果）
//         let feedbackContent = '';  // 累加反馈内容
//         let questionContent = '';  // 累加问题内容
//         let reportContent = '';    // 累加报告内容
//         let currentMessageDiv = null;  // 当前正在更新的消息 DOM 元素
// 
//         // ========== 步骤6：循环读取数据流 ==========
//         // ReadableStream 是异步的，需要使用 while 循环逐块读取
//         while (true) {
//             // 读取一块数据（chunk）
//             // done: 布尔值，表示流是否结束
//             // value: Uint8Array，包含二进制数据
//             const { done, value } = await reader.read();
//             if (done) break;  // 流结束，退出循环
// 
//             // ========== 步骤7：解码二进制数据为文本 ==========
//             // 将 Uint8Array 解码为 UTF-8 字符串
//             const chunk = decoder.decode(value);
//             // 按行分割（SSE 协议中，每条消息以 \n\n 结尾）
//             const lines = chunk.split('\n');
// 
//             // ========== 步骤8：逐行解析 SSE 消息 ==========
//             for (const line of lines) {
//                 // SSE 消息格式：data: {...}
//                 if (line.startsWith('data: ')) {
//                     // 提取 JSON 数据（去掉 "data: " 前缀）
//                     const data = line.slice(6);
// 
//                     // 跳过结束标记
//                     if (data === '[DONE]') {
//                         continue;
//                     }
// 
//                     try {
//                         // ========== 步骤9：解析 JSON 数据 ==========
//                         const json = JSON.parse(data);
// 
//                         // 处理错误消息
//                         if (json.error) {
//                             showError(json.error);
//                             return;
//                         }
// 
//                         // ========== 步骤10：根据消息类型处理（打字机效果的核心！）==========
// 
//                         // ---------- 反馈相关消息 ----------
//                         if (json.type === 'feedback_start') {
//                             // 反馈开始：重置累加变量，创建新的消息 DOM 元素
//                             feedbackContent = '';
//                             currentMessageDiv = addStreamingMessage('ai', '📊 反馈结果：\n\n');
//                         } else if (json.type === 'feedback' && json.content) {
//                             // 反馈内容：逐字符累加并更新 UI（打字机效果！）
//                             feedbackContent += json.content;  // 累加新内容
//                             updateStreamingMessage(currentMessageDiv, `📊 反馈结果：\n\n${feedbackContent}`);
//                         } else if (json.type === 'feedback_end') {
//                             // 反馈结束：保存到状态，清空当前消息元素
//                             interviewState.lastFeedback = feedbackContent;
//                             currentMessageDiv = null;
//                         }
// 
//                         // ---------- 问题相关消息 ----------
//                         else if (json.type === 'question_start') {
//                             // 问题开始：重置累加变量，创建新的消息 DOM 元素
//                             questionContent = '';
//                             currentMessageDiv = addStreamingMessage('ai', '❓ 下一个问题：\n\n');
//                         } else if (json.type === 'question' && json.content) {
//                             // 问题内容：逐字符累加并更新 UI（打字机效果！）
//                             questionContent += json.content;  // 累加新内容
//                             updateStreamingMessage(currentMessageDiv, `❓ 下一个问题：\n\n${questionContent}`);
//                         } else if (json.type === 'question_end') {
//                             // 问题结束：保存到状态，清空当前消息元素
//                             interviewState.currentQuestion = questionContent;
//                             currentMessageDiv = null;
//                         }
// 
//                         // ---------- 报告相关消息 ----------
//                         else if (json.type === 'report_start') {
//                             // 报告开始：重置累加变量，创建新的消息 DOM 元素
//                             reportContent = '';
//                             currentMessageDiv = addStreamingMessage('ai', '🎉 面试已完成！\n\n📋 最终报告：\n\n');
//                         } else if (json.type === 'report' && json.content) {
//                             // 报告内容：逐字符累加并更新 UI（打字机效果！）
//                             reportContent += json.content;  // 累加新内容
//                             updateStreamingMessage(currentMessageDiv, `🎉 面试已完成！\n\n📋 最终报告：\n\n${reportContent}`);
//                         } else if (json.type === 'report_end') {
//                             // 报告结束：保存到状态，清空当前消息元素
//                             interviewState.finalReport = reportContent;
//                             currentMessageDiv = null;
//                         }
// 
//                         // ---------- 流程控制消息 ----------
//                         else if (json.type === 'continue') {
//                             // 面试继续：更新轮次，保存状态
//                             interviewState.currentRound = json.round;
//                             interviewState.isReadOnly = false;
//                             saveInterviewState(interviewState);
//                         } else if (json.type === 'finished') {
//                             // 面试结束：更新状态，重新加载记录列表
//                             interviewState.currentRound = json.round;
//                             interviewState.currentQuestion = null;
//                             interviewState.isReadOnly = false;
//                             saveInterviewState(interviewState);
//                             // 重新加载记录列表（面试完成后会新增一条记录）
//                             renderInterviewRecords();
//                         }
//                     } catch (e) {
//                         // JSON 解析失败，打印错误日志
//                         console.error('解析 JSON 失败:', e, data);
//                     }
//                 }
//             }
//         }
// 
//     } catch (error) {
//         hideLoading();
//         showError(`提交失败：${error.message}`);
//     }
// }

// 处理提交答案（非流式版本 - 已弃用，使用 handleSubmitAnswerStream 代替）
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

            addMessage('ai', `🎉 面试已完成！\n\n最终报告：\n${result.report || '暂无报告'}`);

            // 重新加载记录列表（面试完成后会新增一条记录）
            renderInterviewRecords();
        } else {
            // 继续下一轮
            interviewState.currentQuestion = result.question || '';
            interviewState.currentRound = result.round;
            interviewState.isReadOnly = false;

            saveInterviewState(interviewState);
            // hideLoading();

            addMessage('ai', `✅ 反馈已生成！\n\n当前轮次：${result.round} / ${interviewState.maxRounds}\n\n❓ 下一个问题：\n${result.question || ''}`);
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
                item.addEventListener('click', () => {
                    loadInterviewRecord(threadId);
                });
            }
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
            <button class="chat-menu-btn">⋯</button>
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

        // 显示简历内容
        if (record.resume_text) {
            addMessage('ai', `📄 简历内容：\n\n${record.resume_text}`);
        }

        // 显示面试历史
        if (record.history && record.history.length > 0) {
            record.history.forEach((item, index) => {
                // 显示问题
                if (item.question) {
                    addMessage('ai', `📊 第 ${index + 1} 轮\n\n❓ 问题：\n${item.question}`);
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
            addMessage('ai', `🎉 最终报告：\n\n${record.report}`);
        }

        // 显示记录信息
        addMessage('ai', `📋 记录信息\n\n用户：${record.user_name}\n会话ID：${record.thread_id}\n创建时间：${record.created_at}\n总轮次：${record.history ? record.history.length : 0}`);

        // 更新面试状态（设置为只读模式）
        interviewState = {
            threadId: record.thread_id,
            currentQuestion: null,
            currentRound: record.history ? record.history.length : 0,
            maxRounds: record.history ? record.history.length : 0,
            resumeText: record.resume_text,
            lastFeedback: null,
            finalReport: record.report,
            isReadOnly: true  // 标记为只读模式
        };

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

    // 恢复面试状态
    interviewState = getInterviewState();

    // 清除待发送文件（页面刷新后重新开始）
    pendingFile = null;

    // 如果有进行中的面试，显示当前问题
    if (interviewState.currentQuestion && !interviewState.isReadOnly) {
        addMessage('ai', `📊 继续面试\n\n当前轮次：${interviewState.currentRound} / ${interviewState.maxRounds}\n\n❓ 问题：\n${interviewState.currentQuestion}`);
    }

    // 加载面试记录列表
    renderInterviewRecords();

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
        sendBtn.addEventListener('click', () => {
            const text = chatInput.value.trim();

            // 如果是只读模式（查看历史记录），不允许开始新面试
            if (interviewState.isReadOnly) {
                addMessage('ai', '当前正在查看历史记录，无法开始新面试。请点击"开启新对话"开始新的面试。');
                chatInput.value = '';
                autoResizeTextarea(chatInput);
                return;
            }

            // 如果有待发送的文件，优先处理文件上传和开始面试
            if (pendingFile) {
                handleStartInterview();
                chatInput.value = '';
                autoResizeTextarea(chatInput);
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
            } else if (!pendingFile) {
                // 没有文本也没有文件，提示用户
                addMessage('ai', '请先上传简历文件或输入内容。');
            }
        });

        // 回车发送（Shift+Enter换行）
        chatInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendBtn.click();
            }
        });

        // 自动调整高度
        chatInput.addEventListener('input', () => {
            autoResizeTextarea(chatInput);
        });
    }

}

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', () => {
    initMainPage();
});
