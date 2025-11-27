#image_recognition_routes.py

import os
import logging
from typing import List, Dict
import uuid
from flask import Blueprint, request, jsonify, send_file
from models.cara import Cara
import cv2

# Importación de rutas y utilidades de configuración e IA
from config import IMAGENES_REFERENCIA, IMAGENES_ANALIZAR, IMAGENES_DETECTADAS, get_models, read_image_safe, add_reference_encoding
from utils.detection_images import detect_faces_in_image, detect_objects_with_yolo, _save_detected_image
from utils.detection_video import process_video_from_path
from models.individuo import Individuo, serialize_individuo

# Funciones MongoDB para CRUD de individuos y caras
from mongo.mongo_individuos import (modificar_individuo, get_individuo_by_id, buscar_individuo_por_cara
)
from mongo.mongo_caras import crear_cara, borrar_cara 


# Crear blueprint para agrupar las rutas del módulo
image_recognition_bp = Blueprint("image_recognition", __name__)
logger = logging.getLogger("detector.routes.image_recognition")

# Cargar modelos globales de reconocimiento: KDTree, nombres y YOLO
kdtree, reference_names, yolo_model = get_models()


# -------------------------
# Helper para parámetro live
# -------------------------
def _parse_live_param() -> bool:
    """
    Extrae el parámetro 'live' desde query params, form-data o JSON.
    Permite controlar si una detección debe ser en tiempo real.
    """
    val = request.args.get("live") or request.form.get("live")
    if val is None:
        try:
            j = request.get_json(silent=True) or {}
            val = j.get("live")
        except Exception:
            val = None

    # Si ya es booleano, se devuelve directamente
    if isinstance(val, bool):
        return val

    # Si no existe, por defecto es False
    if val is None:
        return False

    # Convertir string a booleano
    return str(val).lower() == "true"


# -------------------------
# Detectar imagen
# -------------------------
@image_recognition_bp.route("/detectar_imagen", methods=["POST"])
def detectar_imagen():
    file = request.files.get("file")
    if not file or not file.filename:
        return jsonify({"error": "No se envió ningún archivo"}), 400

    # Guardar temporalmente
    import uuid, os
    unique_name = f"{uuid.uuid4().hex}_{file.filename}"
    save_path = os.path.join(IMAGENES_DETECTADAS, unique_name)
    if not os.path.exists(IMAGENES_DETECTADAS):
        os.makedirs(IMAGENES_DETECTADAS)
    file.save(save_path)

    # Leer la imagen directamente
    from config import read_image_safe
    try:
        frame = read_image_safe(save_path)
        # Convertir de RGB a BGR, ya que detect_faces_in_image espera BGR
        frame_bgr = frame[:, :, ::-1].copy()
    except Exception as e:
        return jsonify({"error": f"No se pudo leer la imagen: {e}"}), 400

    # Detectar
    from utils.detection_images import detect_faces_in_image
    frame_annotated, faces = detect_faces_in_image(frame_bgr)

    # Guardar imagen anotada
    save_path_annotated = os.path.join(IMAGENES_DETECTADAS, f"annotated_{unique_name}")
    
    cv2.imwrite(save_path_annotated, frame_annotated)

    # Construir lista de individuos detectados
    from mongo.mongo_individuos import get_individuo_by_id
    individuos_detectados = []
    for f in faces:
        if f["id"]:
            ind = get_individuo_by_id(f["id"])
            if ind:
                individuos_detectados.append(ind.to_dict())

    return jsonify({
        "individuos_detectados": individuos_detectados,
        "frames_deteccion": [{"individuo": f.get("id"), "path": save_path_annotated.replace("\\", "/")} for f in faces]
    })



# -------------------------
# Detectar video
# -------------------------
@image_recognition_bp.route("/detectar_video", methods=["POST"])
def endpoint_detectar_video():
    # Parámetro live
    live = _parse_live_param()

    # Obtener archivo
    file = request.files.get("file")
    if not file or not file.filename:
        return jsonify({"error": "No se envió ningún archivo"}), 400

    # Guardar archivo temporalmente
    filename = os.path.basename(file.filename)
    file_path = os.path.join(IMAGENES_ANALIZAR, filename)
    file.save(file_path)

    try:
        # Procesar video frame a frame
        result = process_video_from_path(file_path, live=live)
    except Exception as e:
        logger.exception(f"Error procesando video: {e}")
        return jsonify({"error": f"Error procesando video: {e}"}), 500

    frames_out = []
    individuos_result: List[Dict] = []
    vistos = set()

    # Recorrer detecciones en video
    for entry in result.get("frames_deteccion", []):
        detected_name = entry.get("individuo")
        frame_path = entry.get("path")

        if not detected_name or not frame_path:
            continue

        # Buscar individuo por nombre detectado
        ind = buscar_individuo_por_cara(detected_name)

        if ind:
            # Si aún no se agregó a la lista
            if ind.id not in vistos:
                vistos.add(ind.id)
                individuos_result.append(ind.to_dict())

            frames_out.append({"individuo": ind.to_dict(), "frame_path": frame_path})
        else:
            # Caso desconocido
            if detected_name not in vistos:
                vistos.add(detected_name)
                individuos_result.append({"nombre_detectado": detected_name})

            frames_out.append({"individuo": {"nombre_detectado": detected_name}, "frame_path": frame_path})

    # Lista de objetos detectados en el video
    objetos = result.get("objetos", [])

    return jsonify({
        "individuos": individuos_result,
        "objetos": objetos,
        "frames_deteccion": frames_out
    })

