# AI智能面试辅助系统V1.0，作者刘梦畅
"""
智能面试顾问 API 路由
支持对话记忆和历史记录存储
"""
import uuid
from fastapi import APIRouter, HTTPException, Header, Depends
from sqlalchemy.orm import Session
from typing import Optional
from backend.graph.agents.consultant_agent import get_consultant_agent
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
from fastapi.responses import StreamingResponse
import json
from datetime import datetime

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


# ====================================================================
# 旧版本（非流式）- 已暂时禁用，被下方的流式版本替代
# 如需恢复非流式版本，可以取消注释并修改路由路径为 /chat-sync
# ====================================================================
# @router.post("/chat", response_model=ChatResponse)
# async def chat_with_agent(
#     request: ChatRequest,
#     user_name: Optional[str] = Header(None, alias="X-User-Name"),
#     db: Session = Depends(get_db)
# ):
#     """
#     与智能面试客服对话
    
#     Args:
#         request: 包含用户消息和可选的 thread_id
#         user_name: 用户名（从 Header 获取）
#         db: 数据库会话
        
#     Returns:
#         ChatResponse: Agent 的回复和 thread_id
#     """
#     try:
#         if not request.message or not request.message.strip():
#             raise HTTPException(status_code=400, detail="消息不能为空")
        
#         if not user_name:
#             raise HTTPException(status_code=401, detail="需要登录")
        
#         # 1. 确定 thread_id
#         if request.thread_id:
#             thread_id = request.thread_id
#         else:
#             # 新会话，生成新的 thread_id
#             thread_id = f"consultant-{uuid.uuid4()}"
        
#         # 2. 调用 Agent（带 checkpoint 支持）
#         config = {"configurable": {"thread_id": thread_id}}
        
#         result = consultant_agent.invoke({
#             "messages": [HumanMessage(content=request.message)]
#         }, config)
        
#         # 3. 提取回复
#         if result and "messages" in result:
#             last_message = result["messages"][-1]
#             reply = last_message.content
            
#             # 4. 保存到数据库
#             try:
#                 # 提取消息：保存所有用户消息 + 每轮的最后一条AI回复
#                 # 策略：遍历消息，遇到 human 就保存，遇到 ai 就暂存，直到下一个 human 或结束
                
#                 messages_to_save = []
#                 last_ai_message = None
                
#                 for msg in result["messages"]:
#                     if not hasattr(msg, 'type'):
#                         continue
                    
#                     if msg.type == 'human':
#                         # 如果之前有AI消息，先保存它
#                         if last_ai_message:
#                             messages_to_save.append(last_ai_message)
#                             last_ai_message = None
                        
#                         # 保存用户消息
#                         if msg.content and msg.content.strip():
#                             messages_to_save.append({
#                                 "role": "human",
#                                 "content": msg.content
#                             })
                    
#                     elif msg.type == 'ai':
#                         # 暂存AI消息（只保留最后一条非空的）
#                         if msg.content and msg.content.strip():
#                             last_ai_message = {
#                                 "role": "ai",
#                                 "content": msg.content
#                             }
                
#                 # 保存最后一条AI消息
#                 if last_ai_message:
#                     messages_to_save.append(last_ai_message)
                
#                 # 查询是否已有记录
#                 record = db.query(ConsultantRecord).filter(
#                     ConsultantRecord.thread_id == thread_id
#                 ).first()
                
#                 if record:
#                     # 更新已有记录
#                     record.messages = messages_to_save
#                     from datetime import datetime
#                     record.updated_at = datetime.now()
#                 else:
#                     # 创建新记录
#                     # 生成标题：从第一条用户消息提取（前20个字符）
#                     title = "新咨询会话"
#                     if messages_to_save:
#                         first_user_msg = next((m for m in messages_to_save if m['role'] == 'human'), None)
#                         if first_user_msg and first_user_msg['content']:
#                             content = first_user_msg['content'].strip()
#                             title = content[:20] + ('...' if len(content) > 20 else '')
                    
#                     record = ConsultantRecord(
#                         thread_id=thread_id,
#                         user_name=user_name,
#                         title=title,
#                         messages=messages_to_save
#                     )
#                     db.add(record)
                
#                 db.commit()
#             except Exception as db_e:
#                 db.rollback()
#                 print(f"保存顾问对话记录失败: {db_e}")
#                 # 不影响返回结果
#         else:
#             reply = "抱歉，我现在无法回答这个问题。请稍后重试。"
        
#         return ChatResponse(
#             reply=reply,
#             thread_id=thread_id,
#             success=True
#         )
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         print(f"客服对话错误：{str(e)}")
#         import traceback
#         traceback.print_exc()
        
#         raise HTTPException(
#             status_code=500,
#             detail=f"处理您的请求时出现了错误: {str(e)}"
#         )


# ====================================================================
# 新版本（流式输出）- 使用 SSE (Server-Sent Events) 实现打字机效果
# ====================================================================
@router.post("/chat")
async def chat_with_agent_stream(
    request: ChatRequest,
    user_name: Optional[str] = Header(None, alias="X-User-Name")
):
    """
    与智能咨询顾问进行对话（流式输出版本）
    
    使用 SSE 实现打字机效果，提供更好的用户体验
    
    Args:
        request: 包含用户消息和可选的 thread_id
        user_name: 用户名（从 Header 获取）
        
    Returns:
        StreamingResponse: SSE 格式的流式数据
        
    SSE 事件类型:
        - thread_id: 返回会话ID
        - token: 流式文本内容
        - status: 工具调用状态提示
        - done: 生成完成标记
        - error: 错误信息
    """
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="消息不能为空")
    
    if not user_name:
        raise HTTPException(status_code=401, detail="需要登录")
    
    # 1. 确定 thread_id
    if request.thread_id:
        thread_id = request.thread_id
    else:
        thread_id = f"consultant-{uuid.uuid4()}"
    
    # 2. 定义流式生成器
    async def event_generator():
        db = SessionLocal()
        try:
            # 一次性获取 Agent（无记忆版本）
            agent = await get_consultant_agent()
            
            # 不再使用 config，因为没有 checkpointer
            # config = {
            #     "configurable": {
            #         "thread_id": thread_id
            #     }
            # }
            
            # 立即返回 thread_id
            yield f"data: {json.dumps({'type': 'thread_id', 'content': thread_id}, ensure_ascii=False)}\n\n"
            
            print(f"[Consultant] 开始流式对话，thread_id={thread_id}, user={user_name}")
            
            full_response = ""
            tools_used = []  # 记录本轮对话使用的工具
            event_count = 0
            
            # 使用 astream_events 监听流式事件（不传 config）
            async for event in agent.astream_events(
                {"messages": [HumanMessage(content=request.message)]},
                version="v2"
            ):
                kind = event["event"]
                event_count += 1
                
                # 详细日志：打印所有事件类型（调试用）
                if kind not in ["on_chat_model_stream"]:  # 避免 token 日志刷屏
                    print(f"[Consultant] 事件 {event_count}: {kind}")
                
                # 监听 LLM 的流式输出
                if kind == "on_chat_model_stream":
                    chunk = event["data"]["chunk"]
                    if chunk.content:
                        content = chunk.content
                        # 过滤工具调用相关的内容：
                        # 1. 完整标记：<tool_call>, </tool_call>
                        # 2. 单字符片段：单独的 }, <, >, /
                        # 3. 可疑的短内容：}\n, }\r\n 等
                        is_tool_marker = (
                            '<tool_call>' in content or 
                            '</tool_call>' in content or
                            (len(content.strip()) == 1 and content.strip() in ['}', '<', '>', '/'])
                        )
                        
                        if not is_tool_marker:
                            full_response += content
                            yield f"data: {json.dumps({'type': 'token', 'content': content}, ensure_ascii=False)}\n\n"
                
                # 监听工具调用开始
                elif kind == "on_tool_start":
                    tool_name = event["name"]
                    print(f"[Consultant] 🛠️ 工具调用: {tool_name}")  # 详细日志
                    
                    # 记录工具使用（检查多种可能的工具名称）
                    if "knowledge" in tool_name.lower():
                        if "knowledge_base" not in tools_used:
                            tools_used.append("knowledge_base")
                        status_msg = "🔍 正在搜索知识库..."
                    elif "tavily" in tool_name.lower() or "search" in tool_name.lower():
                        if "tavily_search" not in tools_used:
                            tools_used.append("tavily_search")
                        status_msg = "🌐 正在联网搜索..."
                    else:
                        # 其他未知工具，也记录下来
                        if tool_name not in tools_used:
                            tools_used.append(tool_name)
                        status_msg = f"🛠️ 正在使用工具: {tool_name}"
                    
                    yield f"data: {json.dumps({'type': 'status', 'content': status_msg}, ensure_ascii=False)}\n\n"
                
                # 监听工具调用结束（清空状态，让前端准备接收内容）
                elif kind == "on_tool_end":
                    # 清空状态提示，准备接收 LLM 输出
                    yield f"data: {json.dumps({'type': 'status', 'content': ''}, ensure_ascii=False)}\n\n"
            
            print(f"[Consultant] 事件循环结束，共处理 {event_count} 个事件，生成 {len(full_response)} 字符")
            
            # 如果没有生成内容，记录日志但不重试（避免重复发送消息导致对话混乱）
            if not full_response.strip():
                print(f"[Consultant] ⚠️ 流式输出为空，可能是 Agent 认为无需回答或已在之前回答过")

            # 流式输出结束标记（同时返回工具使用信息）
            yield f"data: {json.dumps({'type': 'done', 'content': '', 'tools_used': tools_used}, ensure_ascii=False)}\n\n"
            
            print(f"[Consultant] 流式输出完成，开始保存数据库")
            
            # 3. 保存到数据库（不使用 checkpoint，直接保存当前对话）
            try:
                # 构建要保存的消息
                messages_to_save = []
                
                # 查询已有记录
                record = db.query(ConsultantRecord).filter(
                    ConsultantRecord.thread_id == thread_id,
                    ConsultantRecord.user_name == user_name
                ).first()
                
                # 如果有已有记录，保留历史消息
                if record and record.messages:
                    messages_to_save = record.messages.copy()
                
                # 添加当前对话
                messages_to_save.append({
                    "role": "human",
                    "content": request.message
                })
                
                if full_response.strip():
                    messages_to_save.append({
                        "role": "ai",
                        "content": full_response,
                        "tools_used": tools_used
                    })
                
                print(f"[Consultant] 准备保存 {len(messages_to_save)} 条消息，工具使用: {tools_used}")
                
                # 查询或创建记录
                if record:
                    # 更新已有记录
                    record.messages = messages_to_save
                    record.updated_at = datetime.now()
                else:
                    # 生成标题（使用第一条用户消息）
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
                print(f"[Consultant] 数据库保存成功")
            except Exception as db_error:
                print(f"[Consultant] 数据库保存失败: {db_error}")
                import traceback
                traceback.print_exc()
                db.rollback()
                
        except Exception as e:
            print(f"[Consultant] 流式对话错误：{e}")
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)}, ensure_ascii=False)}\n\n"
        finally:
            db.close()
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")


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
