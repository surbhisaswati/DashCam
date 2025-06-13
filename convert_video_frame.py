import cv2
import os

# Input folder containing videos
input_folder = '/home/smlab/Desktop/dashcam/front'

# Output folder for all images (flat)
output_folder = os.path.join(input_folder, 'frames_output')
os.makedirs(output_folder, exist_ok=True)

# Loop through all video files
for filename in os.listdir(input_folder):
    if filename.endswith(('.mp4', '.avi', '.mov', '.mkv')):  # Add more formats if needed
        video_path = os.path.join(input_folder, filename)
        cap = cv2.VideoCapture(video_path)

        video_name = os.path.splitext(filename)[0]
        frame_count = 0

        while True:
            success, frame = cap.read()
            if not success:
                break

            # Save with unique name: videoName_frame_00001.jpg
            frame_filename = f"{video_name}_frame_{frame_count:05d}.jpg"
            frame_path = os.path.join(output_folder, frame_filename)
            cv2.imwrite(frame_path, frame)
            frame_count += 1

        cap.release()
        print(f"Extracted {frame_count} frames from {filename}")
