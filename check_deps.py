"""
验证 requirements.txt 中的关键依赖是否已正确安装
"""

def check_imports():
    """检查关键包是否可以导入"""
    errors = []
    success = []
    
    # 关键包列表
    packages = {
        'fastapi': 'FastAPI',
        'uvicorn': 'Uvicorn',
        'sqlalchemy': 'SQLAlchemy',
        'alembic': 'Alembic',
        'aiomysql': 'aiomysql',
        'pymysql': 'PyMySQL',
        'redis': 'Redis',
        'celery': 'Celery',
        'jose': 'python-jose',
        'passlib': 'Passlib',
        'pydantic': 'Pydantic',
        'pydantic_settings': 'pydantic-settings',
        'websockets': 'WebSockets',
        'socketio': 'python-socketio',
        'minio': 'MinIO',
        'dotenv': 'python-dotenv',
        'requests': 'Requests',
        'pytest': 'Pytest',
        'httpx': 'HTTPX',
    }
    
    # AI包（可选）
    ai_packages = {
        'torch': 'PyTorch',
        'torchvision': 'torchvision',
        'onnxruntime': 'ONNXRuntime',
        'numpy': 'NumPy',
        'cv2': 'opencv-python',
        'librosa': 'librosa',
    }
    
    print("=" * 60)
    print("检查核心依赖...")
    print("=" * 60)
    
    for pkg, name in packages.items():
        try:
            __import__(pkg)
            success.append(name)
            print(f"✓ {name:30} - 已安装")
        except ImportError as e:
            errors.append((name, str(e)))
            print(f"✗ {name:30} - 未安装或有错误")
    
    print("\n" + "=" * 60)
    print("检查AI相关依赖（可选）...")
    print("=" * 60)
    
    for pkg, name in ai_packages.items():
        try:
            __import__(pkg)
            success.append(name)
            print(f"✓ {name:30} - 已安装")
        except ImportError as e:
            print(f"⚠ {name:30} - 未安装（AI功能暂不可用）")
    
    print("\n" + "=" * 60)
    print("检查结果汇总")
    print("=" * 60)
    print(f"✓ 成功安装: {len(success)} 个包")
    
    if errors:
        print(f"✗ 安装失败: {len(errors)} 个包")
        print("\n详细错误信息:")
        for name, error in errors:
            print(f"  - {name}: {error}")
        return False
    else:
        print("✓ 所有核心依赖已正确安装！")
        return True


def check_versions():
    """检查关键包的版本"""
    print("\n" + "=" * 60)
    print("检查关键包版本...")
    print("=" * 60)
    
    try:
        import fastapi
        print(f"FastAPI: {fastapi.__version__}")
    except: pass
    
    try:
        import sqlalchemy
        print(f"SQLAlchemy: {sqlalchemy.__version__}")
    except: pass
    
    try:
        import pydantic
        print(f"Pydantic: {pydantic.__version__}")
    except: pass
    
    try:
        import redis
        print(f"Redis: {redis.__version__}")
    except: pass
    
    try:
        import torch
        print(f"PyTorch: {torch.__version__}")
    except:
        print("PyTorch: 未安装")


if __name__ == "__main__":
    print("\n🔍 开始检查依赖安装情况...\n")
    
    success = check_imports()
    check_versions()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ 依赖检查完成！可以启动应用了。")
        print("运行命令: python main.py")
    else:
        print("❌ 部分依赖缺失，请重新安装:")
        print("运行命令: pip install -r requirements.txt")
    print("=" * 60 + "\n")
