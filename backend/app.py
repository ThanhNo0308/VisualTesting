from fastapi import FastAPI, File, UploadFile, HTTPException, Form  # ✅ THÊM Form
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

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
from typing import Optional

app = FastAPI(title="Visual Testing API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ TẠO THƯ MỤC TRONG PROJECT DIRECTORY
BASE_DIR = Path(__file__).parent
UPLOAD_FOLDER = BASE_DIR / "uploads"
RESULT_FOLDER = BASE_DIR / "results"

UPLOAD_FOLDER.mkdir(exist_ok=True)
RESULT_FOLDER.mkdir(exist_ok=True)

app.mount("/uploads", StaticFiles(directory=str(UPLOAD_FOLDER)), name="uploads")
app.mount("/results", StaticFiles(directory=str(RESULT_FOLDER)), name="results")

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
        color_diff = np.sqrt(np.sum((img1_resized.astype(float) - img2_resized.astype(float)) ** 2, axis=2))
        
        # === PHƯƠNG PHÁP 3: So sánh từng kênh màu ===
        b1, g1, r1 = cv2.split(img1_resized)
        b2, g2, r2 = cv2.split(img2_resized)
        
        diff_b = cv2.absdiff(b1, b2)
        diff_g = cv2.absdiff(g1, g2)
        diff_r = cv2.absdiff(r1, r2)
        
        channel_diff = np.maximum(np.maximum(diff_b, diff_g), diff_r)
        
        # === PHƯƠNG PHÁP 4: Threshold động ===
        ssim_diff_normalized = ((1 - ssim_diff) * 255).astype(np.uint8)
        _, ssim_thresh = cv2.threshold(ssim_diff_normalized, 30, 255, cv2.THRESH_BINARY)
        
        color_diff_normalized = np.clip(color_diff * 2, 0, 255).astype(np.uint8)
        _, color_thresh = cv2.threshold(color_diff_normalized, 20, 255, cv2.THRESH_BINARY)
        
        _, channel_thresh = cv2.threshold(channel_diff, 15, 255, cv2.THRESH_BINARY)
        
        # === KẾT HOP TẤT CẢ PHƯƠNG PHÁP ===
        combined_mask = cv2.bitwise_or(ssim_thresh, color_thresh)
        combined_mask = cv2.bitwise_or(combined_mask, channel_thresh)
        
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_CLOSE, kernel)
        combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN, kernel)
        
        # === TÌM VÀ VẼ KHÁC BIỆT ===
        contours, _ = cv2.findContours(combined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        result_img = img2_resized.copy()
        differences_count = 0
        difference_details = []
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 25:
                x, y, w, h = cv2.boundingRect(contour)
                
                region_diff = color_diff[y:y+h, x:x+w]
                avg_difference = np.mean(region_diff)
                
                if avg_difference > 50:
                    color = (0, 0, 255)
                    thickness = 3
                    diff_level = "high"
                elif avg_difference > 25:
                    color = (0, 165, 255)
                    thickness = 2
                    diff_level = "medium"
                else:
                    color = (0, 255, 255)
                    thickness = 2
                    diff_level = "low"
                
                cv2.rectangle(result_img, (x, y), (x + w, y + h), color, thickness)
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
        
        # === TẠO ẢNH HEATMAP ===
        heatmap = cv2.applyColorMap(color_diff_normalized, cv2.COLORMAP_JET)
        alpha = 0.3
        heatmap_overlay = cv2.addWeighted(img2_resized, 1-alpha, heatmap, alpha, 0)
        
        # Lưu ảnh kết quả
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_filename = f"comparison_result_{timestamp}.jpg"
        heatmap_filename = f"heatmap_{timestamp}.jpg"
        
        result_path = RESULT_FOLDER / result_filename
        heatmap_path = RESULT_FOLDER / heatmap_filename
        
        cv2.imwrite(str(result_path), result_img)
        cv2.imwrite(str(heatmap_path), heatmap_overlay)
        
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

def simple_template_matching(template_path: str, screenshot_path: str):
    """Template matching đơn giản - trả về kích thước thực tế tìm thấy"""
    try:
        template = cv2.imread(template_path)
        screenshot = cv2.imread(screenshot_path)
        
        if template is None or screenshot is None:
            return None, "Không thể đọc template hoặc screenshot"
        
        template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        screenshot_gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
        
        h, w = template_gray.shape
        print(f"🔍 Template size: {w}x{h}")
        print(f"📸 Screenshot size: {screenshot_gray.shape[1]}x{screenshot_gray.shape[0]}")
        
        # Template matching với multiple scales
        best_match = None
        best_confidence = 0
        
        scales = [1.0, 0.8, 0.6, 0.5, 0.4, 0.3, 0.25, 0.2]
        
        for scale in scales:
            new_w = int(w * scale)
            new_h = int(h * scale)
            
            if new_w < 30 or new_h < 30:
                continue
            if new_w > screenshot_gray.shape[1] or new_h > screenshot_gray.shape[0]:
                continue
            
            resized_template = cv2.resize(template_gray, (new_w, new_h))
            result = cv2.matchTemplate(screenshot_gray, resized_template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)
            
            print(f"Scale {scale:.2f}: confidence = {max_val:.3f} at {max_loc}")
            
            if max_val > best_confidence:
                best_confidence = max_val
                best_match = {
                    'location': max_loc,
                    'actual_size': (new_w, new_h),  # ✅ Kích thước thực tế tìm thấy
                    'original_size': (w, h),        # Kích thước gốc template
                    'scale': scale
                }
        
        if best_match and best_confidence > 0.3:
            x, y = best_match['location']
            # ✅ SỬ DỤNG KÍCH THƯỚC THỰC TẾ
            actual_w, actual_h = best_match['actual_size']
            
            print(f"✅ Tìm thấy! Vị trí: ({x}, {y}), Kích thước thực tế: {actual_w}x{actual_h}, Confidence: {best_confidence:.3f}")
            return {
                'found': True,
                'x': x, 'y': y, 
                'width': actual_w, 'height': actual_h,  # ✅ Trả về kích thước thực tế
                'confidence': best_confidence,
                'scale': best_match['scale']
            }, None
        else:
            print(f"❌ Không tìm thấy template (best confidence: {best_confidence:.3f})")
            return {'found': False}, "Không tìm thấy template trong screenshot"
            
    except Exception as e:
        return None, f"Lỗi template matching: {str(e)}"
    
def crop_exact_banner(screenshot_img, x, y, w, h, template_path, timestamp):
    """Crop chính xác banner và resize về kích thước template để so sánh"""
    try:
        # ✅ BƯỚC 1: Crop chính xác vùng banner tìm thấy
        print(f"✂️ Crop banner tại: ({x}, {y}) với kích thước: {w}x{h}")
        
        # Đảm bảo không crop ngoài biên ảnh
        img_h, img_w = screenshot_img.shape[:2]
        x_safe = max(0, x)
        y_safe = max(0, y)
        w_safe = min(w, img_w - x_safe)
        h_safe = min(h, img_h - y_safe)
        
        # Crop chính xác banner
        cropped_banner = screenshot_img[y_safe:y_safe+h_safe, x_safe:x_safe+w_safe]
        
        if cropped_banner.size == 0:
            return None, "Vùng crop trống"
        
        print(f"📐 Banner đã crop: {cropped_banner.shape[1]}x{cropped_banner.shape[0]}")
        
        # ✅ BƯỚC 2: Resize về kích thước template để so sánh công bằng
        template_img = cv2.imread(template_path)
        template_h, template_w = template_img.shape[:2]
        
        # Resize banner về kích thước template
        banner_resized = cv2.resize(cropped_banner, (template_w, template_h))
        
        # ✅ BƯỚC 3: Lưu cả ảnh gốc và ảnh đã resize
        # Lưu banner gốc (kích thước thực tế)
        original_filename = f"banner_original_{timestamp}.png"
        original_path = UPLOAD_FOLDER / original_filename
        cv2.imwrite(str(original_path), cropped_banner)
        
        # Lưu banner đã resize (để so sánh)
        resized_filename = f"banner_resized_{timestamp}.png"
        resized_path = UPLOAD_FOLDER / resized_filename
        cv2.imwrite(str(resized_path), banner_resized)
        
        print(f"✅ Đã lưu banner gốc: {original_filename}")
        print(f"✅ Đã lưu banner resize: {resized_filename}")
        
        return resized_filename, None
        
    except Exception as e:
        return None, f"Lỗi crop banner: {str(e)}"

def capture_and_find_banner(url: str, template_path: str):
    """Chụp trang web và tìm banner - cải tiến crop chính xác"""
    try:
        # Setup Chrome
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
        except Exception:
            driver = webdriver.Chrome(options=chrome_options)
        
        try:
            print(f"🌐 Đang truy cập: {url}")
            driver.get(url)
            time.sleep(5)
            
            # Chụp full page
            total_height = driver.execute_script("return document.body.scrollHeight")
            print(f"📏 Tổng chiều cao trang: {total_height}px")
            
            driver.set_window_size(1920, total_height)
            time.sleep(2)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_filename = f"fullpage_{timestamp}.png"
            screenshot_path = UPLOAD_FOLDER / screenshot_filename
            
            driver.save_screenshot(str(screenshot_path))
            print(f"📸 Đã chụp full page: {screenshot_filename}")
            
            # Template matching
            match_result, error = simple_template_matching(template_path, str(screenshot_path))
            
            if error:
                # Cleanup screenshot
                if os.path.exists(str(screenshot_path)):
                    os.remove(str(screenshot_path))
                return None, error
            
            if not match_result['found']:
                # Cleanup screenshot
                if os.path.exists(str(screenshot_path)):
                    os.remove(str(screenshot_path))
                return None, "Không tìm thấy banner trên trang web"
            
            # ✅ CROP CHÍNH XÁC BANNER
            screenshot_img = cv2.imread(str(screenshot_path))
            x = match_result['x']
            y = match_result['y']
            w = match_result['width']   # Kích thước thực tế
            h = match_result['height']  # Kích thước thực tế
            
            print(f"🎯 Banner tìm thấy:")
            print(f"   - Vị trí: ({x}, {y})")
            print(f"   - Kích thước thực tế: {w}x{h}")
            print(f"   - Scale: {match_result['scale']:.2f}")
            print(f"   - Confidence: {match_result['confidence']:.3f}")
            
            # Crop banner chính xác
            banner_filename, error = crop_exact_banner(
                screenshot_img, x, y, w, h, template_path, timestamp
            )
            
            if error:
                return None, error
            
            # Cleanup screenshot gốc
            os.remove(str(screenshot_path))
            
            return banner_filename, None
            
        finally:
            driver.quit()
            
    except Exception as e:
        return None, f"Lỗi capture: {str(e)}"

@app.get("/")
async def root():
    return {"message": "Visual Testing API with Template Matching", "version": "2.0.0"}

# ✅ ENDPOINT DUY NHẤT - HỖ TRỢ CẢ 2 CHẾĐỘ
@app.post("/upload")
async def compare_images(
    image1: UploadFile = File(...),
    image2: Optional[UploadFile] = File(None),
    compare_url: Optional[str] = Form(None),
    sensitivity: str = Form("high")
):
    """
    Upload và so sánh ảnh - hỗ trợ 2 chế độ:
    1. Upload 2 ảnh: image1 + image2
    2. Template matching: image1 + compare_url
    """
    try:
        # Kiểm tra input
        if not image2 and not compare_url:
            raise HTTPException(status_code=400, detail="Cần có ảnh thứ 2 hoặc URL để so sánh")
        
        if image2 and compare_url:
            raise HTTPException(status_code=400, detail="Chỉ có thể chọn ảnh thứ 2 HOẶC URL, không thể cả hai")
        
        # Lưu ảnh 1 (template hoặc baseline)
        if not allowed_file(image1.filename):
            raise HTTPException(status_code=400, detail="File ảnh không hợp lệ")
        
        filename1 = f"{uuid.uuid4()}_{image1.filename}"
        filepath1 = UPLOAD_FOLDER / filename1
        
        with open(filepath1, "wb") as buffer:
            content = await image1.read()
            buffer.write(content)
        
        print(f"💾 Đã lưu ảnh 1: {filename1}")
        
        # Xử lý ảnh 2 hoặc URL
        if image2:
            # ✅ CHẾĐỘ 1: Upload 2 ảnh
            print("📁 Chế độ: Upload 2 ảnh")
            
            if not allowed_file(image2.filename):
                raise HTTPException(status_code=400, detail="File ảnh thứ 2 không hợp lệ")
            
            filename2 = f"{uuid.uuid4()}_{image2.filename}"
            filepath2 = UPLOAD_FOLDER / filename2
            
            with open(filepath2, "wb") as buffer:
                content = await image2.read()
                buffer.write(content)
            
            print(f"💾 Đã lưu ảnh 2: {filename2}")
        
        else:
            # ✅ CHẾĐỘ 2: Template matching với URL
            print(f"🌐 Chế độ: Template Matching với URL: {compare_url}")
            
            cropped_filename, error = capture_and_find_banner(compare_url, str(filepath1))
            
            if error:
                raise HTTPException(status_code=400, detail=f"Template matching failed: {error}")
            
            filename2 = cropped_filename
            filepath2 = UPLOAD_FOLDER / filename2
            
            print(f"🎯 Template matching thành công: {filename2}")
        
        # So sánh ảnh
        print("🔄 Bắt đầu so sánh ảnh...")
        result, error = enhanced_compare_images(str(filepath1), str(filepath2))
        
        if error:
            raise HTTPException(status_code=500, detail=error)
        
        # Thêm metadata
        result['image1_path'] = filename1
        result['image2_path'] = filename2
        result['comparison_method'] = 'upload' if image2 else 'template_matching'
        
        if compare_url:
            result['source_url'] = compare_url
        
        print(f"✅ Hoàn thành! Độ tương đồng: {result['similarity_score']}%")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Lỗi server: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Lỗi server: {str(e)}")

def compare_images_ssim(image1_path: str, image2_path: str):
    return enhanced_compare_images(image1_path, image2_path)

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)