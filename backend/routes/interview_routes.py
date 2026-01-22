# AI智能面试辅助系统V1.0，作者刘梦畅
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
from fastapi.responses import StreamingResponse, FileResponse
from pathlib import Path
from sqlalchemy.orm import Session
from typing import Optional
# AI智能面试辅助系统V1.0，作者刘梦畅
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
from fastapi.responses import StreamingResponse, FileResponse
from pathlib import Path
from sqlalchemy.orm import Session
from typing import Optional

from backend.graph.state import InterviewState
from backend.models.schemas import (
    StartInterviewResponse,
    SubmitAnswerRequest,
    InterviewRecordListResponse,
    InterviewRecordDetailResponse,
    InterviewStatusResponse
)
from backend.graph.workflow import create_interview_graph
from backend.config import SessionLocal
from backend.models import InterviewRecord

router = APIRouter(prefix="/api/interview", tags=["interview"])

# PDF文件存储目录
UPLOADS_DIR = Path(__file__).parent.parent.parent / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)


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
    pdf_file_path = None
    try:
        # 1. 生成会话 ID
        thread_id = str(uuid.uuid4())
        
        # 2. 保存PDF文件到持久化目录（用于后续预览）
        file_ext = os.path.splitext(file.filename)[1] or ".pdf"
        pdf_file_path = UPLOADS_DIR / f"{thread_id}{file_ext}"
        
        with open(pdf_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 3. 初始化状态
        initial_state: InterviewState = {
            "round": 0,
            "max_rounds": max_rounds,
            "resume_path": str(pdf_file_path),  # 持久化文件路径
            "resume_text": "",  # 将由 LLM 提取关键信息
            "target_position": "",  # 将由 LLM 提取目标岗位
            "history": [],
            "report": "",
            "is_finished": False
        }
        
        # 4. 启动工作流执行
        workflow = create_interview_graph()
        config = {"configurable": {"thread_id": thread_id}}
        result = workflow.invoke(initial_state, config)
        
        # 5. 返回解析的文档内容、第一个问题和PDF访问URL
        history = result.get('history', [])
        question = history[-1].get('question', '') if history else ''
        
        # 构建PDF文件的访问URL
        resume_file_url = f"/api/interview/resume/{thread_id}"
        
        return StartInterviewResponse(
            thread_id=thread_id,
            resume_text=result.get('resume_text', ''),
            target_position=result.get('target_position', '未识别'),
            question=question,
            round=result.get('round', 0) + 1,
            resume_file_url=resume_file_url
        )
    
    except Exception as e:
        # 出错时清理已保存的文件
        if pdf_file_path and pdf_file_path.exists():
            pdf_file_path.unlink()
        import traceback
        print(f"[start_interview] 发生异常: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"开始面试失败: {str(e)}")


@router.get("/resume/{thread_id}")
async def get_resume_pdf(thread_id: str):
    """
    获取简历PDF文件
    用于在前端预览原始PDF文件
    """
    # 查找对应的PDF文件
    pdf_file_path = UPLOADS_DIR / f"{thread_id}.pdf"
    
    if not pdf_file_path.exists():
        raise HTTPException(status_code=404, detail="简历文件不存在")
    
    # 返回PDF文件（inline模式允许浏览器直接预览）
    return FileResponse(
        path=str(pdf_file_path),
        media_type="application/pdf",
        filename=f"resume_{thread_id}.pdf",
        headers={"Content-Disposition": "inline"}  # inline表示在浏览器中预览
    )


# 非流式输出
@router.post("/submit", response_model=InterviewStatusResponse)
async def submit_answer(
    request: SubmitAnswerRequest,
    db: Session = Depends(get_db)
):
    """
    第三阶段：提交回答
    处理用户回答，评分，并决定下一步
    """
    try:
        workflow = create_interview_graph()
        config = {"configurable": {"thread_id": request.thread_id}}
        
        # 1. 获取当前状态，将用户回答更新到 history 的最后一条记录中
        current_state = workflow.get_state(config)
        if current_state.values:
            history = current_state.values.get('history', [])
            if history:
                # 更新最后一条记录的答案
                history[-1]['answer'] = request.answer
                workflow.update_state(config, {"history": history})
        
        # 2. 恢复工作流执行
        result = workflow.invoke(None, config)
        
        # 3. 获取当前轮次的反馈（从 history 中获取最新的有反馈的记录）
        history = result.get('history', [])
        # 从后往前查找，找到有反馈的记录（因为如果未结束，最后一条可能是新问题）
        current_feedback = ''
        for entry in reversed(history):
            if entry.get('feedback'):
                current_feedback = entry.get('feedback', '')
                break
        
        # 4. 构建响应
        is_finished = result.get('is_finished', False)
        
        response = InterviewStatusResponse(
            thread_id=request.thread_id,
            is_finished=is_finished,
            feedback=current_feedback,
            round=result.get('round', 0) + (0 if is_finished else 1)
        )
        
        if is_finished:
            response.report = result.get('report', '')
            
            # 面试完成时，保存面试记录到数据库
            try:
                # 获取完整的面试数据
                resume_text = result.get('resume_text', '')
                history = result.get('history', [])
                report = result.get('report', '')
                
                # 创建新记录
                new_record = InterviewRecord(
                    thread_id=request.thread_id,
                    user_name=request.user_name,
                    resume_text=resume_text,
                    history=history,
                    report=report
                    # created_at 创建面试记录表时，已经设置默认值为当前本地时间
                )
                db.add(new_record)
                db.commit()
                print(f"面试记录已保存: thread_id={request.thread_id}, user_name={request.user_name}")
            except Exception as e:
                db.rollback()
                print(f"保存面试记录失败: {e}")
        else:
            # 检查工作流状态，看是否在 interviewer_agent 后中断
            state_info = workflow.get_state(config)
            if state_info.next and "interviewer_agent" in state_info.next:
                # 如果下一步是 interviewer_agent，说明还没生成新问题，需要继续执行
                continue_result = workflow.invoke(None, config)
                # 从 history 中获取新问题
                continue_history = continue_result.get('history', [])
                response.question = continue_history[-1].get('question', '') if continue_history else ''
            else:
                # 从 history 中获取问题
                result_history = result.get('history', [])
                response.question = result_history[-1].get('question', '') if result_history else ''
            
        return response
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"提交回答失败: {str(e)}")


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

# @router.post("/submit/stream")
# async def submit_answer_stream(
#     request: SubmitAnswerRequest,
#     db: Session = Depends(get_db)
# ):
#     """
#     【流式输出接口】提交用户答案并流式返回 AI 反馈
#     
#     核心技术：
#     1. SSE (Server-Sent Events) 协议：单向推送数据流
#     2. LangGraph 的 astream_events：监听工作流中每个节点的事件
#     3. 打字机效果：逐字符流式输出 LLM 生成的内容
#     
#     流程：
#     1. 更新用户答案到工作流状态
#     2. 恢复工作流执行（evaluator -> check_finish -> [interviewer/report]）
#     3. 监听工作流事件，实时推送 LLM 输出
#     4. 保存面试记录（如果面试结束）
#     """
#     async def generate_stream():
#         """
#         【异步生成器】生成 SSE 格式的数据流
#         
#         SSE 数据格式：
#         - 每条消息以 "data: " 开头
#         - 消息体是 JSON 字符串
#         - 每条消息以 "\n\n" 结尾（两个换行符）
#         
#         示例：
#         data: {"type": "feedback_start"}\n\n
#         data: {"type": "feedback", "content": "您"}\n\n
#         data: {"type": "feedback", "content": "的"}\n\n
#         data: {"type": "feedback", "content": "回答"}\n\n
#         """
#         try:
#             # ========== 步骤1：初始化工作流 ==========
#             workflow = create_interview_graph()
#             config = {"configurable": {"thread_id": request.thread_id}}
#             
#             # ========== 步骤2：更新用户回答到工作流状态 ==========
#             current_state = workflow.get_state(config)
#             if not current_state.values:
#                 yield f"data: {json.dumps({'error': '会话不存在'}, ensure_ascii=False)}\n\n"
#                 return
#             
#             history = current_state.values.get('history', [])
#             resume_text = current_state.values.get('resume_text', '')
#             
#             if history:
#                 history[-1]['answer'] = request.answer
#                 workflow.update_state(config, {"history": history})
#             
#             # ========== 步骤3：执行工作流 (非流式执行) ==========
#             # 直接等待工作流执行完成，获取最终结果
#             result = await workflow.ainvoke(None, config)
#             
#             # ========== 步骤4：处理执行结果并推送 ==========
#             
#             # 4.1 获取反馈 (Evaluator 生成的)
#             # 反馈通常在 history 的倒数第二条（如果是新的一轮）或者最后一条（如果结束了）
#             # 我们遍历 history 找到最新的 feedback
#             result_history = result.get('history', [])
#             latest_feedback = ""
#             if result_history:
#                 # 从后往前找有 feedback 的记录
#                 for entry in reversed(result_history):
#                     if entry.get('feedback'):
#                         latest_feedback = entry.get('feedback')
#                         break
#             
#             if latest_feedback:
#                 yield f"data: {json.dumps({'type': 'feedback_start'}, ensure_ascii=False)}\n\n"
#                 yield f"data: {json.dumps({'type': 'feedback', 'content': latest_feedback}, ensure_ascii=False)}\n\n"
#                 yield f"data: {json.dumps({'type': 'feedback_end'}, ensure_ascii=False)}\n\n"
#             
#             # 4.2 检查是否结束
#             is_finished = result.get('is_finished', False)
#             round_num = result.get('round', 0)
#             
#             if is_finished:
#                 # ========== 面试结束 ==========
#                 final_report = result.get('report', '')
#                 
#                 # 推送报告
#                 yield f"data: {json.dumps({'type': 'report_start'}, ensure_ascii=False)}\n\n"
#                 yield f"data: {json.dumps({'type': 'report', 'content': final_report}, ensure_ascii=False)}\n\n"
#                 yield f"data: {json.dumps({'type': 'report_end'}, ensure_ascii=False)}\n\n"
#                 
#                 # 保存记录
#                 try:
#                     new_record = InterviewRecord(
#                         thread_id=request.thread_id,
#                         user_name=request.user_name,
#                         resume_text=resume_text,
#                         history=result_history,
#                         report=final_report
#                     )
#                     db.add(new_record)
#                     db.commit()
#                 except Exception as e:
#                     db.rollback()
#                     print(f"保存面试记录失败: {e}")
#                 
#                 yield f"data: {json.dumps({'type': 'finished', 'round': round_num}, ensure_ascii=False)}\n\n"
#                 
#             else:
#                 # ========== 面试继续 ==========
#                 # 获取新生成的问题
#                 latest_question = ""
#                 if result_history:
#                     latest_question = result_history[-1].get('question', '')
#                 
#                 if latest_question:
#                     yield f"data: {json.dumps({'type': 'question_start'}, ensure_ascii=False)}\n\n"
#                     yield f"data: {json.dumps({'type': 'question', 'content': latest_question}, ensure_ascii=False)}\n\n"
#                     yield f"data: {json.dumps({'type': 'question_end'}, ensure_ascii=False)}\n\n"
#                 
#                 yield f"data: {json.dumps({'type': 'continue', 'round': round_num + 1}, ensure_ascii=False)}\n\n"
#             
#             # ========== 步骤5：推送结束标记 ==========
#             yield "data: [DONE]\n\n"
#             
#         except Exception as e:
#             import traceback
#             traceback.print_exc()
#             yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
#     
#     # ========== 返回 StreamingResponse ==========
#     # StreamingResponse 是 FastAPI 提供的流式响应类
#     # media_type="text/event-stream" 表示使用 SSE 协议
#     return StreamingResponse(
#         generate_stream(),  # 传入异步生成器
#         media_type="text/event-stream",  # SSE 协议的 MIME 类型
#         headers={
#             "Cache-Control": "no-cache",  # 禁用缓存（确保实时推送）
#             "Connection": "keep-alive",  # 保持连接（SSE 需要长连接）
#             "X-Accel-Buffering": "no"  # 禁用 nginx 缓冲（如果使用 nginx 反向代理）
#         }
#     )
