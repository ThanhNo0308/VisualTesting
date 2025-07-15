import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim
import os
from pathlib import Path
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

# CONSTANTS
BASE_DIR = Path(__file__).parent
UPLOAD_FOLDER = BASE_DIR / "uploads"
RESULT_FOLDER = BASE_DIR / "results"
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}

# Tạo thư mục nếu chưa có
UPLOAD_FOLDER.mkdir(exist_ok=True)
RESULT_FOLDER.mkdir(exist_ok=True)

def allowed_file(filename: str) -> bool:
    """Kiểm tra file có hợp lệ không"""
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
    """So sánh 2 ảnh với độ chính xác cao - Độ nhạy cố định cao nhất"""
    try:
        # CỐ ĐỊNH SSIM THRESHOLD = 1.0 (NHẠY NHẤT)
        ssim_threshold = 1.0
        
        # Đọc ảnh
        img1 = cv2.imread(image1_path)
        img2 = cv2.imread(image2_path)
        
        if img1 is None or img2 is None:
            return None, "Không thể đọc một hoặc cả hai ảnh"
        
        print(f"🎯 SSIM threshold: {ssim_threshold} (cố định - độ nhạy cao nhất)")
        
        # Resize về cùng kích thước
        img1_resized, img2_resized = resize_images_to_same_size(img1, img2)
        
        # TÍNH SSIM
        gray1 = cv2.cvtColor(img1_resized, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(img2_resized, cv2.COLOR_BGR2GRAY)
        similarity_score, ssim_diff = ssim(gray1, gray2, full=True)
        
        # ✅ SỬ DỤNG SSIM THRESHOLD CỐ ĐỊNH = 1.0
        ssim_threshold_val = int((1 - ssim_threshold) * 255)  # = 0
        print(f"🔧 Using fixed SSIM threshold value: {ssim_threshold_val}")
        
        # So sánh màu sắc
        color_diff = np.sqrt(np.sum((img1_resized.astype(float) - img2_resized.astype(float)) ** 2, axis=2))
        
        # So sánh từng kênh màu
        b1, g1, r1 = cv2.split(img1_resized)
        b2, g2, r2 = cv2.split(img2_resized)
        
        diff_b = cv2.absdiff(b1, b2)
        diff_g = cv2.absdiff(g1, g2)
        diff_r = cv2.absdiff(r1, r2)
        channel_diff = np.maximum(np.maximum(diff_b, diff_g), diff_r)
        
        # THRESHOLD CỐ ĐỊNH CHO ĐỘ NHẠY CAO NHẤT
        ssim_diff_normalized = ((1 - ssim_diff) * 255).astype(np.uint8)
        _, ssim_thresh = cv2.threshold(ssim_diff_normalized, ssim_threshold_val, 255, cv2.THRESH_BINARY)
        
        color_diff_normalized = np.clip(color_diff * 2, 0, 255).astype(np.uint8)
        _, color_thresh = cv2.threshold(color_diff_normalized, 20, 255, cv2.THRESH_BINARY)
        
        _, channel_thresh = cv2.threshold(channel_diff, 15, 255, cv2.THRESH_BINARY)
        
        # Kết hợp tất cả phương pháp
        combined_mask = cv2.bitwise_or(ssim_thresh, color_thresh)
        combined_mask = cv2.bitwise_or(combined_mask, channel_thresh)
        
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_CLOSE, kernel)
        combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN, kernel)
        
        # Tìm và vẽ khác biệt
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
                    "x": int(x), "y": int(y), 
                    "width": int(w), "height": int(h),
                    "area": int(area),
                    "avg_difference": float(avg_difference),
                    "level": diff_level
                })
        
        # Tạo heatmap
        heatmap = cv2.applyColorMap(color_diff_normalized, cv2.COLORMAP_JET)
        heatmap_overlay = cv2.addWeighted(img2_resized, 0.7, heatmap, 0.3, 0)
        
        # Lưu kết quả
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_filename = f"comparison_result_{timestamp}.jpg"
        heatmap_filename = f"heatmap_{timestamp}.jpg"
        
        cv2.imwrite(str(RESULT_FOLDER / result_filename), result_img)
        cv2.imwrite(str(RESULT_FOLDER / heatmap_filename), heatmap_overlay)
        
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
            'settings': {
                'ssim_threshold': ssim_threshold,
                'mode': 'fixed_high_sensitivity'
            },
            'status': 'success'
        }, None
        
    except Exception as e:
        return None, f"Lỗi xử lý ảnh: {str(e)}"

def simple_template_matching(template_path: str, screenshot_path: str):
    """Template matching đơn giản với multiple scales"""
    try:
        template = cv2.imread(template_path)
        screenshot = cv2.imread(screenshot_path)
        
        if template is None or screenshot is None:
            return None, "Không thể đọc template hoặc screenshot"
        
        template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        screenshot_gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
        
        h, w = template_gray.shape
        print(f"🔍 Template: {w}x{h}, Screenshot: {screenshot_gray.shape[1]}x{screenshot_gray.shape[0]}")
        
        best_match = None
        best_confidence = 0
        scales = [1.0, 0.8, 0.6, 0.5, 0.4, 0.3, 0.25, 0.2]
        
        for scale in scales:
            new_w, new_h = int(w * scale), int(h * scale)
            
            if new_w < 30 or new_h < 30 or new_w > screenshot_gray.shape[1] or new_h > screenshot_gray.shape[0]:
                continue
            
            resized_template = cv2.resize(template_gray, (new_w, new_h))
            result = cv2.matchTemplate(screenshot_gray, resized_template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)
            
            print(f"Scale {scale:.2f}: confidence = {max_val:.3f}")
            
            if max_val > best_confidence:
                best_confidence = max_val
                best_match = {
                    'location': max_loc,
                    'actual_size': (new_w, new_h),
                    'scale': scale
                }
        
        if best_match and best_confidence > 0.3:
            x, y = best_match['location']
            actual_w, actual_h = best_match['actual_size']
            
            print(f"✅ Tìm thấy tại ({x}, {y}) với size {actual_w}x{actual_h}, confidence: {best_confidence:.3f}")
            return {
                'found': True,
                'x': x, 'y': y, 
                'width': actual_w, 'height': actual_h,
                'confidence': best_confidence,
                'scale': best_match['scale']
            }, None
        else:
            print(f"❌ Không tìm thấy (best confidence: {best_confidence:.3f})")
            return {'found': False}, "Không tìm thấy template trong screenshot"
            
    except Exception as e:
        return None, f"Lỗi template matching: {str(e)}"

def crop_exact_banner(screenshot_img, x, y, w, h, template_path, timestamp):
    """Crop chính xác banner và resize về kích thước template"""
    try:
        print(f"✂️ Crop banner tại ({x}, {y}) với size {w}x{h}")
        
        # Đảm bảo crop trong biên ảnh
        img_h, img_w = screenshot_img.shape[:2]
        x_safe = max(0, x)
        y_safe = max(0, y)
        w_safe = min(w, img_w - x_safe)
        h_safe = min(h, img_h - y_safe)
        
        cropped_banner = screenshot_img[y_safe:y_safe+h_safe, x_safe:x_safe+w_safe]
        
        if cropped_banner.size == 0:
            return None, "Vùng crop trống"
        
        # Resize về kích thước template để so sánh công bằng
        template_img = cv2.imread(template_path)
        template_h, template_w = template_img.shape[:2]
        banner_resized = cv2.resize(cropped_banner, (template_w, template_h))
        
        # Lưu banner đã resize
        resized_filename = f"banner_resized_{timestamp}.png"
        resized_path = UPLOAD_FOLDER / resized_filename
        cv2.imwrite(str(resized_path), banner_resized)
        
        print(f"✅ Đã crop và resize banner: {resized_filename}")
        return resized_filename, None
        
    except Exception as e:
        return None, f"Lỗi crop banner: {str(e)}"

def setup_chrome_driver():
    """Setup Chrome driver với các options tối ưu"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    try:
        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=chrome_options)
    except Exception:
        return webdriver.Chrome(options=chrome_options)

def capture_full_page(driver, url):
    """Chụp full page của trang web"""
    print(f"🌐 Đang truy cập: {url}")
    driver.get(url)
    time.sleep(5)
    
    # Chụp full page
    total_height = driver.execute_script("return document.body.scrollHeight")
    print(f"📏 Tổng chiều cao: {total_height}px")
    
    driver.set_window_size(1920, total_height)
    time.sleep(2)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_filename = f"fullpage_{timestamp}.png"
    screenshot_path = UPLOAD_FOLDER / screenshot_filename
    
    driver.save_screenshot(str(screenshot_path))
    print(f"📸 Đã chụp: {screenshot_filename}")
    
    return str(screenshot_path), timestamp

def capture_and_find_banner(url: str, template_path: str):
    """Chụp trang web và tìm banner - Function chính"""
    driver = None
    screenshot_path = None
    
    try:
        # Setup driver
        driver = setup_chrome_driver()
        
        # Chụp full page
        screenshot_path, timestamp = capture_full_page(driver, url)
        
        # Template matching
        match_result, error = simple_template_matching(template_path, screenshot_path)
        
        if error or not match_result.get('found'):
            return None, error or "Không tìm thấy banner"
        
        # Crop banner
        screenshot_img = cv2.imread(screenshot_path)
        x, y, w, h = match_result['x'], match_result['y'], match_result['width'], match_result['height']
        
        print(f"🎯 Banner tìm thấy: ({x}, {y}) - {w}x{h}, confidence: {match_result['confidence']:.3f}")
        
        banner_filename, crop_error = crop_exact_banner(
            screenshot_img, x, y, w, h, template_path, timestamp
        )
        
        if crop_error:
            return None, crop_error
        
        return banner_filename, None
        
    except Exception as e:
        return None, f"Lỗi capture: {str(e)}"
        
    finally:
        # Cleanup
        if driver:
            driver.quit()
        if screenshot_path and os.path.exists(screenshot_path):
            os.remove(screenshot_path)