# models/individuo.py
from typing import List, Dict, Optional

def serialize_individuo(individuo: Optional[Dict]) -> Optional[Dict]:
    """
    Convierte un documento MongoDB a JSON serializable.
    Retorna None si el documento no existe.
    """
    if not individuo:
        return None

    return {
        "_id": str(individuo["_id"]),
        "nombre": individuo.get("nombre", ""),
        "apellido1": individuo.get("apellido1", ""),
        "apellido2": individuo.get("apellido2", ""),
        "caras": individuo.get("caras", [])
    }

class Individuo:
    def __init__(self, nombre: str, apellido1: str = "", apellido2: str = "", caras: Optional[List[str]] = None):
        self.nombre = nombre
        self.apellido1 = apellido1
        self.apellido2 = apellido2
        self.caras = caras or []

    def to_dict(self) -> Dict:
        return {
            "nombre": self.nombre,
            "apellido1": self.apellido1,
            "apellido2": self.apellido2,
            "caras": self.caras
        }

    def agregar_cara(self, file_path: str):
        if file_path not in self.caras:
            self.caras.append(file_path)
