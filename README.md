# AI Interview

一个面向 AI 应用开发岗位学习与实践的智能模拟面试系统。项目使用外层 LangGraph 状态图管理确定性业务流程，在工作流节点内部使用 LangChain `create_agent` 完成面试出题、学习资源推荐和 RAG 面试咨询，并围绕 Agent 调用边界、质量门禁、错误恢复、证据链和离线评测进行了工程化设计。

> 本项目适合作为 Agent / AI 应用开发的完整实践项目，不宣称具备高并发、分布式或企业生产环境能力。

## 核心能力

- 上传 PDF 简历，提取目标岗位、核心技能、项目经历和面试关注点
- 8 节点 LangGraph 面试工作流，支持人工回答中断与 SQLite Checkpoint 恢复
- 面试官 Agent 根据简历和轮次调用 Tavily 搜索并生成结构化问题
- 三层问题质量控制：确定性规则、边界案例结构化 Judge、一次重写后的模板兜底
- 反馈 Agent 分析薄弱项并检索带来源的学习资源
- 顾问 Agent 优先检索 Chroma 私有知识库，低置信度时降级到 Tavily
- Agent 模型调用、工具调用、重试次数均有显式预算
- 外部 I/O 节点支持异步执行、瞬时错误重试、超时和节点恢复路由
- SSE 输出 token、工具开始/结束和降级事件，前端可展示执行进度
- 本地离线评测覆盖路由、Agent 预算、问题质量和 RAG 来源

## 架构设计

### 外层工作流与内层 Agent

```mermaid
flowchart TB
    start([START]) --> parse["① 解析简历<br/>parse_resume"]
    parse --> validate{"② 简历有效性校验<br/>validate_resume"}

    validate -- 无效 --> invalid_end([END])
    validate -- 有效 --> interviewer[["③ 面试官 Agent<br/>interviewer_agent"]]

    interviewer --> review{"④ 问题质量门禁<br/>review_question"}
    review -- 重写一次 --> interviewer
    review -- 通过 --> answer["⑤ 等待候选人回答<br/>answer · interrupt"]

    answer --> finish{"⑥ 是否完成全部轮次<br/>check_finish"}
    finish -- 继续下一题 --> interviewer
    finish -- 完成 --> feedback[["⑦ 反馈 Agent<br/>feedback_agent"]]

    feedback --> report["⑧ 生成面试报告<br/>generate_report"]
    report --> done([END])

    classDef terminal fill:#172554,color:#ffffff,stroke:#172554,stroke-width:2px;
    classDef process fill:#eff6ff,color:#1e3a8a,stroke:#60a5fa,stroke-width:1.5px;
    classDef decision fill:#fffbeb,color:#78350f,stroke:#f59e0b,stroke-width:1.5px;
    classDef agent fill:#f5f3ff,color:#4c1d95,stroke:#8b5cf6,stroke-width:2px;
    classDef human fill:#ecfdf5,color:#064e3b,stroke:#34d399,stroke-width:1.5px;

    class start,invalid_end,done terminal;
    class parse,report process;
    class validate,review,finish decision;
    class interviewer,feedback agent;
    class answer human;
```

外层 `StateGraph` 负责顺序、条件路由、人工中断、状态持久化和错误恢复；内部三个 Agent 统一使用官方 `create_agent`，不维护自定义 ReAct 循环：

```mermaid
flowchart TB
    subgraph create_agent["三个 Agent 统一使用的 create_agent 运行循环"]
        direction TB
        agent_start([START]) --> model["模型推理<br/>model"]
        model -- tool_calls --> tools["执行工具<br/>tools"]
        tools -- ToolMessage --> model
        model -- 最终回答或结构化输出 --> agent_end([END])
    end

    classDef terminal fill:#172554,color:#ffffff,stroke:#172554,stroke-width:2px;
    classDef modelNode fill:#f5f3ff,color:#4c1d95,stroke:#8b5cf6,stroke-width:2px;
    classDef toolNode fill:#ecfeff,color:#164e63,stroke:#22d3ee,stroke-width:1.5px;

    class agent_start,agent_end terminal;
    class model modelNode;
    class tools toolNode;

    style create_agent fill:#faf5ff,stroke:#8b5cf6,stroke-width:2px;
```

上图用于解释稳定的架构语义。需要核对 LangGraph 编译后的全部节点、条件边和 Middleware hook 时，可运行 `python backend/utils/workflow_visualizer.py`，完整 `xray=True` 调试图会生成到 `.artifacts/langgraph_xray.png`，不作为 README 展示图。

| Agent | 主要工具 | 模型调用上限 | 工具调用上限 |
|---|---|---:|---:|
| Interviewer | `search_interview_questions` | 4 | 搜索 1 次 |
| Feedback | `search_learning_resources` | 6 | 搜索 3 次 |
| Consultant | `search_knowledge_base`、`tavily_search` | 5 | 总计 2 次；每个工具 1 次 |

中间件使用 `ModelRetryMiddleware`、`ToolRetryMiddleware`、`ModelCallLimitMiddleware` 和 `ToolCallLimitMiddleware`。只有分类为瞬时错误的异常允许重试；配置缺失和输入校验错误不会盲目重试。

### 问题质量门禁

1. 规则层检查问句格式、简历证据、历史重复风险和轮次难度。
2. 高置信问题直接通过，明显不合格问题直接重写。
3. 只有边界分数调用温度为 0 的结构化 LLM Judge。
4. 最多自动重写一次，第二次仍失败时使用与轮次对应的确定性模板。

该设计减少不必要的模型调用，同时避免质量审核自身形成无界循环。

### 工作流容错

外部 I/O 节点使用异步 API，并配置 `RetryPolicy`、节点超时和 `error_handler`：

- `parse_resume`：PDF 在线程池解析，LLM 异步提取；失败后进入简历校验终止路径
- `interviewer_agent`：瞬时错误重试一次；失败后生成已审核的模板问题
- `review_question`：Judge 超时后使用模板问题
- `feedback_agent`：失败不阻断报告，写入降级提示后继续
- `generate_report`：失败时生成不含虚构资源的基础报告

运行控制状态与面试业务状态分离，Checkpoint 中记录运行 ID、工作流版本、重试计数、降级组件和安全错误摘要。原始异常、API Key、完整 Prompt 和模型思考过程不会写入公开事件。

### 证据化 RAG

知识库按 Markdown 标题切分并写入以下元数据：

- `document_id`、`section`、`chunk_index`
- `content_hash`
- `embedding_model`、`splitter_version`
- `manifest_fingerprint`

检索服务扩大候选集后按内容哈希去重，保留距离分数和来源信息，并输出 `high`、`medium`、`low` 置信度。`fallback_required=true` 时，Consultant Agent 才进入 Tavily 联网搜索路径；工具失败时不会伪造 URL。

## 技术栈

- Python 3.11+
- FastAPI、SQLAlchemy、MySQL
- LangChain 1.3.13、LangGraph 1.2.9
- SQLite / AsyncSqliteSaver（工作流 Checkpoint）
- Chroma（本地向量库）
- OpenAI API 兼容模型与 Embedding 接口
- Tavily Search
- 原生 HTML、CSS、JavaScript、SSE
- pytest、pytest-asyncio

## 项目结构

```text
backend/
├── evaluation/             # 固定用例、确定性评测器与报告 CLI
├── graph/
│   ├── agents/             # 三个 create_agent 工厂
│   ├── nodes/              # 8 节点主面试流程
│   ├── quality/            # 问题规则、Judge 与兜底
│   ├── rag/                # Chroma 初始化、manifest、检索服务
│   ├── runtime/            # 契约、错误分类、预算、中间件、恢复、事件
│   ├── state/              # InterviewState
│   ├── tools/              # 标准化 ToolResult 工具
│   └── workflow/           # LangGraph 编排与异步 Checkpoint 会话
├── models/                 # SQLAlchemy 与 Pydantic 模型
├── routes/                 # 认证、面试、顾问 API
└── main.py                 # FastAPI 入口
frontend/                   # 原生前端
tests/
├── unit/
├── integration/
└── evaluation/
```

## 本地运行

### 1. 准备环境

需要 Python 3.11+、MySQL 5.7+/8.0+。Windows、macOS 和 Linux 均可本地运行。

```bash
git clone https://github.com/Lucky-LMC/AI-Interview.git
cd AI-Interview
python -m venv .venv
```

Windows PowerShell：

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

Linux / macOS：

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. 创建数据库

```sql
CREATE DATABASE interview_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

应用启动时由 SQLAlchemy 初始化业务表。

### 3. 配置环境变量

在项目根目录创建 `.env`：

```env
OPENAI_API_KEY=your_key
OPENAI_API_BASE=https://your-openai-compatible-endpoint/v1
MODEL_NAME=your-chat-model
TEMPERATURE=0.7
EMBEDDING_MODEL=BAAI/bge-m3

TAVILY_API_KEY=your_tavily_key
LANGSMITH_API_KEY=

DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=interview_db
DATABASE_URL=mysql+pymysql://root:your_password@localhost:3306/interview_db?charset=utf8mb4
```

聊天模型需要支持工具调用和结构化输出。`TAVILY_API_KEY` 缺失时，相关工具会返回不可重试的 `NOT_CONFIGURED` 结果，不影响无联网依赖的离线测试。

### 4. 初始化知识库

```bash
python backend/graph/rag/init_vectorstore.py
```

该命令读取 `backend/graph/rag/interview_knowledge_base.md`，重建本地 Chroma collection，并生成与文档、Embedding 模型和切分版本关联的 manifest。`chroma_db/` 属于本地运行产物，不提交到 Git。

### 5. 启动服务

```bash
python backend/main.py
```

访问 `http://localhost:8000`。主要接口：

- `POST /api/auth/register`、`POST /api/auth/login`
- `POST /api/interview/start`：上传 PDF 并返回第一个问题
- `POST /api/interview/submit`：提交答案并恢复 Checkpoint
- `GET /api/interview/records`：查询面试记录
- `POST /api/customer-service/chat`：顾问 SSE 对话
- `GET /api/customer-service/records`：查询顾问记录

## 测试与离线评测

安装开发依赖：

```powershell
pip install -r requirements-dev.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

运行全部测试：

```powershell
python -m compileall backend -q
python -m pytest -q
```

运行确定性、无需 API Key 的离线评测：

```powershell
python -m backend.evaluation.runner --offline --output .artifacts/evaluation
```

当前固定评测集包含 9 个用例，验证：

- 有效/无效简历路由
- Interviewer 与 Consultant 调用预算
- 问题规则的 approve / judge / rewrite 分流
- RAG 预期来源与低置信度降级

评测输出 `evaluation.json` 和 `evaluation.md`；任一必需用例失败时命令返回非零退出码。`.artifacts/` 仅用于本地验证，不提交到仓库。

## SSE 执行事件

顾问接口保留 token 流式输出，并提供：

- `thread_id`
- `tool_start`
- `tool_end`
- `degraded`
- `token`
- `done`
- `error`

为兼容原前端，后端仍发送旧 `status` 事件。公开事件只展示工具生命周期和降级摘要，不展示模型隐式思考过程。

## 数据边界

- MySQL：用户、面试记录、顾问对话记录
- SQLite：主面试工作流 Checkpoint
- Chroma：本地面试知识库向量索引
- `uploads/`：本地简历文件

`.env`、上传文件、Checkpoint、Chroma 索引、评测产物和本地设计文档均已加入 `.gitignore`。提交公开仓库前仍应执行密钥扫描，并确认历史提交中不存在真实凭据。

## 已知限制

- 当前认证和数据库层仍是单体应用实现，不是分布式生产架构
- 默认使用本地文件保存上传简历和 SQLite Checkpoint，多实例部署需要重新设计共享存储
- RAG 阈值依赖所选 Embedding 模型与知识库数据，切换模型后应重建索引并重新评测
- `PyPDF2` 已进入弃用状态，测试会提示迁移到 `pypdf`；本次工程化范围未包含 PDF 库迁移
- 联网搜索与模型真实效果依赖外部供应商、模型能力和配额；自动测试不调用真实 API

## License

MIT License

## Author

刘梦畅
