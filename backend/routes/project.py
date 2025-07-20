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
    """Tạo project mới"""
    try:
        user = db.query(User).filter(User.id == owner_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User không tồn tại")
        
        new_project = Project(
            name=name,
            description=description,
            owner_id=owner_id,
            figma_url=figma_url
        )
        
        db.add(new_project)
        db.commit()
        db.refresh(new_project)
        
        return {
            "message": "Tạo project thành công",
            "project": {
                "id": new_project.id,
                "name": new_project.name,
                "description": new_project.description,
                "owner_id": new_project.owner_id,
                "figma_url": new_project.figma_url,
                "created_at": new_project.created_at
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Lỗi tạo project: {str(e)}")

@project_router.get("/projects")
async def get_projects(
    user_id: Optional[int] = Query(None), 
    db: Session = Depends(get_db)
):
    """Lấy danh sách projects theo user"""
    try:
        query = db.query(Project).order_by(Project.created_at.desc())
        
        # ✅ FILTER THEO USER_ID
        if user_id:
            query = query.filter(Project.owner_id == user_id)
        
        projects = query.all()
        
        projects_list = []
        for p in projects:
            projects_list.append({
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "owner_id": p.owner_id,
                "figma_url": p.figma_url,
                "created_at": p.created_at
            })
        
        return {"projects": projects_list}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi lấy projects: {str(e)}")

# ✅ THÊM ENDPOINT LẤY PROJECT CỦA USER
@project_router.get("/users/{user_id}/projects")
async def get_user_projects(user_id: int, db: Session = Depends(get_db)):
    """Lấy danh sách projects của user"""
    try:
        # Kiểm tra user tồn tại
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User không tồn tại")
        
        projects = db.query(Project).filter(
            Project.owner_id == user_id
        ).order_by(Project.created_at.desc()).all()
        
        return {
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email
            },
            "projects": [
                {
                    "id": p.id,
                    "name": p.name,
                    "description": p.description,
                    "owner_id": p.owner_id,
                    "figma_url": p.figma_url,
                    "created_at": p.created_at
                }
                for p in projects
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi lấy user projects: {str(e)}")

# ✅ GIỮ NGUYÊN CÁC ENDPOINT KHÁC
@project_router.delete("/projects/{project_id}")
async def delete_project(
    project_id: int, 
    user_id: int = Query(...), 
    db: Session = Depends(get_db)
):
    """Xóa project"""
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        
        if not project:
            raise HTTPException(status_code=404, detail="Project không tồn tại")
        
        # ✅ KIỂM TRA QUYỀN - chỉ owner mới xóa được
        if project.owner_id != user_id:
            raise HTTPException(status_code=403, detail="Chỉ owner mới có thể xóa project này")
        
        db.delete(project)
        db.commit()
        
        return {"message": "Xóa project thành công"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Lỗi xóa project: {str(e)}")

@project_router.put("/projects/{project_id}")
async def update_project(
    project_id: int,
    name: str = Form(...),
    description: Optional[str] = Form(None),
    figma_url: Optional[str] = Form(None),
    user_id: int = Form(...),  
    db: Session = Depends(get_db)
):
    """Cập nhật project"""
    try:
        existing_project = db.query(Project).filter(Project.id == project_id).first()
        
        if not existing_project:
            raise HTTPException(status_code=404, detail="Project không tồn tại")
        
        # ✅ KIỂM TRA QUYỀN - chỉ owner mới cập nhật được
        if existing_project.owner_id != user_id:
            raise HTTPException(status_code=403, detail="Chỉ owner mới có thể cập nhật project này")
        
        # Cập nhật thông tin
        existing_project.name = name
        existing_project.description = description
        existing_project.figma_url = figma_url
        
        db.commit()
        db.refresh(existing_project)
        
        return {
            "message": "Cập nhật project thành công",
            "project": {
                "id": existing_project.id,
                "name": existing_project.name,
                "description": existing_project.description,
                "owner_id": existing_project.owner_id,
                "figma_url": existing_project.figma_url,
                "created_at": existing_project.created_at
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Lỗi cập nhật project: {str(e)}")

@project_router.get("/projects/{project_id}")
async def get_project(project_id: int, db: Session = Depends(get_db)):
    """Lấy chi tiết project"""
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        
        if not project:
            raise HTTPException(status_code=404, detail="Project không tồn tại")
        
        return {
            "project": {
                "id": project.id,
                "name": project.name,
                "description": project.description,
                "owner_id": project.owner_id,
                "figma_url": project.figma_url,
                "created_at": project.created_at
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi lấy project: {str(e)}")