# AI智能面试辅助系统V1.0，作者刘梦畅
"""
请求响应模型 - 定义 API 的请求和响应数据结构
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional


# ========== 工作流请求模型 ==========

class SubmitAnswerRequest(BaseModel):
    """提交答案请求"""
    thread_id: str = Field(..., description="会话ID")
    answer: str = Field(..., description="用户回答", min_length=1)
    user_name: Optional[str] = Field(None, description="用户名（可选，用于保存记录）")


# ========== 响应模型 ==========

class StartInterviewResponse(BaseModel):
    """启动面试响应"""
    thread_id: str = Field(..., description="会话ID")
    resume_text: str = Field(..., description="解析出的简历内容")
    question: str = Field(..., description="第一个问题")
    round: int = Field(..., description="当前轮次")


class InterviewStatusResponse(BaseModel):
    """面试状态响应"""
    thread_id: str = Field(..., description="会话ID")
    is_finished: bool = Field(..., description="是否结束")
    question: Optional[str] = Field(None, description="新问题（如果未结束）")
    feedback: Optional[str] = Field(None, description="上一轮反馈")
    report: Optional[str] = Field(None, description="最终报告（如果已结束）")
    round: int = Field(..., description="当前轮次")


# ========== 用户认证模型 ==========

class UserBase(BaseModel):
    """用户公共字段"""
    user_name: str = Field(..., description="用户名", min_length=3, max_length=64)


class UserRegisterRequest(UserBase):
    """用户注册请求"""
    password: str = Field(..., description="密码", min_length=3, max_length=128)


class UserLoginRequest(UserBase):
    """用户登录请求"""
    password: str = Field(..., description="密码", min_length=3, max_length=128)


class UserResponse(UserBase):
    """用户操作响应"""
    message: str = Field(..., description="提示信息")


# ========== 面试记录模型 ==========

class InterviewRecordListResponse(BaseModel):
    """面试记录列表响应"""
    records: List[Dict[str, str]] = Field(..., description="面试记录列表，每个记录包含 thread_id 和 created_at")


class InterviewRecordDetailResponse(BaseModel):
    """面试记录详情响应"""
    thread_id: str = Field(..., description="会话ID")
    user_name: str = Field(..., description="用户名")
    resume_text: str = Field(..., description="简历文本")
    history: List[Dict[str, str]] = Field(..., description="面试历史记录")
    report: Optional[str] = Field(None, description="最终报告")
    created_at: str = Field(..., description="创建时间")