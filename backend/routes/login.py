from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
import hashlib

from models.database import get_db
from models.models import User
from models.schemas import UserRegister, UserLogin

auth_router = APIRouter()

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

@auth_router.post("/register")
async def register(user: UserRegister, db: Session = Depends(get_db)):
    """Đăng ký"""
    try:
        existing_user = db.query(User).filter(User.email == user.email).first()
        if existing_user:
            raise HTTPException(400, "Email đã được sử dụng")
        
        new_user = User(
            name=user.name, email=user.email,
            password=hash_password(user.password)
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        return {
            "message": "Đăng ký thành công",
            "user": {"id": new_user.id, "name": new_user.name, "email": new_user.email}
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Lỗi đăng ký: {str(e)}")

@auth_router.post("/login")
async def login(user: UserLogin, db: Session = Depends(get_db)):
    """Đăng nhập"""
    try:
        user_data = db.query(User).filter(
            User.email == user.email,
            User.password == hash_password(user.password)
        ).first()
        
        if not user_data:
            raise HTTPException(401, "Email hoặc mật khẩu không đúng")
        
        return {
            "message": "Đăng nhập thành công",
            "user": {"id": user_data.id, "name": user_data.name, "email": user_data.email}
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Lỗi đăng nhập: {str(e)}")