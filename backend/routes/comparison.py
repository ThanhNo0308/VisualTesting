from fastapi import APIRouter, HTTPException, File, UploadFile, Form, Depends
from sqlalchemy.orm import Session
from typing import Optional
import cloudinary.uploader
import tempfile
import os

from models.database import get_db
from models.models import Comparison, User
from utils import allowed_file, enhanced_compare_images, capture_and_find_banner, UPLOAD_FOLDER

# Cloudinary config
cloudinary.config(
    cloud_name="dvtrropzc",
    api_key="245757555842261", 
    api_secret="TK9ie-U_fX0yS1FZD07rV5lLwbM"
)

compare_router = APIRouter()

def upload_to_cloudinary(file_path: str, folder: str) -> str:
    try:
        response = cloudinary.uploader.upload(file_path, folder=f"visual_testing/{folder}")
        return response['public_id']
    except Exception as e:
        raise HTTPException(500, f"Lỗi upload: {str(e)}")

def get_cloudinary_url(public_id: str) -> str:
    return cloudinary.utils.cloudinary_url(public_id)[0]

@compare_router.post("/upload")
async def compare_images(
    image1: UploadFile = File(...),
    image2: Optional[UploadFile] = File(None),
    compare_url: Optional[str] = Form(None),
    project_id: Optional[int] = Form(None),
    user_id: int = Form(...),  
    db: Session = Depends(get_db)
):
    """So sánh ảnh"""
    temp_files = []
    
    try:
        # Validation  
        if not image2 and not compare_url:
            raise HTTPException(400, "Cần có ảnh thứ 2 hoặc URL")
        
        if image2 and compare_url:
            raise HTTPException(400, "Chỉ chọn 1 trong 2: ảnh thứ 2 HOẶC URL")
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(404, "User không tồn tại")
        
        # Upload ảnh 1  
        if not allowed_file(image1.filename):
            raise HTTPException(400, "File ảnh không hợp lệ")
        
        temp_file1 = tempfile.NamedTemporaryFile(delete=False, suffix=f"_{image1.filename}")
        temp_files.append(temp_file1.name)
        
        content1 = await image1.read()
        temp_file1.write(content1)
        temp_file1.close()
        
        public_id1 = upload_to_cloudinary(temp_file1.name, "uploads")
        image1_url = get_cloudinary_url(public_id1)
        
        # Xử lý ảnh 2 hoặc URL  
        if image2:
            # Upload 2 ảnh
            if not allowed_file(image2.filename):
                raise HTTPException(400, "File ảnh 2 không hợp lệ")
            
            temp_file2 = tempfile.NamedTemporaryFile(delete=False, suffix=f"_{image2.filename}")
            temp_files.append(temp_file2.name)
            
            content2 = await image2.read()
            temp_file2.write(content2)
            temp_file2.close()
            
            public_id2 = upload_to_cloudinary(temp_file2.name, "uploads")
            image2_url = get_cloudinary_url(public_id2)
            
            # Download để so sánh
            temp_compare_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
            temp_files.append(temp_compare_file.name)
            
            import requests
            img2_response = requests.get(image2_url)
            temp_compare_file.write(img2_response.content)
            temp_compare_file.close()
            
            compare_file_path = temp_compare_file.name
            comparison_method = "upload"
            
        else:
            # Template matching  
            import requests
            template_response = requests.get(image1_url)
            
            temp_template = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
            temp_files.append(temp_template.name)
            temp_template.write(template_response.content)
            temp_template.close()
            
            banner_filename, error = capture_and_find_banner(compare_url, temp_template.name)
            
            if error:
                raise HTTPException(400, f"Template matching thất bại: {error}")
            
            banner_path = UPLOAD_FOLDER / banner_filename
            public_id2 = upload_to_cloudinary(str(banner_path), "uploads")
            image2_url = get_cloudinary_url(public_id2)
            
            # Download để so sánh
            temp_compare_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
            temp_files.append(temp_compare_file.name)
            
            banner_response = requests.get(image2_url)
            temp_compare_file.write(banner_response.content)
            temp_compare_file.close()
            
            compare_file_path = temp_compare_file.name
            comparison_method = "template_matching"
            
            # Cleanup banner
            if os.path.exists(banner_path):
                os.remove(banner_path)
        
        # So sánh ảnh  
        import requests
        img1_response = requests.get(image1_url)
        
        temp_img1 = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        temp_files.append(temp_img1.name)
        temp_img1.write(img1_response.content)
        temp_img1.close()
        
        result, error = enhanced_compare_images(temp_img1.name, compare_file_path)
        
        if error:
            raise HTTPException(500, error)
        
        # Upload kết quả  
        from utils import RESULT_FOLDER
        
        result_path = RESULT_FOLDER / result['result_image']
        result_public_id = upload_to_cloudinary(str(result_path), "results")
        result_image_url = get_cloudinary_url(result_public_id)
        
        heatmap_path = RESULT_FOLDER / result['heatmap_image']
        heatmap_public_id = upload_to_cloudinary(str(heatmap_path), "results")
        heatmap_image_url = get_cloudinary_url(heatmap_public_id)
        
        # Cleanup results
        if os.path.exists(result_path):
            os.remove(result_path)
        if os.path.exists(heatmap_path):
            os.remove(heatmap_path)
        
        # Lưu database  
        comparison = Comparison(
            project_id=project_id,
            user_id=user_id,  
            image1_url=image1_url,
            image2_url=image2_url,
            result_image_url=result_image_url,
            heatmap_image_url=heatmap_image_url,
            similarity_score=result['similarity_score'],
            differences_count=result['differences_count'],
            comparison_method=comparison_method,
            target_url=compare_url if compare_url else None
        )
        
        db.add(comparison)
        db.commit()
        db.refresh(comparison)
        
        # Response  
        result.update({
            'comparison_id': comparison.id,
            'user_id': user_id,
            'user_name': user.name,  
            'image1_url': image1_url,
            'image2_url': image2_url,
            'result_image_url': result_image_url,
            'heatmap_image_url': heatmap_image_url,
            'comparison_method': comparison_method,
            'storage': 'cloudinary'
        })
        
        if compare_url:
            result['source_url'] = compare_url
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Lỗi server: {str(e)}")
    
    finally:
        # Cleanup
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                os.remove(temp_file)

@compare_router.get("/users/{user_id}/comparisons")
async def get_user_comparisons(user_id: int, db: Session = Depends(get_db)):
    """Lấy lịch sử so sánh của user"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(404, "User không tồn tại")
        
        comparisons = db.query(Comparison).filter(
            Comparison.user_id == user_id
        ).order_by(Comparison.created_at.desc()).all()
        
        return {
            "user": {"id": user.id, "name": user.name, "email": user.email},
            "comparisons": [
                {
                    "id": c.id, "project_id": c.project_id,
                    "similarity_score": float(c.similarity_score),
                    "differences_count": c.differences_count,
                    "comparison_method": c.comparison_method,
                    "target_url": c.target_url, "created_at": c.created_at,
                    "image1_url": c.image1_url, "result_image_url": c.result_image_url
                }
                for c in comparisons
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Lỗi lấy user comparisons: {str(e)}")

@compare_router.delete("/comparisons/{comparison_id}")
async def delete_comparison(comparison_id: int, user_id: int, db: Session = Depends(get_db)):
    """Xóa comparison"""
    try:
        comparison = db.query(Comparison).filter(Comparison.id == comparison_id).first()
        
        if not comparison:
            raise HTTPException(404, "Comparison không tồn tại")
        
        if comparison.user_id != user_id:
            raise HTTPException(403, "Chỉ người tạo mới có thể xóa")
        
        db.delete(comparison)
        db.commit()
        
        return {"message": "Xóa thành công"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Lỗi xóa: {str(e)}")