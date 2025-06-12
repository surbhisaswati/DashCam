import cv2
import os

# Set input folder
input_folder = '/home/smlab/Desktop/dashcam/front'

# Create output folder inside input folder
output_folder = os.path.join(input_folder, 'cropped_videos')
os.makedirs(output_folder, exist_ok=True)

# Loop through all video files in the folder
for filename in os.listdir(input_folder):
    if filename.endswith(('.mp4', '.avi', '.mov', '.mkv')):  # Add more formats if needed
        input_path = os.path.join(input_folder, filename)
        output_path = os.path.join(output_folder, filename)

        cap = cv2.VideoCapture(input_path)

        # Get original video properties
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')

        # Calculate cropping dimensions
        crop_x_end = int(width * 0.9)          # Keep 90% width (cut 10% from right)
        crop_y_start = int(height * 0.7)       # Start from 70% down (cut top 70%)
        cropped_width = crop_x_end
        cropped_height = height - crop_y_start

        # Set up video writer
        out = cv2.VideoWriter(output_path, fourcc, fps, (cropped_width, cropped_height))

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Crop the frame
            cropped = frame[crop_y_start:height, 0:crop_x_end]

            # Write the cropped frame
            out.write(cropped)

        cap.release()
        out.release()
        print(f'Cropped and saved to cropped_videos: {filename}')
