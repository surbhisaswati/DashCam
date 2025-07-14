"""
Main Pipeline for Dashcam Pothole Detection and Grading
Orchestrates all modules: YOLO detection, GPS parsing, grading, and OCR processing
"""
import os
import cv2
import csv
from yolo_detection import PotholeDetector
from gps_parser import convert_git_to_data, find_matching_gps
from pothole_grading import grade_pothole, generate_grading_summary
from ocr_processor import OCRProcessor

def main(video_path, gps_git_path, output_video_path="Media/output_with_detections8.mp4", output_dir="output_ocr"):
    """
    Main pipeline function that processes video for pothole detection and grading
    Replicates the exact functionality of merge_ocr_gps_copy copy.py
    
    Args:
        video_path (str): Path to input video file
        gps_git_path (str): Path to GPS .git file
        output_video_path (str): Path for output video with detections
        output_dir (str): Directory for output files
    """
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Load GPS data
    gps_data = convert_git_to_data(gps_git_path)
    
    # Initialize components
    detector = PotholeDetector("Weights/best_26062025.pt", confidence_threshold=0.4)
    ocr_processor = OCRProcessor(['en'], gpu=False)
    
    # Initialize video capture and writer
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))
    
    # Setup CSV output
    csv_path = os.path.join(output_dir, "pothole_gps_merged.csv")
    with open(csv_path, mode='w', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(['Frame', 'Date', 'Time', 'Latitude', 'Longitude', 'Pothole_Count', 'Pothole_Grade'])
        
        frame_count = 0
        while True:
            success, img = cap.read()
            if not success:
                break
            
            pothole_count = 0
            pothole_grades = []
            
            # Detect potholes using YOLO
            detections = detector.detect_potholes(img)
            
            # Process each detection and draw on image
            for detection in detections:
                pothole_count += 1
                
                # Grade the pothole
                w, h = detection['width'], detection['height']
                conf = detection['confidence']
                grade, color = grade_pothole(w, h, conf)
                pothole_grades.append(grade)
                
                # Draw bounding box with grading color (manually to match original exactly)
                x1, y1, w, h = detection['bbox']
                import cvzone
                cvzone.cornerRect(img, (x1, y1, w, h), t=2, colorR=color)
                cvzone.putTextRect(img, f'Pothole {conf}', (max(0, x1), max(35, y1)), scale=1, thickness=1, colorR=color)
                cvzone.putTextRect(img, f'Grade: {grade}', (max(0, x1), max(65, y1 + 30)), scale=0.8, thickness=1, colorR=color)
            
            # Process OCR and GPS only if potholes detected (matching original logic)
            if pothole_count > 0:
                # Extract datetime from frame
                date, time, ocr_texts = ocr_processor.extract_datetime_from_frame(img)
                print(f"OCR raw texts (frame {frame_count}): {ocr_texts}")
                
                if date and time:
                    # Find matching GPS data
                    gps_entry = find_matching_gps(gps_data, date, time)
                    if gps_entry:
                        # Join all grades for this frame
                        grades_str = ", ".join(pothole_grades)
                        
                        csv_writer.writerow([
                            frame_count, date, time,
                            gps_entry['lat'], gps_entry['lon'],
                            pothole_count, grades_str
                        ])
                        
                        print(f"Frame {frame_count}: {date} {time} | Potholes: {pothole_count} | Grades: {pothole_grades}")
                    else:
                        print(f"No GPS match for {date} {time}")
                else:
                    print(f"Frame {frame_count}: Potholes found, but no valid datetime")
            else:
                print(f"Frame {frame_count}: No potholes")
            
            # Write frame to output video
            out.write(img)
            frame_count += 1
    
    # Cleanup
    cap.release()
    out.release()
    
    print(f"\nProcessing Complete!")
    print(f"CSV: {csv_path}")
    print(f"Video: {output_video_path}")
    
    # Generate grading summary
    generate_grading_summary(csv_path, output_dir)

if __name__ == "__main__":
    video_path = "Media/Potholes8.mp4"
    gps_git_path = "20250528110347_1800.git"
    main(video_path, gps_git_path)