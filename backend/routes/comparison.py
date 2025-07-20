from fastapi import APIRouter, HTTPException, File, UploadFile, Form, Depends
from sqlalchemy.orm import Session
from typing import Optional
import uuid
import cloudinary
import cloudinary.uploader
import cloudinary.utils
import tempfile
import os
from pathlib import Path

from models.database import get_db
from models.models import Comparison
from utils import (
    allowed_file,
    enhanced_compare_images,
    capture_and_find_banner
)

# ✅ CLOUDINARY CONFIG
cloudinary.config(
    cloud_name="dvtrropzc",
    api_key="245757555842261",
    api_secret="TK9ie-U_fX0yS1FZD07rV5lLwbM"
)

compare_router = APIRouter()

def upload_to_cloudinary(file_path: str, folder: str) -> str:
    """Upload file lên Cloudinary"""
    try:
        response = cloudinary.uploader.upload(
            file_path,
            folder=f"visual_testing/{folder}",
            resource_type="image"
        )
        return response['public_id']
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi upload Cloudinary: {str(e)}")

def get_cloudinary_url(public_id: str) -> str:
    """Lấy URL từ Cloudinary"""
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
    """So sánh ảnh với Cloudinary storage và lưu database"""
    temp_files = []
    
    try:
        # VALIDATION 
        if not image2 and not compare_url:
            raise HTTPException(status_code=400, detail="Cần có ảnh thứ 2 hoặc URL")
        
        if image2 and compare_url:
            raise HTTPException(status_code=400, detail="Chỉ chọn 1 trong 2: ảnh thứ 2 HOẶC URL")
        
        # ✅ KIỂM TRA USER TỒN TẠI
        from models.models import User
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User không tồn tại")
        
        # ✅ LƯU ẢNH 1 LÊN CLOUDINARY
        if not allowed_file(image1.filename):
            raise HTTPException(status_code=400, detail="File ảnh không hợp lệ")
        
        temp_file1 = tempfile.NamedTemporaryFile(delete=False, suffix=f"_{image1.filename}")
        temp_files.append(temp_file1.name)
        
        content1 = await image1.read()
        temp_file1.write(content1)
        temp_file1.close()
        
        public_id1 = upload_to_cloudinary(temp_file1.name, "uploads")
        image1_url = get_cloudinary_url(public_id1)
        print(f"☁️ Đã upload ảnh 1 lên Cloudinary: {public_id1}")
        
        # ✅ XỬ LÝ ẢNH 2 HOẶC URL
        if image2:
            print("📁 Chế độ: Upload 2 ảnh")
            
            if not allowed_file(image2.filename):
                raise HTTPException(status_code=400, detail="File ảnh 2 không hợp lệ")
            
            temp_file2 = tempfile.NamedTemporaryFile(delete=False, suffix=f"_{image2.filename}")
            temp_files.append(temp_file2.name)
            
            content2 = await image2.read()
            temp_file2.write(content2)
            temp_file2.close()
            
            public_id2 = upload_to_cloudinary(temp_file2.name, "uploads")
            image2_url = get_cloudinary_url(public_id2)
            print(f"☁️ Đã upload ảnh 2 lên Cloudinary: {public_id2}")
            
            # Download về để so sánh
            temp_compare_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
            temp_files.append(temp_compare_file.name)
            
            import requests
            img2_response = requests.get(image2_url)
            temp_compare_file.write(img2_response.content)
            temp_compare_file.close()
            
            compare_file_path = temp_compare_file.name
            comparison_method = "upload"
            
        else:
            print(f"🌐 Chế độ: Template Matching - {compare_url}")
            
            # Download ảnh 1 về để làm template
            import requests
            template_response = requests.get(image1_url)
            
            temp_template = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
            temp_files.append(temp_template.name)
            temp_template.write(template_response.content)
            temp_template.close()
            
            # Template matching
            banner_filename, error = capture_and_find_banner(compare_url, temp_template.name)
            
            if error:
                raise HTTPException(status_code=400, detail=f"Template matching thất bại: {error}")
            
            print(f"🎯 Template matching thành công: {banner_filename}")
            
            # Upload banner result lên Cloudinary
            from utils import UPLOAD_FOLDER
            banner_path = UPLOAD_FOLDER / banner_filename
            public_id2 = upload_to_cloudinary(str(banner_path), "uploads")
            image2_url = get_cloudinary_url(public_id2)
            
            # Download về để so sánh
            temp_compare_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
            temp_files.append(temp_compare_file.name)
            
            import requests
            banner_response = requests.get(image2_url)
            temp_compare_file.write(banner_response.content)
            temp_compare_file.close()
            
            compare_file_path = temp_compare_file.name
            comparison_method = "template_matching"
            
            # Xóa file local của banner
            if os.path.exists(banner_path):
                os.remove(banner_path)
        
        # ✅ SO SÁNH ẢNH
        print("🔄 Bắt đầu so sánh với độ nhạy cố định cao...")
        
        # Download ảnh 1 về để so sánh
        import requests
        img1_response = requests.get(image1_url)
        
        temp_img1 = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        temp_files.append(temp_img1.name)
        temp_img1.write(img1_response.content)
        temp_img1.close()
        
        # So sánh ảnh
        result, error = enhanced_compare_images(temp_img1.name, compare_file_path)
        
        if error:
            raise HTTPException(status_code=500, detail=error)
        
        # ✅ UPLOAD KẾT QUẢ SO SÁNH LÊN CLOUDINARY
        from utils import RESULT_FOLDER
        
        # Upload result image
        result_path = RESULT_FOLDER / result['result_image']
        result_public_id = upload_to_cloudinary(str(result_path), "results")
        result_image_url = get_cloudinary_url(result_public_id)
        
        # Upload heatmap image
        heatmap_path = RESULT_FOLDER / result['heatmap_image']
        heatmap_public_id = upload_to_cloudinary(str(heatmap_path), "results")
        heatmap_image_url = get_cloudinary_url(heatmap_public_id)
        
        print(f"☁️ Đã upload kết quả lên Cloudinary: {result_public_id}, {heatmap_public_id}")
        
        # Xóa file local results
        if os.path.exists(result_path):
            os.remove(result_path)
        if os.path.exists(heatmap_path):
            os.remove(heatmap_path)
        
        # ✅ LƯU VÀO DATABASE - SỬ DỤNG USER_ID THẬT
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
        
        print(f"💾 Đã lưu comparison vào database với ID: {comparison.id} cho user: {user.name}")
        
        # ✅ THÊM METADATA
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
        
        print(f"✅ Hoàn thành! Độ tương đồng: {result['similarity_score']}%")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"❌ Lỗi server: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Lỗi server: {str(e)}")
    
    finally:
        # Cleanup temp files
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                os.remove(temp_file)

# ✅ ENDPOINT LẤY LỊCH SỬ SO SÁNH - THEO USER
@compare_router.get("/comparisons")
async def get_comparisons(
    user_id: Optional[int] = None,
    project_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Lấy lịch sử so sánh"""
    try:
        query = db.query(Comparison)
        
        if user_id:
            query = query.filter(Comparison.user_id == user_id)
        
        if project_id:
            query = query.filter(Comparison.project_id == project_id)
        
        comparisons = query.order_by(Comparison.created_at.desc()).all()
        
        return {
            "comparisons": [
                {
                    "id": c.id,
                    "user_id": c.user_id,
                    "project_id": c.project_id,
                    "similarity_score": float(c.similarity_score),
                    "differences_count": c.differences_count,
                    "comparison_method": c.comparison_method,
                    "target_url": c.target_url,
                    "created_at": c.created_at,
                    "image1_url": c.image1_url,
                    "result_image_url": c.result_image_url
                }
                for c in comparisons
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi lấy comparisons: {str(e)}")

# ✅ ENDPOINT LẤY LỊCH SỬ THEO USER
@compare_router.get("/users/{user_id}/comparisons")
async def get_user_comparisons(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Lấy lịch sử so sánh của user"""
    try:
        # Kiểm tra user tồn tại
        from models.models import User
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User không tồn tại")
        
        comparisons = db.query(Comparison).filter(
            Comparison.user_id == user_id
        ).order_by(Comparison.created_at.desc()).all()
        
        return {
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email
            },
            "comparisons": [
                {
                    "id": c.id,
                    "project_id": c.project_id,
                    "similarity_score": float(c.similarity_score),
                    "differences_count": c.differences_count,
                    "comparison_method": c.comparison_method,
                    "target_url": c.target_url,
                    "created_at": c.created_at,
                    "image1_url": c.image1_url,
                    "result_image_url": c.result_image_url
                }
                for c in comparisons
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi lấy user comparisons: {str(e)}")

# ✅ ENDPOINT CHI TIẾT COMPARISON - KIỂM TRA QUYỀN
@compare_router.get("/comparisons/{comparison_id}")
async def get_comparison_detail(
    comparison_id: int,
    user_id: Optional[int] = None,  
    db: Session = Depends(get_db)
):
    """Lấy chi tiết comparison"""
    try:
        comparison = db.query(Comparison).filter(Comparison.id == comparison_id).first()
        
        if not comparison:
            raise HTTPException(status_code=404, detail="Comparison không tồn tại")
        
        if user_id and comparison.user_id != user_id:
            raise HTTPException(status_code=403, detail="Không có quyền truy cập comparison này")
        
        return {
            "comparison": {
                "id": comparison.id,
                "project_id": comparison.project_id,
                "user_id": comparison.user_id,
                "image1_url": comparison.image1_url,
                "image2_url": comparison.image2_url,
                "result_image_url": comparison.result_image_url,
                "heatmap_image_url": comparison.heatmap_image_url,
                "similarity_score": float(comparison.similarity_score),
                "differences_count": comparison.differences_count,
                "comparison_method": comparison.comparison_method,
                "target_url": comparison.target_url,
                "created_at": comparison.created_at
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi lấy comparison: {str(e)}")

# ✅ ENDPOINT XÓA COMPARISON - KIỂM TRA QUYỀN
@compare_router.delete("/comparisons/{comparison_id}")
async def delete_comparison(
    comparison_id: int,
    user_id: int,  
    db: Session = Depends(get_db)
):
    """Xóa comparison"""
    try:
        comparison = db.query(Comparison).filter(Comparison.id == comparison_id).first()
        
        if not comparison:
            raise HTTPException(status_code=404, detail="Comparison không tồn tại")
        
        # ✅ KIỂM TRA QUYỀN - chỉ owner mới xóa được
        if comparison.user_id != user_id:
            raise HTTPException(status_code=403, detail="Chỉ người tạo mới có thể xóa comparison này")
        
        db.delete(comparison)
        db.commit()
        
        return {"message": "Xóa comparison thành công"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Lỗi xóa comparison: {str(e)}")