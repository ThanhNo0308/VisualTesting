from fastapi import APIRouter, HTTPException, Depends, Form, Query
from sqlalchemy.orm import Session
from typing import Optional

from models.database import get_db
from models.models import Project, User

project_router = APIRouter()

@project_router.post("/projects")
async def create_project(
    name: str = Form(...),
    description: Optional[str] = Form(None),
    figma_url: Optional[str] = Form(None),
    owner_id: int = Form(...),
    db: Session = Depends(get_db)
):
    """Tạo project"""
    try:
        user = db.query(User).filter(User.id == owner_id).first()
        if not user:
            raise HTTPException(404, "User không tồn tại")
        
        new_project = Project(
            name=name, description=description,
            owner_id=owner_id, figma_url=figma_url
        )
        
        db.add(new_project)
        db.commit()
        db.refresh(new_project)
        
        return {
            "message": "Tạo thành công",
            "project": {
                "id": new_project.id, "name": new_project.name,
                "description": new_project.description, "owner_id": new_project.owner_id,
                "figma_url": new_project.figma_url, "created_at": new_project.created_at
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Lỗi tạo: {str(e)}")

@project_router.get("/users/{user_id}/projects")
async def get_user_projects(user_id: int, db: Session = Depends(get_db)):
    """Lấy projects của user"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(404, "User không tồn tại")
        
        projects = db.query(Project).filter(
            Project.owner_id == user_id
        ).order_by(Project.created_at.desc()).all()
        
        return {
            "user": {"id": user.id, "name": user.name, "email": user.email},
            "projects": [
                {
                    "id": p.id, "name": p.name, "description": p.description,
                    "owner_id": p.owner_id, "figma_url": p.figma_url, "created_at": p.created_at
                }
                for p in projects
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Lỗi lấy projects: {str(e)}")

@project_router.delete("/projects/{project_id}")
async def delete_project(project_id: int, user_id: int = Query(...), db: Session = Depends(get_db)):
    """Xóa project"""
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        
        if not project:
            raise HTTPException(404, "Project không tồn tại")
        
        if project.owner_id != user_id:
            raise HTTPException(403, "Chỉ owner mới có thể xóa")
        
        db.delete(project)
        db.commit()
        
        return {"message": "Xóa thành công"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Lỗi xóa: {str(e)}")