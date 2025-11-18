"""
app.py
------
Punto de entrada de la aplicación Flask de reconocimiento facial.
"""

from flask import Flask
from routes.image_recognition import image_recognition_bp

app = Flask(__name__)
app.register_blueprint(image_recognition_bp, url_prefix="/api")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
