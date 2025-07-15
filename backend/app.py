from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uuid
import uvicorn
from pathlib import Path
from typing import Optional

# ✅ IMPORT TẤT CẢ FUNCTIONS TỪ UTILS
from utils import (
    allowed_file,
    enhanced_compare_images,
    capture_and_find_banner,
    UPLOAD_FOLDER,
    RESULT_FOLDER
)

# ✅ SETUP APP
app = FastAPI(title="Visual Testing API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ STATIC FILES
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_FOLDER)), name="uploads")
app.mount("/results", StaticFiles(directory=str(RESULT_FOLDER)), name="results")

@app.get("/")
async def root():
    return {"message": "Visual Testing API", "version": "2.0.0"}

@app.post("/upload")
async def compare_images(
    image1: UploadFile = File(...),
    image2: Optional[UploadFile] = File(None),
    compare_url: Optional[str] = Form(None),
    sensitivity: str = Form("high")
):
    """
    So sánh ảnh - 2 chế độ với độ nhạy cố định cao:
    1. Upload 2 ảnh: image1 + image2
    2. Template matching: image1 + compare_url
    * Độ nhạy cố định ở mức cao nhất (SSIM = 1.0)
    """
    try:
        # ✅ VALIDATION CŨ
        if not image2 and not compare_url:
            raise HTTPException(status_code=400, detail="Cần có ảnh thứ 2 hoặc URL")
        
        if image2 and compare_url:
            raise HTTPException(status_code=400, detail="Chỉ chọn 1 trong 2: ảnh thứ 2 HOẶC URL")
        
        # ✅ LƯU ẢNH 1
        if not allowed_file(image1.filename):
            raise HTTPException(status_code=400, detail="File ảnh không hợp lệ")
        
        filename1 = f"{uuid.uuid4()}_{image1.filename}"
        filepath1 = UPLOAD_FOLDER / filename1
        
        with open(filepath1, "wb") as buffer:
            content = await image1.read()
            buffer.write(content)
        
        print(f"💾 Đã lưu ảnh 1: {filename1}")
        print(f"🎯 Mode: Fixed High Sensitivity (SSIM = 1.0)")
        
        # ✅ XỬ LÝ ẢNH 2 HOẶC URL
        if image2:
            # Chế độ 1: Upload 2 ảnh
            print("📁 Chế độ: Upload 2 ảnh")
            
            if not allowed_file(image2.filename):
                raise HTTPException(status_code=400, detail="File ảnh 2 không hợp lệ")
            
            filename2 = f"{uuid.uuid4()}_{image2.filename}"
            filepath2 = UPLOAD_FOLDER / filename2
            
            with open(filepath2, "wb") as buffer:
                content = await image2.read()
                buffer.write(content)
            
            print(f"💾 Đã lưu ảnh 2: {filename2}")
        
        else:
            # Chế độ 2: Template matching
            print(f"🌐 Chế độ: Template Matching - {compare_url}")
            
            filename2, error = capture_and_find_banner(compare_url, str(filepath1))
            
            if error:
                raise HTTPException(status_code=400, detail=f"Template matching thất bại: {error}")
            
            print(f"🎯 Template matching thành công: {filename2}")
        
        # ✅ SO SÁNH ẢNH VỚI ĐỘ NHẠY CỐ ĐỊNH
        print("🔄 Bắt đầu so sánh với độ nhạy cố định cao...")
        result, error = enhanced_compare_images(
            str(filepath1), 
            str(UPLOAD_FOLDER / filename2)
        )
        
        if error:
            raise HTTPException(status_code=500, detail=error)
        
        # ✅ THÊM METADATA
        result.update({
            'image1_path': filename1,
            'image2_path': filename2,
            'comparison_method': 'upload' if image2 else 'template_matching'
        })
        
        if compare_url:
            result['source_url'] = compare_url
        
        print(f"✅ Hoàn thành! Độ tương đồng: {result['similarity_score']}%")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Lỗi server: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Lỗi server: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)