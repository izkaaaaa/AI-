@echo off
REM ========================================
REM AI Anti-Fraud Detection System
REM 团队开发环境初始化脚本 (Windows)
REM ========================================
chcp 65001 >nul

echo.
echo ========================================
echo   AI 反诈骗检测系统开发 - 环境初始化
echo ========================================
echo.

REM 1. 检查Python版本
echo [1/8] 检查Python版本...
python --version
if errorlevel 1 (
    echo [错误] 未找到Python，请先安装Python 3.11+
    pause
    exit /b 1
)
echo.
 
REM 2. 创建虚拟环境
echo [2/8] 创建Python虚拟环境...
if exist venv (
    echo [提示] 虚拟环境已存在，跳过创建
) else (
    python -m venv venv
    echo [完成] 虚拟环境创建成功
)
echo.

REM 3. 激活虚拟环境
echo [3/8] 激活虚拟环境...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [错误] 虚拟环境激活失败
    pause
    exit /b 1
)
echo [完成] 虚拟环境已激活
echo.

REM 4. 升级pip
echo [4/8] 升级pip...
python -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple
echo.

REM 5. 安装依赖
echo [5/8] 安装Python依赖包...
echo [提示] 使用清华镜像源加速下载...
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
if errorlevel 1 (
    echo [错误] 依赖安装失败，请检查网络连接
    pause
    exit /b 1
)
echo [完成] 依赖安装成功
echo.

REM 6. 复制环境变量配置
echo [6/8] 配置环境变量...
if not exist .env (
    if exist .env.example (
        copy .env.example .env
        echo [完成] 已复制 .env.example 到 .env
        echo [重要] 请编辑 .env 文件，修改数据库密码等配置
    ) else (
        echo [警告] .env.example 文件不存在
    )
) else (
    echo [提示] .env 文件已存在，保持原配置
)
echo.

REM 7. 检查Docker
echo [7/8] 检查Docker环境...
docker --version >nul 2>&1
if errorlevel 1 (
    echo [警告] Docker未安装或未启动
    echo [提示] 请手动安装Docker Desktop并启动服务
    echo [提示] 或使用本地安装的MySQL/Redis/MinIO
    echo.
) else (
    echo [检测] Docker已安装，尝试启动服务...
    docker compose up -d mysql redis minio
    if errorlevel 1 (
        echo [警告] Docker服务启动失败，请检查Docker Desktop是否运行
    ) else (
        echo [完成] Docker服务启动成功
        echo [提示] 等待数据库启动...
        timeout /t 15 /nobreak >nul
    )
)
echo.

REM 8. 初始化数据库
echo [8/8] 初始化数据库表结构...
alembic upgrade head
if errorlevel 1 (
    echo [警告] 数据库迁移失败，可能是数据库未启动
    echo [提示] 请确保数据库服务正常运行后，手动执行: alembic upgrade head
) else (
    echo [完成] 数据库表结构初始化成功
)
echo.

echo ========================================
echo   初始化完成！
echo ========================================
echo.
echo [下一步操作]
echo 1. 编辑 .env 文件，配置数据库密码等信息
echo 2. 确保Docker服务正常运行 (docker compose ps)
echo 3. 启动应用: python main.py
echo 4. 访问文档: http://localhost:8000/docs
echo.
echo [团队协作提示]
echo - 不要提交 .env 文件到Git
echo - 依赖更新后通知团队成员重新安装
echo - 数据库迁移文件需要提交到Git
echo - 每位成员请本地运行 setup.bat 自动创建并使用 venv（不会提交到Git）
echo.

pause
