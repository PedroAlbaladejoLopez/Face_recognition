import os
import cv2
from typing import List, Dict
import numpy as np
import face_recognition

from config import IMAGENES_DETECTADAS, get_models, read_image_safe
from models.individuo import Individuo
from mongo.mongo_individuos import get_individuo_by_id, buscar_individuo_por_cara  # funciones planas

def detect_faces_in_image(image: np.ndarray):
    """
    Detecta caras en la imagen y retorna la imagen anotada y lista de dicts con info de cada cara.
    Cada dict contiene:
        - name: nombre del individuo detectado (o "Desconocido")
        - location: tuple (top, right, bottom, left)
    """
    kdtree, reference_names, _ = get_models()
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    face_locations = face_recognition.face_locations(rgb)
    print("FACE_LOC: ", face_locations)
    face_encodings = face_recognition.face_encodings(rgb, face_locations)
    print("FACE_ENC: ", face_encodings)

    faces: List[Dict] = []

    for loc, enc in zip(face_locations, face_encodings):
        distances, indexes = kdtree.query([enc], k=1)
        if distances[0][0] < 0.6:
            nombre_imagen = reference_names[indexes[0][0]]
            individuo_id = nombre_imagen.split("___")[0]
        else:
            nombre_imagen = "Desconocido"
            individuo_id = None

        if individuo_id:
            print("IND_ID: ", individuo_id)
            individuo = get_individuo_by_id(individuo_id)
            if individuo:
                name = f"{individuo.nombre}_{individuo.apellido1}"
            else:
                name = "Desconocido"
        else:
            name = "Desconocido"

        faces.append({"id": individuo_id, "location": loc})

        top, right, bottom, left = loc
        cv2.rectangle(image, (left, top), (right, bottom), (0, 255, 0), 2)
        cv2.putText(
            image,
            name,
            (left, top - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0),
            2,
        )

    return image, faces


def detect_objects_with_yolo(image: np.ndarray, image_name: str = "image"):
    """
    Detecta objetos usando YOLO (si está cargado).
    Devuelve la imagen anotada y lista de objetos con bbox.
    """
    _, _, yolo_model = get_models()
    objects: List[Dict] = []
    if yolo_model is None:
        return image, objects

    results = yolo_model(image)

    for result in results:
        for box, cls in zip(result.boxes.xyxy, result.boxes.cls):
            x1, y1, x2, y2 = map(int, box)
            label = yolo_model.names[int(cls)]

            objects.append({"label": label, "bbox": [x1, y1, x2, y2]})

            cv2.rectangle(image, (x1, y1), (x2, y2), (255, 0, 0), 2)
            cv2.putText(
                image,
                label,
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 0, 0),
                2,
            )

    return image, objects


def _save_detected_image(image: np.ndarray, original_filename: str) -> str:
    if not os.path.exists(IMAGENES_DETECTADAS):
        os.makedirs(IMAGENES_DETECTADAS)

    save_path = os.path.join(IMAGENES_DETECTADAS, original_filename)
    cv2.imwrite(save_path, image)
    return save_path
