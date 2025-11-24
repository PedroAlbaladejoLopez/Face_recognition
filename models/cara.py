class Cara:
    def __init__(self, id: str, path: str = ""):
        self.id = id
        self.path = path  # corregido

    def to_dict(self):
        return {
            "id": self.id,
            "path": self.path
        }

    @classmethod
    def from_dict(cls, data):
        if data is None:
            return None
        
        return cls(
            id=data.get("id"),
            path=data.get("path", "")
        )
