"""
Main Pipeline for Dashcam Pothole Detection and Grading
Orchestrates all modules: YOLO detection, GPS parsing, grading, and OCR processing

Features:
- GPU-accelerated YOLO pothole detection using CUDA
- GPU-accelerated OCR text extraction using CUDA  
- Automatic fallback to CPU if GPU not available
- Consolidated GPS data processing from all .git files
- Smart caching to avoid re-processing GPS data
- Enhanced CSV output with GPS source tracking
"""
import os
import cv2
import csv
import glob
import base64
import numpy as np
from yolo_detection import PotholeDetector
from gps_parser import convert_git_to_data, find_matching_gps
from pothole_grading import grade_pothole, generate_grading_summary
from ocr_processor import OCRProcessor

def consolidate_gps_files(git_directory="git", output_dir="output_ocr", consolidated_csv="consolidated_gps_data.csv"):
    """
    Consolidate all GPS .git files into one CSV file
    
    Args:
        git_directory (str): Directory containing .git files
        output_dir (str): Output directory for consolidated CSV
        consolidated_csv (str): Name of the consolidated CSV file
    
    Returns:
        str: Path to the consolidated CSV file
    """
    consolidated_path = os.path.join(output_dir, consolidated_csv)
    
    # Check if consolidated file already exists
    if os.path.exists(consolidated_path):
        print(f"Consolidated GPS file already exists: {consolidated_path}")
        return consolidated_path
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Find all .git files
    git_files = glob.glob(os.path.join(git_directory, "*.git"))
    
    if not git_files:
        print(f"No .git files found in {git_directory}")
        return None
    
    print(f"Found {len(git_files)} .git files. Consolidating GPS data...")
    
    all_gps_data = []
    processed_files = 0
    
    # Process each .git file
    for git_file in sorted(git_files):
        try:
            print(f"Processing: {os.path.basename(git_file)}")
            gps_data = convert_git_to_data(git_file)
            
            # Add source file information to each GPS entry
            for entry in gps_data:
                entry['source_file'] = os.path.basename(git_file)
            
            all_gps_data.extend(gps_data)
            processed_files += 1
            
        except Exception as e:
            print(f"Error processing {git_file}: {e}")
            continue
    
    # Write consolidated GPS data to CSV
    if all_gps_data:
        with open(consolidated_path, mode='w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['source_file', 'date', 'time', 'lat', 'lon', 'speed', 'alt']
            csv_writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # Write header
            csv_writer.writeheader()
            
            # Write all GPS data
            csv_writer.writerows(all_gps_data)
        
        print(f"Consolidated {len(all_gps_data)} GPS entries from {processed_files} files")
        print(f"Consolidated GPS data saved to: {consolidated_path}")
        return consolidated_path
    else:
        print("No GPS data found to consolidate")
        return None

def load_consolidated_gps_data(consolidated_csv_path):
    """
    Load GPS data from consolidated CSV file
    
    Args:
        consolidated_csv_path (str): Path to consolidated GPS CSV file
    
    Returns:
        list: List of GPS data dictionaries
    """
    gps_data = []
    
    if not os.path.exists(consolidated_csv_path):
        print(f"Consolidated GPS file not found: {consolidated_csv_path}")
        return gps_data
    
    try:
        with open(consolidated_csv_path, mode='r', newline='', encoding='utf-8') as csvfile:
            csv_reader = csv.DictReader(csvfile)
            for row in csv_reader:
                # Convert string values back to appropriate types
                if row['lat']:
                    row['lat'] = float(row['lat'])
                if row['lon']:
                    row['lon'] = float(row['lon'])
                if row['speed']:
                    row['speed'] = float(row['speed'])
                if row['alt']:
                    row['alt'] = float(row['alt'])
                
                gps_data.append(row)
        
        print(f"Loaded {len(gps_data)} GPS entries from consolidated file")
        return gps_data
        
    except Exception as e:
        print(f"Error loading consolidated GPS data: {e}")
        return gps_data

def check_gpu_availability():
    """
    Check if GPU is available for acceleration
    
    Returns:
        bool: True if GPU is available, False otherwise
    """
    try:
        import torch
        return torch.cuda.is_available()
    except ImportError:
        return False

def get_gpu_info():
    """
    Get GPU information if available
    
    Returns:
        dict: GPU information or None if not available
    """
    try:
        import torch
        if torch.cuda.is_available():
            return {
                'name': torch.cuda.get_device_name(0),
                'memory_gb': torch.cuda.get_device_properties(0).total_memory / 1024**3,
                'available': True
            }
    except ImportError:
        pass
    
    return {'available': False}

def frame_to_base64(frame, quality=85):
    """
    Convert frame to base64 encoded string for storage in CSV
    
    Args:
        frame: OpenCV frame (numpy array)
        quality (int): JPEG compression quality (1-100, higher = better quality)
    
    Returns:
        str: Base64 encoded frame data
    """
    try:
        # Encode frame as JPEG to reduce size
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
        result, encoded_img = cv2.imencode('.jpg', frame, encode_param)
        
        if result:
            # Convert to base64 string
            frame_data = base64.b64encode(encoded_img).decode('utf-8')
            return frame_data
        else:
            print("Warning: Failed to encode frame")
            return ""
    except Exception as e:
        print(f"Error encoding frame: {e}")
        return ""

def base64_to_frame(base64_string):
    """
    Convert base64 string back to OpenCV frame
    
    Args:
        base64_string (str): Base64 encoded frame data
    
    Returns:
        numpy.ndarray: OpenCV frame or None if failed
    """
    try:
        # Decode base64 string
        img_data = base64.b64decode(base64_string)
        
        # Convert to numpy array
        nparr = np.frombuffer(img_data, np.uint8)
        
        # Decode image
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return frame
    except Exception as e:
        print(f"Error decoding frame: {e}")
        return None

def main(video_path, git_directory="git", output_video_path="Media/output_with_detections.mp4", output_dir="output_ocr"):
    """
    Main pipeline function that processes video for pothole detection and grading
    Now uses consolidated GPS data from all .git files with GPU acceleration
    
    Args:
        video_path (str): Path to input video file
        git_directory (str): Directory containing GPS .git files
        output_video_path (str): Path for output video with detections
        output_dir (str): Directory for output files
    """
    # Check GPU availability
    print("🔍 Checking GPU availability...")
    gpu_info = get_gpu_info()
    if gpu_info['available']:
        print(f"✅ GPU Available: {gpu_info['name']} ({gpu_info['memory_gb']:.1f}GB VRAM)")
    else:
        print("⚠️ GPU not available, using CPU")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Consolidate GPS files (only if not already done)
    consolidated_gps_path = consolidate_gps_files(git_directory, output_dir)
    if not consolidated_gps_path:
        print("Failed to consolidate GPS files. Exiting.")
        return
    
    # Load consolidated GPS data
    gps_data = load_consolidated_gps_data(consolidated_gps_path)
    
    # Initialize components with GPU acceleration
    gpu_available = check_gpu_availability()
    
    detector = PotholeDetector("Weights/best.pt", confidence_threshold=0.4)
    # Enable GPU for YOLO model if available
    if gpu_available and hasattr(detector.model, 'to'):
        try:
            detector.model.to('cuda')
            print("✅ YOLO model moved to GPU (CUDA)")
        except Exception as e:
            print(f"⚠️ Failed to move YOLO to GPU: {e}")
    else:
        print("⚠️ YOLO using CPU")
    
    # Initialize OCR processor with GPU acceleration
    ocr_processor = OCRProcessor(['en'], gpu=gpu_available)
    if gpu_available:
        print("✅ OCR processor using GPU (CUDA)")
    else:
        print("⚠️ OCR using CPU")
    
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
        csv_writer.writerow(['Frame', 'Date', 'Time', 'Latitude', 'Longitude', 'Pothole_Count', 'Pothole_Grade', 'GPS_Source', 'Frame_Data'])
        
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
                    # Find matching GPS data from consolidated data
                    gps_entry = find_matching_gps(gps_data, date, time)
                    if gps_entry:
                        # Join all grades for this frame
                        grades_str = ", ".join(pothole_grades)
                        
                        # Include GPS source file information
                        gps_source = gps_entry.get('source_file', 'Unknown')
                        
                        # Convert frame to base64 for storage
                        print(f"Encoding frame {frame_count} with {pothole_count} potholes...")
                        frame_data = frame_to_base64(img, quality=75)  # Lower quality to reduce size
                        
                        csv_writer.writerow([
                            frame_count, date, time,
                            gps_entry['lat'], gps_entry['lon'],
                            pothole_count, grades_str, gps_source, frame_data
                        ])
                        
                        print(f"Frame {frame_count}: {date} {time} | Potholes: {pothole_count} | Grades: {pothole_grades} | GPS Source: {gps_source} | Frame stored")
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
    print(f"Consolidated GPS: {consolidated_gps_path}")
    
    # Generate grading summary
    generate_grading_summary(csv_path, output_dir)

if __name__ == "__main__":
    video_path = "Media/Potholes8.mp4"
    git_directory = "git"  # Directory containing all .git files
    main(video_path, git_directory)
