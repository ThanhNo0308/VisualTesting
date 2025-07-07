from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim
import os
from pathlib import Path
import uuid
from datetime import datetime
import uvicorn

app = FastAPI(title="Visual Testing API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Tạo thư mục
UPLOAD_FOLDER = "uploads"
RESULT_FOLDER = "results"
Path(UPLOAD_FOLDER).mkdir(exist_ok=True)
Path(RESULT_FOLDER).mkdir(exist_ok=True)

# Mount static files
app.mount("/uploads", StaticFiles(directory=UPLOAD_FOLDER), name="uploads")
app.mount("/results", StaticFiles(directory=RESULT_FOLDER), name="results")

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}

def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def resize_images_to_same_size(img1, img2):
    """Resize 2 ảnh về cùng kích thước"""
    h1, w1 = img1.shape[:2]
    h2, w2 = img2.shape[:2]
    
    target_height = max(h1, h2)
    target_width = max(w1, w2)
    
    img1_resized = cv2.resize(img1, (target_width, target_height))
    img2_resized = cv2.resize(img2, (target_width, target_height))
    
    return img1_resized, img2_resized

def enhanced_compare_images(image1_path: str, image2_path: str):
    """So sánh 2 ảnh với độ chính xác cao hơn"""
    try:
        # Đọc ảnh
        img1 = cv2.imread(image1_path)
        img2 = cv2.imread(image2_path)
        
        if img1 is None or img2 is None:
            return None, "Không thể đọc một hoặc cả hai ảnh"
        
        # Resize về cùng kích thước
        img1_resized, img2_resized = resize_images_to_same_size(img1, img2)
        
        # === PHƯƠNG PHÁP 1: SSIM trên ảnh xám ===
        gray1 = cv2.cvtColor(img1_resized, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(img2_resized, cv2.COLOR_BGR2GRAY)
        similarity_score, ssim_diff = ssim(gray1, gray2, full=True)
        
        # === PHƯƠNG PHÁP 2: So sánh màu sắc trực tiếp ===
        # Tính khoảng cách Euclidean giữa các pixel màu
        color_diff = np.sqrt(np.sum((img1_resized.astype(float) - img2_resized.astype(float)) ** 2, axis=2))
        
        # === PHƯƠNG PHÁP 3: So sánh từng kênh màu ===
        b1, g1, r1 = cv2.split(img1_resized)
        b2, g2, r2 = cv2.split(img2_resized)
        
        # Tính khác biệt cho từng kênh màu
        diff_b = cv2.absdiff(b1, b2)
        diff_g = cv2.absdiff(g1, g2)
        diff_r = cv2.absdiff(r1, r2)
        
        # Kết hợp khác biệt từ tất cả kênh màu
        channel_diff = np.maximum(np.maximum(diff_b, diff_g), diff_r)
        
        # === PHƯƠNG PHÁP 4: Threshold động ===
        # Sử dụng nhiều mức threshold khác nhau
        
        # Threshold cho SSIM
        ssim_diff_normalized = ((1 - ssim_diff) * 255).astype(np.uint8)
        _, ssim_thresh = cv2.threshold(ssim_diff_normalized, 30, 255, cv2.THRESH_BINARY)
        
        # Threshold cho màu sắc (nhạy hơn)
        color_diff_normalized = np.clip(color_diff * 2, 0, 255).astype(np.uint8)
        _, color_thresh = cv2.threshold(color_diff_normalized, 20, 255, cv2.THRESH_BINARY)
        
        # Threshold cho từng kênh màu
        _, channel_thresh = cv2.threshold(channel_diff, 15, 255, cv2.THRESH_BINARY)
        
        # === KẾT HOP TẤT CẢ PHƯƠNG PHÁP ===
        # Kết hợp tất cả mask khác biệt
        combined_mask = cv2.bitwise_or(ssim_thresh, color_thresh)
        combined_mask = cv2.bitwise_or(combined_mask, channel_thresh)
        
        # Áp dụng morphological operations để làm sạch noise
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_CLOSE, kernel)
        combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN, kernel)
        
        # === TÌM VÀ VẼ KHÁC BIỆT ===
        contours, _ = cv2.findContours(combined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Tạo ảnh kết quả
        result_img = img2_resized.copy()
        
        # Vẽ khung đỏ với các kích thước khác nhau tùy theo mức độ khác biệt
        differences_count = 0
        difference_details = []
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 25:  # Giảm ngưỡng diện tích để phát hiện khác biệt nhỏ hơn
                x, y, w, h = cv2.boundingRect(contour)
                
                # Tính mức độ khác biệt trong vùng này
                region_diff = color_diff[y:y+h, x:x+w]
                avg_difference = np.mean(region_diff)
                
                # Chọn màu và độ dày viền dựa trên mức độ khác biệt
                if avg_difference > 50:
                    color = (0, 0, 255)  # Đỏ - khác biệt lớn
                    thickness = 3
                    diff_level = "high"
                elif avg_difference > 25:
                    color = (0, 165, 255)  # Cam - khác biệt trung bình  
                    thickness = 2
                    diff_level = "medium"
                else:
                    color = (0, 255, 255)  # Vàng - khác biệt nhỏ
                    thickness = 2
                    diff_level = "low"
                
                cv2.rectangle(result_img, (x, y), (x + w, y + h), color, thickness)
                
                # Thêm nhãn mức độ khác biệt
                cv2.putText(result_img, diff_level, (x, y-5), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
                
                differences_count += 1
                difference_details.append({
                    "x": int(x),
                    "y": int(y), 
                    "width": int(w),
                    "height": int(h),
                    "area": int(area),
                    "avg_difference": float(avg_difference),
                    "level": diff_level
                })
        
        # === TẠO ẢNH HEATMAP KHÁC BIỆT ===
        # Tạo heatmap để hiển thị mức độ khác biệt
        heatmap = cv2.applyColorMap(color_diff_normalized, cv2.COLORMAP_JET)
        
        # Kết hợp heatmap với ảnh gốc
        alpha = 0.3
        heatmap_overlay = cv2.addWeighted(img2_resized, 1-alpha, heatmap, alpha, 0)
        
        # Lưu ảnh kết quả
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_filename = f"comparison_result_{timestamp}.jpg"
        heatmap_filename = f"heatmap_{timestamp}.jpg"
        
        result_path = os.path.join(RESULT_FOLDER, result_filename)
        heatmap_path = os.path.join(RESULT_FOLDER, heatmap_filename)
        
        cv2.imwrite(result_path, result_img)
        cv2.imwrite(heatmap_path, heatmap_overlay)
        
        return {
            'similarity_score': round(similarity_score * 100, 2),
            'result_image': result_filename,
            'heatmap_image': heatmap_filename,
            'differences_count': differences_count,
            'difference_details': difference_details,
            'analysis': {
                'total_pixels': int(img1_resized.shape[0] * img1_resized.shape[1]),
                'different_pixels': int(np.sum(combined_mask > 0)),
                'difference_percentage': round((np.sum(combined_mask > 0) / (img1_resized.shape[0] * img1_resized.shape[1])) * 100, 3)
            },
            'status': 'success'
        }, None
        
    except Exception as e:
        return None, f"Lỗi xử lý ảnh: {str(e)}"

# Giữ lại function cũ cho compatibility
def compare_images_ssim(image1_path: str, image2_path: str):
    return enhanced_compare_images(image1_path, image2_path)

@app.get("/")
async def root():
    return {"message": "Visual Testing API", "version": "1.0.0"}

@app.post("/upload")
async def compare_images(
    image1: UploadFile = File(...),
    image2: UploadFile = File(...),
    sensitivity: str = "high"  # Thêm tham số độ nhạy
):
    """Upload và so sánh 2 ảnh với độ chính xác cao"""
    try:
        # Kiểm tra file hợp lệ
        if not allowed_file(image1.filename) or not allowed_file(image2.filename):
            raise HTTPException(status_code=400, detail="Chỉ hỗ trợ file ảnh (png, jpg, jpeg, gif, bmp)")
        
        # Tạo tên file unique
        filename1 = f"{uuid.uuid4()}_{image1.filename}"
        filename2 = f"{uuid.uuid4()}_{image2.filename}"
        
        filepath1 = os.path.join(UPLOAD_FOLDER, filename1)
        filepath2 = os.path.join(UPLOAD_FOLDER, filename2)
        
        # Lưu file
        with open(filepath1, "wb") as buffer:
            content = await image1.read()
            buffer.write(content)
            
        with open(filepath2, "wb") as buffer:
            content = await image2.read()
            buffer.write(content)
        
        # So sánh ảnh với thuật toán cải tiến
        result, error = enhanced_compare_images(filepath1, filepath2)
        
        if error:
            raise HTTPException(status_code=500, detail=error)
        
        # Thêm đường dẫn ảnh gốc
        result['image1_path'] = filename1
        result['image2_path'] = filename2
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi server: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)