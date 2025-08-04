import os
import pydicom
import pytesseract
from PIL import Image
import numpy as np
import cv2
folder_path=r"C:\CT\Alaa Eldin"
def extract_total_dlp_from_dicom_files(folder_path):
    total_dlp_found = False

    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith(".dcm"):
                file_path = os.path.join(root, file)
                try:
                    ds = pydicom.dcmread(file_path)

                    # نحاول نحول الصورة لـ grayscale لاستخدام OCR
                    if 'PixelData' in ds:
                        image = ds.pixel_array.astype(np.float32)
                        image = cv2.normalize(image, None, 0, 255, cv2.NORM_MINMAX)
                        image = image.astype(np.uint8)

                        # تحويل لصورة PIL عشان OCR
                        pil_img = Image.fromarray(image)
                        text = pytesseract.image_to_string(pil_img)

                        # نبحث عن Total DLP
                        for line in text.split("\n"):
                            if "Total DLP" in line:
                                print(f"From file: {file_path}")
                                print(f"Line: {line}")
                                dlp_value = extract_number_from_text(line)
                                if dlp_value:
                                    print(f"✅ Total DLP Found: {dlp_value} mGy·cm\n")
                                    total_dlp_found = True
                except Exception as e:
                    print(f"❌ Error reading file {file_path}: {e}")

    if not total_dlp_found:
        print("❌ لم يتم العثور على Total DLP في أي ملف.")

def extract_number_from_text(text):
    """Extract first float number from a line of text."""
    import re
    matches = re.findall(r"[\d\.]+", text)
    if matches:
        return float(matches[0])
    return None
