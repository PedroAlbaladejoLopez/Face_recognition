from typing import List, Optional, Dict, Any
from bson import ObjectId
from models.cara import Cara
from pymongo import MongoClient

# -------------------------
# Conexión Mongo y colección
# -------------------------
client = MongoClient("mongodb://localhost:27017/")
db = client["reconocimiento_facial"]
caras_col = db["caras"]

# ----------------- CREATE -----------------
def crear_cara(cara: Cara) -> Cara:
    """
    Guarda un objeto Cara en Mongo y retorna el objeto con id asignado.
    """
    data = {"path": cara.path}
    result = caras_col.insert_one(data)
    cara.id = str(result.inserted_id)
    return cara

# ----------------- DELETE -----------------
def borrar_cara(cara_id: str) -> bool:
    try:
        object_id = ObjectId(cara_id)
    except Exception:
        return False
    result = caras_col.delete_one({"_id": object_id})
    return result.deleted_count > 0

# ----------------- UPDATE -----------------
def modificar_cara(cara_id: str, nuevo_path: str) -> bool:
    try:
        object_id = ObjectId(cara_id)
    except Exception:
        return False
    result = caras_col.update_one({"_id": object_id}, {"$set": {"path": nuevo_path}})
    return result.modified_count > 0

# ----------------- GET ALL -----------------
def get_caras() -> List[Cara]:
    caras: List[Cara] = []
    for doc in caras_col.find():
        doc["id"] = str(doc["_id"])
        del doc["_id"]
        cara_obj = Cara.from_dict(doc)
        if cara_obj:
            caras.append(cara_obj)
    return caras

# ----------------- GET BY ID -----------------
def get_cara_id(cara_id: str) -> Optional[Cara]:
    try:
        object_id = ObjectId(cara_id)
    except Exception:
        return None
    doc = caras_col.find_one({"_id": object_id})
    if not doc:
        return None
    doc["id"] = str(doc["_id"])
    del doc["_id"]
    return Cara.from_dict(doc)

# ----------------- GET BY PATH -----------------
def get_cara_path(path: str) -> Optional[Cara]:
    print("Path buscar: ", path)
    doc = caras_col.find_one({"path": path})
    if not doc:
        return None
    doc["id"] = str(doc["_id"])
    del doc["_id"]
    return Cara.from_dict(doc)
