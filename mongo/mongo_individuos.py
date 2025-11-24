from typing import List, Dict, Optional
from bson import ObjectId
from pymongo import MongoClient
from models.individuo import Individuo
from models.cara import Cara
from mongo.mongo_caras import get_cara_id, get_cara_path

# -------------------------
# Conexión Mongo y colección
# -------------------------
client = MongoClient("mongodb://localhost:27017/")
db = client["reconocimiento_facial"]
individuos_col = db["individuos"]

# ----------------- CREATE -----------------
def crear_individuo(individuo: Individuo) -> Optional[Individuo]:
    data = individuo.to_dict()
    result = individuos_col.insert_one(data)
    data["id"] = str(result.inserted_id)
    return Individuo.from_dict(data)

# ----------------- MODIFY -----------------
def modificar_individuo(individuo: Individuo) -> Optional[Individuo]:
    if not individuo.id:
        return None
    try:
        obj_id = ObjectId(individuo.id)
    except Exception:
        return None

    data = individuo.to_dict()
    # Nunca incluir _id en el update
    data.pop("id", None)
    data.pop("_id", None)

    # Intentar el update
    result = individuos_col.update_one({"_id": obj_id}, {"$set": data})

    # Comprobar que el documento existe (matched_count) en lugar de modified_count
    if result.matched_count == 0:
        return None  # No existe el documento

    # Retornar el documento actualizado
    return get_individuo_by_id(individuo.id)



# ----------------- DELETE -----------------
def borrar_individuo(individuo_id: str) -> bool:
    try:
        obj_id = ObjectId(individuo_id)
    except Exception:
        return False
    result = individuos_col.delete_one({"_id": obj_id})
    return result.deleted_count > 0

# ----------------- GET INDIVIDUO -----------------
def get_individuo_by_id(individuo_id: str) -> Optional[Individuo]:
    try:
        obj_id = ObjectId(individuo_id)
    except Exception:
        return None
    doc = individuos_col.find_one({"_id": obj_id})
    if not doc:
        return None
    doc["id"] = str(doc["_id"])
    del doc["_id"]
    return Individuo.from_dict(doc)

# ----------------- AGREGAR CARAS -----------------
def agregar_caras_a_individuo(individuo_id: str, caras: List[str]) -> Optional[Individuo]:
    try:
        obj_id = ObjectId(individuo_id)
    except Exception:
        return None

    doc = individuos_col.find_one({"_id": obj_id})
    if not doc:
        return None

    caras_existentes = doc.get("caras", [])
    nuevas_caras = [c for c in caras if c not in caras_existentes]

    if nuevas_caras:
        individuos_col.update_one(
            {"_id": obj_id},
            {"$addToSet": {"caras": {"$each": nuevas_caras}}}
        )

    return get_individuo_by_id(individuo_id)

# ----------------- ELIMINAR CARA -----------------
def eliminar_cara_de_individuo(individuo_id: str, cara_id: str) -> Optional[Individuo]:
    try:
        obj_id = ObjectId(individuo_id)
    except Exception:
        return None

    doc = individuos_col.find_one({"_id": obj_id})
    if not doc:
        return None

    cara_obj = get_cara_id(cara_id)
    if not cara_obj:
        return None

    path = cara_obj.path
    if path in doc.get("caras", []):
        individuos_col.update_one({"_id": obj_id}, {"$pull": {"caras": path}})

    return get_individuo_by_id(individuo_id)

# ----------------- CONSULTAR CARAS -----------------
def consultar_caras_individuo(individuo_id: str) -> List[Cara]:
    try:
        obj_id = ObjectId(individuo_id)
    except Exception:
        return []

    doc = individuos_col.find_one({"_id": obj_id})
    if not doc:
        return []

    caras_paths = doc.get("caras", [])
    caras_objs: List[Cara] = []
    for path in caras_paths:
        cara = get_cara_path(path)
        if cara:
            caras_objs.append(cara)
    return caras_objs

# ----------------- BUSCAR POR CARA -----------------
def buscar_individuo_por_cara(cara_path_or_name: str) -> Optional[Individuo]:
    doc = individuos_col.find_one({"caras": {"$in": [cara_path_or_name]}})
    if not doc:
        return None
    doc["id"] = str(doc["_id"])
    del doc["_id"]
    return Individuo.from_dict(doc)
