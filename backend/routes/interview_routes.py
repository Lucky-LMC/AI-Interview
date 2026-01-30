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
import sqlite3
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

# LangGraph checkpoints 数据库路径
CHECKPOINTS_DIR = Path(__file__).parent.parent.parent / "checkpoints-sqlite"
CHECKPOINT_DB = CHECKPOINTS_DIR / "checkpoints.sqlite"


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
    max_rounds: int = Form(3),
    user_name: Optional[str] = Header(None, alias="X-User-Name"),
    db: Session = Depends(get_db)
):
    """
    开始面试（非流式版本）
    合并文件上传和工作流启动：
    1. 接收上传的文件
    2. 保存文件并启动工作流
    3. 创建初始面试记录
    4. 返回解析的文档内容和第一个问题
    """
    if not user_name:
         # 临时兼容：如果 header 没传，尝试从 form 传或者报错，这里假设前端会传
         # 若前端未改，可能需要 permissive 一点，但为了记录关联，必须要有用户名
         raise HTTPException(status_code=401, detail="需要登录")

    pdf_file_path = None
    try:
        # 1. 生成会话 ID
        thread_id = str(uuid.uuid4())
        
        # 2. 保存PDF文件到持久化目录
        file_ext = os.path.splitext(file.filename)[1] or ".pdf"
        pdf_file_path = UPLOADS_DIR / f"{thread_id}{file_ext}"
        
        with open(pdf_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 3. 初始化状态
        initial_state: InterviewState = {
            "round": 0,
            "max_rounds": max_rounds,
            "resume_path": str(pdf_file_path),
            "resume_text": "",
            "target_position": "",
            "history": [],
            "report": "",
            "is_finished": False
        }
        
        # 4. 启动工作流执行
        workflow = create_interview_graph()
        config = {"configurable": {"thread_id": thread_id}}
        result = workflow.invoke(initial_state, config)
        
        # 5. 获取结果
        history = result.get('history', [])
        question = history[-1].get('question', '') if history else ''
        resume_text = result.get('resume_text', '')
        
        # 6. 【新增】立即创建数据库记录
        try:
            new_record = InterviewRecord(
                thread_id=thread_id,
                user_name=user_name,
                resume_text=resume_text,
                resume_file_path=str(pdf_file_path),  # 保存文件路径
                resume_file_name=file.filename,  # 保存原始文件名
                history=history,
                report="",
                is_finished=False
            )
            db.add(new_record)
            db.commit()
        except Exception as db_e:
            db.rollback()
            print(f"创建初始面试记录失败: {db_e}")
            # 不阻断流程，但记录错误

        # 构建PDF文件的访问URL
        resume_file_url = f"/api/interview/resume/{thread_id}"
        
        return StartInterviewResponse(
            thread_id=thread_id,
            resume_text=resume_text,
            target_position=result.get('target_position', '未识别'),
            question=question,
            round=result.get('round', 0),
            resume_file_url=resume_file_url
        )
    
    except Exception as e:
        if pdf_file_path and pdf_file_path.exists():
            try:
                pdf_file_path.unlink()
            except:
                pass
        import traceback
        print(f"[start_interview] 发生异常: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"开始面试失败: {str(e)}")


@router.get("/resume/{thread_id}")
async def get_resume_pdf(thread_id: str):
    """
    获取简历PDF文件
    """
    pdf_file_path = UPLOADS_DIR / f"{thread_id}.pdf"
    
    if not pdf_file_path.exists():
        raise HTTPException(status_code=404, detail="简历文件不存在")
    
    return FileResponse(
        path=str(pdf_file_path),
        media_type="application/pdf",
        filename=f"resume_{thread_id}.pdf",
        headers={"Content-Disposition": "inline"}
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
        
        # 1. 获取当前状态
        current_state = workflow.get_state(config)
        
        # 关键检查：如果状态为空，说明该 thread_id 在数据库中找不到（可能是重启前的内存数据丢失了）
        if not current_state.values:
             raise HTTPException(
                 status_code=410,
                 detail="会话已过期（服务端重启导致旧内存数据丢失），请点击左侧'开启新对话'重新开始。"
             )

        if current_state.values:
            history = current_state.values.get('history', [])
            if history:
                history[-1]['answer'] = request.answer
                workflow.update_state(config, {"history": history})
        
        # 2. 恢复工作流执行
        result = workflow.invoke(None, config)
        
        # 3. 获取最新状态数据
        is_finished = result.get('is_finished', False)
        history = result.get('history', [])
        report = result.get('report', '')
        
        # 4. 【新增】实时更新数据库
        try:
            record = db.query(InterviewRecord).filter(
                InterviewRecord.thread_id == request.thread_id
            ).first()
            
            if record:
                record.history = history # 更新完整历史
                record.is_finished = is_finished # 直接同步状态
                if is_finished:
                    record.report = report
                
                # 即使没结束也保存 history
                db.commit()
            else:
                # 理论上不应该进这里，除非 start 时保存失败
                # 如果找不到记录，尝试新建（补救措施）
                if request.user_name:
                     new_record = InterviewRecord(
                        thread_id=request.thread_id,
                        user_name=request.user_name,
                        resume_text=result.get('resume_text', ''),
                        history=history,
                        report=report,
                        is_finished=is_finished
                    )
                     db.add(new_record)
                     db.commit()

        except Exception as db_e:
            db.rollback()
            print(f"更新面试记录失败: {db_e}")

        # 5. 构建响应
        response = InterviewStatusResponse(
            thread_id=request.thread_id,
            is_finished=is_finished,
            round=result.get('round', 0)
        )
        
        if is_finished:
            response.report = report
        else:
            state_info = workflow.get_state(config)
            if state_info.next and "interviewer_agent" in state_info.next:
                continue_result = workflow.invoke(None, config)
                continue_history = continue_result.get('history', [])
                response.question = continue_history[-1].get('question', '') if continue_history else ''
                # 再次更新数据库以保存新生成的问题
                try:
                     if record:
                        record.history = continue_history
                        db.commit()
                except:
                    pass
            else:
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
        
        # 构建PDF文件访问URL（如果存在文件路径）
        resume_file_url = None
        if record.resume_file_path:
            # 从完整路径中提取 thread_id
            resume_file_url = f"/api/interview/resume/{record.thread_id}"
        
        return InterviewRecordDetailResponse(
            thread_id=record.thread_id,
            user_name=record.user_name,
            resume_text=record.resume_text,
            resume_file_url=resume_file_url,
            resume_file_name=record.resume_file_name,  # 返回原始文件名
            history=record.history if record.history else [],
            report=record.report,
            is_finished=record.is_finished,
            created_at=record.created_at.strftime("%Y-%m-%d %H:%M:%S")
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取面试记录详情失败: {str(e)}")


@router.delete("/records/{thread_id}")
async def delete_interview_record(
    thread_id: str,
    user_name: Optional[str] = Header(None, alias="X-User-Name"),
    db: Session = Depends(get_db)
):
    """
    删除面试记录
    
    删除步骤：
    1. 验证用户权限（只能删除自己的记录）
    2. 删除数据库记录
    3. 删除 PDF 文件
    4. 删除 LangGraph 会话记录
    """
    if not user_name:
        raise HTTPException(status_code=401, detail="需要登录")
    
    try:
        # 1. 查询记录（验证权限）
        record = db.query(InterviewRecord).filter(
            InterviewRecord.thread_id == thread_id,
            InterviewRecord.user_name == user_name
        ).first()
        
        if not record:
            raise HTTPException(status_code=404, detail="面试记录不存在或无权删除")
        
        # 2. 删除 PDF 文件
        if record.resume_file_path:
            pdf_path = Path(record.resume_file_path)
            if pdf_path.exists():
                try:
                    pdf_path.unlink()
                    print(f"[删除文件] 成功删除 PDF: {pdf_path}")
                except Exception as e:
                    print(f"[删除文件] 删除 PDF 失败: {e}")
        
        # 3. 删除 LangGraph 会话记录
        try:
            if CHECKPOINT_DB.exists():
                conn = sqlite3.connect(str(CHECKPOINT_DB))
                cursor = conn.cursor()
                cursor.execute("DELETE FROM checkpoints WHERE thread_id = ?", (thread_id,))
                cursor.execute("DELETE FROM writes WHERE thread_id = ?", (thread_id,))
                conn.commit()
                conn.close()
                print(f"[删除检查点] 成功删除 thread_id={thread_id} 的会话记录")
        except Exception as e:
            print(f"[删除检查点] 删除会话记录失败: {e}")
        
        # 4. 删除数据库记录
        db.delete(record)
        db.commit()
        
        print(f"[删除记录] 成功删除面试记录: thread_id={thread_id}, user={user_name}")
        
        return {"message": "删除成功", "thread_id": thread_id}
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"[删除记录] 删除失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除面试记录失败: {str(e)}")
