from flask_mysqldb import MySQL
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required
from config import configuracion
from Models.ModeloUsuario import ModeloUsuario
from Models.entities.Usuario import Usuario


app = Flask(__name__)

"""Conexion a la base de datos"""
BaseDatos = MySQL(app)

"""Inidicacion para mantener el usuario conectado y mantener su informacion"""
app_inicio_sesion = LoginManager(app)


@app_inicio_sesion.user_loader
def load_user(id):
    return ModeloUsuario.get_by_id(BaseDatos, id)


"""Ubicación del renderizado de la plantilla con su ruta"""


@app.route('/')
def index():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        correo = request.form['correo']
        contra = request.form['contra']
        usuario_conectado = ModeloUsuario.Iniciar(BaseDatos, correo, contra)
        if usuario_conectado is not None:
            if usuario_conectado.contra:
                login_user(usuario_conectado)
                return redirect(url_for('home'))
            else:
                flash("Contraseña incorrecta")
                return render_template('auth/login.html')
        else:
            flash("Usuario no encontrado")
            return render_template('auth/login.html')
    else:
        return render_template('auth/login.html')


@app.route('/home')
def home():
    return render_template('home.html')


if __name__ == '__main__':
    app.config.from_object(configuracion['desarrollo'])
    app.run()
