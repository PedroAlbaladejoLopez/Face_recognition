"""
utils/detection_video.py
------------------------
Procesamiento de video frame a frame para detección de rostros y objetos.
"""

import cv2
from config import FRAME_SKIP, DOWNSCALE
from utils.detection_images import detect_faces_in_image, detect_objects_with_yolo, _save_detected_image

def process_video_from_path(video_path: str, live: bool = False):
    cap = cv2.VideoCapture(video_path)
    results_all = []
    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if DOWNSCALE != 1.0:
            frame = cv2.resize(frame, (0, 0), fx=DOWNSCALE, fy=DOWNSCALE)

        if frame_count % FRAME_SKIP == 0:
            frame_annotated, faces = detect_faces_in_image(frame.copy(), f"frame_{frame_count}")
            frame_annotated, objects = detect_objects_with_yolo(frame_annotated, f"frame_{frame_count}")

            results_all.append({
                "frame": frame_count,
                "faces": faces,
                "objects": objects
            })

            if live:
                cv2.imshow("Video Detection", frame_annotated)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

        frame_count += 1

    cap.release()
    cv2.destroyAllWindows()
    return results_all
