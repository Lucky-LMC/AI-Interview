# AI智能面试辅助系统V1.0，作者刘梦畅
"""
请求响应模型 - 定义 API 的请求和响应数据结构
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional


# ========== 1. 用户认证模型 (Auth) ==========

class UserBase(BaseModel):
    """用户公共字段"""
    user_name: str = Field(..., description="用户名", min_length=3, max_length=64)


# ========== 1. 用户认证模型 (Auth) ==========

# --- Requests ---

class UserRegisterRequest(UserBase):
    """用户注册请求"""
    password: str = Field(..., description="密码", min_length=3, max_length=128)


class UserLoginRequest(UserBase):
    """用户登录请求"""
    password: str = Field(..., description="密码", min_length=3, max_length=128)

# --- Responses ---

class UserResponse(UserBase):
    """用户操作响应"""
    message: str = Field(..., description="提示信息")


# ========== 2. 面试核心流程模型 (Interview Core) ==========

# --- Requests ---

class SubmitAnswerRequest(BaseModel):
    """提交答案请求"""
    thread_id: str = Field(..., description="会话ID")
    answer: str = Field(..., description="用户回答", min_length=1)
    user_name: Optional[str] = Field(None, description="用户名（可选，用于保存记录）")

# --- Responses ---

class StartInterviewResponse(BaseModel):
    """启动面试响应"""
    thread_id: str = Field(..., description="会话ID")
    resume_text: str = Field(..., description="LLM提取的简历关键信息")
    target_position: str = Field(..., description="LLM提取的目标岗位")
    question: str = Field(..., description="第一个问题")
    round: int = Field(..., description="当前轮次")
    resume_file_url: Optional[str] = Field(None, description="简历PDF文件访问URL")


class InterviewStatusResponse(BaseModel):
    """面试状态响应"""
    thread_id: str = Field(..., description="会话ID")
    is_finished: bool = Field(..., description="是否结束")
    question: Optional[str] = Field(None, description="新问题（如果未结束）")
    report: Optional[str] = Field(None, description="最终报告（如果已结束）")
    round: int = Field(..., description="当前轮次")


# ========== 3. 面试记录模型 (Records) ==========

# --- Responses ---

class InterviewRecordListResponse(BaseModel):
    """面试记录列表响应"""
    records: List[Dict[str, str]] = Field(..., description="面试记录列表，每个记录包含 thread_id 和 created_at")


class InterviewRecordDetailResponse(BaseModel):
    """面试记录详情响应"""
    thread_id: str = Field(..., description="会话ID")
    user_name: str = Field(..., description="用户名")
    resume_text: str = Field(..., description="简历文本")
    resume_file_url: Optional[str] = Field(None, description="简历PDF文件访问URL")
    resume_file_name: Optional[str] = Field(None, description="简历原始文件名")
    history: List[Dict[str, str]] = Field(..., description="面试历史记录")
    report: Optional[str] = Field(None, description="最终报告")
    is_finished: bool = Field(..., description="面试是否完成")
    created_at: str = Field(..., description="创建时间")
    updated_at: Optional[str] = Field(None, description="更新时间")


# ========== 4. 智能顾问模型 (Consultant) ==========

# --- Requests ---

class ChatRequest(BaseModel):
    """聊天请求模型"""
    message: str = Field(..., description="用户消息")
    thread_id: Optional[str] = Field(None, description="会话ID（用于保持对话上下文）")

# --- Responses ---

class ChatResponse(BaseModel):
    """聊天响应模型"""
    reply: str = Field(..., description="Agent 回复")
    thread_id: str = Field(..., description="会话ID")
    success: bool = Field(True, description="是否成功")


class ConsultantRecordListResponse(BaseModel):
    """顾问对话记录列表响应"""
    records: List[Dict[str, str]] = Field(..., description="对话记录列表，每个记录包含 thread_id 和 created_at")


class ConsultantRecordDetailResponse(BaseModel):
    """顾问对话记录详情响应"""
    thread_id: str = Field(..., description="会话ID")
    user_name: str = Field(..., description="用户名")
    title: str = Field(..., description="会话标题")
    messages: List[Dict[str, str]] = Field(..., description="对话历史")
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")