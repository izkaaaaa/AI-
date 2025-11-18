"""
WebSocket连接管理器
"""
from fastapi import WebSocket
from typing import Dict, List
import asyncio
from datetime import datetime


class ConnectionManager:
    """管理所有WebSocket连接"""
    
    def __init__(self):
        # 存储活跃连接 {user_id: websocket}
        self.active_connections: Dict[int, WebSocket] = {}
        # 连接时间记录
        self.connection_times: Dict[int, datetime] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int):
        """接受新连接"""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        self.connection_times[user_id] = datetime.now()
        print(f"User {user_id} connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, user_id: int):
        """断开连接"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        if user_id in self.connection_times:
            del self.connection_times[user_id]
        print(f"User {user_id} disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: dict, user_id: int):
        """发送个人消息"""
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            await websocket.send_json(message)
    
    async def broadcast(self, message: dict, exclude_user: int = None):
        """广播消息给所有连接(可排除某个用户)"""
        for user_id, websocket in self.active_connections.items():
            if exclude_user and user_id == exclude_user:
                continue
            try:
                await websocket.send_json(message)
            except Exception as e:
                print(f"Failed to send message to user {user_id}: {e}")
    
    async def send_to_family(self, message: dict, family_id: int, family_members: List[int]):
        """发送消息给家庭组成员"""
        for user_id in family_members:
            await self.send_personal_message(message, user_id)
    
    def get_active_users(self) -> List[int]:
        """获取所有在线用户ID"""
        return list(self.active_connections.keys())
    
    def is_user_online(self, user_id: int) -> bool:
        """检查用户是否在线"""
        return user_id in self.active_connections
    
    async def heartbeat_check(self, interval: int = 30):
        """
        心跳检测
        定期检查连接状态并清理失效连接
        """
        while True:
            await asyncio.sleep(interval)
            disconnected_users = []
            
            for user_id, websocket in list(self.active_connections.items()):
                try:
                    # 发送心跳ping
                    await websocket.send_json({
                        "type": "heartbeat",
                        "timestamp": datetime.now().isoformat()
                    })
                except Exception:
                    # 连接已断开
                    disconnected_users.append(user_id)
            
            # 清理断开的连接
            for user_id in disconnected_users:
                self.disconnect(user_id)


# 全局连接管理器实例
connection_manager = ConnectionManager()
