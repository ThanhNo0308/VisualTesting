import os, tempfile, json, joblib, re
from flask import Flask, request, jsonify, render_template
import numpy as np, cv2, pytesseract
from difflib import SequenceMatcher
from skimage.metrics import structural_similarity as ssim

PROJECT_DIR = os.path.abspath(os.path.dirname(__file__))
ART_DIR = os.path.join(PROJECT_DIR, "visualtesting", "artifacts")
MODEL_PATH = os.path.join(ART_DIR, "model.pkl")
META_PATH = os.path.join(ART_DIR, "metadata.json")

pytesseract.pytesseract.tesseract_cmd = os.environ.get(
    "TESSERACT_CMD", r"D:\Apps\Tesseract-OCR\tesseract.exe"
)

if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(f"Model not found: {MODEL_PATH}")
if not os.path.exists(META_PATH):
    raise FileNotFoundError(f"Metadata not found: {META_PATH}")

model = joblib.load(MODEL_PATH)
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
            return float(np.clip((val + 1.0) / 2.0, 0.0, 1.0))
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
    return {"label": inv_map[y_int]}

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/static/<path:filename>")
def static_files(filename):
    return app.send_static_file(filename)

@app.route("/predict", methods=["POST"])
def predict():
    if "original" not in request.files or "variant" not in request.files:
        return jsonify({"error":"Missing files"}), 400
    op = save_upload(request.files["original"])
    vp = save_upload(request.files["variant"])
    try:
        res = predict_pair(op, vp)
        return jsonify(res)
    finally:
        for p in (op, vp):
            try: os.remove(p)
            except: pass

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)