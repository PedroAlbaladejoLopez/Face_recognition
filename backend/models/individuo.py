from typing import List, Dict, Optional
from models.cara import Cara

def serialize_individuo(individuo: Optional[Dict]) -> Optional[Dict]:
    """
    Convierte un documento MongoDB a JSON serializable.
    Las caras se devuelven como IDs (str).
    """
    if not individuo:
        return None

    return {
        "id": str(individuo["_id"]) if "_id" in individuo else None,
        "nombre": individuo.get("nombre", ""),
        "apellido1": individuo.get("apellido1", ""),
        "apellido2": individuo.get("apellido2", ""),
        "caras": individuo.get("caras", [])  # en Mongo son IDs
    }


class Individuo:
    def __init__(
        self,
        nombre: str,
        apellido1: str = "",
        apellido2: str = "",
        caras: Optional[List[Cara]] = None,  # ahora son objetos Cara
        id: Optional[str] = None
    ):
        self.id = id
        self.nombre = nombre
        self.apellido1 = apellido1
        self.apellido2 = apellido2
        self.caras = caras or []

    def to_dict(self) -> Dict:
        """
        Convierte el Individuo a dict para Mongo.
        Solo guarda los IDs de las caras.
        """
        data: Dict = {
            "nombre": self.nombre,
            "apellido1": self.apellido1,
            "apellido2": self.apellido2,
            "caras": [cara.id for cara in self.caras]  # guardamos solo IDs
        }

        if self.id:
            data["_id"] = self.id

        return data

    def agregar_cara(self, cara: Cara):
        """
        Añade un objeto Cara al individuo.
        """
        if not any(c.id == cara.id for c in self.caras):
            self.caras.append(cara)

    def eliminar_cara(self, cara_id: str):
        """
        Elimina una cara por su ID.
        """
        self.caras = [c for c in self.caras if c.id != cara_id]

    def getNombre(self):
        return self.nombre

    @classmethod
    def from_dict(cls, data: Dict) -> "Individuo":
        """
        Crea un Individuo desde un dict de Mongo.
        Mongo solo manda IDs de caras, aquí creamos objetos Cara.
        """
        if data is None:
            return None

        # Convertimos IDs -> objetos Cara (sin path todavía)
        caras = []
        for cara_id in data.get("caras", []):
            caras.append(Cara(id=cara_id))

        return cls(
            id=str(data.get("_id") or data.get("id")) if data.get("_id") or data.get("id") else None,
            nombre=data.get("nombre", ""),
            apellido1=data.get("apellido1", ""),
            apellido2=data.get("apellido2", ""),
            caras=caras
        )
