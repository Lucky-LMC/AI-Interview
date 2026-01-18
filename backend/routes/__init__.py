# AI智能面试辅助系统V1.0，作者刘梦畅
"""
路由层 - 导出所有路由
"""
from .interview_routes import router as interview_router
from .auth_routes import router as auth_router

__all__ = ["interview_router", "auth_router"]
