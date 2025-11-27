import cv2
from config import FRAME_SKIP, DOWNSCALE
from utils.detection_images import detect_faces_in_image, detect_objects_with_yolo, _save_detected_image
from mongo.mongo_individuos import buscar_individuo_por_cara, get_individuo_by_id

def process_video_from_path(video_path: str, live: bool = False):
    """
    Procesa un video y detecta caras y objetos.
    - live: si True muestra el video en tiempo real.
    Retorna dict con frames detectados, objetos e individuos detectados.
    """
    cap = cv2.VideoCapture(video_path)

    saved_frames = {}  # Guarda un frame por individuo detectado
    saved_objects = set()
    frame_count = 0
    results_all = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if DOWNSCALE != 1.0:
            frame = cv2.resize(frame, (0, 0), fx=DOWNSCALE, fy=DOWNSCALE)

        if frame_count % FRAME_SKIP == 0:
            # Detectar caras y objetos
            frame_annotated, faces = detect_faces_in_image(frame.copy())
            frame_annotated, objects = detect_objects_with_yolo(frame_annotated, f"frame_{frame_count}")

            # Registrar objetos detectados
            for obj in objects:
                saved_objects.add(obj["label"])

            # Guardar un único frame por individuo
            for f in faces:
                id = f["id"]
                if id != "Desconocido" and id not in saved_frames:
                    path = _save_detected_image(frame_annotated, f"{id}_frame_{frame_count}.jpg")
                    saved_frames[id] = path

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

    # Construir resultados finales
    individuos_result = []
    vistos = set()
    for id in saved_frames.keys():
        ind = get_individuo_by_id(id)
        if ind:
            if ind.id not in vistos:
                vistos.add(ind.id)
                individuos_result.append(ind.to_dict())

    return {
        "frames_deteccion": [{"individuo": k, "path": v} for k, v in saved_frames.items()],
        "objetos": sorted(list(saved_objects)),
        "individuos_detectados": individuos_result
    }
