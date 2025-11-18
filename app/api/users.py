"""
用户管理API路由
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.db.database import get_db
from app.models.user import User
from app.schemas import (
    UserCreate,
    UserLogin,
    UserResponse,
    TokenResponse,
    ResponseModel
)
from app.core.security import verify_password, get_password_hash, create_access_token, get_current_user_id
from app.core.sms import verify_sms_code, send_sms_code

router = APIRouter(prefix="/api/users", tags=["用户管理"])

@router.post("/send-code", response_model=ResponseModel)
async def send_verification_code(phone: str):
    """发送短信验证码"""
    # 验证手机号格式
    if len(phone) != 11 or not phone.isdigit():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="手机号格式不正确"
        )
    
    # 发送验证码
    success = send_sms_code(phone)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="验证码发送失败"
        )
    
    return ResponseModel(
        code=200,
        message="验证码已发送",
        data={"phone": phone}
    )

@router.post("/register",
            response_model=ResponseModel, 
            status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """用户注册"""
    # 验证短信验证码
    if not verify_sms_code(user_data.phone, user_data.sms_code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="验证码错误或已过期"
        )
    
    # 检查手机号是否已存在
    result = await db.execute(select(User).where(User.phone == user_data.phone))
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该手机号已注册"
        )
    
    # 创建新用户
    new_user = User(
        phone=user_data.phone,
        name=user_data.name,
        password_hash=get_password_hash(user_data.password)
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return ResponseModel(
        code=201,
        message="注册成功",
        data={"user_id": new_user.user_id}
    )


@router.post("/login", response_model=TokenResponse)
async def login(login_data: UserLogin, db: AsyncSession = Depends(get_db)):
    """用户登录"""
    
    # 查询用户
    result = await db.execute(select(User).where(User.phone == login_data.phone))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(login_data.password, user.password_hash):  # type: ignore[arg-type]
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="手机号或密码错误"
        )
    
    if not user.is_active:  # type: ignore[truthy-bool]
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账号已被禁用"
        )
    
    # 生成JWT令牌
    access_token = create_access_token(data={"sub": str(user.user_id), "phone": user.phone})
    
    return TokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user)
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取当前用户信息"""
    # 查询用户
    result = await db.execute(select(User).where(User.user_id == current_user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    return UserResponse.model_validate(user)


@router.put("/family/{family_id}", response_model=ResponseModel)
async def bind_family(
    family_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """绑定家庭组"""
    # 查询用户
    result = await db.execute(select(User).where(User.user_id == current_user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 更新家庭组ID
    user.family_id = family_id  # type: ignore[assignment]
    await db.commit()
    await db.refresh(user)
    
    return ResponseModel(
        code=200,
        message="绑定成功",
        data={
            "user_id": user.user_id,
            "family_id": user.family_id
        }
    )


@router.delete("/family", response_model=ResponseModel)
async def unbind_family(
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """解绑家庭组"""
    # 查询用户
    result = await db.execute(select(User).where(User.user_id == current_user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 解除家庭组绑定
    user.family_id = None  # type: ignore[assignment]
    await db.commit()
    await db.refresh(user)
    
    return ResponseModel(
        code=200,
        message="解绑成功",
        data={"user_id": user.user_id}
    )
