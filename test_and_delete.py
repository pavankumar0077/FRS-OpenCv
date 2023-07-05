import cv2
import psutil
import GPUtil
import tempfile
import os
import time
from simple_facerec import SimpleFacerec
from deepface import DeepFace

############## ADDED FACE EXPRESSION #############

# RTSP
rtsp_url = 'rtsp://192.168.138.116:8080/h264_ulaw.sdp'
rtmp_url = 'rtmp://192.168.138.121:1935/live/demo'

# Encode faces from a folder
sfr = SimpleFacerec()
sfr.load_encoding_images("images_test/")

# Load camera
# cap = cv2.VideoCapture(rtmp_url)
cap = cv2.VideoCapture(0)

# Emotion labels supported by DeepFace
emotion_labels = {
    'angry': 'Angry',
    'disgust': 'Disgust',
    'fear': 'Fear',
    'happy': 'Happy',
    'sad': 'Sad',
    'surprise': 'Surprise',
    'neutral': 'Neutral'
}

# Create a file to store CPU and GPU usage details
cpu_gpu_file = os.path.join(os.getcwd(), "memory.txt")

# Initialize variables for calculating average times
cpu_total_time = 0
gpu_total_time = 0
detection_total_time = 0
analysis_total_time = 0
iteration_count = 0

while True:
    ret, frame = cap.read()

    # Start timer
    start_time = time.time()

    # Detect Faces
    face_locations, face_names = sfr.detect_known_faces(frame)

    # Calculate time taken for face detection
    detection_time = time.time() - start_time

    for face_loc, name in zip(face_locations, face_names):
        y1, x2, y2, x1 = face_loc[0], face_loc[1], face_loc[2], face_loc[3]

        cv2.putText(frame, name, (x1, y1 - 10), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 200), 2)
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 200), 4)

        # Crop face region for emotional detection
        face_image = frame[y1:y2, x1:x2]

        try:
            # Start timer for emotion analysis
            analysis_start_time = time.time()

            # Perform emotional analysis
            emotions = DeepFace.analyze(face_image, actions=['emotion'], enforce_detection=False)

            # Calculate time taken for emotion analysis
            analysis_time = time.time() - analysis_start_time

            # Get the dominant emotion label
            emotion_scores = emotions[0]['emotion']
            dominant_emotions = [label for label, score in emotion_scores.items() if score == max(emotion_scores.values())]

            # Display the predicted emotions
            emotion_text = ', '.join([emotion_labels[emotion] for emotion in dominant_emotions])
            cv2.putText(frame, emotion_text, (x1, y2 + 25), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 200), 2)

        except ValueError:
            # Face detection failed
            print("Face could not be detected")

    # Display CPU usage and FPS on screen
    cpu_usage = psutil.cpu_percent()
    gpu_usage = 0

    gpus = GPUtil.getGPUs()
    if gpus:
        gpu_usage = gpus[0].load * 100

    cv2.putText(frame, f"CPU Usage: {cpu_usage}%", (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_COMPLEX, 0.7, (0, 0, 200), 2)
    cv2.putText(frame, f"GPU Usage: {gpu_usage}%", (10, frame.shape[0] - 40), cv2.FONT_HERSHEY_COMPLEX, 0.7, (0, 0, 200), 2)
    cv2.putText(frame, f"Face Detection Time: {detection_time:.2f} seconds", (10, frame.shape[0] - 70), cv2.FONT_HERSHEY_COMPLEX, 0.7, (0, 0, 200), 2)
    cv2.putText(frame, f"Emotion Analysis Time: {analysis_time:.2f} seconds", (10, frame.shape[0] - 100), cv2.FONT_HERSHEY_COMPLEX, 0.7, (0, 0, 200), 2)

    # Write CPU and GPU usage details to the file
    with open(cpu_gpu_file, 'a') as file:
        file.write(f"CPU Usage: {cpu_usage}%\n")
        file.write(f"GPU Usage: {gpu_usage}%\n")
        file.write(f"Face Detection Time: {detection_time:.2f} seconds\n")
        file.write(f"Emotion Analysis Time: {analysis_time:.2f} seconds\n\n")

    # Calculate total times for averaging
    cpu_total_time += cpu_usage
    gpu_total_time += gpu_usage
    detection_total_time += detection_time
    analysis_total_time += analysis_time
    iteration_count += 1

    cv2.imshow("Frame", frame)

    key = cv2.waitKey(1)
    if key == 27:
        break

# Calculate average times
avg_cpu_time = cpu_total_time / iteration_count
avg_gpu_time = gpu_total_time / iteration_count
avg_detection_time = detection_total_time / iteration_count
avg_analysis_time = analysis_total_time / iteration_count

# Get CPU details using psutil
cpu_percent = psutil.cpu_percent(interval=2)
cpu_count = psutil.cpu_count()
percpu_percent = psutil.cpu_percent(interval=2, percpu=True)

# Erase the old content in the file
with open(cpu_gpu_file, 'w') as file:
    file.write("")

# Write average times and CPU details to the file
with open(cpu_gpu_file, 'a') as file:
    file.write(f"Average CPU Usage: {avg_cpu_time:.2f}%\n")
    file.write(f"Average GPU Usage: {avg_gpu_time:.2f}%\n")
    file.write(f"Average Face Detection Time: {avg_detection_time:.2f} seconds\n")
    file.write(f"Average Emotion Analysis Time: {avg_analysis_time:.2f} seconds\n")
    file.write(f"CPU Percent: {cpu_percent}%\n")
    file.write(f"CPU Count: {cpu_count}\n")
    file.write(f"Per CPU Percent: {percpu_percent}\n")

cap.release()
cv2.destroyAllWindows()
