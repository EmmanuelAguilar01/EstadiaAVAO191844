from flask import Flask, render_template
from config import configuracion

app = Flask(__name__)


@app.route('/')
def index():
    """Ubicación del renderizado de la plantilla con su ruta"""
    return render_template('auth/login.html')


if __name__ == '__main__':
    app.config.from_object(configuracion['desarrollo'])
    app.run()
