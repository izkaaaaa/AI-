# AI伪造检测与诈骗预警系统 - 后端

## 项目简介
基于FastAPI的AI伪造检测与诈骗预警系统后端服务，提供实时通话检测、Deepfake识别、诈骗话术分析等功能。

## 技术栈
- **Web框架**: FastAPI (异步)
- **数据库**: MySQL 8.0 + SQLAlchemy (异步)
- **缓存**: Redis
- **对象存储**: MinIO
- **异步任务**: Celery
- **AI框架**: PyTorch / TensorFlow (ONNX Runtime)
- **容器化**: Docker
- **测试框架**: Pytest + pytest-asyncio

## 快速开始

### 方式一: 使用自动化脚本 (推荐)
```bash
# Windows环境一键初始化
setup.bat
```
脚本会自动:
- 创建Python虚拟环境
- 安装所有依赖
- 复制环境变量配置文件

### 方式二: 手动配置

#### 1. 环境准备
```bash
# 创建Python虚拟环境
python -m venv venv

# 激活虚拟环境 (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# 安装依赖
pip install -r requirements.txt

# 注意: 如果遇到bcrypt版本兼容问题,请安装特定版本:
pip install bcrypt==4.1.3
```

#### 2. 配置环境变量
```bash
# 复制环境变量模板
copy .env.example .env

#### 3. 启动Docker服务 (MySQL + Redis + MinIO)
```bash
# 启动MySQL容器 (映射到本地3307端口,避免与本地MySQL冲突)
docker-compose up -d mysql

# 或启动所有依赖服务
docker-compose up -d mysql redis minio
```

#### 4. 初始化数据库
```bash
# 执行数据库迁移 (会自动创建所有表)
python -m alembic upgrade head
```

> **注意**: 
> - 数据库会通过Docker自动创建,无需手动创建
> - 表结构会在应用启动时通过异步init_db自动创建
> - 正常开发中只需要对数据库进行增删改查操作
> - alembic配置已修改为使用pymysql驱动
> - 数据库URL使用 `mysql+aiomysql://` 前缀支持异步

#### 5. 启动应用
```bash
# 开发模式 (带热重载)
python main.py

# 或直接使用uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### 6. 启动Celery Worker (可选,用于异步任务)
```bash
# Windows
start_celery.bat

# 或手动启动
python -m celery -A app.tasks.celery_app worker --loglevel=info --pool=solo
```

#### 6. 访问API文档
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **健康检查**: http://localhost:8000/health

#### 7. 测试实时检测功能
```bash
# 运行测试脚本
python test_realtime_detection.py
```

## 项目结构
```
d:/00_frameFile/
├── app/
│   ├── __init__.py
│   ├── api/              # API路由
│   │   ├── __init__.py
│   │   ├── users.py      # 用户管理接口 (异步)
│   │   ├── detection.py  # 实时检测接口 (WebSocket + 文件上传)
│   │   └── tasks.py      # 异步任务管理接口
│   ├── core/             # 核心配置
│   │   ├── __init__.py
│   │   ├── config.py     # 配置管理
│   │   ├── security.py   # JWT认证 (异步)
│   │   ├── redis.py      # Redis工具
│   │   ├── sms.py        # 短信验证码服务
│   │   └── storage.py    # MinIO存储
│   ├── db/               # 数据库
│   │   ├── __init__.py
│   │   └── database.py   # 异步数据库连接
│   ├── models/           # 数据模型
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── call_record.py
│   │   ├── ai_detection_log.py
│   │   ├── risk_rule.py
│   │   └── blacklist.py
│   ├── schemas/          # Pydantic模型
│   │   └── __init__.py
│   ├── services/         # 服务层
│   │   ├── __init__.py
│   │   ├── websocket_manager.py  # WebSocket连接管理
│   │   ├── audio_processor.py    # 音频处理
│   │   ├── video_processor.py    # 视频处理
│   │   └── model_service.py      # AI模型服务
│   └── tasks/            # Celery异步任务
│       ├── __init__.py
│       ├── celery_app.py         # Celery配置
│       └── detection_tasks.py    # 检测任务
├── tests/                # 单元测试
│   ├── __init__.py
│   └── test_users.py     # 用户模块测试
├── alembic/              # 数据库迁移
│   ├── env.py
│   └── script.py.mako
├── models/               # AI模型文件目录
├── main.py               # 应用入口
├── requirements.txt      # 依赖列表
├── .env.example          # 环境变量模板
├── .gitignore
├── alembic.ini           # Alembic配置
├── docker-compose.yml    # Docker编排
├── start_celery.bat      # Celery启动脚本
└── Dockerfile            # Docker镜像
```

## API接口

### 用户管理
- `POST /api/users/send-code?phone={phone}` - 发送短信验证码
- `POST /api/users/register` - 用户注册 (需要短信验证码)
- `POST /api/users/login` - 用户登录
- `GET /api/users/me` - 获取当前用户信息 (需要JWT)
- `PUT /api/users/family/{family_id}` - 绑定家庭组 (需要JWT)
- `DELETE /api/users/family` - 解绑家庭组 (需要JWT)

### 实时检测
- `WS /api/detection/ws/{user_id}` - WebSocket实时音视频检测连接
- `POST /api/detection/upload/audio` - 上传音频文件 (需要JWT)
- `POST /api/detection/upload/video` - 上传视频文件 (需要JWT)
- `POST /api/detection/extract-frames` - 提取视频关键帧 (需要JWT)

### 异步任务
- `POST /api/tasks/audio/detect` - 提交音频检测任务 (需要JWT)
- `POST /api/tasks/video/detect` - 提交视频检测任务 (需要JWT)
- `POST /api/tasks/text/detect` - 提交文本检测任务 (需要JWT)
- `GET /api/tasks/status/{task_id}` - 查询任务状态

### 系统接口
- `GET /` - 系统信息
- `GET /health` - 健康检查

## 已实现功能

- ✅ 异步数据库连接和操作
- ✅ JWT用户认证
- ✅ 短信验证码服务(Redis存储)
- ✅ 用户注册、登录
- ✅ 家庭组绑定/解绑
- ✅ 完整的单元测试
- ✅ Docker容器化部署
- ✅ 数据库迁移支持
- ✅ WebSocket实时通信
- ✅ 音视频流处理
- ✅ MinIO文件存储
- ✅ AI模型服务层
- ✅ Celery异步任务队列
- ✅ 任务状态监控

## 数据库表结构

### users (用户表)
- user_id: 用户ID
- phone: 手机号
- name: 姓名
- password_hash: 密码哈希
- family_id: 家庭组ID
- is_active: 是否激活
- created_at: 创建时间

### call_records (通话记录表)
- call_id: 通话ID
- user_id: 用户ID
- caller_number: 来电号码
- start_time: 开始时间
- end_time: 结束时间
- duration: 通话时长
- detected_result: 检测结果
- audio_url: 录音URL

### ai_detection_logs (AI检测日志表)
- log_id: 日志ID
- call_id: 通话ID
- voice_confidence: 声音置信度
- video_confidence: 视频置信度
- text_confidence: 文本置信度
- overall_score: 综合评分

### risk_rules (风险规则表)
- rule_id: 规则ID
- keyword: 关键词
- action: 动作
- risk_level: 风险等级

### number_blacklist (号码黑名单表)
- id: ID
- number: 电话号码
- source: 来源
- report_count: 举报次数

## 开发指南

### 异步编程规范

**本项目使用异步架构**,请遵循以下规范:

1. **路由函数必须使用 `async def`**
2. **数据库操作必须使用 `await`**
3. **使用 `AsyncSession` 而非 `Session`**
4. **使用 `select()` 而非 `.query()`**

#### 异步数据库操作示例

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.database import get_db
from fastapi import Depends

@router.get("/example")
async def some_function(db: AsyncSession = Depends(get_db)):
    # 查询
    result = await db.execute(select(User).where(User.id == 1))
    user = result.scalar_one_or_none()
    
    # 添加
    new_user = User(name="test")
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    # 更新
    user.name = "new_name"
    await db.commit()
    
    # 删除
    await db.delete(user)
    await db.commit()
```

### 运行单元测试

```bash
# 运行所有测试
python -m pytest tests/ -v

# 运行特定测试文件
python -m pytest tests/test_users.py -v

# 运行特定测试函数
python -m pytest tests/test_users.py::test_register_success -v

# 显示详细输出
python -m pytest tests/ -v -s
```

#### 测试覆盖
- ✅ 健康检查和根路径
- ✅ 用户注册(成功+重复手机号)
- ✅ 用户登录(成功+密码错误)
- ✅ JWT认证和用户信息获取
- ✅ 家庭组绑定和解绑
- ✅ WebSocket实时连接和心跳
- ✅ 音频/视频流处理
- ✅ 文件上传到MinIO
- ✅ Celery异步任务执行

### 添加新的API路由
1. 在 `app/api/` 目录下创建新的路由文件
2. 在 `app/api/__init__.py` 中导出路由
3. 在 `main.py` 中注册路由

### 添加新的数据模型
1. 在 `app/models/` 目录下创建模型文件
2. 继承 `Base` 类定义表结构
3. 创建对应的 Pydantic Schema
4. 运行 `alembic revision --autogenerate` 生成迁移

## 停止服务

### 停止FastAPI应用
```bash
# 在运行应用的终端按 Ctrl+C
```

### 停止Docker容器
```bash
# 停止所有容器
docker-compose down

# 仅停止MySQL
docker-compose down mysql
```

## 部署

### Docker部署
```bash
# 构建镜像
docker build -t ai-fraud-detection-api .

# 启动所有服务
docker-compose up -d
```

## 常见问题

### 1. Docker镜像拉取失败
配置Docker国内镜像源 (Docker Desktop → Settings → Docker Engine):
```json
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com"
  ]
}
```

### 2. 数据库连接失败
检查:
- Docker MySQL容器是否已启动: `docker ps`
- `.env` 文件中数据库配置是否正确 (端口3307)
- MySQL密码是否为 `123456`

### 3. 端口被占用
- FastAPI默认端口: 8000
- MySQL端口: 3307 (容器内3306)
- Redis端口: 6379
- MinIO端口: 9000, 9001

### 4. bcrypt版本兼容问题
如果遇到 "password cannot be longer than 72 bytes" 错误:
```bash
pip install bcrypt==4.1.3
```

### 5. 异步编程常见错误
- ❌ 忘记使用 `await` 导致获取协程对象而非结果
- ❌ 在同步函数中直接调用 `await`
- ❌ 混用 `AsyncSession` 与同步 `query()` 方法
- ✅ 所有数据库操作都要使用 `await`
- ✅ 所有路由函数都要用 `async def`

### 6. Celery启动问题
如果遇到 "Unable to create process" 错误:
```bash
# 使用 python -m celery 而不是直接调用 celery
python -m celery -A app.tasks.celery_app worker --loglevel=info --pool=solo
```

### 7. MinIO连接问题
检查MinIO是否启动:
```bash
docker ps | findstr minio
# 如未启动
docker-compose up -d minio
```

## 下一步开发计划
- [x] 实现JWT认证中间件
- [x] 集成短信验证码服务
- [x] 添加单元测试 (9个测试用例全部通过)
- [x] 实现异步数据库架构
- [x] 完善家庭组功能 (绑定/解绑)
- [x] WebSocket实时通信
- [x] 音视频流处理
- [x] MinIO文件存储集成
- [x] AI模型服务层架构
- [x] Celery异步任务队列
- [ ] 加载实际AI模型文件
- [ ] 实现真实的音频特征提取(MFCC)
- [ ] 集成人脸检测模型
- [ ] 开发通话记录管理API
- [ ] 实现WebSocket断线重连
- [ ] 添加任务优先级机制
- [ ] 集成Prometheus监控

## 许可证
MIT License
