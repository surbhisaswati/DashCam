"""
OCR Processor Module
Handles OCR text extraction and datetime parsing from video frames
"""
import re
import easyocr

class OCRProcessor:
    """
    OCR processor for extracting datetime information from video frames
    """
    
    def __init__(self, languages=['en'], gpu=False):
        """
        Initialize OCR reader
        
        Args:
            languages (list): List of languages for OCR
            gpu (bool): Whether to use GPU acceleration
        """
        self.reader = easyocr.Reader(languages, gpu=gpu)
    
    def crop_bottom_10_percent(self, image):
        """
        Crop bottom 10% of image where timestamp usually appears
        
        Args:
            image: Input image (numpy array)
        
        Returns:
            image: Cropped image
        """
        height = image.shape[0]
        start_row = int(height * 0.9)
        return image[start_row:, :]
    
    def extract_datetime_from_ocr_results(self, ocr_results):
        """
        Extract date and time from OCR results
        
        Args:
            ocr_results: OCR results from easyocr
        
        Returns:
            tuple: (date, time) or None if not found
        """
        texts = [text for (_, text, _) in ocr_results]
        
        for i in range(len(texts)):
            # Look for date pattern MM/DD/YYYY
            date_match = re.match(r"\d{2}/\d{2}/\d{4}", texts[i])
            if date_match:
                date = date_match.group()
                time = ""
                ampm = ""

                # Check next text for time
                if i + 1 < len(texts):
                    if re.search(r"\d{1,2}[:.]?\d{2}[:.]?\d{2}", texts[i + 1]):
                        time = texts[i + 1].replace(".", ":")
                        if i + 2 < len(texts) and re.search(r"\b(AM|PM)\b", texts[i + 2], re.IGNORECASE):
                            ampm = texts[i + 2].upper()
                    elif re.search(r"\d{1,2}[:.]?\d{2}[:.]?\d{2}\s*(AM|PM)", texts[i + 1], re.IGNORECASE):
                        combined = texts[i + 1].replace(".", ":").upper()
                        parts = combined.split()
                        time = parts[0]
                        ampm = parts[1] if len(parts) > 1 else ""

                # Check if date and time are in the same text
                elif re.search(r"\d{2}/\d{2}/\d{4}\s+\d{1,2}[:.]?\d{2}[:.]?\d{2}\s*(AM|PM)", texts[i], re.IGNORECASE):
                    dt_match = re.search(r"(\d{2}/\d{2}/\d{4})\s+(\d{1,2}[:.]?\d{2}[:.]?\d{2})\s*(AM|PM)", texts[i], re.IGNORECASE)
                    if dt_match:
                        date = dt_match.group(1)
                        time = dt_match.group(2).replace(".", ":")
                        ampm = dt_match.group(3).upper()

                if date and time and ampm:
                    return date, f"{time} {ampm}"
        
        return None
    
    def extract_datetime_from_frame(self, image):
        """
        Extract datetime from video frame using OCR
        
        Args:
            image: Input video frame
        
        Returns:
            tuple: (date, time, ocr_texts) or (None, None, ocr_texts)
        """
        # Crop bottom part of image where timestamp appears
        cropped = self.crop_bottom_10_percent(image)
        
        # Perform OCR
        ocr_results = self.reader.readtext(cropped)
        ocr_texts = [text for (_, text, _) in ocr_results]
        
        # Extract datetime
        datetime_result = self.extract_datetime_from_ocr_results(ocr_results)
        
        if datetime_result:
            date, time = datetime_result
            return date, time, ocr_texts
        else:
            return None, None, ocr_texts
