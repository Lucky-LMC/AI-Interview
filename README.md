# AI智能面试辅助系统 V1.0 🤖

> 作者：刘梦畅

这是一个基于大语言模型（LLM）和 LangGraph 工作流引擎开发的智能模拟面试系统。它能够模拟真实的面试场景，通过简历解析、针对性提问和智能资源推荐，帮助求职者全面提升面试表现。

## ✨ 核心亮点

### 🔄 LangGraph 工作流架构
- 采用专业的 Agent 工作流设计，实现从简历解析到报告生成的完整面试逻辑
- 支持工作流可视化，清晰展示节点间的流转关系
- 使用 SQLite Checkpointer 实现状态持久化和断点续传

### 🤖 多 Agent 协作系统
- **面试官 Agent**：基于简历生成针对性问题，支持多轮深入提问
- **反馈 Agent**：分析面试表现，联网搜索真实学习资源（Tavily API）
- **面试顾问 Agent**：采用 RAG（检索增强生成）技术，提供专业面试咨询

### 🔍 RAG 智能顾问系统
- **私有知识库**：使用 Chroma 向量数据库存储面试知识（本地部署）
- **语义检索**：基于 BAAI/bge-large-zh-v1.5 嵌入模型进行向量检索
- **兜底机制**：知识库无结果时自动降级到联网搜索（Tavily API）
- **相似度过滤**：距离分数 < 0.8 才返回结果，确保检索质量
- **对话记忆**：支持多轮对话，理解上下文

### 💾 双数据库架构
- **MySQL**：存储用户信息、面试记录、顾问对话记录（业务数据）
- **SQLite**：存储 LangGraph Checkpoint（对话状态和记忆）
- **数据同步**：创建、更新、删除操作同时作用于两个数据库
- **历史记录**：支持查询、恢复、删除历史会话

### 🎨 现代化 UI 设计
- **Glassmorphism**：玻璃拟态设计风格，磨砂玻璃侧边栏
- **Markdown 渲染**：GitHub 风格文档面板，支持代码高亮
- **响应式布局**：适配多种屏幕尺寸
- **流光效果**：赛博科技风微交互动画

## 🛠️ 技术架构

### 后端技术栈
- **核心框架**: Python 3.9+, FastAPI
- **AI 框架**: LangChain, LangGraph
- **LLM**: 支持 OpenAI API 兼容接口（推荐使用 Qwen2.5-14B-Instruct）
- **向量数据库**: Chroma（本地部署，用于 RAG 知识库）
- **嵌入模型**: BAAI/bge-large-zh-v1.5（硅基流动平台）
- **搜索引擎**: Tavily API（联网搜索学习资源和最新信息）
- **数据库**: 
  - MySQL 8.0+（用户数据、面试记录、顾问对话记录）
  - SQLite（LangGraph Checkpoint，对话状态持久化）
- **ORM**: SQLAlchemy 2.0+
- **文档解析**: PyPDF2

### 前端技术栈
- **核心**: 原生 HTML5, CSS3 (Variables + Flexbox/Grid), ES6+ JavaScript
- **设计风格**: **Glassmorphism** (玻璃拟态) + **Cyberpunk** (赛博科技风微交互)
- **文档渲染**: `marked.js` + GitHub-style CSS (优化版紧凑样式)
- **通信**: RESTful API + `fetch`
- **特性**: 响应式布局、动态流光效果、无阴影极简气泡、全屏沉浸体验、实时数据同步

### 系统架构全览图

系统包含两大核心工作流：主面试流程 和 智能客服流程。

<div align="center">
    <img src="system_architecture_graph.png" alt="AI智能面试系统全览图" width="500" />
</div>

**1. 主面试工作流（左图）**：
1. **START** → **parse_resume**（简历解析节点）：解析 PDF 格式简历，提取关键信息
2. **parse_resume** → **interviewer_agent**（面试官 Agent）：基于简历生成针对性问题
3. **interviewer_agent** → **answer**（用户回答节点）：等待用户输入答案（中断点）
4. **answer** → **check_finish**（检查完成节点）：判断是否完成所有轮次
5. **check_finish** → **interviewer_agent**（继续）或 **feedback_agent**（结束）：条件路由
6. **feedback_agent** → **generate_report**（报告生成节点）：搜索学习资源并生成最终报告
7. **generate_report** → **END**：流程结束

**2. 智能顾问工作流（右图）**：
- 专门处理用户的咨询问题（如"面试流程是什么"、"如何准备自我介绍"、"阿里巴巴面试考什么"）
- 采用 **RAG（检索增强生成）** 策略：
  1. **优先检索私有知识库**：使用 Chroma 向量数据库 + BAAI/bge-large-zh-v1.5 嵌入模型进行语义检索
  2. **相似度过滤**：距离分数 < 0.8 才返回结果，确保检索质量
  3. **兜底联网搜索**：若知识库无结果或相似度不足，自动调用 Tavily API 搜索最新信息
- 独立于主面试流程运行，支持多轮对话和记忆功能

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
│   │   │   ├── feedback_agent.py     # 反馈 Agent（搜索资源）
│   │   │   ├── consultant_agent.py   # 面试顾问 Agent（RAG + 搜索）
│   │   │   └── __init__.py
│   │   ├── nodes/            # 工作流节点
│   │   │   ├── parse_resume_node.py      # 简历解析节点
│   │   │   ├── ask_question_node.py      # 出题节点
│   │   │   ├── answer_node.py            # 回答节点（中断点）
│   │   │   ├── check_finish_node.py      # 检查完成节点
│   │   │   ├── feedback_node.py          # 搜索资源节点
│   │   │   ├── generate_report_node.py   # 报告生成节点
│   │   │   └── __init__.py
│   │   ├── tools/            # 工具函数
│   │   │   ├── feedback_tools.py     # 搜索工具（Tavily）
│   │   │   ├── interviewer_tools.py  # 面试工具
│   │   │   ├── consultant_tools.py   # 顾问工具（知识库+搜索）
│   │   │   └── __init__.py
│   │   ├── state/            # 状态定义
│   │   │   ├── interview_state.py  # 面试状态
│   │   │   └── __init__.py
│   │   ├── workflow/         # 工作流定义
│   │   │   ├── interview_workflow.py  # 面试工作流
│   │   │   └── __init__.py
│   │   ├── llm/              # LLM 辅助
│   │   │   ├── llm_helper.py    # LLM 实例管理（OpenAI + Embeddings）
│   │   │   └── __init__.py
│   │   ├── rag/              # RAG 知识库
│   │   │   ├── interview_knowledge_base.md  # 面试知识库文档
│   │   │   ├── init_vectorstore.py          # 向量数据库初始化脚本
│   │   │   └── chroma_db/                   # Chroma 向量数据库（自动生成）
│   │   └── __pycache__/
│   ├── models/               # 数据模型
│   │   ├── user.py                 # 用户模型
│   │   ├── interview_record.py     # 面试记录模型
│   │   ├── consultant_record.py    # 顾问对话记录模型
│   │   ├── schemas.py              # API 数据模型
│   │   └── __init__.py
│   ├── routes/              # API 路由
│   │   ├── interview_routes.py    # 面试相关接口
│   │   ├── consultant_routes.py   # 顾问相关接口
│   │   ├── auth_routes.py        # 用户认证接口
│   │   └── __init__.py
│   ├── utils/               # 工具函数
│   │   ├── pdf_parser.py              # PDF 解析工具
│   │   ├── workflow_visualizer.py     # 工作流可视化工具
│   │   ├── sync_checkpoints_with_mysql.py  # Checkpoint 同步工具
│   │   └── __init__.py
│   ├── main.py              # 应用入口
├── frontend/                # 前端代码
│   ├── index.html          # 登录页面
│   ├── register.html       # 注册页面
│   ├── interview.html      # 主页面（面试界面）
│   ├── consultant.html     # 顾问页面
│   ├── css/                # 样式文件
│   │   ├── common.css      # 公共样式
│   │   ├── index.css       # 登录页样式
│   │   ├── register.css    # 注册页样式
│   │   ├── interview.css   # 主页样式
│   │   └── consultant.css  # 顾问页样式
│   └── js/                 # JavaScript 脚本
│       ├── api.js          # API 请求封装
│       ├── index.js        # 登录逻辑
│       ├── register.js     # 注册逻辑
│       ├── interview.js    # 面试逻辑
│       └── consultant.js   # 顾问逻辑
├── uploads/                # 简历文件存储目录
├── checkpoints-sqlite/     # SQLite 持久化存储（LangGraph Checkpoint）
├── .env                    # 环境变量配置（需自行创建）
├── requirements.txt        # Python 依赖
├── system_architecture_graph.png # 系统架构全览图
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
python -m venv .venv

# 激活虚拟环境
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

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
# 推荐使用硅基流动 + Qwen2.5-14B-Instruct（速度快、效果好、免费）
OPENAI_API_KEY=your_api_key_here
OPENAI_API_BASE=https://api.siliconflow.cn/v1
MODEL_NAME=Qwen/Qwen2.5-14B-Instruct

# 温度参数（控制输出随机性，0.0-1.0）
TEMPERATURE=0.7

# Embedding 模型（用于 RAG 向量检索）
EMBEDDING_MODEL=BAAI/bge-large-zh-v1.5

# ========== 搜索工具配置 ==========
# Tavily API 密钥（用于搜索学习资源和最新信息）
# 获取地址：https://tavily.com/
TAVILY_API_KEY=tvly-xxxxxxxxx

# ========== 数据库配置 ==========
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=interview_db
DATABASE_URL=mysql+pymysql://root:your_password@localhost:3306/interview_db?charset=utf8mb4

# ========== LangSmith 配置（可选，用于调试）==========
LANGSMITH_API_KEY=
```

### 5. 初始化 RAG 知识库
```bash
# 初始化向量数据库（首次运行或更新知识库后执行）
python backend/graph/rag/init_vectorstore.py

# 成功后会在 backend/graph/rag/chroma_db/ 目录生成向量数据库文件
```

### 6. 启动服务
```bash
# 进入后端目录
cd backend

# 启动服务
python main.py

# 服务将在 http://localhost:8000 启动
# 前端页面可通过 http://localhost:8000 访问
```

### 7. 可视化工作流（可选）
```bash
# 生成系统全览图（保存到项目根目录）
python backend/utils/workflow_visualizer.py
```

生成的图片将保存到项目根目录：
- `system_architecture_graph.png`：包含面试工作流和顾问 Agent 的系统全览图

## 📖 使用说明

### 1. 注册/登录
- 访问 `http://localhost:8000`
- 首次使用需要注册账号
- 注册成功后自动跳转到登录页面

### 2. 开始面试
- 登录后进入主页面
- 点击"上传简历"按钮，选择 PDF 格式的简历
- 设置面试轮数（默认 3 轮）
- 点击"开始面试"

### 3. 面试过程
- 系统会自动解析简历并生成第一个问题
- 在输入框中输入你的回答
- 点击"提交回答"或按 Enter 发送
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

### 5. 智能面试顾问
- 点击左侧"智能面试顾问"按钮进入顾问页面
- 可以随时咨询面试相关问题：
  - 面试流程和技巧（如"STAR 法则是什么"）
  - 简历优化建议（如"如何写好简历"）
  - 自我介绍准备（如"自我介绍怎么说"）
  - 行为面试问题（如"如何回答离职原因"）
  - 公司/岗位面试题（如"阿里巴巴面试考什么"）
- 顾问采用 RAG 技术：
  - 优先检索私有知识库（Chroma 向量数据库）
  - 知识库无结果或相似度不足时，自动联网搜索最新信息
- 支持多轮对话，具有记忆功能

### 6. 历史记录
- 左侧边栏显示所有历史记录
- 按时间分组：今天、昨天、前天、7天内、30天内、更早
- 点击记录可查看详细内容
- 支持删除记录（同时删除数据库和 Checkpoint）

## 💡 数据存储说明

### 双数据库架构

本系统采用 **MySQL + SQLite** 双数据库架构：

#### 1. MySQL（主数据库）
存储业务数据，支持多用户、跨设备访问：

**users 表**：用户信息
- user_name（主键）
- password_hash
- created_at

**interview_records 表**：面试记录
- thread_id（主键）
- user_name（外键）
- resume_text（简历内容）
- resume_file_path（PDF 文件路径）
- resume_file_name（原始文件名）
- history（面试问答历史，JSON）
- report（最终报告）
- is_finished（是否完成）
- created_at / updated_at

**consultant_records 表**：顾问对话记录
- thread_id（主键）
- user_name（外键）
- title（会话标题，自动从第一条消息提取）
- messages（对话历史，JSON）
- created_at / updated_at

#### 2. SQLite（Checkpoint 数据库）
存储 LangGraph 的对话状态和记忆，位于 `checkpoints-sqlite/checkpoints.sqlite`：

**checkpoints 表**：Agent 执行的每个状态快照
- thread_id（会话ID）
- checkpoint_id（快照ID）
- checkpoint_ns（命名空间）
- parent_checkpoint_id（父快照ID）
- checkpoint（状态数据，二进制）

**writes 表**：Agent 的写入操作记录
- thread_id
- checkpoint_id
- task_id
- channel
- value（写入的数据）

#### 数据同步机制

- **创建记录**：同时写入 MySQL 和 SQLite
- **更新记录**：MySQL 更新业务数据，SQLite 追加新的 checkpoint
- **删除记录**：同时删除 MySQL 记录和 SQLite checkpoint
- **查询记录**：从 MySQL 读取，SQLite 用于恢复对话状态

#### Checkpoint 管理

随着使用，SQLite 中的 checkpoint 会越来越多（每次 Agent 执行都会产生多个快照）。提供了管理工具：

```bash
# 查看 checkpoint 数据并同步清理
python -m backend.utils.sync_checkpoints_with_mysql
```

该工具会：
1. 对比 MySQL 和 SQLite 中的 thread_id
2. 找出"孤儿" checkpoint（在 SQLite 但不在 MySQL）
3. 询问是否删除
4. 显示最终的数据状态

**建议**：定期运行此工具，保持数据一致性。

## 🎯 核心功能详解

### 1. 智能简历解析
- 支持 PDF 格式简历
- 使用 PyPDF2 提取原始文本
- LLM 智能提取关键信息：
  - 目标岗位（智能推断）
  - 个人信息（姓名、学历、工作年限）
  - 核心技能
  - 项目经历亮点
  - 面试关注点
- 输出结构化 Markdown 格式

### 2. 动态问题生成（Interviewer Agent）
- 基于简历内容生成针对性问题
- 结合项目经验提问，避免纯概念题
- 多轮面试，逐步深入
- 避免重复提问
- 支持自定义面试轮数

### 3. RAG 智能顾问（Consultant Agent）
- **私有知识库**：
  - 使用 Chroma 向量数据库（本地部署）
  - 嵌入模型：BAAI/bge-large-zh-v1.5（硅基流动平台）
  - 知识库内容：面试流程、简历优化、行为面试、薪资谈判、STAR 法则等
  - 按 Markdown 标题切分文档，提高检索精度
- **语义检索**：
  - 理解用户问题的语义，而非简单关键词匹配
  - 相似度阈值：距离分数 < 0.8（越小越相似）
  - 返回最相关的 2 个文档块
- **兜底机制**：
  - 知识库无结果或相似度不足时，自动调用 Tavily API 联网搜索
  - 重试机制：搜索失败时自动重试 3 次
- **对话记忆**：
  - 使用 LangGraph Checkpoint 存储对话状态
  - 支持多轮对话，理解上下文
- **知识库更新**：
  - 手动更新模式：修改 `backend/graph/rag/interview_knowledge_base.md` 后
  - 运行 `python backend/graph/rag/init_vectorstore.py` 重新初始化向量数据库

### 4. 智能资源推荐（Feedback Agent）
- 自动分析面试表现中的薄弱点
- **联网搜索**最新的学习资料（书籍/课程/文档）
- 推荐真实可访问的资源链接
- 精选高质量资源（每个不足推荐 2-3 个资源）

### 5. 完整面试报告
- 整体表现总结
- 优势与不足分析
- 学习资源推荐（附带链接）
- 简历优化建议
- 录用建议

### 6. 数据持久化
- MySQL 数据库存储用户信息和面试记录
- SQLite 存储 LangGraph Checkpoint（对话状态）
- 支持历史记录查询和恢复
- 支持简历文件预览（PDF）
- 删除记录时同步清理数据库和文件

## 🔧 技术特性详解

### LangGraph 工作流设计
- **状态管理**：使用 TypedDict 定义面试状态，类型安全
- **节点编排**：清晰的节点职责划分，易于维护和扩展
- **条件路由**：根据面试进度动态决策下一步
- **中断机制**：在用户回答前中断，实现交互式对话
- **Checkpointer**：使用 SqliteSaver 实现状态持久化和断点续传

### RAG 技术实现
- **向量数据库**：Chroma（本地部署，无需外部服务）
- **嵌入模型**：BAAI/bge-large-zh-v1.5（中文优化，768 维向量）
- **文档切分**：按 Markdown 二级和三级标题切分，保持语义完整性
- **相似度计算**：使用余弦距离，阈值 < 0.8
- **懒加载**：向量数据库单例模式，首次调用时加载
- **手动更新**：知识库更新后需手动运行初始化脚本

### 两节点报告生成架构
为了确保 Agent 可靠地调用搜索工具，采用了两节点设计：

1. **feedback_node**（搜索资源节点）
   - 职责：调用 Feedback Agent 搜索学习资源
   - 输入：面试问答记录（简短版，只包含问题和回答）
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
- **单例模式**：LLM 实例和向量数据库复用，提高性能
- **错误处理**：完善的异常捕获和日志记录
- **事务回滚**：操作失败时自动清理数据库、文件和 Checkpoint

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

### 更新 RAG 知识库
1. 编辑 `backend/graph/rag/interview_knowledge_base.md`
2. 使用 Markdown 格式，按标题组织内容
3. 运行初始化脚本：
   ```bash
   python backend/graph/rag/init_vectorstore.py
   ```
4. 重启后端服务

### API 接口说明

#### 面试相关接口
- `POST /api/interview/start`：开始面试（上传简历）
- `POST /api/interview/submit`：提交回答
- `GET /api/interview/resume/{thread_id}`：获取简历 PDF
- `GET /api/interview/records`：获取面试记录列表
- `GET /api/interview/records/{thread_id}`：获取面试记录详情
- `DELETE /api/interview/records/{thread_id}`：删除面试记录

#### 顾问相关接口
- `POST /api/customer-service/chat`：与顾问对话
- `GET /api/customer-service/records`：获取顾问对话记录列表
- `GET /api/customer-service/records/{thread_id}`：获取对话记录详情
- `DELETE /api/customer-service/records/{thread_id}`：删除对话记录

#### 用户认证接口
- `POST /api/auth/register`：用户注册
- `POST /api/auth/login`：用户登录

## 🔍 常见问题

### 1. 如何获取 Tavily API Key？
访问 [Tavily 官网](https://tavily.com/) 注册账号，在控制台获取 API Key。免费版每月有 1000 次搜索额度。

### 2. 支持哪些 LLM？
支持所有兼容 OpenAI API 的模型，推荐使用：
- **Qwen2.5-14B-Instruct**（推荐）：速度快、效果好、免费（硅基流动平台）
- **Qwen2.5-7B-Instruct**：更快，适合资源受限环境
- **DeepSeek-V3**：性能强大但速度较慢
- **GPT-4/GPT-3.5**：OpenAI 官方模型

注意：模型必须支持 Function Calling（工具调用）功能。

### 3. 如何修改面试轮数？
在前端上传简历时可以设置，或在 `backend/routes/interview_routes.py` 中修改默认值。

### 4. 数据库连接失败怎么办？
检查 `.env` 文件中的数据库配置是否正确，确保 MySQL 服务已启动。

### 5. Checkpoint 数据太多怎么办？
运行清理工具：
```bash
python -m backend.utils.sync_checkpoints_with_mysql
```
该工具会删除 MySQL 中不存在的"孤儿" checkpoint，保持数据一致性。

### 6. 如何切换 LLM 模型？
修改 `.env` 文件中的 `MODEL_NAME` 和 `OPENAI_API_BASE`，然后重启后端服务。

### 7. 顾问 Agent 不调用工具怎么办？
- 确保使用的模型支持工具调用（Function Calling）
- 推荐使用 Qwen2.5 系列（工具调用稳定）
- 检查提示词是否明确要求调用工具
- 查看后端日志，确认工具是否被正确注册

### 8. RAG 知识库如何更新？
1. 编辑 `backend/graph/rag/interview_knowledge_base.md`
2. 运行初始化脚本：`python backend/graph/rag/init_vectorstore.py`
3. 重启后端服务

### 9. 向量检索效果不好怎么办？
- 调整相似度阈值（在 `consultant_tools.py` 中修改 `< 0.8`）
- 增加返回的文档块数量（修改 `k=2`）
- 优化知识库内容，使用更清晰的标题和结构
- 考虑使用更强大的嵌入模型

### 10. 如何部署到生产环境？
- 使用 Gunicorn 或 uWSGI 作为 WSGI 服务器
- 使用 Nginx 作为反向代理
- 配置 HTTPS 证书
- 修改 CORS 配置，限制允许的域名
- 定期备份 MySQL 数据库
- 定期清理 SQLite checkpoint
- 使用环境变量管理敏感信息

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
- [Chroma](https://www.trychroma.com/) - 向量数据库
- [硅基流动](https://siliconflow.cn/) - LLM 和 Embedding 模型服务

---

**注意**：本项目仅供学习和研究使用，请勿用于商业用途。
