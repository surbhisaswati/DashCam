import cv2
import os
import numpy as np

# Input folder containing videos
input_folder = 'video_rishi'

# Output folder for all images (flat)
output_folder = os.path.join(input_folder, 'frames_output')
os.makedirs(output_folder, exist_ok=True)

# Loop through all video files
for filename in os.listdir(input_folder):
    if filename.endswith(('.mp4', '.avi', '.mov', '.mkv')):
        video_path = os.path.join(input_folder, filename)
        cap = cv2.VideoCapture(video_path)

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames < 100:
            print(f"Video {filename} has less than 100 frames ({total_frames}), skipping.")
            cap.release()
            continue

        # Generate 100 equally spaced frame indices
        frame_indices = np.linspace(0, total_frames - 1, 100, dtype=int)

        video_name = os.path.splitext(filename)[0]
        saved_count = 0

        for frame_id in frame_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_id)
            success, frame = cap.read()
            if success:
                frame_filename = f"{video_name}_frame_{saved_count:05d}.jpg"
                frame_path = os.path.join(output_folder, frame_filename)
                cv2.imwrite(frame_path, frame)
                saved_count += 1

        cap.release()
        print(f"Extracted 100 frames from {filename}")
