import os, tempfile, json, joblib, re, base64, requests
from flask import Flask, request, jsonify, render_template
import numpy as np, cv2, pytesseract
from skimage.metrics import structural_similarity as ssim
from xgboost import XGBClassifier
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urljoin
import time

PROJECT_DIR = os.path.abspath(os.path.dirname(__file__))
ART_DIR = os.path.join(PROJECT_DIR, "visualtesting", "artifacts")
MODEL_PKL = os.path.join(ART_DIR, "model.pkl")
MODEL_JSON = os.path.join(ART_DIR, "model.json")
META_PATH = os.path.join(ART_DIR, "metadata.json")

pytesseract.pytesseract.tesseract_cmd = os.environ.get(
    "TESSERACT_CMD", r"D:\Apps\Tesseract-OCR\tesseract.exe"
)

if os.path.exists(MODEL_PKL):
    model = joblib.load(MODEL_PKL)
elif os.path.exists(MODEL_JSON):
    model = XGBClassifier()
    model.load_model(MODEL_JSON)
else:
    raise FileNotFoundError(f"Model not found: {MODEL_PKL} or {MODEL_JSON}")

meta = json.load(open(META_PATH, "r", encoding="utf-8"))
label_map = meta["label_map"]
inv_map = {v: k for k, v in label_map.items()}

class Extractor:
    def __init__(self):
        self.orb = cv2.ORB_create(nfeatures=150)
        self._ocr_cache = {}

    def prep_gray(self, img_path):
        g = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
        if g is None: return None
        h, w = g.shape
        if h * w > 700_000:
            s = (700_000 / (h * w)) ** 0.5
            g = cv2.resize(g, (int(w * s), int(h * s)))
        return cv2.medianBlur(g, 3)

    def ensure_same_size(self, g1, g2):
        if g1 is None or g2 is None: return None, None
        if g1.shape == g2.shape: return g1, g2
        h1, w1 = g1.shape
        return g1, cv2.resize(g2, (w1, h1))

    def f_ssim(self, a, b):
        try:
            g1 = self.prep_gray(a)
            g2 = self.prep_gray(b)
            g1, g2 = self.ensure_same_size(g1, g2)
            if g1 is None or g2 is None: return 0.5
            val = ssim(g1, g2, data_range=255) 
            return float(np.clip(val, 0.0, 1.0))
        except: return 0.5

    def f_ocr(self, a, b):
        def get_words(p, gimg):
            if p in self._ocr_cache: return self._ocr_cache[p]
            bw = cv2.adaptiveThreshold(gimg, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                    cv2.THRESH_BINARY, 21, 8)
            txt = pytesseract.image_to_string(bw, config="--oem 3 --psm 6")
            ws = re.sub(r'[^A-Za-z0-9 ]+', ' ', txt).lower().split()
            self._ocr_cache[p] = ws
            return ws
        try:
            g1 = self.prep_gray(a)
            g2 = self.prep_gray(b)
            if g1 is None or g2 is None: return 0.5
            t1 = get_words(a, g1)
            t2 = get_words(b, g2)
            s1, s2 = set(t1), set(t2)
            if not s1 and not s2: return 0.8      
            if not s1 or not s2:  return 0.3      
            jacc = len(s1 & s2) / len(s1 | s2)   
            return float(jacc)
        except:
            return 0.5

    def f_hist(self, a, b):
        try:
            c1, c2 = cv2.imread(a), cv2.imread(b)
            if c1 is None or c2 is None: return 0.5
            sims = []
            for ch in range(3):
                h1 = cv2.calcHist([c1],[ch],None,[32],[0,256])
                h2 = cv2.calcHist([c2],[ch],None,[32],[0,256])
                cv2.normalize(h1,h1,alpha=1.0,norm_type=cv2.NORM_L1)
                cv2.normalize(h2,h2,alpha=1.0,norm_type=cv2.NORM_L1)
                sims.append((cv2.compareHist(h1,h2,cv2.HISTCMP_CORREL)+1)/2)
            return float(np.mean(sims))
        except: return 0.5

    def f_orb(self, a, b):
        try:
            g1 = self.prep_gray(a); g2 = self.prep_gray(b)
            kp1, d1 = self.orb.detectAndCompute(g1, None)
            kp2, d2 = self.orb.detectAndCompute(g2, None)
            if d1 is None or d2 is None: return 0.5
            bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
            knn = bf.knnMatch(d1, d2, k=2)
            good = []
            for pr in knn:
                if len(pr) < 2: continue
                m, n = pr
                if m.distance < 0.75 * n.distance: good.append(m)
            if not good: return 0.5
            ratio = len(good) / max(1, min(len(kp1), len(kp2)))
            quality = 1 - np.mean([m.distance for m in good]) / 256.0
            return float(np.clip(0.5 * ratio + 0.5 * quality, 0, 1))
        except: return 0.5

    def f_layout(self, a, b):
        try:
            g1 = self.prep_gray(a); g2 = self.prep_gray(b)
            g1, g2 = self.ensure_same_size(g1, g2)
            if g1 is None or g2 is None: return 0.5
            e1 = cv2.Canny(g1, 50, 150) > 0
            e2 = cv2.Canny(g2, 50, 150) > 0
            inter = np.logical_and(e1, e2).sum()
            uni = np.logical_or(e1, e2).sum()
            return 1.0 if uni == 0 else float(inter/uni)
        except: return 0.5

    def features(self, a, b):
        return [self.f_ssim(a,b), self.f_ocr(a,b), self.f_hist(a,b), self.f_orb(a,b), self.f_layout(a,b)]

extractor = Extractor()
app = Flask(__name__)

def save_upload(file_storage):
    fd, path = tempfile.mkstemp(suffix=os.path.splitext(file_storage.filename)[-1])
    os.close(fd)
    file_storage.save(path)
    return path

def predict_pair(original_path, variant_path):
    f = extractor.features(original_path, variant_path)
    y_int = int(model.predict([f])[0])
    
    try:
        proba = model.predict_proba([f])[0]
        confidence = float(max(proba))
        proba_dict = {inv_map[i]: float(proba[i]) for i in range(len(proba))}
    except:
        confidence = 1.0
        proba_dict = {}
    
    return {
        "label": inv_map[y_int],
        "confidence": confidence,
        "probabilities": proba_dict,
        "features": {
            "SSIM": f[0],
            "OCR": f[1], 
            "Histogram": f[2],
            "ORB": f[3],
            "Layout": f[4]
        }
    }

def get_image_from_web(url, selector):
    """Lấy ảnh từ web theo selector"""
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    
    driver = None
    try:
        driver = webdriver.Chrome(options=options)
        driver.get(url)
        time.sleep(3)
        
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)
        
        element = WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
        driver.execute_script("""
            arguments[0].style.display = 'block';
            arguments[0].style.visibility = 'visible';
            arguments[0].classList.remove('hidden');
            arguments[0].scrollIntoView({block: 'center'});
        """, element)
        time.sleep(1)
        
        img_src = None
        if element.tag_name.lower() == 'img':
            img_src = element.get_attribute('src') or element.get_attribute('data-src')
        else:
            for img in element.find_elements(By.TAG_NAME, 'img'):
                driver.execute_script("arguments[0].classList.remove('hidden');", img)
                src = img.get_attribute('src') or img.get_attribute('data-src')
                if src and not src.startswith('data:'):
                    img_src = src
                    break
        
        if not img_src or img_src.startswith('data:'):
            raise Exception("Không tìm thấy URL ảnh hợp lệ")
        
        img_url = urljoin(url, img_src)
        response = requests.get(img_url, headers={'Referer': url}, timeout=15)
        response.raise_for_status()
        
        temp_path = tempfile.mktemp(suffix='.jpg')
        with open(temp_path, 'wb') as f:
            f.write(response.content)
        
        return temp_path
        
    except Exception as e:
        raise Exception(f"Lỗi crawl: {str(e)}")
    finally:
        if driver:
            driver.quit()

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/predict", methods=["POST"])
def predict():
    if "original" not in request.files or "variant" not in request.files:
        return jsonify({"error":"Missing files"}), 400
    
    op = vp = None
    try:
        op = save_upload(request.files["original"])
        vp = save_upload(request.files["variant"])
        res = predict_pair(op, vp)
        return jsonify(res)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        for p in (op, vp):
            if p:
                try: os.remove(p)
                except: pass

@app.route("/crawl-all", methods=["POST"])
def crawl_all():
    """Crawl tất cả trang web trong danh sách"""
    try:
        websites = json.loads(request.headers.get('X-Websites', '[]'))
    except:
        return jsonify({"error": "Dữ liệu websites không hợp lệ"}), 400
    
    if "original" not in request.files:
        return jsonify({"error": "Thiếu ảnh gốc"}), 400
    
    if not websites:
        return jsonify({"error": "Không có trang web nào để test"}), 400
    
    op = None
    results = []
    
    try:
        op = save_upload(request.files["original"])
        
        for i, site in enumerate(websites):
            url = site.get('url', '').strip()
            selector = site.get('selector', '').strip()
            branch = site.get('branch', f'Site {i+1}').strip()
            
            if not url or not selector:
                results.append({
                    "branch": branch,
                    "error": "Thiếu URL hoặc selector",
                    "status": "failed"
                })
                continue
            
            downloaded_path = None
            try:
                downloaded_path = get_image_from_web(url, selector)
            
                comparison = predict_pair(op, downloaded_path)
                
                with open(downloaded_path, 'rb') as f:
                    img_b64 = base64.b64encode(f.read()).decode()
                
                results.append({
                    "branch": branch,
                    "url": url,
                    "label": comparison["label"],
                    "confidence": comparison["confidence"],
                    "downloaded_image": f"data:image/jpeg;base64,{img_b64}",
                    "status": "success"
                })
                
            except Exception as e:
                results.append({
                    "branch": branch,
                    "url": url,
                    "error": str(e),
                    "status": "failed"
                })
            finally:
                if downloaded_path:
                    try: os.remove(downloaded_path)
                    except: pass
        
        return jsonify({"results": results})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if op:
            try: os.remove(op)
            except: pass

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "model": meta.get("model", "Unknown"),
        "version": meta.get("version", "Unknown")
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)