from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from datetime import datetime
from core.auth import get_current_user
from core.db import DB
from core.models import User as DBUser
from core.auth import pwd_context
import os
from .base import success_response, error_response
router = APIRouter(prefix="/user", tags=["用户管理"])

@router.get("", summary="获取用户信息")
async def get_user_info(current_user: dict = Depends(get_current_user)):
    session = DB.get_session()
    try:
        user = session.query(DBUser).filter(
            DBUser.username == current_user["username"]
        ).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    code=40401,
                    message="用户不存在"
                )
            )
        return success_response({
            "username": user.username,
            "nickname": user.nickname if user.nickname else user.username,
            "avatar": user.avatar if user.avatar else "/static/default-avatar.png",
            "email": user.email if user.email else "",
            "role": user.role,
            "is_active": user.is_active,
        })
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_201_CREATED,
            detail=error_response(
                code=50001,
                message="获取用户信息失败"
            )
        )

@router.put("", summary="修改用户资料")
async def update_user_info(
    update_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """修改用户基本信息(不包括密码)"""
    session = DB.get_session()
    try:
        user = session.query(DBUser).filter(
            DBUser.username == current_user["username"]
        ).first()
        if not user:
            from .base import error_response
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    code=40401,
                    message="用户不存在"
                )
            )
        
        # 不允许通过此接口修改密码
        if "password" in update_data:
            from .base import error_response
            raise HTTPException(
                status_code=status.HTTP_200_OK,
                detail=error_response(
                    code=40002,
                    message="请使用专门的密码修改接口"
                )
            )
            
        if "is_active" in update_data:
            user.is_active = bool(update_data["is_active"])
        if "email" in update_data:
            user.email = update_data["email"]
        
        user.updated_at = datetime.now()
        session.commit()
        return success_response(message="更新成功")
    except HTTPException as e:
        raise e
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail=f"更新失败: {str(e)}"
        )
   

@router.put("/password", summary="修改密码")
async def change_password(
    password_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """修改用户密码"""
    session = DB.get_session()
    try:
        # 验证请求数据
        if "old_password" not in password_data or "new_password" not in password_data:
            from .base import error_response
            raise HTTPException(
                status_code=status.HTTP_200_OK,
                detail=error_response(
                    code=40001,
                    message="需要提供旧密码和新密码"
                )
            )
            
        # 获取用户
        user = session.query(DBUser).filter(
            DBUser.username == current_user["username"]
        ).first()
        if not user:
            from .base import error_response
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    code=40401,
                    message="用户不存在"
                )
            )
            
        # 验证旧密码
        if not pwd_context.verify(password_data["old_password"], user.password_hash):
            from .base import error_response
            raise HTTPException(
                status_code=status.HTTP_200_OK,
                detail=error_response(
                    code=40003,
                    message="旧密码不正确"
                )
            )
            
        # 验证新密码复杂度
        new_password = password_data["new_password"]
        if len(new_password) < 8:
            from .base import error_response
            raise HTTPException(
                status_code=status.HTTP_200_OK,
                detail=error_response(
                    code=40004,
                    message="密码长度不能少于8位"
                )
            )
            
        # 更新密码
        user.password_hash = pwd_context.hash(new_password)
        user.updated_at = datetime.now()
        session.commit()
        
        # 清除用户缓存，确保新密码立即生效
        from core.auth import clear_user_cache
        clear_user_cache(current_user["username"])
        
        from .base import success_response
        return success_response(message="密码修改成功")
        
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail=f"密码修改失败: {str(e)}"
        )
import typing
@router.post("/avatar", summary="上传用户头像")
async def upload_avatar(
    file: UploadFile = File(...),
    # file: typing.Optional[UploadFile] = None,
    current_user: dict = Depends(get_current_user)
):
    """处理用户头像上传"""
    try:
        avatar_path="files/avatars"
        # 确保头像目录存在
        os.makedirs(avatar_path, exist_ok=True)
        from core.res.avatar import avatar_dir
        # 保存文件
        file_path = f"{avatar_dir}/{current_user['username']}.jpg"
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
        
        # 更新用户头像字段
        session = DB.get_session()
        try:
            user = session.query(DBUser).filter(
                DBUser.username == current_user["username"]
            ).first()
            if user:
                user.avatar = f"/{avatar_path}/{current_user['username']}.jpg"
                session.commit()
        except Exception as e:
            session.rollback()
            raise HTTPException(
                status_code=status.HTTP_406_NOT_ACCEPTABLE,
                detail=f"更新用户头像失败: {str(e)}"
            )

        from .base import success_response
        return success_response(data={"avatar": f"/{avatar_path}/{current_user['username']}.jpg"})
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail=f"头像上传失败: {str(e)}"
        )