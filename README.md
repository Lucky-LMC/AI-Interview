# AI智能面试辅助系统 V1.0 🤖

> 作者：刘梦畅

这是一个基于大语言模型（LLM）和 LangGraph 工作流引擎开发的智能模拟面试系统。它能够模拟真实的面试场景，通过简历解析、针对性提问和智能资源推荐，帮助求职者全面提升面试表现。

## ✨ 项目亮点

- **🔄 LangGraph 工作流架构**：采用专业的 Agent 工作流设计，实现从简历解析到报告生成的完整面试逻辑
- **📊 工作流可视化**：支持生成工作流结构图，清晰展示节点间的流转关系
- **🤖 多 Agent 协作**：面试官 Agent、教练 Agent、客服 Agent 分工明确，各司其职
- **� 智能客服助手**：专门的 RAG 客服 Agent，解答面试流程、技巧等问题，支持私有知识库 + 联网搜索兜底
- **�🔍 智能资源推荐**：基于 Tavily 搜索引擎，自动搜索并推荐真实的学习资源（书籍/课程/文档）
- **💬 交互式面试**：支持多轮问答，基于简历项目经验提出针对性问题
- **📝 完整面试报告**：面试结束后自动生成包含优势分析、不足改进、简历优化的完整报告
- **🎨 极致 UI 体验**：采用 **Glassmorphism（玻璃拟态）** 设计风格，配合磨砂玻璃侧边栏和流光动态效果
- **📄 沉浸式阅读**：简历拆解、面试题、最终报告均采用 **GitHub 风格 Markdown 文档面板**，支持代码高亮与紧凑排版
- **💾 数据持久化**：MySQL 数据库存储面试记录，支持历史记录查询和断点续传

## 🛠️ 技术架构

### 后端技术栈
- **核心框架**: Python 3.9+, FastAPI
- **AI 框架**: LangChain, LangGraph
- **LLM**: 支持 OpenAI API 兼容接口（OpenAI、DeepSeek、Gemini 等）
- **搜索引擎**: Tavily API（联网搜索学习资源）
- **数据库**: SQLAlchemy + MySQL
- **文档解析**: PyPDF2, python-docx

### 前端技术栈
- **核心**: 原生 HTML5, CSS3 (Variables + Flexbox/Grid), ES6+ JavaScript
- **设计风格**: **Glassmorphism** (玻璃拟态) + **Cyberpunk** (赛博科技风微交互)
- **文档渲染**: `marked.js` + GitHub-style CSS (优化版紧凑样式)
- **通信**: RESTful API + `fetch`
- **特性**: 响应式布局、动态流光效果、无阴影极简气泡、全屏沉浸体验

### 系统架构全览图

系统包含两大核心工作流：主面试流程 和 智能客服流程。

<div align="center">
    <img src="system_architecture_graph.png" alt="AI智能面试系统全览图" width="500" />
</div>

**1. 主面试工作流（左图）**：
1. **START** → **parse_resume**（简历解析节点）：解析 PDF/Word 格式简历，提取关键信息
2. **parse_resume** → **interviewer_agent**（面试官 Agent）：基于简历生成针对性问题
3. **interviewer_agent** → **answer**（用户回答节点）：等待用户输入答案（中断点）
4. **answer** → **check_finish**（检查完成节点）：判断是否完成所有轮次
5. **check_finish** → **interviewer_agent**（继续）或 **coach_agent**（结束）：条件路由
6. **coach_agent** → **generate_report**（报告生成节点）：搜索学习资源并生成最终报告
7. **generate_report** → **END**：流程结束

**2. 智能客服工作流（右图）**：
- 专门处理用户的咨询问题（如"面试流程是什么"、"如何准备自我介绍"）
- 采用 **RAG（检索增强生成）** 策略：
  1. 优先检索 **私有知识库**（FAQ文档）
  2. 若无结果，自动降级调用 **联网搜索** 工具
- 独立于主面试流程运行，提供随时随地的帮助

> 💡 **提示**：运行 `python backend/utils/workflow_visualizer.py` 可在项目根目录生成最新的系统全览图

## 📂 项目结构

```
Interview/
├── backend/                    # 后端代码
│   ├── config/                # 配置模块
│   │   ├── config.py         # 环境变量配置
│   │   ├── database.py       # 数据库配置
│   │   └── __init__.py
│   ├── graph/                 # LangGraph 工作流
│   │   ├── agents/           # Agent 定义
│   │   │   ├── interviewer_agent.py  # 面试官 Agent
│   │   │   ├── coach_agent.py        # 教练 Agent（搜索资源）
│   │   │   ├── customer_service_agent.py # 客服 Agent（RAG + 搜索）
│   │   │   └── __init__.py
│   │   ├── nodes/            # 工作流节点
│   │   │   ├── parse_resume_node.py      # 简历解析节点
│   │   │   ├── ask_question_node.py      # 出题节点
│   │   │   ├── answer_node.py            # 回答节点（中断点）
│   │   │   ├── check_finish_node.py      # 检查完成节点
│   │   │   ├── coach_node.py             # 搜索资源节点
│   │   │   ├── generate_report_node.py   # 报告生成节点
│   │   │   └── __init__.py
│   │   ├── tools/            # 工具函数
│   │   │   ├── coach_tools.py        # 搜索工具（Tavily）
│   │   │   ├── interviewer_tools.py  # 面试工具
│   │   │   └── __init__.py
│   │   ├── state/            # 状态定义
│   │   │   ├── interview_state.py  # 面试状态
│   │   │   └── __init__.py
│   │   ├── workflow/         # 工作流定义
│   │   │   ├── interview_workflow.py  # 面试工作流
│   │   │   └── __init__.py
│   │   ├── llm/              # LLM 辅助
│   │   │   ├── llm_helper.py    # LLM 实例管理
│   │   │   └── __init__.py
│   │   └── __pycache__/
│   ├── models/               # 数据模型
│   │   ├── user.py          # 用户模型
│   │   ├── interview_record.py  # 面试记录模型
│   │   ├── schemas.py       # API 数据模型
│   │   └── __init__.py
│   ├── routes/              # API 路由
│   │   ├── interview_routes.py  # 面试相关接口
│   │   ├── auth_routes.py      # 用户认证接口
│   │   └── __init__.py
│   ├── utils/               # 工具函数
│   │   ├── pdf_parser.py   # PDF 解析工具
│   │   ├── workflow_visualizer.py # 工作流可视化工具
│   │   └── __init__.py
│   ├── main.py              # 应用入口
├── frontend/                # 前端代码
│   ├── index.html          # 登录页面
│   ├── register.html       # 注册页面
│   ├── main.html           # 主页面（面试界面）
│   ├── css/                # 样式文件
│   │   ├── common.css      # 公共样式
│   │   ├── index.css       # 登录页样式
│   │   ├── register.css    # 注册页样式
│   │   └── main.css        # 主页样式
│   └── js/                 # JavaScript 脚本
│       ├── api.js          # API 请求封装
│       ├── index.js        # 登录逻辑
│       ├── register.js     # 注册逻辑
│       └── main.js         # 面试逻辑
├── uploads/                # 简历文件存储目录
├── checkpoints-sqlite/     # SQLite 持久化存储
├── .env                    # 环境变量配置（需自行创建）
├── requirements.txt        # Python 依赖
├── system_architecture_graph.png # 系统架构全览图
├── Git操作指南.md          # Git 使用指南
└── README.md              # 项目说明
```

## 🚀 快速上手

### 1. 环境准备
确保你的电脑已安装：
- Python 3.9+
- MySQL 5.7+
- Git

### 2. 克隆并安装
```bash
# 克隆项目
git clone https://github.com/Lucky-LMC/AI-Interview.git
cd AI-Interview

# 创建虚拟环境（推荐）
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖（使用清华镜像加速）
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 3. 配置数据库
```bash
# 登录 MySQL
mysql -u root -p

# 创建数据库
CREATE DATABASE interview_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# 创建用户并授权（可选）
CREATE USER 'interview_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON interview_db.* TO 'interview_user'@'localhost';
FLUSH PRIVILEGES;
```

### 4. 配置环境变量
在项目根目录创建 `.env` 文件并配置以下参数：

```env
# ========== LLM 配置 ==========
# OpenAI API 配置（或兼容接口，如 DeepSeek）
OPENAI_API_KEY=your_api_key_here
OPENAI_API_BASE=https://api.openai.com/v1
MODEL_NAME=gpt-4

# 温度参数（控制输出随机性，0.0-1.0）
TEMPERATURE=0.7

# ========== 搜索工具配置 ==========
# Tavily API 密钥（用于搜索学习资源）
# 获取地址：https://tavily.com/
TAVILY_API_KEY=tvly-xxxxxxxxx

# ========== 数据库配置 ==========
DB_HOST=localhost
DB_PORT=3306
DB_USER=interview_user
DB_PASSWORD=your_password
DB_NAME=interview_db
DATABASE_URL=mysql+pymysql://interview_user:your_password@localhost:3306/interview_db

# ========== Gemini 配置（可选）==========
GEMINI_API_KEY=
GEMINI_API_BASE=
GEMINI_MODEL_NAME=

# ========== LangSmith 配置（可选，用于调试）==========
LANGSMITH_API_KEY=
```

### 5. 启动服务
```bash
# 进入后端目录
cd backend

# 启动服务
python main.py

# 服务将在 http://localhost:8000 启动
# 前端页面可通过 http://localhost:8000 访问
```

### 6. 可视化工作流（可选）
```bash
# 生成系统全览图（保存到项目根目录）
python backend/utils/workflow_visualizer.py
```

生成的图片将保存到项目根目录：
- `system_architecture_graph.png`：包含面试工作流和客服 Agent 的系统全览图

## 📖 使用说明

### 1. 注册/登录
- 访问 `http://localhost:8000`
- 首次使用需要注册账号
- 注册成功后自动跳转到登录页面

### 2. 开始面试
- 登录后进入主页面
- 点击"上传简历"按钮，选择 PDF 或 Word 格式的简历
- 设置面试轮数（默认 3 轮）
- 点击"开始面试"

### 3. 面试过程
- 系统会自动解析简历并生成第一个问题
- 在输入框中输入你的回答
- 点击"提交回答"或按 Ctrl+Enter 发送
- 系统会继续提出下一个问题
- 重复此过程直到完成所有轮次

### 4. 查看报告
- 面试结束后，系统会自动生成详细的面试报告
- 报告包含：
  - 📊 整体表现总结
  - ✅ 优势分析
  - ⚠️ 不足与改进建议（附带学习资源链接）
  - 📝 简历优化建议
  - 🎯 录用建议

### 5. 历史记录
- 点击左侧边栏的历史记录
- 查看之前的面试记录
- 点击记录可查看详细内容

## 🎯 核心功能

### 1. 智能简历解析
- 支持 PDF 文档
- 自动提取关键信息（姓名、技能、项目经验等）
- 识别目标岗位

### 2. 动态问题生成（Interviewer Agent）
- 基于简历内容生成针对性问题
- 结合项目经验提问，避免纯概念题
- 三轮面试，逐步深入
- 避免重复提问

### 3. 智能资源推荐（Coach Agent）
- 自动分析面试表现中的薄弱点
- **联网搜索**最新的学习资料（书籍/课程/文档）
- 推荐真实可访问的资源链接
- 精选高质量资源

### 4. 完整面试报告
- 整体表现总结
- 优势与不足分析
- 学习资源推荐（附带链接）
- 简历优化建议
- 录用建议

### 5. 数据持久化
- MySQL 数据库存储用户信息和面试记录
- 支持历史记录查询
- 支持简历文件预览

## 🔧 技术特性

### LangGraph 工作流设计
- **状态管理**：使用 TypedDict 定义面试状态，类型安全
- **节点编排**：清晰的节点职责划分，易于维护和扩展
- **条件路由**：根据面试进度动态决策下一步
- **中断机制**：在用户回答前中断，实现交互式对话
- **Checkpointer**：使用 MemorySaver 实现状态持久化

### 两节点报告生成架构
为了确保 Agent 可靠地调用搜索工具，采用了两节点设计：

1. **coach_node**（搜索资源节点）
   - 职责：调用 Coach Agent 搜索学习资源
   - 输入：面试问答记录（简短版）
   - 输出：搜索结果存入 `state['learning_resources']`
   - 优势：输入简短，任务明确，Agent 必定调用工具

2. **generate_report_node**（生成报告节点）
   - 职责：生成完整报告（包含简历优化）
   - 实现：使用普通 LLM.invoke()，不再用 Agent
   - 输入：简历 + 面试记录 + 学习资源（已搜索好）
   - 输出：完整的 Markdown 报告

### 代码架构
- **分层设计**：配置层、数据层、业务层、路由层清晰分离
- **包管理**：规范的 Python 包结构，便于维护和扩展
- **类型安全**：使用 TypedDict 和类型注解
- **单例模式**：LLM 实例复用，提高性能
- **错误处理**：完善的异常捕获和日志记录

## 📝 开发说明

### 添加新节点
1. 在 `backend/graph/nodes/` 创建新节点文件
2. 定义节点函数，接收 `InterviewState` 并返回更新后的状态
3. 在 `backend/graph/nodes/__init__.py` 导出
4. 在 `backend/graph/workflow/interview_workflow.py` 中添加到工作流

### 自定义 Agent
1. 在 `backend/graph/agents/` 创建新 Agent
2. 使用 `create_react_agent` 创建 Agent 实例
3. 定义 Agent 的系统提示词
4. 在相应节点中调用

### 添加新工具
1. 在 `backend/graph/tools/` 创建新工具文件
2. 使用 `@tool` 装饰器定义工具函数
3. 在工具列表中导出
4. 在 Agent 创建时传入工具列表

### API 接口说明
- `POST /api/interview/start`：开始面试（上传简历）
- `POST /api/interview/submit`：提交回答
- `GET /api/interview/resume/{thread_id}`：获取简历 PDF
- `GET /api/interview/records`：获取面试记录列表
- `GET /api/interview/records/{thread_id}`：获取面试记录详情
- `POST /api/auth/register`：用户注册
- `POST /api/auth/login`：用户登录

## 🔍 常见问题

### 1. 如何获取 Tavily API Key？
访问 [Tavily 官网](https://tavily.com/) 注册账号，在控制台获取 API Key。

### 2. 支持哪些 LLM？
支持所有兼容 OpenAI API 的模型，包括：
- OpenAI（GPT-4, GPT-3.5）
- DeepSeek
- 通义千问
- 其他兼容接口

### 3. 如何修改面试轮数？
在前端上传简历时可以设置，或在 `backend/routes/interview_routes.py` 中修改默认值。

### 4. 数据库连接失败怎么办？
检查 `.env` 文件中的数据库配置是否正确，确保 MySQL 服务已启动。

### 5. 如何部署到生产环境？
- 使用 Gunicorn 或 uWSGI 作为 WSGI 服务器
- 使用 Nginx 作为反向代理
- 配置 HTTPS 证书
- 修改 CORS 配置，限制允许的域名

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

### 贡献流程
1. Fork 本仓库
2. 创建你的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交你的修改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开一个 Pull Request

## 📄 许可证

MIT License

## 👨‍💻 作者

刘梦畅

## 🙏 致谢

- [LangChain](https://github.com/langchain-ai/langchain) - AI 应用开发框架
- [LangGraph](https://github.com/langchain-ai/langgraph) - 工作流编排引擎
- [FastAPI](https://fastapi.tiangolo.com/) - 现代化的 Web 框架
- [Tavily](https://tavily.com/) - AI 搜索引擎

---

**注意**：本项目仅供学习和研究使用，请勿用于商业用途。
