# config.py
# --------------------------
# Configuración global, carga de modelos y encodings de referencia
# --------------------------

import os
import cv2
import numpy as np
import logging
import face_recognition
from sklearn.neighbors import KDTree
from ultralytics import YOLO
from pymongo import MongoClient
from typing import Union
from PIL import Image


# --------------------------
# Rutas de carpetas
# --------------------------
IMAGENES_REFERENCIA = "imagenes/referencia"
IMAGENES_DETECTADAS = "imagenes/detectadas"
IMAGENES_ANALIZAR = "imagenes/analizar"

# --------------------------
# Parámetros de video
# --------------------------
FRAME_SKIP = 5
DOWNSCALE = 0.6

# --------------------------
# Variables globales
# --------------------------
kdtree = None
reference_names = []
yolo_model = None
mongo_client = None
mongo_db = None

logger = logging.getLogger(__name__)

# --------------------------
# Función para leer imagen de forma segura y convertir a RGB 8bit
# --------------------------


def read_image_safe(path: str) -> np.ndarray:
    print("PATH", path)
    img = Image.open(path)
    print(img)
    img = img.convert("RGB")  # NORMALIZA A RGB REAL
    return np.array(img, dtype=np.uint8)


# --------------------------
# Cargar encodings de referencias
# --------------------------
def load_reference_encodings():
    global kdtree, reference_names

    encodings = []
    names = []

    logger.info(f"Cargando imágenes de referencia desde: {IMAGENES_REFERENCIA}")

    if not os.path.exists(IMAGENES_REFERENCIA):
        os.makedirs(IMAGENES_REFERENCIA)

    for filename in os.listdir(IMAGENES_REFERENCIA):
        if not filename.lower().endswith((".jpg", ".jpeg", ".png")):
            continue

        filepath = os.path.join(IMAGENES_REFERENCIA, filename)
        try:
            img_rgb = read_image_safe(filepath)
            face_encs = face_recognition.face_encodings(img_rgb)
            if len(face_encs) != 1:
                logger.warning(f"[WARN] {filename}: debe contener exactamente UNA cara")
                continue
            encodings.append(face_encs[0])
            names.append(os.path.splitext(filename)[0])
        except Exception as e:
            logger.warning(f"[WARN] Error al generar encodings de {filename}: {e}")
            continue

    if encodings:
        kdtree = KDTree(np.array(encodings))
        reference_names = names
        logger.info(f"[OK] KDTree cargado con {len(reference_names)} referencias")
    else:
        kdtree = None
        reference_names = []
        logger.warning("[WARN] No se encontraron encodings válidos.")

# --------------------------
# Cargar modelo YOLO
# --------------------------
def load_yolo_model(model_path: str = "yolov8n.pt"):
    global yolo_model
    try:
        yolo_model = YOLO(model_path)
        logger.info("[OK] Modelo YOLO cargado correctamente.")
    except Exception as e:
        yolo_model = None
        logger.error(f"[ERROR] No se pudo cargar YOLO: {e}")

# --------------------------
# Conexión a MongoDB
# --------------------------
def test_mongo_connection(uri="mongodb://localhost:27017/", db_name="reconocimiento_facial"):
    global mongo_client, mongo_db
    try:
        mongo_client = MongoClient(uri)
        mongo_db = mongo_client[db_name]
        # Probar conexión
        mongo_client.admin.command("ping")
        logger.info(f"[OK] Conexión exitosa a MongoDB: {uri}, DB: {db_name}")
    except Exception as e:
        mongo_client = None
        mongo_db = None
        logger.error(f"[ERROR] No se pudo conectar a MongoDB: {e}")

# --------------------------
# Obtener modelos globales
# --------------------------
def get_models():
    if kdtree is None:
        raise RuntimeError("KDTree no cargado todavía (sin encodings).")
    return kdtree, reference_names, yolo_model

# --------------------------
# Inicialización automática
# --------------------------
load_reference_encodings()
load_yolo_model()
test_mongo_connection()
