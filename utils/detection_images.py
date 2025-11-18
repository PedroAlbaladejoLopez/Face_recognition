"""
utils/detection_images.py
-------------------------
Funciones para detección de rostros y objetos en imágenes.
"""

import os
import cv2
import numpy as np
import face_recognition
from config import IMAGENES_DETECTADAS, get_models, read_image_safe

def detect_faces_in_image(image, image_name="image"):
    kdtree, reference_names, _ = get_models()
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb)
    face_encodings = face_recognition.face_encodings(rgb, face_locations)
    faces = []

    for loc, enc in zip(face_locations, face_encodings):
        distances, indexes = kdtree.query([enc], k=1)
        name = reference_names[indexes[0][0]] if distances[0][0] < 0.6 else "Desconocido"
        faces.append({"name": name, "location": loc})
        top, right, bottom, left = loc
        cv2.rectangle(image, (left, top), (right, bottom), (0, 255, 0), 2)
        cv2.putText(image, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    return image, faces

def detect_objects_with_yolo(image, image_name="image"):
    _, _, yolo_model = get_models()
    objects = []
    if yolo_model is None:
        return image, objects

    results = yolo_model(image)
    for result in results:
        for box, cls in zip(result.boxes.xyxy, result.boxes.cls):
            x1, y1, x2, y2 = map(int, box)
            label = yolo_model.names[int(cls)]
            objects.append({"label": label, "bbox": [x1, y1, x2, y2]})
            cv2.rectangle(image, (x1, y1), (x2, y2), (255, 0, 0), 2)
            cv2.putText(image, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
    return image, objects

def _save_detected_image(image, original_filename):
    if not os.path.exists(IMAGENES_DETECTADAS):
        os.makedirs(IMAGENES_DETECTADAS)
    save_path = os.path.join(IMAGENES_DETECTADAS, original_filename)
    cv2.imwrite(save_path, image)
    return save_path
