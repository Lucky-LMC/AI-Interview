# AI智能面试辅助系统V1.0，作者刘梦畅
"""
请求响应模型 - 定义 API 的请求和响应数据结构
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any


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


class ResumeValidationResult(BaseModel):
    """简历结构化质量门禁结果"""
    passed: bool = Field(..., description="是否通过简历结构化质量门禁")
    score: float = Field(..., ge=0.0, le=1.0, description="简历结构化完整度分数")
    issues: List[str] = Field(default_factory=list, description="发现的问题")
    rewrite_instruction: str = Field("", description="失败时给后续修复或提示使用的说明")


class QuestionReviewDimension(BaseModel):
    """单个问题质量维度评分"""
    name: str = Field(..., description="维度名称")
    score: float = Field(..., ge=0.0, le=1.0, description="维度分数")
    reason: str = Field("", description="评分理由")


class QuestionReviewResult(BaseModel):
    """面试问题质量审查结果"""
    passed: bool = Field(..., description="问题是否通过质量审查")
    score: float = Field(..., ge=0.0, le=1.0, description="综合质量分数")
    dimensions: List[QuestionReviewDimension] = Field(default_factory=list, description="维度评分")
    issues: List[str] = Field(default_factory=list, description="问题质量缺陷")
    rewrite_instruction: str = Field("", description="重写问题时需要遵守的要求")
    used_fallback: bool = Field(False, description="是否使用了预置题型兜底")


class InterviewQuestion(BaseModel):
    """面试官 Agent 的结构化最终输出。"""

    question: str = Field(..., min_length=8, description="只包含一个面试问题")
    resume_evidence: List[str] = Field(
        default_factory=list,
        description="问题引用的简历项目、技术或经历证据",
    )
    round_focus: str = Field(..., description="当前轮次考察重点")


class LearningResourceRecommendation(BaseModel):
    """单条有来源的学习资源建议。"""

    topic: str
    title: str
    url: Optional[str] = None
    reason: str = ""


class FeedbackRecommendations(BaseModel):
    """反馈 Agent 的结构化最终输出。"""

    summary: str = Field(..., description="候选人主要改进方向摘要")
    weaknesses: List[str] = Field(default_factory=list, max_length=3)
    resources: List[LearningResourceRecommendation] = Field(default_factory=list)

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
    messages: List[Dict[str, Any]] = Field(..., description="对话历史")  # 改为 Any 以支持 tools_used 列表
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")
