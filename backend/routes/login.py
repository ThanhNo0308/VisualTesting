from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional
import hashlib

from models.database import get_db
from models.models import User
from models.schemas import UserRegister, UserLogin

auth_router = APIRouter()

def hash_password(password: str) -> str:
    """Mã hóa password"""
    return hashlib.sha256(password.encode()).hexdigest()

@auth_router.post("/register")
async def register(user: UserRegister, db: Session = Depends(get_db)):
    """Đăng ký tài khoản"""
    try:
        # Kiểm tra email đã tồn tại
        existing_user = db.query(User).filter(User.email == user.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email đã được sử dụng")
        
        # Tạo user mới
        hashed_password = hash_password(user.password)
        new_user = User(
            name=user.name,
            email=user.email,
            password=hashed_password
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        return {
            "message": "Đăng ký thành công",
            "user": {
                "id": new_user.id,
                "name": new_user.name,
                "email": new_user.email
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Lỗi đăng ký: {str(e)}")

@auth_router.post("/login")
async def login(user: UserLogin, db: Session = Depends(get_db)):
    """Đăng nhập"""
    try:
        # Tìm user theo email và password
        hashed_password = hash_password(user.password)
        user_data = db.query(User).filter(
            User.email == user.email,
            User.password == hashed_password
        ).first()
        
        if not user_data:
            raise HTTPException(status_code=401, detail="Email hoặc mật khẩu không đúng")
        
        return {
            "message": "Đăng nhập thành công",
            "user": {
                "id": user_data.id,
                "name": user_data.name,
                "email": user_data.email
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi đăng nhập: {str(e)}")