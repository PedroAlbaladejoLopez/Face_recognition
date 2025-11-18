# mongo/mongo_individuos.py
from typing import List, Dict, Optional
from pymongo import MongoClient
from bson import ObjectId
from models.individuo import serialize_individuo, Individuo

# Conexión a MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["reconocimiento_facial"]
individuos_col = db["individuos"]

# -------------------------------
# Crear un nuevo individuo
# -------------------------------
def crear_individuo(individuo_dict: Dict) -> str:
    """
    Inserta un nuevo individuo en MongoDB.
    Retorna el _id generado como string.
    """
    result = individuos_col.insert_one(individuo_dict)
    return str(result.inserted_id)

# -------------------------------
# Listar todos los individuos
# -------------------------------
def listar_individuos() -> List[Dict]:
    """
    Devuelve todos los individuos en la colección, ignorando None.
    """
    docs = individuos_col.find()
    return [ind for ind in (serialize_individuo(doc) for doc in docs) if ind is not None]

# -------------------------------
# Buscar un individuo por nombre
# -------------------------------
def buscar_individuo(nombre: str) -> Optional[Dict]:
    doc = individuos_col.find_one({"nombre": nombre})
    return serialize_individuo(doc)

# -------------------------------
# Actualizar un individuo por _id
# -------------------------------
def actualizar_individuo(_id: str, datos: Dict) -> bool:
    """
    Retorna True si se modificó algún documento.
    """
    result = individuos_col.update_one({"_id": ObjectId(_id)}, {"$set": datos})
    return result.modified_count > 0

# -------------------------------
# Eliminar un individuo por _id
# -------------------------------
def eliminar_individuo(_id: str) -> bool:
    result = individuos_col.delete_one({"_id": ObjectId(_id)})
    return result.deleted_count > 0
