from flask import Flask, send_from_directory
from flask_cors import CORS
from routes.image_recognition_routes import image_recognition_bp
from routes.individuos_routes import individuos_bp
from config import IMAGENES_DETECTADAS, IMAGENES_REFERENCIA

app = Flask(__name__)
CORS(app, origins=["http://localhost:4200"])

# Registrar blueprints
app.register_blueprint(image_recognition_bp, url_prefix="/api")
app.register_blueprint(individuos_bp, url_prefix="/api")

# Endpoint para servir imágenes de referencia
@app.route("/imagenes/referencia/<filename>")
def servir_imagen_referencia(filename):
    # Devuelve el archivo desde la carpeta de imágenes
    return send_from_directory(IMAGENES_REFERENCIA, filename)

# Endpoint para servir imágenes de referencia
@app.route("/imagenes/detectadas/<filename>")
def servir_imagen_detectada(filename):
    # Devuelve el archivo desde la carpeta de imágenes
    return send_from_directory(IMAGENES_DETECTADAS, filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
