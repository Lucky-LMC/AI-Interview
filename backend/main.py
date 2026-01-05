# AI模拟面试系统v1.0，作者刘梦畅
"""
FastAPI 主入口文件
python -m http.server 8080 -d frontend
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径（必须在其他导入之前）
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routes import interview_router, auth_router
from backend.models import init_db

# 创建 FastAPI 应用
app = FastAPI(
    title="AI 模拟面试系统 API",
    description="基于 LangGraph 的智能面试系统后端服务",
    version="1.0.0"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(interview_router)
app.include_router(auth_router)

# 初始化数据库（确保用户表存在）
init_db()


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "AI 模拟面试系统 API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        # host="172.18.174.107",
        # python -m http.server 8080
        host="0.0.0.0",
        port=8000,
        reload=True
    )
