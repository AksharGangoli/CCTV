"""
============================================================
CCTV SMART MONITOR - INDIAN NUMBER PLATE RECOGNITION (ANPR)
============================================================
This module handles:
- Detecting number plates in video frames
- Reading plate text using OCR
- Parsing Indian plate format (STATE DISTRICT SERIES NUMBER)
- Identifying vehicle by plate
- Tracking blacklisted plates

Indian Number Plate Format:
- Standard: XX 00 XX 0000 (e.g., MH 12 AB 1234)
- Where:
  - XX = State code (MH, KA, DL, TN, etc.)
  - 00 = District/RTO code (01-99)
  - XX = Series letters (AA-ZZ)
  - 0000 = Number (0001-9999)

State Codes Supported:
AP, AR, AS, BR, CG, GA, GJ, HR, HP, JH, KA, KL, MP, MH,
MN, ML, MZ, NL, OD, PB, RJ, SK, TN, TS, TR, UP, UK, WB,
AN, CH, DN, DD, DL, JK, LA, LD, PY
============================================================
"""

import os
import re
import cv2
import numpy as np
from typing import List, Dict, Optional, Tuple
from datetime import datetime

try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False
    print("[ANPR] WARNING: EasyOCR not installed. Plate reading will be limited.")


# Indian state codes and their full names
INDIAN_STATES = {
    'AP': 'Andhra Pradesh', 'AR': 'Arunachal Pradesh',
    'AS': 'Assam', 'BR': 'Bihar',
    'CG': 'Chhattisgarh', 'GA': 'Goa',
    'GJ': 'Gujarat', 'HR': 'Haryana',
    'HP': 'Himachal Pradesh', 'JH': 'Jharkhand',
    'KA': 'Karnataka', 'KL': 'Kerala',
    'MP': 'Madhya Pradesh', 'MH': 'Maharashtra',
    'MN': 'Manipur', 'ML': 'Meghalaya',
    'MZ': 'Mizoram', 'NL': 'Nagaland',
    'OD': 'Odisha', 'PB': 'Punjab',
    'RJ': 'Rajasthan', 'SK': 'Sikkim',
    'TN': 'Tamil Nadu', 'TS': 'Telangana',
    'TR': 'Tripura', 'UP': 'Uttar Pradesh',
    'UK': 'Uttarakhand', 'WB': 'West Bengal',
    'AN': 'Andaman & Nicobar', 'CH': 'Chandigarh',
    'DN': 'Dadra & Nagar Haveli', 'DD': 'Daman & Diu',
    'DL': 'Delhi', 'JK': 'Jammu & Kashmir',
    'LA': 'Ladakh', 'LD': 'Lakshadweep',
    'PY': 'Puducherry'
}



class PlateDetector:
    """
    Indian Number Plate Detection and Recognition.
    Detects plates, reads text, and parses Indian format.
    """

    def __init__(self, db, config: Dict):
        """
        Initialize plate detector.
        
        Args:
            db: Database instance
            config: ANPR settings from config.yaml
        """
        self.db = db
        self.config = config
        self.confidence_threshold = config.get('confidence', 0.1)  # Save everything, even low confidence
        self.save_plate_images = config.get('save_plate_images', True)
        
        # Storage
        self.plates_dir = "storage/plates"
        os.makedirs(self.plates_dir, exist_ok=True)
        
        # Initialize EasyOCR reader (English for Indian plates)
        self.reader = None
        if EASYOCR_AVAILABLE:
            print("[ANPR] Loading OCR model (this may take a moment first time)...")
            self.reader = easyocr.Reader(['en'], gpu=False)
            print("[ANPR] OCR model loaded!")
        
        # Indian plate regex patterns - multiple formats
        # Standard: MH 12 AB 1234 or MH12AB1234
        self.plate_pattern = re.compile(
            r'([A-Z]{2})\s*(\d{1,2})\s*([A-Z]{1,3})\s*(\d{1,4})',
            re.IGNORECASE
        )
        
        # Also accept plates without strict state validation
        # (for better detection of partial reads)
        self.plate_pattern_loose = re.compile(
            r'([A-Z]{2})\s*(\d{1,2})\s*([A-Z0-9]{1,4})\s*(\d{1,4})',
            re.IGNORECASE
        )
        
        # Plate detection using image processing
        self._plate_cascade = None
        cascade_path = cv2.data.haarcascades + 'haarcascade_russian_plate_number.xml'
        if os.path.exists(cascade_path):
            self._plate_cascade = cv2.CascadeClassifier(cascade_path)
        
        # Cooldown to avoid detecting same plate repeatedly
        self._last_plates = {}  # {plate_number: timestamp}
        self._cooldown_seconds = 30
        
        print("[ANPR] Indian Number Plate Recognition initialized")

    def detect_plates(self, frame: np.ndarray, 
                      camera_name: str = "") -> List[Dict]:
        """
        Detect and read number plates in a frame.
        Returns empty list on any error (never crashes).
        """
        if frame is None:
            return []
        
        results = []
        try:
            plate_regions = self._find_plate_regions(frame)
            for region in plate_regions:
                x, y, w, h = region
                plate_img = frame[y:y+h, x:x+w]
                processed = self._preprocess_plate(plate_img)
                plate_text, confidence = self._read_plate_text(processed)
                
                # Debug: show what OCR reads
                if plate_text:
                    print(f"[ANPR] OCR read: '{plate_text}' (confidence: {confidence:.0%})")
                
                if plate_text and confidence >= self.confidence_threshold:
                    # Save plate image ALWAYS (regardless of pattern match)
                    image_path = ""
                    if self.save_plate_images:
                        clean_text = re.sub(r'[^A-Z0-9]', '', plate_text.upper())[:12]
                        if not clean_text:
                            clean_text = "UNKNOWN"
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        img_filename = f"{clean_text}_{timestamp}.jpg"
                        img_filepath = os.path.join(self.plates_dir, img_filename)
                        plate_img_resized = cv2.resize(plate_img, (200, 60))
                        cv2.imwrite(img_filepath, plate_img_resized, [cv2.IMWRITE_JPEG_QUALITY, 60])
                        image_path = img_filename
                    
                    parsed = self._parse_indian_plate(plate_text)
                    
                    if parsed:
                        if self._is_in_cooldown(parsed['full_plate']):
                            continue
                        
                        is_blacklisted = self.db.is_plate_blacklisted(parsed['full_plate'])
                        
                        plate_id = self.db.add_plate(
                            plate_number=parsed['full_plate'],
                            vehicle_type="unknown",
                            image_path=image_path,
                            camera_name=camera_name,
                            confidence=confidence,
                            state_code=parsed['state_code'],
                            district_code=parsed['district_code'],
                            series=parsed['series'],
                            number=parsed['number']
                        )
                        
                        self._last_plates[parsed['full_plate']] = datetime.now()
                        
                        results.append({
                            'plate_number': parsed['full_plate'],
                            'state': parsed['state_name'],
                            'state_code': parsed['state_code'],
                            'district_code': parsed['district_code'],
                            'series': parsed['series'],
                            'number': parsed['number'],
                            'location': (x, y, w, h),
                            'confidence': confidence,
                            'image_path': image_path,
                            'is_blacklisted': is_blacklisted,
                            'plate_id': plate_id
                        })
                        
                        status = "⚠️ BLACKLISTED" if is_blacklisted else "✓"
                        print(f"[ANPR] {status} Plate: {parsed['full_plate']} "
                              f"({parsed['state_name']}) [{confidence:.0%}]")
        except Exception as e:
            print(f"[ANPR] Error detecting plates: {e}")
        
        return results


    def _find_plate_regions(self, frame: np.ndarray) -> List[Tuple]:
        """
        Find potential number plate regions in the frame.
        Uses multiple methods for better detection.
        """
        regions = []
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Method 1: Cascade classifier
        if self._plate_cascade is not None:
            plates = self._plate_cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=4,
                minSize=(60, 20), maxSize=(300, 100)
            )
            for (x, y, w, h) in plates:
                regions.append((x, y, w, h))
        
        # Method 2: Contour-based detection (for Indian white/yellow plates)
        contour_regions = self._find_plates_by_contour(frame, gray)
        regions.extend(contour_regions)
        
        # Remove duplicate/overlapping regions
        regions = self._remove_overlapping(regions)
        
        if regions:
            print(f"[ANPR] Found {len(regions)} potential plate region(s)")
        
        return regions

    def _find_plates_by_contour(self, frame: np.ndarray, 
                                 gray: np.ndarray) -> List[Tuple]:
        """Find plates using contour analysis (works well for Indian plates)."""
        regions = []
        
        # Apply bilateral filter to reduce noise while keeping edges sharp
        filtered = cv2.bilateralFilter(gray, 11, 17, 17)
        
        # Edge detection
        edges = cv2.Canny(filtered, 30, 200)
        
        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_TREE, 
                                        cv2.CHAIN_APPROX_SIMPLE)
        
        # Sort by area (largest first)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:30]
        
        for contour in contours:
            # Approximate the contour
            peri = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.018 * peri, True)
            
            # Number plates are typically rectangular (4 corners)
            if len(approx) >= 4 and len(approx) <= 6:
                x, y, w, h = cv2.boundingRect(approx)
                
                # Indian plates have aspect ratio between 2:1 and 5:1
                aspect_ratio = w / h if h > 0 else 0
                if 2.0 <= aspect_ratio <= 5.5 and w > 60 and h > 15:
                    regions.append((x, y, w, h))
        
        return regions

    def _preprocess_plate(self, plate_img: np.ndarray) -> np.ndarray:
        """
        Preprocess plate image for better OCR accuracy.
        Indian plates: white/yellow background with black text.
        """
        # Resize for better OCR
        plate_img = cv2.resize(plate_img, (300, 80))
        
        # Convert to grayscale
        gray = cv2.cvtColor(plate_img, cv2.COLOR_BGR2GRAY)
        
        # Increase contrast
        gray = cv2.equalizeHist(gray)
        
        # Apply Gaussian blur to reduce noise
        gray = cv2.GaussianBlur(gray, (3, 3), 0)
        
        # Threshold to get black text on white background
        _, thresh = cv2.threshold(gray, 0, 255, 
                                   cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Morphological operations to clean up
        kernel = np.ones((2, 2), np.uint8)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        return thresh

    def _read_plate_text(self, plate_img: np.ndarray) -> Tuple[str, float]:
        """
        Read text from preprocessed plate image using OCR.
        
        Returns:
            (plate_text, confidence) tuple
        """
        if self.reader is None:
            return ("", 0.0)
        
        try:
            # Use EasyOCR
            results = self.reader.readtext(plate_img, detail=1,
                                           allowlist='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ')
            
            if not results:
                return ("", 0.0)
            
            # Combine all detected text
            full_text = ""
            total_confidence = 0.0
            
            for (bbox, text, confidence) in results:
                full_text += text + " "
                total_confidence += confidence
            
            avg_confidence = total_confidence / len(results) if results else 0.0
            plate_text = full_text.strip().upper()
            
            # Clean up common OCR mistakes for Indian plates
            plate_text = self._fix_ocr_mistakes(plate_text)
            
            return (plate_text, avg_confidence)
            
        except Exception as e:
            print(f"[ANPR] OCR Error: {e}")
            return ("", 0.0)


    def _fix_ocr_mistakes(self, text: str) -> str:
        """Fix common OCR misreads for Indian plates."""
        # Common character confusions
        replacements = {
            'O': '0',  # Letter O → number 0 (in number positions)
            'I': '1',  # Letter I → number 1
            'S': '5',  # Letter S → number 5
            'B': '8',  # Letter B → number 8
        }
        
        # Remove extra spaces and special characters
        text = re.sub(r'[^A-Z0-9\s]', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text

    def _parse_indian_plate(self, plate_text: str) -> Optional[Dict]:
        """
        Parse Indian number plate format.
        Tries strict pattern first, then loose pattern.
        """
        # Try strict pattern first
        match = self.plate_pattern.search(plate_text)
        
        if not match:
            # Try loose pattern
            match = self.plate_pattern_loose.search(plate_text)
        
        if match:
            state_code = match.group(1).upper()
            district_code = match.group(2)
            series = match.group(3).upper()
            number = match.group(4)
            
            # Get state name (or use "Unknown State" if not found)
            state_name = INDIAN_STATES.get(state_code, f"State: {state_code}")
            
            # Format the plate nicely
            full_plate = f"{state_code} {district_code} {series} {number}"
            
            return {
                'full_plate': full_plate,
                'state_code': state_code,
                'state_name': state_name,
                'district_code': district_code,
                'series': series,
                'number': number
            }
        
        # If no pattern matched but text looks like it could be a plate
        # (has at least 6 alphanumeric characters), save it anyway
        cleaned = re.sub(r'[^A-Z0-9]', '', plate_text.upper())
        if len(cleaned) >= 6:
            print(f"[ANPR] Partial plate detected: '{plate_text}' → saving as-is")
            return {
                'full_plate': plate_text.upper().strip(),
                'state_code': cleaned[:2] if len(cleaned) >= 2 else '',
                'state_name': INDIAN_STATES.get(cleaned[:2], 'Unknown'),
                'district_code': '',
                'series': '',
                'number': cleaned
            }
        
        print(f"[ANPR] Text '{plate_text}' did not match any plate pattern")
        return None

    def _save_plate_image(self, plate_img: np.ndarray, 
                          plate_number: str) -> str:
        """Save plate image crop to disk. Returns just filename for web serving."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        clean_plate = plate_number.replace(' ', '_')
        filename = f"{clean_plate}_{timestamp}.jpg"
        filepath = os.path.join(self.plates_dir, filename)
        
        # Resize and compress to save space
        plate_img = cv2.resize(plate_img, (200, 60))
        cv2.imwrite(filepath, plate_img, [cv2.IMWRITE_JPEG_QUALITY, 60])
        
        # Return just filename (not full path) for cross-platform web serving
        return filename

    def _is_in_cooldown(self, plate_number: str) -> bool:
        """Check if plate was recently detected."""
        last_time = self._last_plates.get(plate_number)
        if last_time is None:
            return False
        elapsed = (datetime.now() - last_time).total_seconds()
        return elapsed < self._cooldown_seconds

    def _remove_overlapping(self, regions: List[Tuple], 
                            overlap_thresh: float = 0.5) -> List[Tuple]:
        """Remove overlapping bounding boxes."""
        if not regions:
            return []
        
        # Simple non-maximum suppression
        unique = []
        for region in regions:
            x1, y1, w1, h1 = region
            is_duplicate = False
            
            for existing in unique:
                x2, y2, w2, h2 = existing
                # Check overlap
                overlap_x = max(0, min(x1+w1, x2+w2) - max(x1, x2))
                overlap_y = max(0, min(y1+h1, y2+h2) - max(y1, y2))
                overlap_area = overlap_x * overlap_y
                area1 = w1 * h1
                
                if area1 > 0 and overlap_area / area1 > overlap_thresh:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique.append(region)
        
        return unique

    def draw_plates_on_frame(self, frame: np.ndarray, 
                             detections: List[Dict]) -> np.ndarray:
        """Draw plate boxes and text on frame for display."""
        annotated = frame.copy()
        
        for det in detections:
            x, y, w, h = det['location']
            plate_num = det['plate_number']
            state = det['state']
            
            # Color: red for blacklisted, green for normal
            color = (0, 0, 255) if det['is_blacklisted'] else (0, 255, 0)
            
            # Draw box around plate
            cv2.rectangle(annotated, (x, y), (x+w, y+h), color, 2)
            
            # Draw text
            label = f"{plate_num} ({state})"
            cv2.putText(annotated, label, (x, y-10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        return annotated

    def search_plate(self, query: str) -> List[Dict]:
        """Search for a plate number in database."""
        return self.db.search_plate(query)

    def blacklist_plate(self, plate_number: str):
        """Add a plate to the blacklist."""
        self.db.blacklist_plate(plate_number)
        print(f"[ANPR] Blacklisted plate: {plate_number}")
