import cv2
from config import FRAME_SKIP
from utils.detection_images import detect_faces_in_image, detect_objects_with_yolo, _save_detected_image

def process_video_from_path(video_path: str, live: bool = False):
    cap = cv2.VideoCapture(video_path)
    saved_frames = {}  # Guarda un frame por individuo detectado
    saved_objects = set()
    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count % FRAME_SKIP == 0:
            frame_annotated, faces = detect_faces_in_image(frame.copy())
            frame_annotated, objects = detect_objects_with_yolo(frame_annotated, f"frame_{frame_count}")

            # Registrar objetos detectados
            for obj in objects:
                saved_objects.add(obj["label"])

            # Guardar un único frame por individuo conocido
            for f in faces:
                ind_id = f.get("id")
                if ind_id and ind_id != "Desconocido" and ind_id not in saved_frames:
                    path = _save_detected_image(frame_annotated, f"{ind_id}_frame_{frame_count}.jpg")
                    saved_frames[ind_id] = path

            if live:
                cv2.imshow("Video Detection", frame_annotated)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

        frame_count += 1

    cap.release()
    cv2.destroyAllWindows()

    return {
        "frames_deteccion": [{"individuo": k, "frame_path": v.replace("\\", "/")} for k, v in saved_frames.items()],
        "objetos": sorted(list(saved_objects))
    }
