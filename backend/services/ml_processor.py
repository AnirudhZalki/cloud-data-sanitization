import cv2
import pytesseract
import numpy as np
import re
from PIL import Image
import os
import sys

# Windows tesseract path fallback 
# You might need to change this depending on where Tesseract is installed
if sys.platform == "win32":
    if os.path.exists(r'C:\Program Files\Tesseract-OCR\tesseract.exe'):
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Patterns for Sensitive Data
SENSITIVE_PATTERNS = {
    "EMAIL": r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
    "PHONE": r'\+?(\d{1,3})?[-. (]?\d{3}[-. )]?\d{3}[-. ]?\d{4}',
    # Aadhaar-style 12-digit or SSN-style IDs
    "ID_NUMBER": r'\b\d{4}\s?\d{4}\s?\d{4}\b|\b\d{3}-\d{2}-\d{4}\b',
    # PAN card: exactly 10 alphanumeric chars in AAAAA9999A format
    "PAN_NUMBER": r'\b[A-Z]{5}[0-9]{4}[A-Z]\b',
    # Date of birth patterns like 31/07/2004 or 31-07-2004
    "DATE_OF_BIRTH": r'\b\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4}\b',
}

# Noise characters that Tesseract produces when OCR-ing Hindi/decorative text
_NOISE_CHARS_RE = re.compile(r"[^\x20-\x7E]+")  # strip non-printable / non-ASCII

def _clean_ocr_token(token: str) -> str:
    """Remove non-ASCII garbage characters that result from OCR on Hindi/decorative text."""
    cleaned = _NOISE_CHARS_RE.sub("", token).strip()
    # Also drop tokens that are purely punctuation noise after cleaning
    return cleaned if re.search(r'[A-Za-z0-9]', cleaned) else ""


def preprocess_for_ocr(img):
    """
    Enhance image quality for better OCR accuracy.
    Steps: upscale → denoise → convert to grayscale → adaptive threshold
    """
    # 1. Upscale to at least 300 DPI-equivalent width (helps Tesseract a lot)
    h, w = img.shape[:2]
    target_width = 1400
    if w < target_width:
        scale = target_width / w
        img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_CUBIC)

    # 2. Denoise
    img = cv2.fastNlMeansDenoisingColored(img, None, 10, 10, 7, 21)

    # 3. Convert to greyscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 4. Adaptive threshold → clean black-on-white text
    thresh = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=15,
        C=9
    )

    return thresh

def load_face_cascade():
    cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    return cv2.CascadeClassifier(cascade_path)

def blur_faces(img):
    """
    Detects faces in an image and blurs them out.
    """
    face_cascade = load_face_cascade()
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(30, 30)
    )
    
    for (x, y, w, h) in faces:
        roi = img[y:y+h, x:x+w]
        ksize = max(w // 3, h // 3)
        if ksize % 2 == 0:
            ksize += 1
            
        blurred_face = cv2.GaussianBlur(roi, (ksize, ksize), 30)
        img[y:y+h, x:x+w] = blurred_face
        
    return img

def redact_text(img):
    """
    Extracts text using pytesseract with preprocessing for better accuracy.
    Looks for sensitive patterns and draws black rectangles over them on the original image.
    Returns the processed image, cleaned extracted text, and a list of found sensitive data.
    """
    orig_h, orig_w = img.shape[:2]

    # Preprocess a copy of the image for OCR (upscaled, denoised, thresholded)
    preprocessed = preprocess_for_ocr(img.copy())
    pre_h, pre_w = preprocessed.shape[:2]

    # Scale factors to map preprocessed coords → original image coords
    scale_x = orig_w / pre_w
    scale_y = orig_h / pre_h

    extracted_text_list = []
    sensitive_data_list = []

    # --oem 3 = LSTM engine
    # --psm 6 = assume a single uniform block of text (better than psm 11 for structured docs)
    # lang=eng → avoids OCR-ing Hindi Devanagari as garbled ASCII
    tess_config = '--oem 3 --psm 6 -l eng'
    try:
        data = pytesseract.image_to_data(
            preprocessed, config=tess_config, output_type=pytesseract.Output.DICT
        )
    except Exception as e:
        print(f"OCR Error (Is Tesseract installed?): {e}")
        return img, "", []

    n_boxes = len(data['text'])

    for i in range(n_boxes):
        raw_token = data['text'][i]
        conf = int(data['conf'][i]) if data['conf'][i] != '-1' else 0

        # Skip low confidence detections and empty tokens
        if conf < 40 or not raw_token.strip():
            continue

        # Clean non-ASCII / Hindi noise from the token
        token = _clean_ocr_token(raw_token)
        if not token:
            continue

        extracted_text_list.append(token)

        redact = False
        for pattern_name, pattern in SENSITIVE_PATTERNS.items():
            if re.search(pattern, token):
                redact = True
                sensitive_data_list.append({"type": pattern_name, "text": token})
                break

        if redact:
            # Map bounding box from preprocessed → original image coordinates
            px, py, pw, ph = (
                data['left'][i], data['top'][i],
                data['width'][i], data['height'][i]
            )
            x = int(px * scale_x)
            y = int(py * scale_y)
            w = int(pw * scale_x)
            h = int(ph * scale_y)
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 0), -1)

    return img, " ".join(extracted_text_list), sensitive_data_list

def process_file_content(file_bytes, is_pdf=False):
    """
    Process file directly from bytes in memory.
    """
    all_extracted_text = []
    all_sensitive_data = []
    
    if is_pdf:
        import fitz
        doc = fitz.open("pdf", file_bytes)
        
        for page in doc:
            # Fast text extraction natively
            page_text = page.get_text()
            all_extracted_text.append(page_text)
            
            # Find and redact sensitive words natively
            words = page.get_text("words")
            for w in words:
                text = w[4].strip()
                if not text:
                    continue
                    
                redact = False
                for pattern_name, pattern in SENSITIVE_PATTERNS.items():
                    if re.search(pattern, text):
                        redact = True
                        all_sensitive_data.append({"type": pattern_name, "text": text})
                        break
                if redact:
                    rect = fitz.Rect(w[:4])
                    page.add_redact_annot(rect, fill=(0, 0, 0))
            
            # Apply redactions quickly
            page.apply_redactions()
            
        final_bytes = doc.write() if hasattr(doc, 'write') else doc.tobytes()
        return final_bytes, " ".join(all_extracted_text), all_sensitive_data
    else:
        nparr = np.frombuffer(file_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise ValueError("File is not a valid image or couldn't be decoded")

        # Only limit truly huge images (>4000px) to prevent memory issues;
        # preprocess_for_ocr() will upscale small images internally for better OCR accuracy.
        max_dim = 4000
        h, w = img.shape[:2]
        if max(h, w) > max_dim:
            scale = max_dim / max(h, w)
            img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)


        img = blur_faces(img)
        img, text, data = redact_text(img)
        all_extracted_text.append(text)
        all_sensitive_data.extend(data)
        
        success, encoded_img = cv2.imencode('.png', img)
        if not success:
             raise ValueError("Failed to encode processed image")
             
        return encoded_img.tobytes(), " ".join(all_extracted_text), all_sensitive_data
