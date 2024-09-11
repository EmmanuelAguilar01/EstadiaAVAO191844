# Importación de librerias para el proyecto
from datetime import datetime, date, timedelta
import os
from flask_mail import Mail, Message
from flask_mysqldb import MySQL
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_wtf.csrf import CSRFProtect
from flask_jwt_extended import create_access_token, JWTManager, decode_token
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from werkzeug.security import generate_password_hash
from config import configuracion
from Models.ModeloUsuario import ModeloUsuario
import subprocess
import threading

# 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

# Inicialización de la Aplicación
app = Flask(__name__)

# Uso de las configuraciones del archivo "config.py" para BD y Mail
app.config.from_object(configuracion['desarrollo'])
app.config.update(configuracion['codigoR'].__dict__)

# Conexión para el servidor de correo electrónico
Correo = Mail(app)
# Creación del Token de seguridad
Token = CSRFProtect()
# Conexion a la base de datos
BaseDatos = MySQL(app)

# Configuración de el directorio de Datasets:
UPLOAD_FOLDER = r'C:\Users\nayel\Desktop\Estadia - AVAO191844\Sistema\src\Datasets'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Configuración para uso del administrador de correo electrónico
Recu_Contra = JWTManager(app)


# Indicacion para mantener el usuario conectado y mantener su informacion
app_inicio_sesion = LoginManager(app)

# Configuración de la libreria de Load_user para solicitar la información del usuario desde su ID


@app_inicio_sesion.user_loader
def load_user(id):
    return ModeloUsuario.get_by_id(BaseDatos, id)


# Ubicación del renderizado de la plantilla con su ruta

# Es la ruta por defecto o la principal siendo solo la ruta vacia que automáticamente manda a la ruta LOGIN
@app.route('/')
def index():
    return redirect(url_for('login'))

# Configuración de la ruta LOGIN, solicitud y envio de los datos que se obtienen en el formulario


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        # Obtención de los datos del formulario
        correo = request.form['correo']
        contra = request.form['contra']
        # Comparación de que no este vacío ninguno de los dos campos
        if not correo or not contra:
            # Mensaje de error
            flash("Debes ingresar un correo y una contraseña")
            # Regresa a la misma vista
            return render_template('auth/login.html')
        # Configuración de la variable para recibir los datos del Modelo (Usuario) Cuando se haga la solicitud.
        usuario_conectado = ModeloUsuario.Iniciar(BaseDatos, correo, contra)
        # Comparación de que el "Usuario conectado" no esté vacío
        if usuario_conectado is not None:
            # Comparación de la contraseña
            if usuario_conectado.contra:
                # Se logea un usuario al ser todo correcto y se identifica con la libreria de "Login_User"
                login_user(usuario_conectado)
                # Se hace la comparación del tipo de usuario que se registra
                if usuario_conectado.tipo == 'Administrador':
                    # Si el usuario registrado es de tipo administrador, se envia a la vista "Admin"
                    return redirect(url_for('admin'))
                # Si el usuario registrado es del tipo Tester, se envia a la vista "Tester"
                elif usuario_conectado.tipo == 'Tester':
                    return redirect(url_for('tester'))
            else:
                # En caso de que no sea correcta la contraseña se indica el mensaje y se redirecciona a la página Login
                flash("Contraseña incorrecta")
                return render_template('auth/login.html')
        else:
            # En caso de que no exista el correo electrónico se envia mensaje y se redicciona a la pagina de login
            flash("Usuario no encontrado")
            return render_template('auth/login.html')
    else:
        # Si no se quiere hacer nada, solo se renderiza la vista de Login
        return render_template('auth/login.html')

# Configuración de la ruta de Cerrar Sesión (LOGOUT), usando la libreria de Logout y redirigiendo a Login


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/recuperacion')
def recuperacion():
    return render_template('recuperacion.html')

# Configuración de la ruta para crear un nuevo usuario directamente sin inicar sesión


@app.route('/new')
def new():
    return render_template('test/nuevoUsuario.html')

# Configuración de la ruta para acceso de Administrador, siendo asegurada por medio de la libreria de "Login_Required"


@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    return render_template('admin/admin.html')

# Configuración de la ruta para acceso de Tester, siendo asegurada por medio de la libreria de "Login_Required"


@app.route('/tester', methods=['GET', 'POST'])
@login_required
def tester():
    return render_template('test/Tester.html')

# Configuración de la ruta para crear un nuevo usuario cuando ya se haya iniciado sesión (SOLO ADMINISTRADOR), siendo asegurada por medio de la libreria de "Login_Required"


@app.route('/nuevoUsuarioA')
@login_required
def nuevoUsuarioA():
    return render_template('admin/nuevoUsuarioA.html')


# Configuración de la ruta para crear un nuevo usuario cuando ya se haya iniciado sesión (SOLO ADMINISTRADOR), siendo asegurada por medio de la libreria de "Login_Required"


@app.route('/experimentadorA')
@login_required
def experimentadorA():
    cursor = BaseDatos.connection.cursor()
    cursor.execute("""
        SELECT 
            d.NombreDataExp, 
            d.FormatoExp, 
            d.Imagenes, 
            u.Nombre, 
            tb.TipoBasura,
            d.Tecnologia
        FROM 
            dataexperiment d
        INNER JOIN 
            Usuarios u ON d.idUsuarios = u.idUsuarios
        INNER JOIN 
            TiposBasura tb ON d.idTiposBasura = tb.idTiposBasura
    """)

    datas = cursor.fetchall()
    cursor.close()
    return render_template('admin/experimentadorA.html', datas=datas)


@app.route('/EjecExperimentador', methods=['POST'])
def EjecExperimentador():
    tecnologia = request.form.get('Tecnologia')
    epocas = request.form.get('epocas')
    batch_size = request.form.get('batch_size')
    threshold = request.form.get('threshold')
    iou_threshold = request.form.get('iou_threshold')

    print(f"Tecnología: {tecnologia}, Épocas: {epocas}, Batch size: {batch_size}, Threshold: {threshold}, IOU threshold: {iou_threshold}")

    if not all([tecnologia, epocas, batch_size, threshold, iou_threshold]):
        return jsonify({'error': 'Faltan valores requeridos'}), 400

    if tecnologia == "YOLO":
        imgsz = request.form.get('imgsz')
        data = request.files.get('data')
        cfg = request.files.get('cfg')
        name = request.form.get('name')

        print(f"imgsz: {imgsz}, data: {data}, cfg: {cfg}, name: {name}")

        if not all([imgsz, data, cfg, name]):
            flash('Faltan valores requeridos para YOLO')
            return redirect(url_for('experimentadorA'))

        print(
            f"Entrenando YOLO con imgsz: {imgsz}, data: {data}, cfg: {cfg}, name: {name}")

        data_filename = os.path.join(
            app.config['UPLOAD_FOLDER'], data.filename)
        cfg_filename = os.path.join(app.config['UPLOAD_FOLDER'], cfg.filename)

        data.save(data_filename)
        cfg.save(cfg_filename)

        # Inicia el hilo para entrenar YOLO
        thread = threading.Thread(target=YOLO, args=(
            epocas, batch_size, threshold, iou_threshold, imgsz, data_filename, cfg_filename, name))
        mensaje = "Entrenando YoloV5"

    elif tecnologia == "TRANS":
        # Inicia el hilo para entrenar TRANSFORMER
        thread = threading.Thread(target=Transformers, args=(
            epocas, batch_size, threshold, iou_threshold))
        mensaje = "Entrenando Transformer"

    # Inicia el hilo de entrenamiento y envía la respuesta
    thread.start()
    return jsonify({'mensaje': mensaje})


def YOLO(epocas, batch_size, threshold, iou_threshold, imgsz, data, cfg, name):
    env = os.environ.copy()
    env['CONF_THRES'] = str(threshold)
    env['IOU_THRES'] = str(iou_threshold)

    print(
        f"Iniciando YOLO con los siguientes parámetros: {epocas}, {batch_size}, {imgsz}, {data}, {cfg}, {name}")

    subprocess.run([r'C:\Users\nayel\Desktop\Estadia - AVAO191844\Sistema\Sistema\Scripts\python.exe',
                    r'C:\Users\nayel\Desktop\Estadia - AVAO191844\Sistema\src\Models\YoloV5\YOLOV5.py',
                    '--epochs', epocas, '--batch-size', batch_size, '--imgsz', imgsz, '--data', data,
                    '--cfg', cfg, '--name', name], shell=True, check=True)


def Transformers(epocas, batch_size, threshold, iou_threshold):
    subprocess.run([r'C:\Users\nayel\Desktop\Estadia - AVAO191844\Sistema\Sistema\Scripts\python.exe',
                    r'C:\Users\nayel\Desktop\Estadia - AVAO191844\Sistema\src\Models\Transformers\Transformer.py',
                    '--epocas', epocas, '--batch_size', batch_size, '--threshold', threshold,
                    '--iou_threshold', iou_threshold], shell=True, check=True)


@app.route('/progreso', methods=['GET'])
def progreso():
    # Devolver el estado de la ejecución del script
    return jsonify({'progreso': '50%'})


@app.route('/evaluadorA')
@login_required
def evaluadorA():
    return render_template('admin/evaluadorA.html')


@app.route('/tiposBasuraA')
@login_required
def tiposBasuraA():
    return render_template('admin/tiposBasuraA.html')


@app.route('/reportesA')
@login_required
def reportesA():
    return render_template('admin/reportesA.html')


@app.route('/CrudDatasetA')
@login_required
def CrudDatasetA():
    cursor = BaseDatos.connection.cursor()
    cursor.execute('SELECT TipoBasura FROM tiposBasura')
    tipos = cursor.fetchall()
    cursor.close()
    return render_template('admin/crudDatasetPruebaA.html', tipos=tipos)


@app.route('/agregarDataset', methods=['POST'])
def agregarDataset():
    accion = request.form.get('accion')

    if accion == 'validar':
        return validar_dataset()
    elif accion == 'guardar':
        return guardar_dataset()
    else:
        return "Acción no reconocida"


def validar_dataset():
    # Obtener los archivos subidos
    archivos = request.files.getlist("Dataset[]")

    # Obtener la carpeta seleccionada por el usuario
    nombre_dataset = request.form.get('nombreDataset')

    # Obtener la tecnología seleccionada por el usuario
    tecnologia = request.form.get('Tecnologia')

    # Verificar si los campos están vacíos
    if not all([nombre_dataset, archivos, tecnologia]):
        flash('Por favor, complete todos los campos')
        return redirect(url_for('CrudDatasetA'))

    # Diccionario para almacenar las rutas de archivos por carpetas para YOLO
    dataset_estructura_yolo = {
        "train": {"labels": [], "images": []},
        "test": {"labels": [], "images": []},
        "valid": {"labels": [], "images": []}
    }

    # Diccionario para almacenar las rutas de archivos por carpetas para Transformer
    dataset_estructura_transformer = {
        "train": {"images": [], "json": False},
        "test": {"images": [], "json": False},
        "valid": {"images": [], "json": False}
    }

    # Procesar todos los archivos recibidos
    for archivo in archivos:
        # Obtener la ruta relativa del archivo dentro del directorio
        ruta_relativa = archivo.filename

        if tecnologia == "YOLO":
            # Validación para YOLO
            if 'train/' in ruta_relativa:
                if '/labels/' in ruta_relativa and ruta_relativa.endswith('.txt'):
                    dataset_estructura_yolo['train']['labels'].append(
                        ruta_relativa)
                elif '/images/' in ruta_relativa and (ruta_relativa.endswith('.jpg') or ruta_relativa.endswith('.png')):
                    dataset_estructura_yolo['train']['images'].append(
                        ruta_relativa)
            elif 'test/' in ruta_relativa:
                if '/labels/' in ruta_relativa and ruta_relativa.endswith('.txt'):
                    dataset_estructura_yolo['test']['labels'].append(
                        ruta_relativa)
                elif '/images/' in ruta_relativa and (ruta_relativa.endswith('.jpg') or ruta_relativa.endswith('.png')):
                    dataset_estructura_yolo['test']['images'].append(
                        ruta_relativa)
            elif 'valid/' in ruta_relativa:
                if '/labels/' in ruta_relativa and ruta_relativa.endswith('.txt'):
                    dataset_estructura_yolo['valid']['labels'].append(
                        ruta_relativa)
                elif '/images/' in ruta_relativa and (ruta_relativa.endswith('.jpg') or ruta_relativa.endswith('.png')):
                    dataset_estructura_yolo['valid']['images'].append(
                        ruta_relativa)

        elif tecnologia == "Transformer":
            # Validación para Transformer
            if 'train/' in ruta_relativa:
                if ruta_relativa.endswith('.jpg') or ruta_relativa.endswith('.png'):
                    dataset_estructura_transformer['train']['images'].append(
                        ruta_relativa)
                elif ruta_relativa.endswith('.json'):
                    dataset_estructura_transformer['train']['json'] = True
            elif 'test/' in ruta_relativa:
                if ruta_relativa.endswith('.jpg') or ruta_relativa.endswith('.png'):
                    dataset_estructura_transformer['test']['images'].append(
                        ruta_relativa)
                elif ruta_relativa.endswith('.json'):
                    dataset_estructura_transformer['test']['json'] = True
            elif 'valid/' in ruta_relativa:
                if ruta_relativa.endswith('.jpg') or ruta_relativa.endswith('.png'):
                    dataset_estructura_transformer['valid']['images'].append(
                        ruta_relativa)
                elif ruta_relativa.endswith('.json'):
                    dataset_estructura_transformer['valid']['json'] = True

    # Validación final para YOLO
    if tecnologia == "YOLO":
        for carpeta, contenido in dataset_estructura_yolo.items():
            if not contenido['labels'] or not contenido['images']:
                return f"Error: La carpeta {carpeta} no contiene los archivos necesarios para YOLO"
        mensaje = f"Estructura correcta para el dataset: {nombre_dataset}, si vas a usar YOLO"

        flash(mensaje)  # Envía el mensaje a través de flash
        return redirect(url_for('CrudDatasetA'))

    # Validación final para Transformer
    elif tecnologia == "Transformer":
        for carpeta, contenido in dataset_estructura_transformer.items():
            if not contenido['images'] or not contenido['json']:
                return f"Error: La carpeta {carpeta} no contiene los archivos necesarios para Transformer"
        mensaje = f"Estructura correcta para el dataset: {nombre_dataset}, si vas a usar Transformer"
        flash(mensaje)  # Envía el mensaje a través de flash
    return redirect(url_for('CrudDatasetA'))


def guardar_dataset():
    nombre_dataset = request.form.get('nombreDataset')
    formato = request.form['Formato']
    tecnologia = request.form['Tecnologia']
    tipo_basura = request.form['tipoBasura']
    usuario_id = current_user.id
    archivos = request.files.getlist('Dataset')
    imagenes = [
        archivo for archivo in archivos if archivo.filename.lower().endswith('.jpg')]
    cantidad_imagenes = len(imagenes)

    # Verificar si los campos están vacíos
    if not all([nombre_dataset, formato, tipo_basura, tecnologia]):
        flash('Por favor, complete todos los campos')
        return redirect(url_for('CrudDatasetA'))

    cursor = BaseDatos.connection.cursor()

    cursor.execute(
        "SELECT idTiposBasura FROM tiposbasura WHERE TipoBasura = %s", (tipo_basura,))

    id_tipo_basura = cursor.fetchone()[0]

    cursor.execute("INSERT INTO dataexperiment (idUsuarios, idTiposBasura, NombreDataExp,FormatoExp,Imagenes,Tecnologia) VALUES (%s, %s, %s, %s, %s,%s)",
                   (usuario_id, id_tipo_basura, nombre_dataset, formato, cantidad_imagenes, tecnologia))

    BaseDatos.connection.commit()

    flash("El dataset {nombre_dataset} ha sido guardado en la base de datos.")
    return redirect(url_for('experimentadorA'))


@ app.route('/eliminarDataset/<string:NombreDataExp>')
def eliminarDataset(NombreDataExp):
    cursor = BaseDatos.connection.cursor()
    cursor.execute(
        'DELETE FROM dataexperiment WHERE NombreDataExp = %s', (NombreDataExp,))
    BaseDatos.connection.commit()
    flash('Dataset eliminado satisfactoriamente')
    return redirect(url_for('experimentadorA'))


@ app.route('/editarDataset/<string:NombreDataExp>')
def editarDataset(NombreDataExp):
    cursor = BaseDatos.connection.cursor()
    sql = "SELECT NombreDataExp, FormatoExp, Tecnologia FROM dataexperiment WHERE NombreDataExp = %s"
    cursor.execute(sql, (NombreDataExp,))
    dataset = cursor.fetchone()
    Nombre = dataset[0]
    Formato = dataset[1]
    Tecnologia = dataset[2]

    return render_template('admin/editarDatasetExpAd.html', nombreDataset=Nombre, Tecnologia=Tecnologia,
                           Formato=Formato)


@ app.route('/modificarDataset/<string:NombreDataExp>', methods=['POST'])
def modificarDataset(NombreDataExp):
    if request.method == 'POST':
        Nombre = request.form['nombreDataset']
        Tecnologia = request.form['Tecnologia']
        Formato = request.form['Formato']

        cursor = BaseDatos.connection.cursor()
        sql = """UPDATE dataexperiment SET NombreDataExp = %s,Tecnologia = %s, FormatoExp = %s WHERE NombreDataExp = %s"""
        cursor.execute(sql, (Nombre, Tecnologia, Formato, Nombre))
        BaseDatos.connection.commit()
        flash('Dataset actualizado satisfactoriamente')
        return redirect(url_for('experimentadorA'))

# Configuración del módulo para agregar un nuevo usuario sin ininicar sesión


@ app.route('/agregarNuevo', methods=['POST'])
def agregarNuevo():
    # Se captan los datos de los diferentes elementos del formulario
    if request.method == 'POST':
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        correo = request.form['correo']
        # Se encripta la contraseña antes de realizar el envio hacia la base de datos
        contra = generate_password_hash(request.form['contra'])
        # Como se tiene este módulo sin iniciar sesión, todos los usuarios van a ser "Tester"
        tipo = "Tester"
        # La Fecha de registro será automática tomada desde el sistema
        fechaRegistro = date.today().strftime('%Y-%m-%d')
        intereses = request.form['intereses']
        procedencia = request.form['procedencia']

        # Verificar si los campos están vacíos
        if not all([nombre, apellido, correo, contra, intereses, procedencia]):
            flash('Por favor, complete todos los campos')
            return redirect(url_for('new'))

        # Se crea el cursor para direccionar a la base de datos
        cursor = BaseDatos.connection.cursor()

        # Se crea la sentencia SQL Para validar si ya existe el correo que se quiere registrar
        cursor.execute("SELECT 1 FROM usuarios WHERE correo = %s", (correo,))
        # Si ya esta registrado el correo se envia mensaje
        if cursor.fetchone() is not None:
            flash('Ya existe un usuario con ese correo electrónico')
            return redirect(url_for('new'))
        # En caso negativo (NO ESTE REGISTRADO) se hace nuevamente la conexión a la Base de datos
        cursor = BaseDatos.connection.cursor()
        # Se crea nueva sentencia SQL para la inserción de todos los datos captados en el formulario a todas las columnas de la Base.
        sql = """INSERT INTO usuarios (Nombre,Apellido,Correo,Contra,Tipo,FechaRegistro,
        Intereses,Procedencia) VALUES
                ('{0}', '{1}', '{2}', '{3}', '{4}', '{5}', '{6}', '{7}')""".format(
            nombre, apellido, correo, contra,  tipo, fechaRegistro, intereses, procedencia)
        # Se ejecuta la sentencia SQL junto con el cursor.
        cursor.execute(sql)
        # Se realiza el envio de los datos.
        BaseDatos.connection.commit()
        # Mensaje de guardado correcto
        flash('Nuevo usuario, guardado satisfactoriamente')
        # Al terminar el proceso se redirecciona a la ruta de "New"
        return redirect(url_for('new'))

# Se crea el módulo para agregar nuevo usuario pero en este caso siendo Administrador


@ app.route('/agregarNuevoA', methods=['POST'])
def agregarNuevoA():
    if request.method == 'POST':
        if not all(request.form.values()):
            flash('Por favor, complete todos los campos')
            return redirect(url_for('nuevoUsuarioA'))

        nombre = request.form['nombre']
        apellido = request.form['apellido']
        correo = request.form['correo']
        contra = generate_password_hash(request.form['contra'])
        # A comparación del modulo anterior este se toma el tipo que se selecciona en el radio (Adimistrador o Tester)
        tipo = request.form['tipo']
        fechaRegistro = date.today().strftime('%Y-%m-%d')
        intereses = request.form['intereses']
        procedencia = request.form['procedencia']

        cursor = BaseDatos.connection.cursor()

        cursor.execute("SELECT 1 FROM usuarios WHERE correo = %s", (correo,))

        if cursor.fetchone() is not None:
            flash('Ya existe un usuario con ese correo electrónico')
            return redirect(url_for('nuevoUsuarioA'))
        cursor = BaseDatos.connection.cursor()
        sql = """INSERT INTO usuarios (Nombre,Apellido,Correo,Contra,Tipo,FechaRegistro,Intereses,Procedencia)
                VALUES ('{0}', '{1}', '{2}', '{3}', '{4}', '{5}', '{6}', '{7}')""".format(
            nombre, apellido, correo, contra,  tipo, fechaRegistro, intereses, procedencia)
        cursor.execute(sql)
        BaseDatos.connection.commit()
        flash('Nuevo usuario, guardado satisfactoriamente')
        return redirect(url_for('nuevoUsuarioA'))


@ app.route('/agregarBasura', methods=['POST'])
def agregarBasura():
    if request.method == 'POST':
        tipo = request.form['tipoBasura']
        descripcion = request.form['Descripcion']
        afectaciones = request.form['Afectaciones']
        tiempo = request.form['TiempoDegradacion']

        # Verificar si los campos están vacíos
        if not all([tipo, descripcion, afectaciones, tiempo]):
            flash('Por favor, complete todos los campos')
            return redirect(url_for('crudBasuraA'))

        # Verificar si el TipoBasura ya existe
        cursor = BaseDatos.connection.cursor()
        cursor.execute(
            "SELECT * FROM tiposbasura WHERE TipoBasura = %s", (tipo,))
        if cursor.fetchone():
            flash('El TipoBasura ya existe')
            return redirect(url_for('crudBasuraA'))

        cursor = BaseDatos.connection.cursor()
        sql = """INSERT INTO tiposbasura (TipoBasura,Descrip,Afectaciones,TiempoDegradacion)
                VALUES ('{0}', '{1}', '{2}', '{3}')""".format(
            tipo, descripcion, afectaciones, tiempo)
        cursor.execute(sql)
        BaseDatos.connection.commit()
        flash('Nueva información, guardada satisfactoriamente')
        return redirect(url_for('crudBasuraA'))


@ app.route('/crudUsuarioA')
@ login_required
def crudUsuarioA():
    cursor = BaseDatos.connection.cursor()
    cursor.execute('SELECT * FROM usuarios')
    usuarios = cursor.fetchall()
    cursor.close()
    return render_template('admin/crudUsuarioA.html', usuarios=usuarios)


@ app.route('/eliminarA/<string:correo>')
def eliminarA(correo):
    cursor = BaseDatos.connection.cursor()
    cursor.execute(
        'DELETE FROM usuarios WHERE Correo = %s', (correo,))
    BaseDatos.connection.commit()
    flash('Usuario eliminado satisfactoriamente')
    return redirect(url_for('crudUsuarioA'))


@ app.route('/editarA/<string:correo>')
def editarA(correo):
    cursor = BaseDatos.connection.cursor()
    sql = "SELECT * FROM usuarios WHERE Correo = %s"
    cursor.execute(sql, (correo,))
    usuario = cursor.fetchone()
    nombre = usuario[1]
    apellido = usuario[2]
    correo = usuario[3]
    contra = usuario[4]
    tipo = usuario[5]
    fechaRegistro = usuario[6]
    intereses = usuario[7]
    procedencia = usuario[8]
    return render_template('admin/editarUsuarioA.html', nombre=nombre, apellido=apellido,
                           correo=correo, contra=contra, tipo=tipo, fechaRegistro=fechaRegistro, intereses=intereses,
                           procedencia=procedencia)


@ app.route('/editarUsuarioA/<string:correo>', methods=['POST'])
def editarUsuarioA(correo):
    if request.method == 'POST':
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        nuevo_correo = request.form['correo']
        tipo = request.form['tipo']
        fechaRegistro = request.form['FechaRegistro']
        intereses = request.form['intereses']
        procedencia = request.form['procedencia']
        contra = request.form.get('contra')

        if not all([nombre, apellido, nuevo_correo, tipo, fechaRegistro, intereses, procedencia]):
            flash('Todos los campos deben estar llenos')
            return redirect(url_for('crudUsuarioA'))

        # Normalizar la fecha del formulario
        fechaRegistro = datetime.strptime(fechaRegistro, '%Y-%m-%d').date()

        cursor = BaseDatos.connection.cursor()
        cursor.execute(
            "SELECT 1 FROM usuarios WHERE correo = %s AND correo != %s", (nuevo_correo, correo))
        if cursor.fetchone() is not None:
            flash('Ya existe un usuario con ese correo electrónico')
            return redirect(url_for('crudUsuarioA'))

        cursor.execute("SELECT * FROM usuarios WHERE correo = %s", (correo,))
        usuario_antiguo = cursor.fetchone()

        # Obtener la fecha de la base de datos
        fecha_base_datos = usuario_antiguo[6]
        if isinstance(fecha_base_datos, datetime):
            fecha_base_datos = fecha_base_datos.date()

        # Manejo de actualización de contraseña y fecha de registro
        if contra:
            contra = generate_password_hash(contra)
            if fechaRegistro != fecha_base_datos:
                sql = """UPDATE usuarios SET nombre = %s, apellido = %s, correo = %s, contra = %s, tipo = %s,
                    fechaRegistro = %s, intereses = %s, procedencia = %s
                    WHERE correo = %s"""
                cursor.execute(sql, (nombre, apellido, nuevo_correo, contra,
                                     tipo, fechaRegistro, intereses, procedencia, correo))
            else:
                sql = """UPDATE usuarios SET nombre = %s, apellido = %s, correo = %s, contra = %s, tipo = %s,
                    intereses = %s, procedencia = %s
                    WHERE correo = %s"""
                cursor.execute(sql, (nombre, apellido, nuevo_correo, contra,
                                     tipo, intereses, procedencia, correo))
        else:
            if fechaRegistro != fecha_base_datos:
                sql = """UPDATE usuarios SET nombre = %s, apellido = %s, correo = %s, tipo = %s,
                    fechaRegistro = %s, intereses = %s, procedencia = %s
                    WHERE correo = %s"""
                cursor.execute(sql, (nombre, apellido, nuevo_correo, tipo,
                                     fechaRegistro, intereses, procedencia, correo))
            else:
                sql = """UPDATE usuarios SET nombre = %s, apellido = %s, correo = %s, tipo = %s,
                    intereses = %s, procedencia = %s
                    WHERE correo = %s"""
                cursor.execute(sql, (nombre, apellido, nuevo_correo, tipo,
                                     intereses, procedencia, correo))

        BaseDatos.connection.commit()

        modificaciones = []
        if usuario_antiguo[1] != nombre:
            modificaciones.append(f"Nombre: {usuario_antiguo[1]} -> {nombre}")
        if usuario_antiguo[2] != apellido:
            modificaciones.append(
                f"Apellido: {usuario_antiguo[2]} -> {apellido}")
        if usuario_antiguo[3] != nuevo_correo:
            modificaciones.append(
                f"Correo: {usuario_antiguo[3]} -> {nuevo_correo}")
        if contra and usuario_antiguo[4] != contra:
            modificaciones.append(f"Contraseña: ******** -> ********")
        if usuario_antiguo[5] != tipo:
            modificaciones.append(f"Tipo: {usuario_antiguo[5]} -> {tipo}")
        if fecha_base_datos != fechaRegistro:
            modificaciones.append(
                f"Fecha de registro: {fecha_base_datos.strftime('%Y-%m-%d')} -> {fechaRegistro.strftime('%Y-%m-%d')}")
        if usuario_antiguo[7] != intereses:
            modificaciones.append(
                f"Intereses: {usuario_antiguo[7]} -> {intereses}")
        if usuario_antiguo[8] != procedencia:
            modificaciones.append(
                f"Procedencia: {usuario_antiguo[8]} -> {procedencia}")

        flash('Contacto actualizado satisfactoriamente. <br> Modificaciones realizadas:<br>' + '<br>'.join(
            modificaciones))

        return redirect(url_for('crudUsuarioA'))

# CRUD DE BASURA


@ app.route('/crudBasuraA')
@ login_required
def crudBasuraA():
    cursor = BaseDatos.connection.cursor()
    cursor.execute('SELECT * FROM tiposbasura')
    basuras = cursor.fetchall()
    cursor.close()
    return render_template('admin/tiposBasuraA.html', basuras=basuras)


@ app.route('/eliminarBasuraA/<string:tipoBasura>')
def eliminarBasuraA(tipoBasura):
    cursor = BaseDatos.connection.cursor()
    cursor.execute(
        'DELETE FROM tiposbasura WHERE tipoBasura = %s', (tipoBasura,))
    BaseDatos.connection.commit()
    flash('Usuario eliminado satisfactoriamente')
    return redirect(url_for('crudBasuraA'))


@ app.route('/editarBasuraA/<string:tipoBasura>')
def editarBasuraA(tipoBasura):
    cursor = BaseDatos.connection.cursor()
    sql = "SELECT * FROM tiposbasura WHERE tipoBasura = %s"
    cursor.execute(sql, (tipoBasura,))
    basura = cursor.fetchone()
    tipoBasura = basura[1]
    descripcion = basura[2]
    afectaciones = basura[3]
    tiempoDegradacion = basura[4]
    return render_template('admin/editarBasuraA.html', tipoBasura=tipoBasura, descripcion=descripcion,
                           afectaciones=afectaciones, tiempoDegradacion=tiempoDegradacion)


@ app.route('/editarBasuraAdmin/<string:tipoBasura>', methods=['POST'])
def editarBasuraAdmin(tipoBasura):
    if request.method == 'POST':
        tipoBasura = request.form['tipoBasura']
        descripcion = request.form['Descripcion']
        afectaciones = request.form['Afectaciones']
        tiempoDegradacion = request.form['TiempoDegradacion']
        cursor = BaseDatos.connection.cursor()
        sql = """UPDATE tiposbasura SET tipoBasura = %s, Descrip = %s,Afectaciones = %s, TiempoDegradacion = %s
                       WHERE tipoBasura = %s"""
        cursor.execute(sql, (tipoBasura, descripcion, afectaciones,
                       tiempoDegradacion, tipoBasura))
        BaseDatos.connection.commit()
        flash('Contacto actualizado satisfactoriamente')
        return redirect(url_for('crudBasuraA'))


# MANEJO DE USUARIO TESTER
@ app.route('/experimentadorT')
@ login_required
def experimentadorT():
    return render_template('test/experimentadorT.html')


@ app.route('/evaluadorT')
@ login_required
def evaluadorT():
    return render_template('test/evaluadorT.html')


@ app.route('/reportesT')
@ login_required
def reportesT():
    return render_template('test/reportesT.html')


@ app.route('/crudUsuarioT')
@ login_required
def crudUsuarioT():
    return render_template('test/crudUsuarioT.html')


@ app.route('/editarUsuarioT/<string:correo>', methods=['POST'])
def editarUsuarioT(correo):
    if request.method == 'POST':
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        correo = request.form['correo']
        fechaRegistro = request.form['FechaRegistro']
        intereses = request.form['intereses']
        procedencia = request.form['procedencia']
        if 'contra' in request.form:
            contra = generate_password_hash(request.form['contra'])
        else:
            contra = None
        cursor = BaseDatos.connection.cursor()
        sql = """UPDATE usuarios SET nombre = %s, apellido = %s,correo = %s, contra = %s,
                       fechaRegistro = %s, intereses = %s,procedencia = %s
                       WHERE correo = %s"""
        cursor.execute(sql, (nombre, apellido, correo,
                       contra, fechaRegistro, intereses, procedencia, correo))
        BaseDatos.connection.commit()
        flash('Contacto actualizado satisfactoriamente')
        return redirect(url_for('crudUsuarioT'))

# Recuperación de contraseña


@ app.route('/buscar_correo', methods=['POST'])
def buscar_correo():
    if request.method == 'POST':
        correo = request.form['correo']
        cursor = BaseDatos.connection.cursor()
        sql = "SELECT idUsuarios FROM usuarios WHERE correo = %s"
        cursor.execute(sql, (correo,))
        BaseDatos.connection.commit()
        resultado = cursor.fetchone()
        cursor.close()

        if resultado:
            id_usuario = resultado[0]
            Token_Contra = create_access_token(
                identity=id_usuario, expires_delta=timedelta(hours=24))
            enviar_correo_recuperacion(correo, Token_Contra)
            flash('Se ha enviado el enlace para recuperar tu contraseña al correo.')
            return redirect(url_for('recuperacion'))
        else:
            flash('El correo electrónico no esta registrado')
            return redirect(url_for('recuperacion'))


def enviar_correo_recuperacion(correo, Token_Contra):
    mensaje = Message(
        subject='Recuperar contraseña',
        sender='Estadia-AVAO191844<r-emmanuel_n@hotmail.com>',
        recipients=[correo],
        html=f'Haz clic en el siguiente enlace para restablecer tu contraseña:{url_for("nuevaContra", Token_Contra=Token_Contra, _external=True)}'
    )
    try:
        Correo.send(mensaje)
        print(f'Correo enviado a {correo}')
    except Exception as e:
        print(f'Error al enviar el correo: {e}')
        raise  # Para obtener más detalles sobre el error


@app.route('/nuevaContra/<Token_Contra>', methods=['GET', 'POST'])
def nuevaContra(Token_Contra):
    try:
        # Verifica el token y extrae el ID del usuario
        token_data = decode_token(Token_Contra)
        id_usuario = token_data['sub']

        if request.method == 'POST':
            # Obtén la nueva contraseña del formulario
            nueva_contra = request.form['nuevac']
            confirmar_contra = request.form['confirmar_nuevac']

            # Verifica si ambas contraseñas coinciden
            if nueva_contra == confirmar_contra:
                # Genera el hash de la nueva contraseña
                nueva_contraHS = generate_password_hash(nueva_contra)

                # Actualiza la contraseña en la base de datos
                cursor = BaseDatos.connection.cursor()
                sql = "UPDATE usuarios SET contra = %s WHERE idUsuarios = %s"
                cursor.execute(sql, (nueva_contraHS, id_usuario))
                BaseDatos.connection.commit()
                cursor.close()

                # Muestra mensaje de éxito y redirige al inicio de sesión
                flash('Contraseña actualizada con éxito')
                return redirect(url_for('login'))
            else:
                flash('Las contraseñas no coinciden')
                return redirect(url_for('nuevaContra', Token_Contra=Token_Contra))

        # Muestra el formulario
        return render_template('nuevaContra.html', Token_Contra=Token_Contra)

    except ExpiredSignatureError:
        return 'Error: Token ha expirado, solicita uno nuevo'
    except InvalidTokenError:
        return 'Error: Token inválido, solicita uno nuevo'
    except Exception as e:
        return f'Error inesperado: {str(e)}'


# Configuración del manejo de errores


def status_401(error):
    return redirect(url_for('login'))


def status_404(error):
    return "<h1>Esta página no existe</h1>", 404


# Configuración y ejecución del sistema como el llamado al módulo "configuración"
if __name__ == '__main__':
    Token.init_app(app)
    app.register_error_handler(401, status_401)
    app.register_error_handler(404, status_404)
    app.run(debug=True)
