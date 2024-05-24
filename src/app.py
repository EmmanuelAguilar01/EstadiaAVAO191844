from flask_mysqldb import MySQL
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required
from config import configuracion
from flask_wtf.csrf import CSRFProtect
from Models.ModeloUsuario import ModeloUsuario
from datetime import date
from werkzeug.security import generate_password_hash


app = Flask(__name__)
Token = CSRFProtect()
# Conexion a la base de datos
BaseDatos = MySQL(app)

# Inidicacion para mantener el usuario conectado y mantener su informacion
app_inicio_sesion = LoginManager(app)


@app_inicio_sesion.user_loader
def load_user(id):
    return ModeloUsuario.get_by_id(BaseDatos, id)


# Ubicación del renderizado de la plantilla con su ruta


@app.route('/')
def index():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        correo = request.form['correo']
        contra = request.form['contra']
        if not correo or not contra:
            flash("Debes ingresar un correo y una contraseña")
            return render_template('auth/login.html')
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


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/new')
def new():
    return render_template('nuevoUsuario.html')


@app.route('/home')
@login_required
def home():
    return render_template('home.html')


@app.route('/agregarNuevo', methods=['POST'])
def agregarNuevo():
    if request.method == 'POST':
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        correo = request.form['correo']
        contra = generate_password_hash(request.form['contra'])
        tipo = "Usuario"
        fechaRegistro = date.today().strftime('%Y-%m-%d')
        intereses = request.form['intereses']
        procedencia = request.form['procedencia']
        cursor = BaseDatos.connection.cursor()
        cursor.execute("SELECT 1 FROM usuarios WHERE correo = %s", (correo,))
        if cursor.fetchone() is not None:
            flash('Ya existe un usuario con ese correo electrónico')
            return redirect(url_for('new'))

        cursor = BaseDatos.connection.cursor()
        sql = """INSERT INTO usuarios (Nombre,Apellido,Correo,Contra,Tipo,FechaRegistro,Intereses,Procedencia) VALUES
                ('{0}', '{1}', '{2}', '{3}', '{4}', '{5}', '{6}', '{7}')""".format(nombre, apellido, correo, contra,  tipo, fechaRegistro, intereses, procedencia)
        cursor.execute(sql)
        BaseDatos.connection.commit()
        flash('Nuevo usuario, guardado satisfactoriamente')
        return redirect(url_for('new'))


def status_401(error):
    return redirect(url_for('login'))


def status_404(error):
    return "<h1>Esta página no existe</h1>", 404


if __name__ == '__main__':
    app.config.from_object(configuracion['desarrollo'])
    Token.init_app(app)
    app.register_error_handler(401, status_401)
    app.register_error_handler(404, status_404)
    app.run()
