import logging
from pathlib import Path

logger = logging.getLogger("detector.config")

# Puedes cambiar el framework que uses: ultralytics, yolov5, opencv DNN, etc.
# Aquí vamos a usar un ejemplo con ultralytics YOLO
try:
    from ultralytics import YOLO
except ImportError:
    YOLO = None
    logger.warning("[WARN] No se pudo importar ultralytics YOLO. Instala la librería ultralytics.")

yolo_model_instance = None

def load_yolo_model(model_path: str = "yolo_weights/best.pt"):
    """
    Carga el modelo YOLO desde un archivo .pt.
    Devuelve el objeto modelo listo para detección.
    """
    global yolo_model_instance

    if yolo_model_instance is not None:
        return yolo_model_instance

    if YOLO is None:
        logger.warning("[WARN] No hay YOLO disponible.")
        return None

    model_file = Path(model_path)
    if not model_file.exists():
        logger.warning(f"[WARN] Archivo de pesos YOLO no encontrado: {model_file}")
        return None

    try:
        yolo_model_instance = YOLO(str(model_file))
        logger.info("[OK] Modelo YOLO cargado correctamente.")
        return yolo_model_instance
    except Exception as e:
        logger.warning(f"[WARN] Error al cargar modelo YOLO: {e}")
        return None
