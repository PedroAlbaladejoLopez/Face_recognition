# Reconocimiento Facial y Detección de Objetos con Flask

Este proyecto es una API REST construida con **Flask** que permite detectar **caras** y **objetos** en imágenes y videos. Utiliza:

- **face_recognition** para reconocimiento facial.
- **YOLOv8** (ultralytics) para detección de objetos.
- **OpenCV** y **NumPy** para procesamiento de imágenes.
- **Scikit-learn KDTree** para búsquedas rápidas de caras conocidas.

---

## Estructura del Proyecto

.
├── app.py # Punto de entrada de la API Flask
├── config.py # Configuración global y carga de modelos
├── requirements.txt # Dependencias del proyecto
├── routes/
│ └── image_recognition.py # Endpoints de imágenes y videos
├── utils/
│ ├── detection_images.py # Funciones de detección de imágenes
│ └── detection_video.py # Funciones de detección en video
├── imagenes_referencia/ # Caras conocidas
├── imagenes_para_analizar/ # Imágenes y videos subidos para análisis
└── imagenes_detectadas/ # Resultados de detección


---

## Requisitos

- Python 3.12 o superior
- Windows / Linux / macOS
- Git

---

## Instalación Paso a Paso

1. **Clonar el repositorio**

```bash
git clone <REPO_URL>
cd Reconocimiento_facial
```

2. **Crear y activar un entorno virtual**

# Windows
```bash
python -m venv venv
venv\Scripts\activate
```

# Linux / macOS
```bash
python3 -m venv venv
source venv/bin/activate
```

3. **Actualizar pip**
```bash
python -m pip install --upgrade pip
```

4. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

5. **Preparación de carpetas**
```bash
imagenes_referencia/      # Coloca imágenes de caras conocidas
imagenes_para_analizar/   # Subidas por los endpoints para analizar
imagenes_detectadas/      # Imágenes/videos detectados

```
6. **Configuración de referencias y modelos**

Al iniciar la app (app.py):

Se cargan automáticamente las imágenes de referencia (imagenes_referencia) y se generan los encodings faciales.

Se carga el modelo YOLOv8 (yolov8n.pt) para detección de objetos.

Se inicializan los modelos globales para uso en los endpoints.

7. **Ejecutar**
````bash
python app.py
````

8. **API**
# API Flask de Reconocimiento de Imágenes y Videos

## Endpoints

### 1. Detectar Imagen

**POST /detect_image**

**Descripción:** Detecta caras y objetos en una imagen.  
Opcionalmente muestra ventana OpenCV en vivo (`live=true`).

**Query Params:**  
- `live` (bool, opcional): Si `true`, se muestra la ventana de detección en tiempo real.

**Body (form-data):**  
- `file` (file, obligatorio): Imagen a analizar (.jpg, .png, .jpeg)

**Ejemplo:**  
POST http://localhost:5000/detect_image?live=true

Body → form-data → file: imagen.jpg


**Respuesta JSON:**
```json
{
  "faces": ["Alice", "Bob"],
  "objects": ["cup", "person"],
  "detected_image": "imagenes_detectadas/imagen_abc123.png"
}
