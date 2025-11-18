"""
AI检测异步任务
"""
from app.tasks.celery_app import celery_app
from app.services.model_service import model_service
from app.services.websocket_manager import connection_manager
import numpy as np
from typing import Dict
import asyncio


@celery_app.task(name="detect_audio", bind=True)
def detect_audio_task(self, audio_features: list, user_id: int, call_id: int) -> Dict:
    """
    音频检测异步任务
    
    Args:
        audio_features: 音频特征列表
        user_id: 用户ID
        call_id: 通话ID
        
    Returns:
        检测结果
    """
    try:
        # 更新任务状态
        self.update_state(state='PROCESSING', meta={'progress': 0})
        
        # 转换为numpy数组
        features = np.array(audio_features)
        
        # 执行AI检测
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(model_service.predict_voice(features))
        loop.close()
        
        # 更新任务状态
        self.update_state(state='PROCESSING', meta={'progress': 80})
        
        # 如果检测到伪造,通过WebSocket推送警告
        if result.get('is_fake'):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(
                connection_manager.send_personal_message({
                    "type": "alert",
                    "message": "检测到伪造语音!",
                    "confidence": result['confidence'],
                    "call_id": call_id
                }, user_id)
            )
            loop.close()
        
        return {
            "status": "success",
            "result": result,
            "call_id": call_id
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "call_id": call_id
        }


@celery_app.task(name="detect_video", bind=True)
def detect_video_task(self, frame_data: list, user_id: int, call_id: int) -> Dict:
    """
    视频检测异步任务
    
    Args:
        frame_data: 视频帧数据
        user_id: 用户ID
        call_id: 通话ID
        
    Returns:
        检测结果
    """
    try:
        # 更新任务状态
        self.update_state(state='PROCESSING', meta={'progress': 0})
        
        # 转换为numpy数组
        frame = np.array(frame_data)
        
        # 执行AI检测
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(model_service.predict_video(frame))
        loop.close()
        
        # 更新任务状态
        self.update_state(state='PROCESSING', meta={'progress': 80})
        
        # 如果检测到Deepfake,通过WebSocket推送警告
        if result.get('is_deepfake'):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(
                connection_manager.send_personal_message({
                    "type": "alert",
                    "message": "检测到Deepfake视频!",
                    "confidence": result['confidence'],
                    "call_id": call_id
                }, user_id)
            )
            loop.close()
        
        return {
            "status": "success",
            "result": result,
            "call_id": call_id
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "call_id": call_id
        }


@celery_app.task(name="detect_text", bind=True)
def detect_text_task(self, text: str, user_id: int, call_id: int) -> Dict:
    """
    文本检测异步任务
    
    Args:
        text: 文本内容
        user_id: 用户ID
        call_id: 通话ID
        
    Returns:
        检测结果
    """
    try:
        # 更新任务状态
        self.update_state(state='PROCESSING', meta={'progress': 0})
        
        # 执行AI检测
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(model_service.predict_text(text))
        loop.close()
        
        # 更新任务状态
        self.update_state(state='PROCESSING', meta={'progress': 80})
        
        # 如果检测到诈骗话术,通过WebSocket推送警告
        if result.get('is_scam'):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(
                connection_manager.send_personal_message({
                    "type": "alert",
                    "message": "检测到诈骗话术!",
                    "confidence": result['confidence'],
                    "keywords": result.get('keywords', []),
                    "call_id": call_id
                }, user_id)
            )
            loop.close()
        
        return {
            "status": "success",
            "result": result,
            "call_id": call_id
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "call_id": call_id
        }


@celery_app.task(name="get_task_status")
def get_task_status(task_id: str) -> Dict:
    """
    获取任务状态
    
    Args:
        task_id: 任务ID
        
    Returns:
        任务状态信息
    """
    task_result = celery_app.AsyncResult(task_id)
    
    return {
        "task_id": task_id,
        "status": task_result.status,
        "result": task_result.result if task_result.successful() else None,
        "info": task_result.info
    }
