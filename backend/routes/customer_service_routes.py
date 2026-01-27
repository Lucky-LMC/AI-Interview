# AI智能面试辅助系统V1.0，作者刘梦畅
"""
智能面试客服 API 路由
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.graph.agents.customer_service_agent import customer_service_agent
from langchain_core.messages import HumanMessage

router = APIRouter(prefix="/api/customer-service", tags=["customer-service"])


class ChatRequest(BaseModel):
    """聊天请求模型"""
    message: str
    user_name: str = "User"


class ChatResponse(BaseModel):
    """聊天响应模型"""
    reply: str
    success: bool = True


@router.post("/chat", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest):
    """
    与智能面试客服对话
    
    Args:
        request: 包含用户消息的请求
        
    Returns:
        ChatResponse: Agent 的回复
    """
    try:
        if not request.message or not request.message.strip():
            raise HTTPException(status_code=400, detail="消息不能为空")
        
        # 调用 Agent（LangGraph CompiledGraph）
        # 使用 invoke 方法，传入消息列表
        result = customer_service_agent.invoke({
            "messages": [HumanMessage(content=request.message)]
        })
        
        # 提取最后一条消息作为回复
        if result and "messages" in result:
            last_message = result["messages"][-1]
            reply = last_message.content
        else:
            reply = "抱歉，我现在无法回答这个问题。请稍后重试。"
        
        return ChatResponse(
            reply=reply,
            success=True
        )
        
    except Exception as e:
        print(f"客服对话错误：{str(e)}")
        import traceback
        traceback.print_exc()
        
        return ChatResponse(
            reply=f"抱歉，处理您的请求时出现了错误。请稍后重试。",
            success=False
        )


@router.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "service": "customer-service"}
