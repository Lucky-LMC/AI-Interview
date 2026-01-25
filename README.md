# AI智能面试辅助系统 V1.0 🤖

> 作者：刘梦畅

这是一个基于大语言模型（LLM）和 LangGraph 工作流引擎开发的智能模拟面试系统。它能够模拟真实的面试场景，通过简历解析、针对性提问、实时评估和智能资源推荐，帮助求职者全面提升面试表现。

## ✨ 项目亮点

- **🔄 LangGraph 工作流架构**：采用专业的 Agent 工作流设计，实现从简历解析到报告生成的完整面试逻辑
- **📊 工作流可视化**：支持生成工作流结构图，清晰展示节点间的流转关系
- **🤖 多 Agent 协作**：面试官 Agent、评价 Agent、教练 Agent 分工明确，各司其职
- **🔍 智能资源推荐**：基于 Tavily 搜索引擎，自动搜索并推荐真实的学习资源（书籍/课程/文档）
- **💬 交互式面试**：支持多轮问答，AI 根据回答动态调整问题难度
- **📝 专业评估报告**：面试结束后自动生成包含优势分析、不足改进、简历优化的完整报告
- **🎨 现代化界面**：简洁美观的前端设计，支持 Markdown 渲染和 PDF 预览
- **💾 数据持久化**：MySQL 数据库存储面试记录，支持历史记录查询

## 🛠️ 技术架构

### 后端技术栈
- **核心框架**: Python 3.9+, FastAPI
- **AI 框架**: LangChain, LangGraph
- **LLM**: 支持 OpenAI API 兼容接口（OpenAI、DeepSeek、Gemini 等）
- **搜索引擎**: Tavily API（联网搜索学习资源）
- **数据库**: SQLAlchemy + MySQL
- **文档解析**: PyPDF2, python-docx

### 前端技术栈
- **技术**: 原生 HTML, CSS, JavaScript
- **设计**: 现代简约设计，响应式布局，DeepSeek 风格
- **通信**: RESTful API
- **渲染**: Markdown 格式支持，PDF 在线预览

### 工作流架构图

系统采用 LangGraph 工作流引擎，实现了完整的面试流程自动化：

<div align="center">
    <img src="workflow_graph1.png" alt="AI智能面试工作流程图" width="350" />
</div>

**工作流说明**：
1. **START** → **parse_resume**（简历解析节点）：解析 PDF/Word 格式简历，提取关键信息
2. **parse_resume** → **interviewer_agent**（面试官 Agent）：基于简历生成针对性问题
3. **interviewer_agent** → **answer**（用户回答节点）：等待用户输入答案（中断点）
4. **answer** → **evaluator_agent**（评价 Agent）：对用户回答进行评分和反馈
5. **evaluator_agent** → **check_finish**（检查完成节点）：判断是否完成所有轮次
6. **check_finish** → **interviewer_agent**（继续）或 **search_resources**（结束）：条件路由
7. **search_resources** → **generate_report**（报告生成节点）：搜索学习资源并生成最终报告
8. **generate_report** → **END**：流程结束
```
Intervie示**：运行 `python backend/test_ization.在项目根目录生成最新的工作流可视化图

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
│   │   │   └── __init__.py
│   │   ├── nodes/            # 工作流节点
│   │   │   ├── parse_resume_node.py      # 简历解析节点
│   │   │   ├── ask_question_node.py      # 出题节点
│   │   │   ├── answer_node.py            # 回答节点
│   │   │   ├── evaluate_node.py          # 评价节点
│   │   │   ├── check_finish_node.py      # 检查完成节点
│   │   │   ├── search_resources_node.py  # 搜索资源节点
│   │   │   ├── generate_report_node.py   # 报告生成节点
│   │   │   └── __init__.py
│   │   ├── tools/            # 工具函数
│   │   │   ├── coach_tools.py   # 搜索工具（Tavily）
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
│   │   └── __init__.py
│   ├── main.py              # 应用入口
│   └── test_graph_visualization.py  # 工作流可视化脚本
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
│       ├── index.js        # 登录逻辑
│       ├── register.js     # 注册逻辑
│       └── main.js         # 面试逻辑
├── uploads/                # 简历文件存储目录
├── .env                    # 环境变量配置（需自行创建）
├── requirements.txt        # Python 依赖
├── workflow_graph.png      # 工作流可视化图
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
# 生成工作流可视化图（保存到项目根目录）
python backend/test_graph_visualization.py
```

生成的图片将保存到项目根目录：
- `workflow_graph.png`：完整版工作流图

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
- AI 会对你的回答进行评价并提出下一个问题
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
- 支持 PDF 和 Word 文档
- 自动提取关键信息（姓名、技能、项目经验等）
- 识别目标岗位

### 2. 动态问题生成（Interviewer Agent）
- 基于简历内容生成针对性问题
- 三轮面试：技术类、沟通类、HR类
- 避免重复提问
- 根据回答质量调整问题难度

### 3. 实时评价反馈（Evaluator Agent）
- 对每个回答进行评分
- 指出回答的优点和不足
- 给出改进建议

### 4. 智能资源推荐（Coach Agent）
- 自动分析面试表现中的薄弱点
- **联网搜索**最新的学习资料（书籍/课程/文档）
- 推荐真实可访问的资源链接
- 避免信息过载，精选高质量资源

### 5. 完整面试报告
- 整体表现总结
- 优势与不足分析
- 学习资源推荐（附带链接）
- 简历优化建议
- 录用建议

### 6. 数据持久化
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

1. **search_resources_node**（搜索资源节点）
   - 职责：调用 Coach Agent 搜索学习资源
   - 输入：简历 + 面试问答记录（简短版）
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
