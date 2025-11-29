import io
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter

try:
    import streamlit as st
except ModuleNotFoundError:
    st = None

# Set temporary directory to project folder to avoid disk space issues
TEMP_DIR = Path(__file__).resolve().parent.parent / "temp_ocr"
TEMP_DIR.mkdir(exist_ok=True)
os.environ['TMPDIR'] = str(TEMP_DIR)
tempfile.tempdir = str(TEMP_DIR)


@dataclass
class OCRMatchResult:
    """Result from OCR-based ID card matching"""
    label: str
    confidence: float
    extracted_text: str
    keywords_found: list[str]
    license_number: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class IDCardOCRMatcher:
    """
    ID Card matcher using OCR text extraction.
    Identifies card type by searching for specific keywords in extracted text.
    """
    
    # Keywords that indicate each card type (expanded for better matching)
    CARD_KEYWORDS = {
        "Drivers Licence": [
            "driver", "licence", "license", "driving", "dvla", 
            "driver's licence", "driver's license", "driving licence",
            "drivers", "drive", "motor", "vehicle", "dl",
            "california", "cardholder", "dmv", "lic", "operator"
        ],
        "Ghana Card": [
            "ghana", "nia", "national identification", "ghana card",
            "national identification authority", "republic of ghana",
            "ghanacard", "national id", "citizenship"
        ],
        "Voter ID": [
            "voter", "electoral", "commission", "voter id", "voter's id",
            "electoral commission", "voter identification", "polling",
            "vote", "election", "elector", "ballot"
        ]
    }
    
    def __init__(self):
        """Initialize the OCR matcher"""
        # Test if tesseract is available
        try:
            pytesseract.get_tesseract_version()
        except Exception as e:
            raise RuntimeError(
                f"Tesseract OCR not found or not properly installed. Error: {e}\n"
                "Please install tesseract-ocr:\n"
                "  macOS: brew install tesseract\n"
                "  Ubuntu: sudo apt-get install tesseract-ocr\n"
                "  Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki"
            )
    
    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Preprocess image for better OCR results using PIL.
        - Convert to grayscale
        - Enhance contrast
        - Sharpen (helps with blur)
        - Resize if too small
        """
        # Resize if image is too small (helps with very small images)
        width, height = image.size
        min_size = 1000
        if width < min_size or height < min_size:
            scale = max(min_size / width, min_size / height)
            new_width = int(width * scale)
            new_height = int(height * scale)
            image = image.resize((new_width, new_height), Image.LANCZOS)
        
        # Convert to grayscale
        gray = image.convert('L')
        
        # Enhance contrast significantly
        enhancer = ImageEnhance.Contrast(gray)
        contrasted = enhancer.enhance(2.5)
        
        # Enhance brightness
        brightness_enhancer = ImageEnhance.Brightness(contrasted)
        brightened = brightness_enhancer.enhance(1.2)
        
        # Apply multiple sharpening passes for blurry images
        sharpened = brightened.filter(ImageFilter.SHARPEN)
        sharpened = sharpened.filter(ImageFilter.SHARPEN)
        sharpened = sharpened.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))
        
        return sharpened
    
    def extract_text(self, image_bytes: bytes) -> str:
        """
        Extract text from image using Tesseract OCR.
        
        Args:
            image_bytes: Raw image bytes
            
        Returns:
            Extracted text as string
        """
        try:
            # Load image
            image = Image.open(io.BytesIO(image_bytes))
            image = image.convert("RGB")
            
            # Try multiple preprocessing approaches and combine results
            texts = []
            
            # Approach 1: Basic preprocessing
            processed1 = self.preprocess_image(image)
            custom_config = r'--oem 3 --psm 6'
            text1 = pytesseract.image_to_string(processed1, config=custom_config)
            texts.append(text1)
            
            # Approach 2: Original image (sometimes works better)
            text2 = pytesseract.image_to_string(image, config=custom_config)
            texts.append(text2)
            
            # Approach 3: Different PSM mode (assume single block of text)
            custom_config2 = r'--oem 3 --psm 3'
            text3 = pytesseract.image_to_string(processed1, config=custom_config2)
            texts.append(text3)
            
            # Combine all extracted texts and remove duplicates
            combined_text = "\n".join(texts)
            
            return combined_text
        except Exception as e:
            raise RuntimeError(f"Failed to extract text from image: {e}")
    
    def match_card_type(self, text: str) -> OCRMatchResult:
        """
        Match card type based on extracted text.
        Uses fuzzy matching to handle OCR errors.
        
        Args:
            text: Extracted text from OCR
            
        Returns:
            OCRMatchResult with card type and confidence
        """
        text_lower = text.lower()
        
        # Count keyword matches for each card type
        match_scores = {}
        keywords_found = {}
        
        for card_type, keywords in self.CARD_KEYWORDS.items():
            score = 0
            found = []
            
            for keyword in keywords:
                # Exact word boundary matching
                pattern = r'\b' + re.escape(keyword) + r'\b'
                matches = re.findall(pattern, text_lower)
                if matches:
                    score += len(matches) * 2  # Exact matches get double weight
                    found.append(keyword)
                    continue
                
                # Fuzzy matching - check if keyword appears with minor errors
                # (e.g., "califonia" matches "california")
                if len(keyword) > 4:  # Only for longer words
                    # Simple substring matching for partial matches
                    if keyword in text_lower:
                        score += 1
                        found.append(f"{keyword}*")  # Mark as fuzzy match
            
            match_scores[card_type] = score
            keywords_found[card_type] = found
        
        # Find best match
        best_card = max(match_scores, key=match_scores.get)
        best_score = match_scores[best_card]
        
        # Calculate confidence (0-100%)
        # Confidence = how much better the best match is compared to other categories
        if best_score == 0:
            confidence = 0.0
            best_card = "Unknown"
            found_keywords = []
        else:
            # Calculate based on the number of keywords found for the best match
            # relative to the total possible keywords for that category
            total_possible_keywords = len(self.CARD_KEYWORDS[best_card])
            keywords_found_count = len(keywords_found[best_card])
            
            # Base confidence on keywords found
            confidence = min(100.0, (keywords_found_count / max(1, total_possible_keywords * 0.3)) * 100)
            
            # Boost confidence if we have strong matches (score is high)
            if best_score >= 4:  # At least 2 exact matches
                confidence = min(100.0, confidence * 1.5)
            
            found_keywords = keywords_found[best_card]
            
            # Ensure minimum confidence if we found any keywords
            if keywords_found_count > 0:
                confidence = max(confidence, 40.0)  # Minimum 40% if any keywords found
        
        return OCRMatchResult(
            label=best_card,
            confidence=confidence,
            extracted_text=text,
            keywords_found=found_keywords
        )
    
    def extract_license_number(self, text: str) -> Optional[str]:
        """
        Extract license number from OCR text.
        Looks for common patterns like: DL123456, 12345678, etc.
        
        Args:
            text: Extracted text from OCR
            
        Returns:
            License number if found, None otherwise
        """
        # Common license number patterns (ordered by specificity)
        patterns = [
            r'(?:DL|D\.L\.|LICENSE|LIC\.?|NO\.?|#|CDL)\s*[:.]?\s*([A-Z0-9]{6,12})',  # DL123456, LICENSE: ABC123
            r'(?:ID|CARD)\s*(?:NO\.?|#)\s*[:.]?\s*([A-Z0-9]{6,12})',  # ID NO: 123456
            r'\b([A-Z]\d{7,10})\b',  # A1234567
            r'\b(\d{8,10})\b',  # 12345678 (8-10 digits only, very common)
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                license_num = match.group(1)
                # Clean up common OCR errors
                license_num = license_num.replace('O', '0').replace('o', '0')  # O -> 0
                license_num = license_num.replace('I', '1').replace('l', '1')  # I/l -> 1
                return license_num
        
        return None
    
    def extract_name(self, text: str) -> tuple[Optional[str], Optional[str]]:
        """
        Extract first and last name from OCR text.
        Looks for common name patterns.
        
        Args:
            text: Extracted text from OCR
            
        Returns:
            Tuple of (first_name, last_name) or (None, None)
        """
        # Look for "NAME:" or "CARDHOLDER:" followed by name
        name_patterns = [
            r'(?:NAME|CARDHOLDER|FN|FIRST|LAST)[:.]?\s*([A-Z][a-z]+)\s+([A-Z][a-z]+)',
            r'(?:NAME)[:.]?\s*([A-Z]+),?\s+([A-Z]+)',  # All caps names
            r'\b([A-Z][a-z]{2,})\s+([A-Z][a-z]{2,})\b',  # Capitalized names (2+ chars each)
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, text)
            if match:
                first = match.group(1).strip().title()
                last = match.group(2).strip().title()
                # Validate names (avoid common OCR mistakes)
                if len(first) >= 2 and len(last) >= 2 and first.isalpha() and last.isalpha():
                    return first, last
        
        return None, None
    
    def classify(self, image_bytes: bytes) -> OCRMatchResult:
        """
        Classify ID card type from image bytes.
        
        Args:
            image_bytes: Raw image bytes
            
        Returns:
            OCRMatchResult with classification details
        """
        # Extract text
        text = self.extract_text(image_bytes)
        
        # Match card type
        result = self.match_card_type(text)
        
        # Extract additional info if it's a driver's license
        if result.label == "Drivers Licence":
            license_number = self.extract_license_number(text)
            first_name, last_name = self.extract_name(text)
            
            # Create new result with extracted info
            result = OCRMatchResult(
                label=result.label,
                confidence=result.confidence,
                extracted_text=result.extracted_text,
                keywords_found=result.keywords_found,
                license_number=license_number,
                first_name=first_name,
                last_name=last_name
            )
        
        return result


def classify_id_ocr(image_bytes: bytes) -> OCRMatchResult:
    """
    Convenience function to classify ID card using OCR.
    
    Args:
        image_bytes: Raw image bytes
        
    Returns:
        OCRMatchResult with card type and details
    """
    matcher = IDCardOCRMatcher()
    return matcher.classify(image_bytes)


def render_streamlit_app() -> None:
    """Standalone Streamlit app for OCR-based ID matching"""
    assert st is not None
    
    st.set_page_config(page_title="ID Matcher OCR", page_icon="📝", layout="centered")
    st.title("Government ID Matcher (OCR)")
    st.caption("Upload an ID card image and we'll identify it by reading the text on the card.")
    
    uploaded_file = st.file_uploader(
        "Upload ID image",
        type=["png", "jpg", "jpeg", "bmp", "gif"],
        accept_multiple_files=False,
        help="Click to upload the ID card image you want to classify.",
    )
    
    if uploaded_file is None:
        st.info("Choose an ID image to begin.")
        return
    
    image_bytes = uploaded_file.read()
    st.image(image_bytes, caption="Uploaded image", use_container_width=True)
    
    if st.button("Identify Card Type", type="primary"):
        with st.spinner("Extracting text and identifying card type..."):
            try:
                matcher = IDCardOCRMatcher()
                result = matcher.classify(image_bytes)
            except Exception as exc:
                st.error(f"Failed to process image: {exc}")
                return
        
        # Display results
        st.markdown("---")
        st.subheader("Results")
        
        if result.label != "Unknown":
            st.success(f"✅ Identified: **{result.label}**")
            st.metric("Confidence", f"{result.confidence:.1f}%")
            
            if result.keywords_found:
                st.info(f"**Keywords found:** {', '.join(result.keywords_found)}")
        else:
            st.error("❌ Could not identify card type")
            st.warning("No recognizable keywords found in the image.")
        
        # Show extracted text in expander
        with st.expander("View Extracted Text"):
            if result.extracted_text.strip():
                st.text(result.extracted_text)
            else:
                st.warning("No text was extracted from the image.")


def _cli() -> None:
    """Command-line interface for OCR-based ID matching"""
    import argparse
    from pathlib import Path
    
    parser = argparse.ArgumentParser(description="Classify an ID image using OCR")
    parser.add_argument("image", nargs="?", type=Path, help="Path to the ID image to classify")
    args = parser.parse_args()
    
    image_path = args.image
    if image_path is None:
        print("No image specified. Usage: python id_card_matcher_ocr.py <image_path>")
        return
    
    if not image_path.exists():
        print(f"Image not found: {image_path}")
        return
    
    print(f"Processing: {image_path}")
    print("-" * 50)
    
    with image_path.open("rb") as f:
        result = classify_id_ocr(f.read())
    
    print(f"Card Type: {result.label}")
    print(f"Confidence: {result.confidence:.1f}%")
    if result.keywords_found:
        print(f"Keywords Found: {', '.join(result.keywords_found)}")
    print("-" * 50)
    print("Extracted Text:")
    print(result.extracted_text)


if __name__ == "__main__":
    if st is not None:
        render_streamlit_app()
    else:
        _cli()
