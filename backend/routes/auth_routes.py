# AI智能面试辅助系统V1.0，作者刘梦畅
"""
用户认证相关路由
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.config import SessionLocal
from backend.models import (
    User,
    UserRegisterRequest,
    UserLoginRequest,
    UserResponse
)


router = APIRouter(prefix="/api/auth", tags=["auth"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/register", response_model=UserResponse)
def register_user(request: UserRegisterRequest, db: Session = Depends(get_db)):
    """
    用户注册接口
    """
    existing = db.query(User).filter(User.user_name == request.user_name).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")

    user = User(user_name=request.user_name, password=request.password)
    db.add(user)
    db.commit()

    return UserResponse(user_name=user.user_name, message="注册成功")


@router.post("/login", response_model=UserResponse)
def login_user(request: UserLoginRequest, db: Session = Depends(get_db)):
    """
    用户登录接口
    """
    user = db.query(User).filter(User.user_name == request.user_name).first()
    if not user or user.password != request.password:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    return UserResponse(user_name=user.user_name, message="登录成功")