# AI智能面试辅助系统V1.0，作者刘梦畅
"""
智能面试顾问 API 路由
支持对话记忆和历史记录存储
"""
import uuid
from fastapi import APIRouter, HTTPException, Header, Depends
from sqlalchemy.orm import Session
from typing import Optional
from backend.graph.agents.consultant_agent import consultant_agent
from langchain_core.messages import HumanMessage
from backend.models.schemas import (
    ChatRequest, 
    ChatResponse,
    ConsultantRecordListResponse,
    ConsultantRecordDetailResponse
)
from backend.config import SessionLocal
from backend.models import ConsultantRecord
import sqlite3
from pathlib import Path

# LangGraph checkpoints 数据库路径（与 interview_routes 保持一致）
CHECKPOINTS_DIR = Path(__file__).parent.parent.parent / "checkpoints-sqlite"
CHECKPOINT_DB = CHECKPOINTS_DIR / "checkpoints.sqlite"

router = APIRouter(prefix="/api/customer-service", tags=["customer-service"])


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/chat", response_model=ChatResponse)
async def chat_with_agent(
    request: ChatRequest,
    user_name: Optional[str] = Header(None, alias="X-User-Name"),
    db: Session = Depends(get_db)
):
    """
    与智能面试客服对话
    
    Args:
        request: 包含用户消息和可选的 thread_id
        user_name: 用户名（从 Header 获取）
        db: 数据库会话
        
    Returns:
        ChatResponse: Agent 的回复和 thread_id
    """
    try:
        if not request.message or not request.message.strip():
            raise HTTPException(status_code=400, detail="消息不能为空")
        
        if not user_name:
            raise HTTPException(status_code=401, detail="需要登录")
        
        # 1. 确定 thread_id
        if request.thread_id:
            thread_id = request.thread_id
        else:
            # 新会话，生成新的 thread_id
            thread_id = f"consultant-{uuid.uuid4()}"
        
        # 2. 调用 Agent（带 checkpoint 支持）
        config = {"configurable": {"thread_id": thread_id}}
        
        print(f"\n{'='*60}")
        print(f"[API: /api/customer-service/chat] 调用 Consultant Agent")
        print(f"  - User: {user_name}")
        print(f"  - Thread ID: {thread_id}")
        print(f"  - Message: {request.message}")
        print(f"{'='*60}\n")
        
        result = consultant_agent.invoke({
            "messages": [HumanMessage(content=request.message)]
        }, config)
        
        # 3. 提取回复
        if result and "messages" in result:
            last_message = result["messages"][-1]
            reply = last_message.content
            
            # 4. 保存到数据库
            try:
                # 提取消息：保存所有用户消息 + 每轮的最后一条AI回复
                # 策略：遍历消息，遇到 human 就保存，遇到 ai 就暂存，直到下一个 human 或结束
                
                messages_to_save = []
                last_ai_message = None
                
                for msg in result["messages"]:
                    if not hasattr(msg, 'type'):
                        continue
                    
                    if msg.type == 'human':
                        # 如果之前有AI消息，先保存它
                        if last_ai_message:
                            messages_to_save.append(last_ai_message)
                            last_ai_message = None
                        
                        # 保存用户消息
                        if msg.content and msg.content.strip():
                            messages_to_save.append({
                                "role": "human",
                                "content": msg.content
                            })
                    
                    elif msg.type == 'ai':
                        # 暂存AI消息（只保留最后一条非空的）
                        if msg.content and msg.content.strip():
                            last_ai_message = {
                                "role": "ai",
                                "content": msg.content
                            }
                
                # 保存最后一条AI消息
                if last_ai_message:
                    messages_to_save.append(last_ai_message)
                
                # 查询是否已有记录
                record = db.query(ConsultantRecord).filter(
                    ConsultantRecord.thread_id == thread_id
                ).first()
                
                if record:
                    # 更新已有记录
                    record.messages = messages_to_save
                    from datetime import datetime
                    record.updated_at = datetime.now()
                else:
                    # 创建新记录
                    # 生成标题：从第一条用户消息提取（前20个字符）
                    title = "新咨询会话"
                    if messages_to_save:
                        first_user_msg = next((m for m in messages_to_save if m['role'] == 'human'), None)
                        if first_user_msg and first_user_msg['content']:
                            content = first_user_msg['content'].strip()
                            title = content[:20] + ('...' if len(content) > 20 else '')
                    
                    record = ConsultantRecord(
                        thread_id=thread_id,
                        user_name=user_name,
                        title=title,
                        messages=messages_to_save
                    )
                    db.add(record)
                
                db.commit()
            except Exception as db_e:
                db.rollback()
                print(f"保存顾问对话记录失败: {db_e}")
                # 不影响返回结果
        else:
            reply = "抱歉，我现在无法回答这个问题。请稍后重试。"
        
        return ChatResponse(
            reply=reply,
            thread_id=thread_id,
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"客服对话错误：{str(e)}")
        import traceback
        traceback.print_exc()
        
        raise HTTPException(
            status_code=500,
            detail=f"处理您的请求时出现了错误: {str(e)}"
        )


@router.get("/records", response_model=ConsultantRecordListResponse)
async def get_consultant_records(
    user_name: Optional[str] = Header(None, alias="X-User-Name"),
    db: Session = Depends(get_db)
):
    """
    获取用户的顾问对话记录列表
    """
    if not user_name:
        raise HTTPException(status_code=401, detail="需要登录")
    
    try:
        # 查询该用户的所有对话记录，按更新时间倒序
        records = db.query(ConsultantRecord).filter(
            ConsultantRecord.user_name == user_name
        ).order_by(ConsultantRecord.updated_at.desc()).all()
        
        # 转换为响应格式
        record_items = []
        for record in records:
            record_items.append({
                "thread_id": record.thread_id,
                "title": record.title if hasattr(record, 'title') else "新咨询会话",
                "created_at": record.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "updated_at": record.updated_at.strftime("%Y-%m-%d %H:%M:%S")
            })
        
        return ConsultantRecordListResponse(records=record_items)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取对话记录列表失败: {str(e)}")


@router.get("/records/{thread_id}", response_model=ConsultantRecordDetailResponse)
async def get_consultant_record_detail(
    thread_id: str,
    user_name: Optional[str] = Header(None, alias="X-User-Name"),
    db: Session = Depends(get_db)
):
    """
    获取特定对话记录的详细信息
    """
    if not user_name:
        raise HTTPException(status_code=401, detail="需要登录")
    
    try:
        # 查询对话记录
        record = db.query(ConsultantRecord).filter(
            ConsultantRecord.thread_id == thread_id,
            ConsultantRecord.user_name == user_name
        ).first()
        
        if not record:
            raise HTTPException(status_code=404, detail="对话记录不存在")
        
        return ConsultantRecordDetailResponse(
            thread_id=record.thread_id,
            user_name=record.user_name,
            title=record.title if hasattr(record, 'title') else "新咨询会话",
            messages=record.messages if record.messages else [],
            created_at=record.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            updated_at=record.updated_at.strftime("%Y-%m-%d %H:%M:%S")
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取对话记录详情失败: {str(e)}")


@router.delete("/records/{thread_id}")
async def delete_consultant_record(
    thread_id: str,
    user_name: Optional[str] = Header(None, alias="X-User-Name"),
    db: Session = Depends(get_db)
):
    """
    删除对话记录
    """
    if not user_name:
        raise HTTPException(status_code=401, detail="需要登录")
    
    try:
        # 查询记录（验证权限）
        record = db.query(ConsultantRecord).filter(
            ConsultantRecord.thread_id == thread_id,
            ConsultantRecord.user_name == user_name
        ).first()
        
        if not record:
            raise HTTPException(status_code=404, detail="对话记录不存在或无权删除")
        
        
        # 2. 删除 LangGraph 会话记录 (SQLite)
        try:
            if CHECKPOINT_DB.exists():
                conn = sqlite3.connect(str(CHECKPOINT_DB))
                cursor = conn.cursor()
                cursor.execute("DELETE FROM checkpoints WHERE thread_id = ?", (thread_id,))
                cursor.execute("DELETE FROM writes WHERE thread_id = ?", (thread_id,))
                conn.commit()
                conn.close()
                print(f"[删除检查点] 成功删除顾问会话记录: thread_id={thread_id}")
        except Exception as e:
            print(f"[删除检查点] 删除顾问会话记录失败: {e}")

        # 3. 删除数据库记录 (MySQL)
        db.delete(record)
        db.commit()
        
        print(f"[删除记录] 成功删除顾问对话记录: thread_id={thread_id}, user={user_name}")
        
        return {"message": "删除成功", "thread_id": thread_id}
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"[删除记录] 删除失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除对话记录失败: {str(e)}")


@router.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "service": "customer-service"}
