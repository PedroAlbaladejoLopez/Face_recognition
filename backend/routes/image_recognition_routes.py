import os
import logging
import uuid
from flask import Blueprint, request, jsonify
import cv2

from config import IMAGENES_ANALIZAR, IMAGENES_DETECTADAS, get_models, read_image_safe
from utils.detection_images import detect_faces_in_image
from utils.detection_video import process_video_from_path
from mongo.mongo_individuos import get_individuo_by_id

# Crear blueprint
image_recognition_bp = Blueprint("image_recognition", __name__)
logger = logging.getLogger("detector.routes.image_recognition")

# Cargar modelos globales (KDTree, nombres, YOLO)
kdtree, reference_names, yolo_model = get_models()


# -------------------------
# Helper para parámetro live
# -------------------------
def _parse_live_param() -> bool:
    val = request.args.get("live") or request.form.get("live")
    if val is None:
        try:
            j = request.get_json(silent=True) or {}
            val = j.get("live")
        except Exception:
            val = None
    if isinstance(val, bool):
        return val
    if val is None:
        return False
    return str(val).lower() == "true"


# -------------------------
# Detectar imagen
# -------------------------
@image_recognition_bp.route("/detectar_imagen", methods=["POST"])
def detectar_imagen():
    file = request.files.get("file")
    if not file or not file.filename:
        return jsonify({"error": "No se envió ningún archivo"}), 400

    unique_name = f"{uuid.uuid4().hex}_{file.filename}"
    save_path = os.path.join(IMAGENES_DETECTADAS, unique_name)
    os.makedirs(IMAGENES_DETECTADAS, exist_ok=True)
    file.save(save_path)

    # Leer imagen
    try:
        frame = read_image_safe(save_path)
        frame_bgr = frame[:, :, ::-1].copy()
    except Exception as e:
        return jsonify({"error": f"No se pudo leer la imagen: {e}"}), 400

    # Detectar caras
    frame_annotated, faces = detect_faces_in_image(frame_bgr)

    # Guardar imagen anotada
    save_path_annotated = os.path.join(IMAGENES_DETECTADAS, f"annotated_{unique_name}")
    cv2.imwrite(save_path_annotated, frame_annotated)

    # Construir lista de individuos detectados
    individuos_detectados = []
    for f in faces:
        ind_id = f.get("id")
        if ind_id:
            ind_obj = get_individuo_by_id(ind_id)
            if ind_obj:
                individuos_detectados.append(ind_obj.to_dict())

    return jsonify({
        "imagen_deteccion": save_path_annotated.replace("\\", "/"),
        "individuos_detectados": individuos_detectados
    })


# -------------------------
# Detectar video
# -------------------------
@image_recognition_bp.route("/detectar_video", methods=["POST"])
def endpoint_detectar_video():
    file = request.files.get("file")
    if not file or not file.filename:
        return jsonify({"error": "No se envió ningún archivo"}), 400

    filename = os.path.basename(file.filename)
    file_path = os.path.join(IMAGENES_ANALIZAR, filename)
    os.makedirs(IMAGENES_ANALIZAR, exist_ok=True)
    file.save(file_path)

    try:
        result = process_video_from_path(file_path)
    except Exception as e:
        logger.exception(e)
        return jsonify({"error": str(e)}), 500

    frames_out = []
    individuos_result = []
    vistos = set()

    # Guardar frames de detección
    for f in result.get("frames_deteccion", []):
        ind_id = f["individuo"]
        frame_path = f["frame_path"]

        ind_obj = get_individuo_by_id(ind_id)
        if not ind_obj:
            continue

        ind_dict = ind_obj.to_dict()
        key = ind_dict["_id"]

        if key not in vistos:
            vistos.add(key)
            individuos_result.append(ind_dict)

        # Cada frame va con el objeto de individuo
        frames_out.append({
            "frame_path": frame_path.replace("\\", "/"),
            "individuo": ind_dict
        })

    return jsonify({
        "frames_deteccion": frames_out,
        "individuos_detectados": individuos_result,
        "objetos": result.get("objetos", [])
    })
