# AI-Interview 模拟面试系统 🤖

这是一个基于大语言模型（LLM）开发的智能模拟面试系统。它能够模拟真实的面试场景，通过简历解析、针对性提问和实时评估，帮助求职者提升面试表现。

## ✨ 项目亮点
- **多节点工作流**：采用 LangGraph 架构，实现从简历解析到报告生成的完整面试逻辑。
- **智能交互**：AI 会根据你的回答进行追问，模拟真实面试的深度。
- **全栈实现**：包含完整的 Python 后端接口和简洁美观的前端交互界面。
- **专业评估**：面试结束后自动生成多维度的评价报告，指出你的优缺点。

## 🛠️ 技术架构
- **后端核心**: Python, FastAPI
- **AI 框架**: LangChain, LangGraph
- **前端技术**: 原生 HTML, CSS, JavaScript (现代简约设计)
- **数据处理**: 异步处理面试状态与记录

## 📂 目录结构
- `backend/`: 存放面试逻辑、路由接口及 AI 节点定义。
- `frontend/`: 存放前端页面、样式及交互脚本。
- [models.json](cci:7://file:///d:/py/project/Interview/models.json:0:0-0:0): 预设的面试模型配置。
- [requirements.txt](cci:7://file:///d:/py/project/Interview/requirements.txt:0:0-0:0): 项目所需的 Python 依赖库。

## 🚀 快速上手

### 1. 环境准备
确保你的电脑已安装 Python 3.9+ 以及 Git。

### 2. 克隆并安装
```bash
# 克隆项目
git clone [https://github.com/Lucky-LMC/AI-Interview.git](https://github.com/Lucky-LMC/AI-Interview.git)

# 进入目录
cd AI-Interview

# 安装依赖
pip install -r requirements.txt
