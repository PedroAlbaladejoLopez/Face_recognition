#individuos_routes.py

import os
import logging
from typing import List, Dict
import uuid
from flask import Blueprint, request, jsonify, send_file
from models.cara import Cara

# Importación de rutas y utilidades de configuración e IA
from config import IMAGENES_REFERENCIA, IMAGENES_ANALIZAR, IMAGENES_DETECTADAS, get_models, read_image_safe, add_reference_encoding
from utils.detection_images import detect_faces_in_image, read_image_safe
from models.individuo import Individuo, serialize_individuo

# Funciones MongoDB para CRUD de individuos y caras
from mongo.mongo_individuos import (
    crear_individuo, borrar_individuo,
    agregar_caras_a_individuo, consultar_caras_individuo, 
    get_cara_id, modificar_individuo, get_individuo_by_id
)
from mongo.mongo_caras import crear_cara, borrar_cara 
from werkzeug.utils import secure_filename

# Crear blueprint para agrupar las rutas del módulo
individuos_bp = Blueprint("individuos", __name__)
logger = logging.getLogger("detector.routes.individuos")

# Cargar modelos globales de reconocimiento: KDTree, nombres y YOLO
kdtree, reference_names, yolo_model = get_models()





# -------------------------
# Crear individuo
# -------------------------
@individuos_bp.route("/crear_individuo", methods=["POST"])
def endpoint_crear_individuo():
    data = request.get_json(silent=True)
    if not data or "nombre" not in data:
        return jsonify({"error": "Nombre obligatorio"}), 400

    individuo = Individuo(
        nombre=data["nombre"],
        apellido1=data.get("apellido1", ""),
        apellido2=data.get("apellido2", ""),
        caras=[]
    )
    individuo_guardado = crear_individuo(individuo)
    if not individuo_guardado:
        return jsonify({"error": "No se pudo crear el individuo"}), 500

    # Agregar caras si vienen en la request
    caras = data.get("caras", [])
    if caras and individuo_guardado.id:
        individuo_guardado = agregar_caras_a_individuo(individuo_guardado.id, caras)
        if not individuo_guardado:
            return jsonify({"error": "No se pudieron agregar las caras"}), 500

    return jsonify({"individuo": serialize_individuo(individuo_guardado.to_dict())})


# -------------------------
# Modificar individuo
# -------------------------
@individuos_bp.route("/modificar_individuo", methods=["PUT"])
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
# Borrar individuo y sus caras
# -------------------------
# -------------------------
# Borrar individuo y sus caras físicas
# -------------------------
@individuos_bp.route("/borrar_individuo/<id>", methods=["DELETE"])
def endpoint_borrar_individuo(id):
    from mongo.mongo_individuos import get_individuo_by_id, borrar_individuo
    from mongo.mongo_caras import borrar_cara
    import os
    import glob
    from config import IMAGENES_REFERENCIA

    # Primero obtener el individuo
    individuo = get_individuo_by_id(id)
    if not individuo:
        return jsonify({"error": "No se encontró el individuo"}), 404

    # Borrar todas las caras de Mongo
    for cara in individuo.caras:
        if cara.id:
            borrar_cara(cara.id)

    # Borrar archivos físicos que empiecen con <individuo_id>___
    patron = os.path.join(IMAGENES_REFERENCIA, f"{id}___*")
    for file_path in glob.glob(patron):
        try:
            os.remove(file_path)
        except Exception as e:
            print(f"No se pudo borrar el archivo {file_path}: {e}")

    # Borrar el individuo de Mongo
    success = borrar_individuo(id)
    if not success:
        return jsonify({"error": "No se pudo borrar el individuo"}), 400

    return jsonify({"message": "Individuo y caras asociadas borrados correctamente"})



# -------------------------
# Consultar individuos con caras completas
# -------------------------
@individuos_bp.route("/consultar_individuos", methods=["GET"])
def endpoint_consultar_individuos():
    from mongo.mongo_individuos import get_individuos
    from mongo.mongo_caras import get_cara_id
    import os

    # Obtener todos los individuos
    individuos = get_individuos()
    if individuos is None:
        return jsonify({"error": "No se pudo obtener individuos"}), 400

    individuos_serializados = []

    for ind in individuos:
        ind_dict = ind.to_dict()

        # Completar las caras como objetos Cara
        caras_completas = []
        for cara_id in ind_dict.get("caras", []):
            cara_obj = get_cara_id(cara_id)
            if cara_obj:
                # Asegurarse que path sea relativo y use '/'
                filename = os.path.basename(cara_obj.path)
                cara_obj.path = f"/imagenes/referencia/{filename}".replace("\\", "/")
                caras_completas.append({"_id": cara_obj.id, "path": cara_obj.path})

        ind_dict["caras"] = caras_completas

        # Asegurar que el _id del individuo esté correcto
        if hasattr(ind, "id"):
            ind_dict["_id"] = ind.id

        individuos_serializados.append(ind_dict)

    return jsonify(individuos_serializados)




# -------------------------
# Consultar caras de un individuo
# -------------------------
@individuos_bp.route("/consultar_caras_individuo/<id>", methods=["GET"])
def endpoint_consultar_caras_individuo(id):
    # Obtener lista de caras desde Mongo
    caras = consultar_caras_individuo(id)

    # Convertir objetos Cara a diccionarios
    caras_serializadas = [c.to_dict() for c in caras]

    return jsonify({"caras": caras_serializadas})


# -------------------------
# Consultar individuo por ID
# -------------------------
@individuos_bp.route("/consultar_individuo/<individuo_id>", methods=["GET"])
def endpoint_consultar_individuo(individuo_id: str):
    from mongo.mongo_individuos import get_individuo_by_id

    # Obtener el individuo
    individuo = get_individuo_by_id(individuo_id)
    if not individuo:
        return jsonify({"error": "No se encontró el individuo"}), 404

    # Devolver como JSON usando to_dict()
    return jsonify({"individuo": individuo.to_dict()})

# -------------------------
# Agregar cara a individuo
# -------------------------
@individuos_bp.route("/agregar_cara_individuo/<id>", methods=["POST"])
def endpoint_agregar_cara_individuo(id: str):
    file = request.files.get("file")
    if not file or not file.filename:
        return jsonify({"error": "No se envió ningún archivo"}), 400

    # Nombre único
    unique_id = uuid.uuid4().hex[:8]
    filename = f"{id}___{unique_id}.jpg"
    if not os.path.exists(IMAGENES_REFERENCIA):
        os.makedirs(IMAGENES_REFERENCIA)
    save_path = os.path.join(IMAGENES_REFERENCIA, filename)
    file.save(save_path)

    try:
        img_rgb = read_image_safe(save_path)
        image_bgr = img_rgb[:, :, ::-1].copy()
    except Exception as e:
        if os.path.exists(save_path):
            os.remove(save_path)
        return jsonify({"error": f"Error leyendo imagen: {e}"}), 400

    image_annotated, faces = detect_faces_in_image(image_bgr)
    if not faces:
        os.remove(save_path)
        return jsonify({"error": "No se detectó ninguna cara en la imagen"}), 400

    # Guardar cara en Mongo
    relative_path = os.path.relpath(save_path, start=os.getcwd())
    relative_path_web = relative_path.replace("\\", "/")
    nueva_cara = Cara(id=None, path=relative_path_web)
    cara_guardada = crear_cara(nueva_cara)
    if not cara_guardada:
        os.remove(save_path)
        return jsonify({"error": "No se pudo guardar la cara en la base de datos"}), 500

    # Agregar cara al individuo
    individuo_actualizado = agregar_caras_a_individuo(id, [cara_guardada.id])
    if not individuo_actualizado:
        os.remove(save_path)
        return jsonify({"error": "No se pudo asociar la cara al individuo"}), 500

    # Actualizar KDTree
    try:
        add_reference_encoding(cara_guardada.path)
    except Exception as e:
        logger.warning(f"No se pudo agregar la cara al KDTree: {e}")

    # Devolver individuo actualizado con caras completas
    ind_dict = individuo_actualizado.to_dict()
    caras_completas: List[Dict] = []
    for cara_id in ind_dict.get("caras", []):
        cara_obj = get_cara_id(cara_id)
        if cara_obj:
            cara_obj.path = cara_obj.path.replace("\\", "/")
            caras_completas.append(cara_obj.to_dict())
    ind_dict["caras"] = caras_completas

    return jsonify(ind_dict), 200



# -------------------------
# Eliminar cara de un individuo y borrar archivo
# -------------------------
@individuos_bp.route("/eliminar_cara/<cara_id>/<individuo_id>", methods=["DELETE"])
def endpoint_eliminar_cara(cara_id: str, individuo_id: str):
    from mongo.mongo_caras import borrar_cara, get_cara_id
    from mongo.mongo_individuos import get_individuo_by_id, modificar_individuo
    import os

    # Obtener el individuo
    individuo = get_individuo_by_id(individuo_id)
    if not individuo:
        return jsonify({"error": "No se encontró el individuo"}), 404

    # Obtener la cara
    cara = get_cara_id(cara_id)
    if not cara:
        return jsonify({"error": "No se encontró la cara"}), 404

    # Borrar de Mongo
    if cara.id:
        borrar_cara(cara.id)

    # Borrar archivo físico
    if cara.path:
        # Convertir ruta relativa a absoluta
        path_absoluto = os.path.join(os.getcwd(), cara.path.replace("/", os.sep))
        if os.path.exists(path_absoluto):
            os.remove(path_absoluto)
        else:
            print(f"No se encontró el archivo: {path_absoluto}")

    # Eliminar referencia de la cara en el individuo
    if cara.id:
        individuo.eliminar_cara(cara.id)

    # Guardar cambios en Mongo
    individuo_modificado = modificar_individuo(individuo)
    if not individuo_modificado:
        return jsonify({"error": "No se pudo actualizar el individuo"}), 500

    return jsonify({
        "message": "Cara eliminada correctamente",
        "individuo": individuo_modificado.to_dict()
    })


# -------------------------
# Crear individuo con posible cara y agregar al KDTree
# -------------------------
@individuos_bp.route("/crear_individuo_con_cara", methods=["POST"])
def endpoint_crear_individuo_con_cara():


    # Obtener datos del FormData
    nombre = request.form.get("nombre")
    apellido1 = request.form.get("apellido1", "")
    apellido2 = request.form.get("apellido2", "")

    if not nombre:
        return jsonify({"error": "Nombre obligatorio"}), 400

    # Crear objeto Individuo
    individuo = Individuo(nombre=nombre, apellido1=apellido1, apellido2=apellido2)
    individuo_guardado = crear_individuo(individuo)

    if individuo_guardado is None:
        return jsonify({"error": "No se pudo crear el individuo"}), 500

    # Si hay archivo de cara
    file = request.files.get("file")
    if file and file.filename:
        # Crear nombre seguro y único
        filename = f"{individuo_guardado.id}___{secure_filename(file.filename)}"
        save_path = os.path.join(IMAGENES_REFERENCIA, filename)
        if not os.path.exists(IMAGENES_REFERENCIA):
            os.makedirs(IMAGENES_REFERENCIA)
        file.save(save_path)

        # Guardar en colección de caras
        relative_path = os.path.relpath(save_path, start=os.getcwd()).replace("\\", "/")
        nueva_cara = Cara(id=None, path=relative_path)
        cara_guardada = crear_cara(nueva_cara)

        if cara_guardada:
            # Asociar cara al individuo
            individuo_guardado = agregar_caras_a_individuo(individuo_guardado.id, [cara_guardada.id])

            # --- NUEVO: agregar al KDTree para detección ---
            try:
                from config import add_reference_encoding
                add_reference_encoding(cara_guardada.path)
            except Exception as e:
                logger.warning(f"No se pudo agregar la cara al KDTree: {e}")

    # Serializar y devolver
    return jsonify(serialize_individuo(individuo_guardado.to_dict())), 200

# -------------------------
# Modificar individuo y opcionalmente actualizar cara
# -------------------------
@individuos_bp.route("/modificar_individuo_con_cara", methods=["PUT"])
def endpoint_modificar_individuo_con_cara():

    # Datos del individuo
    individuo_id = request.form.get("id")
    nombre = request.form.get("nombre")
    apellido1 = request.form.get("apellido1", "")
    apellido2 = request.form.get("apellido2", "")

    if not individuo_id or not nombre:
        return jsonify({"error": "ID y nombre son obligatorios"}), 400

    # Obtener el individuo
    individuo = get_individuo_by_id(individuo_id)
    if not individuo:
        return jsonify({"error": "No se encontró el individuo"}), 404

    # Actualizar campos
    individuo.nombre = nombre
    individuo.apellido1 = apellido1
    individuo.apellido2 = apellido2

    # Revisar si hay archivo enviado
    file = request.files.get("file")
    if file and file.filename:
        # Crear nombre único
        unique_id = uuid.uuid4().hex[:8]
        filename = f"{individuo_id}___{unique_id}.jpg"
        if not os.path.exists(IMAGENES_REFERENCIA):
            os.makedirs(IMAGENES_REFERENCIA)
        save_path = os.path.join(IMAGENES_REFERENCIA, filename)
        file.save(save_path)

        # Leer imagen y detectar cara
        try:
            img_rgb = read_image_safe(save_path)
            image_bgr = img_rgb[:, :, ::-1].copy()
        except Exception as e:
            if os.path.exists(save_path):
                os.remove(save_path)
            return jsonify({"error": f"Error leyendo imagen: {e}"}), 400

        _, faces = detect_faces_in_image(image_bgr)
        if not faces:
            os.remove(save_path)
            return jsonify({"error": "No se detectó ninguna cara en la imagen"}), 400

        # Guardar la cara en Mongo
        relative_path = os.path.relpath(save_path, start=os.getcwd()).replace("\\", "/")
        nueva_cara = crear_cara(Cara(id=None, path=relative_path))
        if not nueva_cara:
            os.remove(save_path)
            return jsonify({"error": "No se pudo guardar la cara en la base de datos"}), 500

        # Asociar la cara al individuo
        individuo = agregar_caras_a_individuo(individuo_id, [nueva_cara.id])
        if not individuo:
            os.remove(save_path)
            return jsonify({"error": "No se pudo asociar la cara al individuo"}), 500

        # Actualizar KDTree
        try:
            add_reference_encoding(nueva_cara.path)
        except Exception as e:
            return jsonify({"warning": f"No se pudo actualizar KDTree: {e}"}), 200

    # Guardar cambios del individuo
    individuo_modificado = modificar_individuo(individuo)
    if not individuo_modificado:
        return jsonify({"error": "No se pudo actualizar el individuo"}), 500

    return jsonify({
        "message": "Individuo actualizado correctamente",
        "individuo": individuo_modificado.to_dict()
    })
