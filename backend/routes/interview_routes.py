# AI模拟面试系统v1.0，作者刘梦畅
"""
路由层 - 面试相关的 API 路由
基于 LangGraph 工作流的有状态设计
"""
import os
import uuid
import shutil
import tempfile
import json
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Header, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional

from backend.graph.state import InterviewState
from backend.models.schemas import (
    StartInterviewResponse,
    SubmitAnswerRequest,
    InterviewRecordListResponse,
    InterviewRecordDetailResponse
)
from backend.graph.workflow import create_interview_graph
from backend.models import SessionLocal, InterviewRecord

router = APIRouter(prefix="/api/interview", tags=["interview"])


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/start", response_model=StartInterviewResponse)
async def start_interview(
    file: UploadFile = File(...),
    max_rounds: int = Form(3)
):
    """
    开始面试（非流式版本）
    合并文件上传和工作流启动：
    1. 接收上传的文件
    2. 保存文件并启动工作流：document_agent -> interviewer_agent -> [INTERRUPT before answer]
    3. 返回解析的文档内容和第一个问题
    """
    temp_file_path = None
    try:
        # 1. 生成会话 ID
        thread_id = str(uuid.uuid4())
        
        # 2. 临时保存文件
        file_ext = os.path.splitext(file.filename)[1] or ".pdf"
        temp_file_path = os.path.join(tempfile.gettempdir(), f"{thread_id}{file_ext}")
        
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 3. 初始化状态
        initial_state: InterviewState = {
            "round": 0,
            "max_rounds": max_rounds,
            "resume_path": temp_file_path,  # 临时文件路径
            "resume_text": "",  # 将由 document_agent 解析
            "history": [],
            "report": "",
            "is_finished": False
        }
        
        # 4. 启动工作流执行
        workflow = create_interview_graph()
        config = {"configurable": {"thread_id": thread_id}}
        result = workflow.invoke(initial_state, config)
        
        # 5. 清理临时文件（解析完成后）
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except:
                pass
        
        # 6. 返回解析的文档内容和第一个问题（从 history 中获取）
        history = result.get('history', [])
        question = history[-1].get('question', '') if history else ''
        
        return StartInterviewResponse(
            thread_id=thread_id,
            resume_text=result.get('resume_text', ''),
            question=question,
            round=result.get('round', 0) + 1
        )
    
    except Exception as e:
        # 出错时也要清理临时文件
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        raise HTTPException(status_code=500, detail=f"开始面试失败: {str(e)}")

# 非流式输出
# @router.post("/submit", response_model=InterviewStatusResponse)
# async def submit_answer(
#     request: SubmitAnswerRequest,
#     db: Session = Depends(get_db)
# ):
#     """
#     第三阶段：提交回答
#     处理用户回答，评分，并决定下一步
#     """
#     try:
#         workflow = create_interview_graph()
#         config = {"configurable": {"thread_id": request.thread_id}}
        
#         # 1. 获取当前状态，将用户回答更新到 history 的最后一条记录中
#         current_state = workflow.get_state(config)
#         if current_state.values:
#             history = current_state.values.get('history', [])
#             if history:
#                 # 更新最后一条记录的答案
#                 history[-1]['answer'] = request.answer
#                 workflow.update_state(config, {"history": history})
        
#         # 2. 恢复工作流执行
#         result = workflow.invoke(None, config)
        
#         # 3. 获取当前轮次的反馈（从 history 中获取最新的有反馈的记录）
#         history = result.get('history', [])
#         # 从后往前查找，找到有反馈的记录（因为如果未结束，最后一条可能是新问题）
#         current_feedback = ''
#         for entry in reversed(history):
#             if entry.get('feedback'):
#                 current_feedback = entry.get('feedback', '')
#                 break
        
#         # 4. 构建响应
#         is_finished = result.get('is_finished', False)
        
#         response = InterviewStatusResponse(
#             thread_id=request.thread_id,
#             is_finished=is_finished,
#             feedback=current_feedback,
#             round=result.get('round', 0) + (0 if is_finished else 1)
#         )
        
#         if is_finished:
#             response.report = result.get('report', '')
            
#             # 面试完成时，保存面试记录到数据库
#             try:
#                 # 获取完整的面试数据
#                 resume_text = result.get('resume_text', '')
#                 history = result.get('history', [])
#                 report = result.get('report', '')
                
#                 # 创建新记录
#                 new_record = InterviewRecord(
#                     thread_id=request.thread_id,
#                     user_name=request.user_name,
#                     resume_text=resume_text,
#                     history=history,
#                     report=report
#                     # created_at 创建面试记录表时，已经设置默认值为当前本地时间
#                 )
#                 db.add(new_record)
#                 db.commit()
#                 print(f"面试记录已保存: thread_id={request.thread_id}, user_name={request.user_name}")
#             except Exception as e:
#                 db.rollback()
#                 print(f"保存面试记录失败: {e}")
#         else:
#             # 检查工作流状态，看是否在 interviewer_agent 后中断
#             state_info = workflow.get_state(config)
#             if state_info.next and "interviewer_agent" in state_info.next:
#                 # 如果下一步是 interviewer_agent，说明还没生成新问题，需要继续执行
#                 continue_result = workflow.invoke(None, config)
#                 # 从 history 中获取新问题
#                 continue_history = continue_result.get('history', [])
#                 response.question = continue_history[-1].get('question', '') if continue_history else ''
#             else:
#                 # 从 history 中获取问题
#                 result_history = result.get('history', [])
#                 response.question = result_history[-1].get('question', '') if result_history else ''
            
#         return response
#     
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"提交回答失败: {str(e)}")


@router.get("/records", response_model=InterviewRecordListResponse)
async def get_interview_records(
    user_name: Optional[str] = Header(None, alias="X-User-Name"),
    db: Session = Depends(get_db)
):
    """
    获取用户的面试记录列表
    """
    if not user_name:
        raise HTTPException(status_code=401, detail="需要登录")
    
    try:
        # 查询该用户的所有面试记录，按创建时间倒序
        records = db.query(InterviewRecord).filter(
            InterviewRecord.user_name == user_name
        ).order_by(InterviewRecord.created_at.desc()).all()
        
        # 转换为响应格式
        record_items = []
        for record in records:
            record_items.append({
                "thread_id": record.thread_id,
                "created_at": record.created_at.strftime("%Y-%m-%d %H:%M:%S")
            })
        
        return InterviewRecordListResponse(records=record_items)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取面试记录列表失败: {str(e)}")


@router.get("/records/{thread_id}", response_model=InterviewRecordDetailResponse)
async def get_interview_record_detail(
    thread_id: str,
    user_name: Optional[str] = Header(None, alias="X-User-Name"),
    db: Session = Depends(get_db)
):
    """
    获取特定面试记录的详细信息
    """
    if not user_name:
        raise HTTPException(status_code=401, detail="需要登录")
    
    try:
        # 查询面试记录
        record = db.query(InterviewRecord).filter(
            InterviewRecord.thread_id == thread_id,
            InterviewRecord.user_name == user_name
        ).first()
        
        if not record:
            raise HTTPException(status_code=404, detail="面试记录不存在")
        
        return InterviewRecordDetailResponse(
            thread_id=record.thread_id,
            user_name=record.user_name,
            resume_text=record.resume_text,
            history=record.history if record.history else [],
            report=record.report,
            created_at=record.created_at.strftime("%Y-%m-%d %H:%M:%S")
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取面试记录详情失败: {str(e)}")

@router.post("/submit/stream")
async def submit_answer_stream(
    request: SubmitAnswerRequest,
    db: Session = Depends(get_db)
):
    """
    【流式输出接口】提交用户答案并流式返回 AI 反馈
    
    核心技术：
    1. SSE (Server-Sent Events) 协议：单向推送数据流
    2. LangGraph 的 astream_events：监听工作流中每个节点的事件
    3. 打字机效果：逐字符流式输出 LLM 生成的内容
    
    流程：
    1. 更新用户答案到工作流状态
    2. 恢复工作流执行（evaluator -> check_finish -> [interviewer/report]）
    3. 监听工作流事件，实时推送 LLM 输出
    4. 保存面试记录（如果面试结束）
    """
    async def generate_stream():
        """
        【异步生成器】生成 SSE 格式的数据流
        
        SSE 数据格式：
        - 每条消息以 "data: " 开头
        - 消息体是 JSON 字符串
        - 每条消息以 "\n\n" 结尾（两个换行符）
        
        示例：
        data: {"type": "feedback_start"}\n\n
        data: {"type": "feedback", "content": "您"}\n\n
        data: {"type": "feedback", "content": "的"}\n\n
        data: {"type": "feedback", "content": "回答"}\n\n
        """
        try:
            # ========== 步骤1：初始化工作流 ==========
            workflow = create_interview_graph()
            # 使用 thread_id 作为会话标识，LangGraph 会自动加载该会话的状态
            config = {"configurable": {"thread_id": request.thread_id}}
            
            # ========== 步骤2：更新用户回答到工作流状态 ==========
            # 获取当前会话的状态（包含 history、round、resume_text 等）
            current_state = workflow.get_state(config)
            if not current_state.values:
                # 会话不存在，返回错误
                yield f"data: {json.dumps({'error': '会话不存在'}, ensure_ascii=False)}\n\n"
                return
            
            # 从状态中提取历史记录和简历文本
            history = current_state.values.get('history', [])
            resume_text = current_state.values.get('resume_text', '')
            
            # 将用户的回答更新到 history 的最后一条记录中
            # history 结构：[{"question": "...", "answer": "...", "feedback": "..."}, ...]
            if history:
                history[-1]['answer'] = request.answer
                # 更新工作流状态（只更新 history 字段）
                workflow.update_state(config, {"history": history})
            
            # ========== 步骤3：使用 astream_events 执行工作流并监听事件 ==========
            # astream_events 是 LangGraph 提供的异步事件流接口
            # 它会在工作流执行过程中，实时推送各种事件（节点开始、LLM 输出、节点结束等）
            current_node = None  # 记录当前正在执行的节点（evaluator/interviewer/report）
            
            # 异步迭代工作流事件流
            # version="v2" 表示使用 LangGraph 的 v2 事件格式
            async for event in workflow.astream_events(None, config, version="v2"):
                event_type = event["event"]  # 事件类型（on_chain_start/on_chat_model_stream/on_chain_end）
                event_name = event.get("name", "")  # 事件名称（包含节点名称）
                
                # ========== 监听节点开始事件 ==========
                # 当某个节点（evaluator/interviewer/report）开始执行时触发
                if event_type == "on_chain_start":
                    # 判断是哪个节点开始执行
                    if "evaluator" in event_name.lower():
                        current_node = "evaluator"  # 评价节点
                        # 推送"反馈开始"事件到前端
                        yield f"data: {json.dumps({'type': 'feedback_start'}, ensure_ascii=False)}\n\n"
                    elif "interviewer" in event_name.lower():
                        current_node = "interviewer"  # 面试官节点
                        # 推送"问题开始"事件到前端
                        yield f"data: {json.dumps({'type': 'question_start'}, ensure_ascii=False)}\n\n"
                    elif "report" in event_name.lower():
                        current_node = "report"  # 报告节点
                        # 推送"报告开始"事件到前端
                        yield f"data: {json.dumps({'type': 'report_start'}, ensure_ascii=False)}\n\n"
                
                # ========== 监听 LLM 流式输出（打字机效果的核心！）==========
                # 当 LLM 生成内容时，会逐个 token（字符）推送
                # 这就是实现打字机效果的关键！
                elif event_type == "on_chat_model_stream":
                    # 从事件中提取 LLM 输出的 chunk（一小段文本，可能是一个字或几个字）
                    chunk = event["data"]["chunk"]
                    # 检查 chunk 是否包含内容
                    if hasattr(chunk, 'content') and chunk.content:
                        content = chunk.content  # 提取文本内容
                        # 根据当前节点，推送不同类型的消息到前端
                        if current_node == "evaluator":
                            # 推送反馈内容（逐字符）
                            yield f"data: {json.dumps({'type': 'feedback', 'content': content}, ensure_ascii=False)}\n\n"
                        elif current_node == "interviewer":
                            # 推送问题内容（逐字符）
                            yield f"data: {json.dumps({'type': 'question', 'content': content}, ensure_ascii=False)}\n\n"
                        elif current_node == "report":
                            # 推送报告内容（逐字符）
                            yield f"data: {json.dumps({'type': 'report', 'content': content}, ensure_ascii=False)}\n\n"
                
                # ========== 监听节点结束事件 ==========
                # 当某个节点执行完成时触发
                elif event_type == "on_chain_end":
                    if current_node == "evaluator":
                        # 推送"反馈结束"事件到前端
                        yield f"data: {json.dumps({'type': 'feedback_end'}, ensure_ascii=False)}\n\n"
                        current_node = None  # 清空当前节点
                    elif current_node == "interviewer":
                        # 推送"问题结束"事件到前端
                        yield f"data: {json.dumps({'type': 'question_end'}, ensure_ascii=False)}\n\n"
                        current_node = None
                    elif current_node == "report":
                        # 推送"报告结束"事件到前端
                        yield f"data: {json.dumps({'type': 'report_end'}, ensure_ascii=False)}\n\n"
                        current_node = None
            
            # ========== 步骤4：获取最终状态并处理 ==========
            # 工作流执行完成后，获取最终状态
            final_state = workflow.get_state(config)
            is_finished = final_state.values.get('is_finished', False)  # 是否面试结束
            round_num = final_state.values.get('round', 0)  # 当前轮次
            
            if is_finished:
                # ========== 面试结束：保存面试记录到数据库 ==========
                try:
                    final_history = final_state.values.get('history', [])
                    final_report = final_state.values.get('report', '')
                    
                    # 创建面试记录对象
                    new_record = InterviewRecord(
                        thread_id=request.thread_id,
                        user_name=request.user_name,
                        resume_text=resume_text,
                        history=final_history,
                        report=final_report
                    )
                    db.add(new_record)
                    db.commit()
                except Exception as e:
                    db.rollback()
                    print(f"保存面试记录失败: {e}")
                
                # 推送"面试结束"事件到前端
                yield f"data: {json.dumps({'type': 'finished', 'round': round_num}, ensure_ascii=False)}\n\n"
            else:
                # ========== 面试继续：推送"继续下一轮"事件 ==========
                yield f"data: {json.dumps({'type': 'continue', 'round': round_num + 1}, ensure_ascii=False)}\n\n"
            
            # ========== 步骤5：推送结束标记 ==========
            # [DONE] 是 SSE 协议的约定，表示数据流结束
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            # 发生错误时，推送错误消息到前端
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
    
    # ========== 返回 StreamingResponse ==========
    # StreamingResponse 是 FastAPI 提供的流式响应类
    # media_type="text/event-stream" 表示使用 SSE 协议
    return StreamingResponse(
        generate_stream(),  # 传入异步生成器
        media_type="text/event-stream",  # SSE 协议的 MIME 类型
        headers={
            "Cache-Control": "no-cache",  # 禁用缓存（确保实时推送）
            "Connection": "keep-alive",  # 保持连接（SSE 需要长连接）
            "X-Accel-Buffering": "no"  # 禁用 nginx 缓冲（如果使用 nginx 反向代理）
        }
    )
