import os
import logging
from typing import List, Dict
from flask import Blueprint, request, jsonify
from models.cara import Cara
import uuid

# Importación de rutas y utilidades de configuración e IA
from config import IMAGENES_REFERENCIA, IMAGENES_ANALIZAR, IMAGENES_DETECTADAS, get_models, read_image_safe
from utils.detection_images import detect_faces_in_image, detect_objects_with_yolo, _save_detected_image
from utils.detection_video import process_video_from_path
from models.individuo import Individuo, serialize_individuo

# Funciones MongoDB para CRUD de individuos y caras
from mongo.mongo_individuos import (
    crear_individuo, modificar_individuo, borrar_individuo, get_individuo_by_id,
    agregar_caras_a_individuo, eliminar_cara_de_individuo, consultar_caras_individuo, buscar_individuo_por_cara
)

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
# Crear individuo
# -------------------------
@image_recognition_bp.route("/crear_individuo", methods=["POST"])
def endpoint_crear_individuo():
    # Obtener JSON enviado
    data = request.get_json(silent=True)
    if not data or "nombre" not in data:
        return jsonify({"error": "Nombre obligatorio"}), 400

    # Extraer campos del individuo
    nombre = data["nombre"]
    apellido1 = data.get("apellido1", "")
    apellido2 = data.get("apellido2", "")
    caras = data.get("caras", [])

    # Crear objeto Individuo sin caras inicialmente
    individuo = Individuo(nombre=nombre, apellido1=apellido1, apellido2=apellido2)
    
    # Guardar en MongoDB
    individuo_guardado = crear_individuo(individuo)

    # Revisar si se guardó correctamente
    if individuo_guardado is None:
        return jsonify({"error": "No se pudo crear el individuo"}), 500

    # Agregar caras si fueron enviadas y si el individuo tiene id
    if caras and individuo_guardado.id:
        individuo_guardado = agregar_caras_a_individuo(individuo_guardado.id, caras)
        if individuo_guardado is None:
            return jsonify({"error": "No se pudieron agregar las caras"}), 500

    # Responder con el individuo serializado
    return jsonify({"individuo": serialize_individuo(individuo_guardado.to_dict())})


# -------------------------
# Modificar individuo
# -------------------------
@image_recognition_bp.route("/modificar_individuo", methods=["PUT"])
def endpoint_modificar_individuo():
    # Obtener JSON enviado
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "No se proporcionaron datos"}), 400

    # Convertir diccionario a objeto Individuo
    try:
        individuo = Individuo.from_dict(data)
    except Exception as e:
        return jsonify({"error": f"Datos de individuo inválidos: {e}"}), 400

    # Validar que tenga id
    if not individuo.id:
        return jsonify({"error": "El objeto Individuo debe tener un id"}), 400

    # Intentar actualizar en MongoDB
    individuo_modificado = modificar_individuo(individuo)
    if not individuo_modificado:
        return jsonify({"error": "No se pudo modificar el individuo (posiblemente no existe)"}), 400

    # Devolver el individuo modificado
    return jsonify({"individuo": individuo_modificado.to_dict()})


# -------------------------
# Borrar individuo
# -------------------------
@image_recognition_bp.route("/borrar_individuo/<id>", methods=["DELETE"])
def endpoint_borrar_individuo(id):
    # Llamar a Mongo para eliminarlo
    success = borrar_individuo(id)
    if not success:
        return jsonify({"error": "No se pudo borrar el individuo"}), 400
    return jsonify({"message": "Individuo borrado correctamente"})


# -------------------------
# Consultar caras de un individuo
# -------------------------
@image_recognition_bp.route("/consultar_caras_individuo/<id>", methods=["GET"])
def endpoint_consultar_caras_individuo(id):
    # Obtener lista de caras desde Mongo
    caras = consultar_caras_individuo(id)

    # Convertir objetos Cara a diccionarios
    caras_serializadas = [c.to_dict() for c in caras]

    return jsonify({"caras": caras_serializadas})


# -------------------------
# Agregar cara a individuo desde archivo
# -------------------------
@image_recognition_bp.route("/agregar_cara_individuo/<id>", methods=["POST"])
def endpoint_agregar_cara_individuo(id: str):
    
    # Obtener archivo enviado
    file = request.files.get("file")
    if not file or not file.filename:
        return jsonify({"error": "No se envió ningún archivo"}), 400

    # Crear nombre único para guardar la imagen
    nombre_base = id
    unique_id = uuid.uuid4().hex[:8]
    filename = f"{nombre_base}___{unique_id}.jpg"
    save_path = os.path.join(IMAGENES_REFERENCIA, filename)

    # Crear carpeta si no existe y guardar archivo
    if not os.path.exists(IMAGENES_REFERENCIA):
        os.makedirs(IMAGENES_REFERENCIA)
    file.save(save_path)

    try:
        # Leer imagen y convertir de RGB a BGR para OpenCV
        img_rgb = read_image_safe(save_path)
        image_bgr = img_rgb[:, :, ::-1].copy()
    except Exception as e:
        # Si falla la lectura, borrar archivo temporal
        if os.path.exists(save_path):
            os.remove(save_path)
        return jsonify({"error": f"Error leyendo imagen: {e}"}), 400

    # Detectar caras en la imagen
    image_annotated, faces = detect_faces_in_image(image_bgr)
    if not faces:
        # Si no hay caras, eliminar archivo
        os.remove(save_path)
        return jsonify({"error": "No se detectó ninguna cara en la imagen"}), 400

    # Crear entrada de Cara en MongoDB
    from mongo.mongo_caras import crear_cara  
    nueva_cara = Cara(id=None, path=save_path)
    cara_guardada = crear_cara(nueva_cara)

    if not cara_guardada:
        os.remove(save_path)
        return jsonify({"error": "No se pudo guardar la cara en la base de datos"}), 500

    # Obtener el individuo asociado
    individuo = get_individuo_by_id(id)
    if not individuo:
        os.remove(save_path)
        return jsonify({"error": "No se encontró el individuo"}), 404

    # Agregar la cara al individuo en memoria
    individuo.agregar_cara(cara_guardada)

    # Guardar cambios en MongoDB
    individuo_modificado = modificar_individuo(individuo)
    if not individuo_modificado:
        return jsonify({"error": "No se pudo actualizar el individuo"}), 500

    return jsonify({
        "message": "Cara agregada correctamente",
        "individuo": individuo_modificado.to_dict(),
        "cara_id": cara_guardada.id
    })


# -------------------------
# Eliminar cara de un individuo
# -------------------------
@image_recognition_bp.route("/eliminar_cara/<cara_id>/<individuo_id>", methods=["DELETE"])
def endpoint_eliminar_cara(cara_id, individuo_id):
    # Quitar referencia a la cara en MongoDB
    individuo_actualizado = eliminar_cara_de_individuo(individuo_id, cara_id)

    if not individuo_actualizado:
        return jsonify({"error": "No se pudo eliminar la cara del individuo"}), 400

    return jsonify({"individuo": individuo_actualizado.to_dict()})


# -------------------------
# Detectar imagen
# -------------------------
@image_recognition_bp.route("/detectar_imagen", methods=["POST"])
def endpoint_detectar_imagen():
    # Leer parámetro 'live'
    live = _parse_live_param()

    # Obtener archivo
    file = request.files.get("file")
    if not file or not file.filename:
        return jsonify({"error": "No se envió ningún archivo"}), 400

    # Guardar imagen para procesar
    filename = os.path.basename(file.filename)
    file_path = os.path.join(IMAGENES_ANALIZAR, filename)
    file.save(file_path)

    try:
        # Leer imagen y convertir formato
        img_rgb = read_image_safe(file_path)
        image_bgr = img_rgb[:, :, ::-1].copy()
    except Exception as e:
        # Borrar si falla
        if os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({"error": f"Error leyendo imagen: {e}"}), 400

    # Detectar caras y objetos
    image_annotated, faces = detect_faces_in_image(image_bgr.copy())
    image_annotated, objects = detect_objects_with_yolo(image_annotated, image_name=filename)

    # Guardar imagen detectada
    detected_path = _save_detected_image(image_annotated, filename)

    individuos_result: List[Dict] = []
    vistos = set()

    # Procesar todas las caras detectadas
    for f in faces:
        id_individuo = f.get("id")
        print("ID_INDIV: ", id_individuo)

        # Ignorar desconocidos
        if not id_individuo or id_individuo == "Desconocido":
            continue

        # Buscar individuo correspondiente en DB
        ind = get_individuo_by_id(id_individuo)

        if ind and ind.id not in vistos:
            vistos.add(ind.id)
            individuos_result.append(ind.to_dict())
        #elif ref_name not in vistos:
        #    vistos.add(ref_name)
         #   individuos_result.append({"nombre_detectado": ref_name})

    # Quitar duplicados de objetos
    unique_objects = sorted({o["label"] for o in objects}) if objects else []

    return jsonify({
        "individuos": individuos_result,
        "objetos": unique_objects,
        "imagen_detectada": detected_path
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
