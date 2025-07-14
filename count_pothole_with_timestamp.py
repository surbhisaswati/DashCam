import cv2
import math
import cvzone
import os
import re
import csv
import easyocr
from ultralytics import YOLO

def crop_bottom_10_percent(image):
    height = image.shape[0]
    start_row = int(height * 0.9)  # Bottom 10%
    return image[start_row:, :]

def extract_datetime_from_ocr_results(ocr_results):
    texts = [text for (_, text, _) in ocr_results]

    for i in range(len(texts)):
        # Check if current line looks like a date
        date_match = re.match(r"\d{2}/\d{2}/\d{4}", texts[i])
        if date_match:
            date = date_match.group()
            time = ""
            ampm = ""

            # Case: date + time + AM on separate lines
            if i + 1 < len(texts):
                if re.search(r"\d{1,2}[:.]?\d{2}[:.]?\d{2}", texts[i + 1]):
                    time = texts[i + 1].replace(".", ":")
                    if i + 2 < len(texts) and re.search(r"\b(AM|PM)\b", texts[i + 2], re.IGNORECASE):
                        ampm = texts[i + 2].upper()

                elif re.search(r"\d{1,2}[:.]?\d{2}[:.]?\d{2}\s*(AM|PM)", texts[i + 1], re.IGNORECASE):
                    # Combined time and AM/PM
                    combined = texts[i + 1].replace(".", ":").upper()
                    parts = combined.split()
                    time = parts[0]
                    ampm = parts[1] if len(parts) > 1 else ""

            # Alternative: everything in one string
            elif re.search(r"\d{2}/\d{2}/\d{4}\s+\d{1,2}[:.]?\d{2}[:.]?\d{2}\s*(AM|PM)", texts[i], re.IGNORECASE):
                dt_match = re.search(r"(\d{2}/\d{2}/\d{4})\s+(\d{1,2}[:.]?\d{2}[:.]?\d{2})\s*(AM|PM)", texts[i], re.IGNORECASE)
                if dt_match:
                    date = dt_match.group(1)
                    time = dt_match.group(2).replace(".", ":")
                    ampm = dt_match.group(3).upper()

            if date and time and ampm:
                return date, f"{time} {ampm}"

    return None

def main(video_path, output_video_path="Media/output_with_detections8.mp4", output_dir="output_ocr"):
    os.makedirs(output_dir, exist_ok=True)

    # Initialize models
    model = YOLO("Weights/best_26062025.pt")
    reader = easyocr.Reader(['en'], gpu=False)
    classNames = ['Pothole']

    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))

    # Output CSV
    csv_path = os.path.join(output_dir, "datetime_data8.csv")
    with open(csv_path, mode='w', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(['Frame_Index', 'Date', 'Time', 'Pothole_Count'])

        frame_count = 0
        while True:
            success, img = cap.read()
            if not success:
                break

            pothole_count = 0
            results = model(img, stream=True)
            for r in results:
                boxes = r.boxes
                for box in boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    w, h = x2 - x1, y2 - y1
                    conf = math.ceil((box.conf[0] * 100)) / 100
                    cls = int(box.cls[0])
                    if conf > 0.4:
                        pothole_count += 1
                        cvzone.cornerRect(img, (x1, y1, w, h), t=2)
                        cvzone.putTextRect(img, f'{classNames[cls]} {conf}', (max(0, x1), max(35, y1)), scale=1, thickness=1)

            if pothole_count > 0:
                cropped = crop_bottom_10_percent(img)
                ocr_results = reader.readtext(cropped)

                print(f"📝 OCR raw texts (frame {frame_count}): {[text for (_, text, _) in ocr_results]}")

                dt = extract_datetime_from_ocr_results(ocr_results)
                if dt:
                    date, time = dt
                    csv_writer.writerow([frame_count, date, time, pothole_count])
                    print(f"✔ Frame {frame_count}: {date} {time} | Potholes: {pothole_count}")
                else:
                    print(f"❌ Frame {frame_count}: Potholes found, but no valid datetime detected")
            else:
                print(f"Frame {frame_count}: No potholes")

            out.write(img)
            frame_count += 1

    cap.release()
    out.release()
    print(f"\n✅ Finished.\nCSV saved at: {csv_path}\nOutput video saved at: {output_video_path}")

if __name__ == "__main__":
    video_path = "Media/Potholes8.mp4"  # Change if needed
    main(video_path)
