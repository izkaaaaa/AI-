"""
实时检测API路由
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, UploadFile, File, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import asyncio
import json
from datetime import datetime

from app.db.database import get_db
from app.core.security import get_current_user_id
from app.core.storage import upload_to_minio
from app.services.websocket_manager import connection_manager
from app.services.audio_processor import AudioProcessor
from app.services.video_processor import VideoProcessor
from app.models.call_record import CallRecord
from app.schemas import ResponseModel

router = APIRouter(prefix="/api/detection", tags=["实时检测"])

# 音频处理器
audio_processor = AudioProcessor()
# 视频处理器
video_processor = VideoProcessor()


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    """
    WebSocket连接端点 - 实时音视频流处理
    
    连接后可以发送:
    1. 音频流数据 (base64编码)
    2. 视频帧数据 (base64编码)
    3. 控制命令 (JSON格式)
    """
    await connection_manager.connect(websocket, user_id)
    
    try:
        while True:
            # 接收数据
            data = await websocket.receive_text()
            
            try:
                # 尝试解析JSON命令
                message = json.loads(data)
                
                if message.get("type") == "audio":
                    # 处理音频数据
                    audio_data = message.get("data")
                    result = await audio_processor.process_chunk(audio_data)
                    await websocket.send_json({
                        "type": "audio_result",
                        "result": result
                    })
                    
                elif message.get("type") == "video":
                    # 处理视频帧
                    frame_data = message.get("data")
                    result = await video_processor.process_frame(frame_data)
                    await websocket.send_json({
                        "type": "video_result",
                        "result": result
                    })
                    
                elif message.get("type") == "heartbeat":
                    # 心跳响应
                    await websocket.send_json({
                        "type": "heartbeat_ack",
                        "timestamp": datetime.now().isoformat()
                    })
                    
            except json.JSONDecodeError:
                # 如果不是JSON,当作原始数据处理
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid message format"
                })
                
    except WebSocketDisconnect:
        connection_manager.disconnect(user_id)
        print(f"User {user_id} disconnected")


@router.post("/upload/audio", response_model=ResponseModel)
async def upload_audio(
    file: UploadFile = File(...),
    call_id: Optional[int] = None,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    上传音频文件到MinIO存储
    
    支持格式: mp3, wav, m4a, ogg
    """
    # 验证文件类型
    allowed_types = ["audio/mpeg", "audio/wav", "audio/x-m4a", "audio/ogg"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的音频格式: {file.content_type}"
        )
    
    # 读取文件内容
    content = await file.read()
    
    # 上传到MinIO
    file_url = await upload_to_minio(
        content,
        f"audio/{current_user_id}/{file.filename}",
        content_type=file.content_type
    )
    
    return ResponseModel(
        code=200,
        message="音频上传成功",
        data={
            "url": file_url,
            "filename": file.filename,
            "size": len(content)
        }
    )


@router.post("/upload/video", response_model=ResponseModel)
async def upload_video(
    file: UploadFile = File(...),
    call_id: Optional[int] = None,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    上传视频文件到MinIO存储
    
    支持格式: mp4, avi, mov, webm
    """
    # 验证文件类型
    allowed_types = ["video/mp4", "video/x-msvideo", "video/quicktime", "video/webm"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的视频格式: {file.content_type}"
        )
    
    # 读取文件内容
    content = await file.read()
    
    # 上传到MinIO
    file_url = await upload_to_minio(
        content,
        f"video/{current_user_id}/{file.filename}",
        content_type=file.content_type
    )
    
    return ResponseModel(
        code=200,
        message="视频上传成功",
        data={
            "url": file_url,
            "filename": file.filename,
            "size": len(content)
        }
    )


@router.post("/extract-frames", response_model=ResponseModel)
async def extract_video_frames(
    file: UploadFile = File(...),
    frame_rate: int = 1,
    current_user_id: int = Depends(get_current_user_id)
):
    """
    从视频中提取关键帧
    
    Args:
        file: 视频文件
        frame_rate: 每秒提取帧数,默认1帧/秒
    """
    # 读取视频内容
    content = await file.read()
    
    # 提取帧
    frames = await video_processor.extract_frames(content, frame_rate)
    
    return ResponseModel(
        code=200,
        message=f"成功提取{len(frames)}帧",
        data={
            "frame_count": len(frames),
            "frame_rate": frame_rate,
            "frames": frames  # 返回base64编码的帧
        }
    )
