"""
routes/image_recognition.py
---------------------------
Endpoints Flask para gestión de referencias y detección.
"""

import os
import uuid
from flask import Blueprint, request, jsonify
import numpy as np
import cv2
import face_recognition

from config import IMAGENES_REFERENCIA, IMAGENES_ANALIZAR, get_models
from utils.detection_images import detect_faces_in_image, detect_objects_with_yolo, _save_detected_image, read_image_safe
from utils.detection_video import process_video_from_path
from models.individuo import Individuo
from mongo.mongo_individuos import crear_individuo

image_recognition_bp = Blueprint("image_recognition", __name__)

kdtree, reference_names, yolo_model = get_models()

def _parse_live_param():
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
# Guardar nueva referencia
# -------------------------
@image_recognition_bp.route("/save_reference_new", methods=["POST"])
def save_reference_new():
    file = request.files.get("file")
    nombre = request.form.get("nombre")
    apellido1 = request.form.get("apellido1", "")
    apellido2 = request.form.get("apellido2", "")

    if not file or not file.filename:
        return jsonify({"error": "No se envió ningún archivo"}), 400
    if not nombre:
        return jsonify({"error": "Debe proporcionar el nombre del individuo"}), 400

    filename = os.path.basename(file.filename)
    save_path = os.path.join(IMAGENES_REFERENCIA, filename)
    file.save(save_path)

    try:
        rgb = read_image_safe(save_path)
        faces = face_recognition.face_locations(rgb)
        if len(faces) != 1:
            os.remove(save_path)
            return jsonify({"error": f"La imagen debe contener exactamente UNA cara (se encontraron {len(faces)})."}), 400
    except Exception as e:
        os.remove(save_path)
        return jsonify({"error": str(e)}), 400

    individuo = Individuo(nombre, apellido1, apellido2)
    individuo.agregar_cara(save_path)
    mongo_id = crear_individuo(individuo.to_dict())
    individuo_dict = individuo.to_dict()
    individuo_dict["_id"] = mongo_id

    return jsonify({"message": "Cara guardada correctamente.", "individuo": individuo_dict})

# -------------------------
# Agregar cara a existente
# -------------------------
@image_recognition_bp.route("/save_reference_existing", methods=["POST"])
def save_reference_existing():
    nombre_base = request.form.get("nombre")
    file = request.files.get("file")

    if not nombre_base or not file or not file.filename:
        return jsonify({"error": "Debe proporcionar nombre y archivo"}), 400

    unique_id = uuid.uuid4().hex[:8]
    filename = f"{nombre_base}___{unique_id}.jpg"
    save_path = os.path.join(IMAGENES_REFERENCIA, filename)
    file.save(save_path)

    try:
        rgb = read_image_safe(save_path)
        faces = face_recognition.face_locations(rgb)
        if len(faces) != 1:
            os.remove(save_path)
            return jsonify({"error": f"La imagen debe contener exactamente UNA cara (se encontraron {len(faces)})."}), 400
    except Exception as e:
        os.remove(save_path)
        return jsonify({"error": str(e)}), 400

    individuo = Individuo(nombre_base)
    individuo.agregar_cara(save_path)
    return jsonify({"message": f"Cara agregada correctamente a '{nombre_base}'", "individuo": individuo.to_dict()})

# -------------------------
# Listar referencias
# -------------------------
@image_recognition_bp.route("/list_references", methods=["GET"])
def list_references():
    files = []
    for fname in os.listdir(IMAGENES_REFERENCIA):
        if fname.lower().endswith((".jpg", ".jpeg", ".png")):
            files.append({"nombre": os.path.splitext(fname)[0], "path": os.path.join(IMAGENES_REFERENCIA, fname)})
    return jsonify({"referencias": files})

# -------------------------
# Detectar imagen
# -------------------------
@image_recognition_bp.route("/detect_image", methods=["POST"])
def detect_image():
    live = _parse_live_param()
    file = request.files.get("file")
    if not file or not file.filename:
        return jsonify({"error": "No se envió ningún archivo"}), 400

    filename = file.filename
    file_path = os.path.join(IMAGENES_ANALIZAR, filename)
    file.save(file_path)

    try:
        image = read_image_safe(file_path)[:, :, ::-1]  # convert RGB->BGR para OpenCV
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    image_annotated, faces = detect_faces_in_image(image.copy(), filename)
    image_annotated, objects = detect_objects_with_yolo(image_annotated, filename)
    detected_path = _save_detected_image(image_annotated, filename)
    unique_faces = sorted({f["name"] for f in faces if f["name"] != "Desconocido"})
    unique_objects = sorted({o["label"] for o in objects})

    return jsonify({"faces": unique_faces, "objects": unique_objects, "detected_image": detected_path})

# -------------------------
# Detectar video
# -------------------------
@image_recognition_bp.route("/detect_video", methods=["POST"])
def detect_video():
    live = _parse_live_param()
    file = request.files.get("file")
    if not file or not file.filename:
        return jsonify({"error": "No se envió ningún archivo"}), 400

    filename = file.filename
    file_path = os.path.join(IMAGENES_ANALIZAR, filename)
    file.save(file_path)

    try:
        results = process_video_from_path(file_path, live=live)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({"processed_video": results})
