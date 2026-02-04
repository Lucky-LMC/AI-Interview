# AI智能面试辅助系统V1.0，作者刘梦畅
"""
FastAPI 主入口文件
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径（必须在其他导入之前）
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routes import interview_router, auth_router
from backend.routes.consultant_routes import router as customer_service_router
from backend.config import init_db

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

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# 注册路由
app.include_router(interview_router)
app.include_router(auth_router)
app.include_router(customer_service_router)  # 新增：智能客服路由

# 初始化数据库（确保用户表存在）
init_db()

# 挂载前端静态文件目录 (放在最后，确保不遮挡 API 路由)
frontend_path = project_root / "frontend"
app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="frontend")


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )