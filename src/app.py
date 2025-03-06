# Importación de librerias para el proyecto
from datetime import datetime, date, timedelta
import os
import sys
import json
import subprocess
import threading
import uuid
import pymysql
import torch
import cv2
import time
from pathlib import Path
from flask_mail import Mail, Message
from flask_mysqldb import MySQL, MySQLdb
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_wtf.csrf import CSRFProtect
from flask_jwt_extended import create_access_token, JWTManager, decode_token
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from werkzeug.security import generate_password_hash
from config import configuracion
from Models.ModeloUsuario import ModeloUsuario
from PIL import Image

# Inicialización de la Aplicación
app = Flask(__name__)

# Uso de las configuraciones del archivo "config.py" para BD y Mail
app.config.from_object(configuracion['desarrollo'])
app.config.update(configuracion['codigoR'].__dict__)

# Conexión para el servidor de correo electrónico
Correo = Mail(app)
# Creación del Token de seguridad
Token = CSRFProtect()
Token.init_app(app)

# Conexion a la base de datos
BaseDatos = MySQL(app)
directorio_script = os.path.dirname(os.path.abspath(__file__))

# Configuración de el directorio de Datasets:
UPLOAD_FOLDER = os.path.join(directorio_script, "Datasets")

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Configuración para uso del administrador de correo electrónico
Recu_Contra = JWTManager(app)


# Indicacion para mantener el usuario conectado y mantener su informacion
app_inicio_sesion = LoginManager(app)

# Configuración de la libreria de Load_user para solicitar la información del usuario desde su ID


@app_inicio_sesion.user_loader
def load_user(id):
    return ModeloUsuario.get_by_id(BaseDatos, id)
############################################################################################################
######################################### CONFIGURACIÓN UNIVERSAL ##########################################
############################################################################################################

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


@app.route('/<path:filename>')
def serve_file(filename):
    base_path = os.path.join(directorio_script)
    return send_from_directory(base_path, filename)

# Configuración del módulo para agregar un nuevo usuario sin ininicar sesión


@app.route('/agregarNuevo', methods=['POST'])
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
        cursor.close()
        # Mensaje de guardado correcto
        flash('Nuevo usuario, guardado satisfactoriamente')
        # Al terminar el proceso se redirecciona a la ruta de "New"
        return redirect(url_for('new'))


def get_db_connection():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='',
        database='detector',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )


@app.route('/EjecExperimentador', methods=['POST'])
def EjecExperimentador():
    tecnologia = request.form.get('Tecnologia')
    epocas = request.form.get('epocas')
    batch_size = request.form.get('batch_size')
    threshold = request.form.get('threshold')
    iou_threshold = request.form.get('iou_threshold')
    dataExperimentador = request.form.get('ruta')
    valorTech = request.form.get('valorTech')
    idDataset = request.form.get('idDataset')
    name = request.form.get('name')
    Usuario = current_user.id
    tipoUsuario = current_user.tipo
    ruta = str(Path(dataExperimentador))

    print(f"Tecnología: {tecnologia}, Épocas: {epocas}, Batch size: {batch_size}, Threshold: {threshold}, IOU threshold: {iou_threshold},Ruta: {ruta}, data5: {valorTech}, Nombre: {name},ID dataset:{idDataset},idUsuario: {Usuario}")

    if not all([tecnologia, epocas, batch_size, threshold, iou_threshold, ruta, name, Usuario]):
        return jsonify({'error': 'Faltan valores requeridos'}), 400

    if tecnologia == "YOLO" and valorTech == "YOLO":
        imgsz = request.form.get('imgsz')

        if not all([imgsz]):
            flash('Faltan valores requeridos para YOLO')
            if tipoUsuario == "Tester":
                return redirect(url_for('experimentadorT'))
            if tipoUsuario == "Administrador":
                return redirect(url_for('experimentadorA'))

        task_id = f"yolo_{Usuario}_{int(time.time())}"

        # Guarda la información de la tarea
        if not hasattr(app, 'task_status'):
            app.task_status = {}

        app.task_status[task_id] = {
            "status": "running",
            "mensaje": "Entrenando YoloV5",
            "tipoUsuario": tipoUsuario,
            "completado": False
        }

        # Función wrapper para actualizar el estado al finalizar
        def run_yolo():
            try:
                YOLO(epocas, batch_size, threshold, iou_threshold,
                     imgsz, ruta, name, idDataset, Usuario, tipoUsuario)
            finally:
                app.task_status[task_id]["completado"] = True

        # Inicia el hilo para entrenar YOLO
        thread = threading.Thread(target=run_yolo)
        thread.daemon = True
        thread.start()

        return jsonify({
            'mensaje': "Entrenando YoloV5",
            'task_id': task_id
        })

    elif tecnologia == "TRANS" and valorTech == "Transformer":

        # Genera un ID único para esta tarea
        task_id = f"transformer_{Usuario}_{int(time.time())}"

        # Guarda la información de la tarea
        if not hasattr(app, 'task_status'):
            app.task_status = {}

        app.task_status[task_id] = {
            "status": "running",
            "mensaje": "Entrenando Transformer",
            "tipoUsuario": tipoUsuario,
            "completado": False
        }

        # Función wrapper para actualizar el estado al finalizar
        def run_transformer():
            try:
                Transformers(epocas, batch_size, threshold, iou_threshold,
                             ruta, name, idDataset, Usuario, tipoUsuario)
            finally:
                app.task_status[task_id]["completado"] = True

        # Inicia el hilo para entrenar TRANSFORMER
        thread = threading.Thread(target=run_transformer)
        thread.daemon = True
        thread.start()

        return jsonify({
            'mensaje': "Entrenando Transformer",
            'task_id': task_id
        })

    else:
        return jsonify({
            'error': 'La tecnología seleccionada no coincide con la tecnología del dataset.'
        }), 400


def YOLO(epocas, batch_size, threshold, iou_threshold, imgsz, ruta, name, idDataset, Usuario, tipoUsuario):
    env = os.environ.copy()
    env['CONF_THRES'] = str(threshold)
    env['IOU_THRES'] = str(iou_threshold)
    env['RUTA'] = ruta
    arquitecturaModelo = "YOLOV5"

    print(
        f"Iniciando YOLO con los siguientes parámetros: Epocas:{epocas}, BS:{batch_size}, IMG:{imgsz}, RutaDataset:{ruta}, Nombre:{name},ID_Usuario:{Usuario},IDDAtaset:{idDataset},Confianza:{threshold},Interseccón:{iou_threshold},Arquitectura:{arquitecturaModelo},TipoUsuario:{tipoUsuario}")

    directorio_base = os.path.dirname(
        directorio_script)

    ruta_python = sys.executable

    ruta_yolo = os.path.join(directorio_base, "src",
                             "Models", "YoloV5", "YOLOV5.py")

    subprocess.run([ruta_python,
                    ruta_yolo,
                    '--epochs', str(epocas),
                    '--batch-size', str(batch_size),
                    '--imgsz', str(imgsz),
                    '--name', name],
                   shell=True, check=True, env=env)

    ruta_pJson = os.path.join(directorio_script, "Pesos", "YOLO")

    ruta_json = os.path.join(ruta_pJson, name, "metricas.json")

    if os.path.exists(ruta_json):
        with open(ruta_json, 'r') as archivo_resultados:
            resultados = json.load(archivo_resultados)

        tiempoEjecutado = resultados.get("tiempo_formateado")
        precisionExperimento = resultados.get("ap_50")
        errorExperimento = resultados.get("error_50")
        direccionCompleta = resultados.get("direccion")

        db_connection = get_db_connection()
        try:
            with db_connection.cursor() as cursor:
                cursor.execute("""
                INSERT INTO experimentador (idUsuarios, idDataSetExp, NombreModelo, Arquitectura, PorcentajeErr, `Precision`, TiempoHoras, Pesos)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (Usuario, idDataset, name, arquitecturaModelo, errorExperimento, precisionExperimento, tiempoEjecutado, direccionCompleta))
                db_connection.commit()

                cursor.execute("SELECT nombre, correo FROM usuarios")
                usuarios = cursor.fetchall()

                for usuario in usuarios:
                    nombre_usuario = usuario[0]
                    email_usuario = usuario[1]
                    notificar_nuevo_modelo(
                        email_usuario, nombre_usuario, name, precisionExperimento, arquitecturaModelo)

        finally:
            db_connection.close()
    else:
        print("El archivo metricas.json no existe.")

    flash('Entrenamiento de YOLO ha finalizado y resultados guardados.')


def Transformers(epocas, batch_size, threshold, iou_threshold, ruta, name, idDataset, Usuario, tipoUsuario):
    arquitecturaModelo = "Transformer"

    print(
        f"Iniciando DETR con los siguientes parámetros: Epocas:{epocas}, BS:{batch_size}, RutaDataset:{ruta}, Nombre:{name},ID_Usuario:{Usuario},IDDAtaset:{idDataset},Confianza:{threshold},Interseccón:{iou_threshold},Arquitectura:{arquitecturaModelo},TipoUsuario:{tipoUsuario}")

    directorio_base = os.path.dirname(
        directorio_script)  # O ajusta según necesites

# Usar sys.executable para obtener la ruta al intérprete de Python actual
    # Esto te da la ruta del intérprete que está ejecutando este código
    ruta_python = sys.executable

    # Construir la ruta al script detect.py
    ruta_Transformer = os.path.join(
        directorio_base, "src", "Models", "Transformers", "Transformer.py")

    subprocess.run([ruta_python,
                    ruta_Transformer,
                    '--epocas', epocas, '--batch_size', batch_size, '--threshold', threshold,
                    '--iou_threshold', iou_threshold, '--ruta', ruta, '--name', name], shell=True, check=True)

    ruta_json = os.path.join(directorio_base, "Pesos",
                             "Transformers", name, "metricas.json")

    if os.path.exists(ruta_json):
        with open(ruta_json, 'r') as archivo_resultados:
            resultados = json.load(archivo_resultados)

        tiempoEjecutado = resultados.get("tiempo_formateado")
        precisionExperimento = resultados.get("ap_50")
        errorExperimento = resultados.get("error_50")
        direccionCompleta = resultados.get("direccion")

        db_connection = get_db_connection()
        try:
            with db_connection.cursor() as cursor:
                cursor.execute("""
                INSERT INTO experimentador (idUsuarios, idDataSetExp, NombreModelo, Arquitectura, PorcentajeErr, `Precision`, TiempoHoras, Pesos)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (Usuario, idDataset, name, arquitecturaModelo, errorExperimento, precisionExperimento, tiempoEjecutado, direccionCompleta))
                db_connection.commit()

                cursor.execute("SELECT nombre, correo FROM usuarios")
                usuarios = cursor.fetchall()

                for usuario in usuarios:
                    nombre_usuario = usuario[0]
                    email_usuario = usuario[1]
                    notificar_nuevo_modelo(
                        email_usuario, nombre_usuario, name, precisionExperimento, arquitecturaModelo)

        finally:
            db_connection.close()
    else:
        print("El archivo metricas.json no existe.")

    flash('Entrenamiento de Transformers finalizado y resultados guardados.')


@app.route('/check_task_status/<task_id>', methods=['GET'])
def check_task_status(task_id):
    if not hasattr(app, 'task_status') or task_id not in app.task_status:
        return jsonify({'status': 'unknown'})

    task = app.task_status[task_id]

    if task["completado"]:
        # Determinar la URL de redirección
        if task["tipoUsuario"] == "Tester":
            redirect_url = url_for('experimentadorT')
        else:
            redirect_url = url_for('experimentadorA')

        # Limpiar la tarea después de devolverla
        # del app.task_status[task_id]  # Comentado para que se pueda verificar múltiples veces

        return jsonify({
            'status': 'completed',
            'redirect_url': redirect_url
        })

    return jsonify({
        'status': 'running',
        'mensaje': task["mensaje"]
    })


@app.route('/check_task_statusEval/<task_id>', methods=['GET'])
def check_task_statusEval(task_id):
    if not hasattr(app, 'task_status') or task_id not in app.task_status:
        return jsonify({'status': 'unknown'})

    task = app.task_status[task_id]

    if task["completado"]:  # Cuando la tarea finaliza
        return jsonify({
            "status": "completed",
            "mensaje": "Evaluación concluida exitosamente.",
            "redirect_url": url_for('resultadosA')  # Redirige a resultadosA
        })

    return jsonify({
        'status': 'running',
        'mensaje': task["mensaje"]
    })

################################################################################################################################################ SECCIÓN PARA ENVIO DE CORREO######################################## ###########################################################################################################

# Ruta que se ejecuta al momento de llamar en el formulario de la vista "nuevaContra.html" para buscar el correo y enviar el enlace de recuperación de contraseña


@app.route('/buscar_correo', methods=['POST'])
def buscar_correo():
    # Se obtiene el correo del formulario
    if request.method == 'POST':
        correo = request.form['correo']
        # Se crea el cursor para la conexión a la base de datos
        cursor = BaseDatos.connection.cursor()
        # Se crea la sentencia SQL para buscar el correo en la base de datos
        sql = "SELECT idUsuarios FROM usuarios WHERE correo = %s"
        # Se ejecuta la sentencia SQL con el cursor
        cursor.execute(sql, (correo,))
        # Se hace el envío de los datos
        BaseDatos.connection.commit()
        # Se obtiene el resultado de la sentencia SQL
        resultado = cursor.fetchone()
        # Se cierra el cursor
        cursor.close()

        # Se verifica si el correo existe en la base de datos
        if resultado:
            # Se crea el token para la recuperación de contraseña el cual se configura para expirar en 24 horas
            id_usuario = resultado[0]
            Token_Contra = create_access_token(
                identity=id_usuario, expires_delta=timedelta(hours=24))
            # Se envía el correo con el enlace de recuperación por medio del método "enviar_correo_recuperacion"
            enviar_correo_recuperacion(correo, Token_Contra)
            # Se envía un mensaje de éxito y se redirige a la vista de recuperación
            flash('Se ha enviado el enlace para recuperar tu contraseña al correo.')
            return redirect(url_for('recuperacion'))
        else:
            # En caso de que el correo no exista en la base de datos se envía un mensaje de error y se redirige a la vista de recuperación
            flash('El correo electrónico no esta registrado')
            return redirect(url_for('recuperacion'))

# Configurar el método para enviar el correo electrónico con el enlace de recuperación de contraseña


def enviar_correo_recuperacion(correo, Token_Contra):
    # Se configura el mensaje del correo el cual contiene el asunto, el remitente, el destinatario y el enlace de recuperación
    mensaje = Message(
        subject='Recuperar contraseña',
        sender='Estadia-AVAO191844<r-emmanuel_n@hotmail.com>',
        recipients=[correo],
        html=f'Haz clic en el siguiente enlace para restablecer tu contraseña:{url_for("nuevaContra", Token_Contra=Token_Contra, _external=True)}'
    )
    try:
        # Se envía el correo
        Correo.send(mensaje)
        # Se imprime un mensaje de éxito en la consola
        print(f'Correo enviado a {correo}')
    # En caso de que ocurra un error al enviar el correo se imprime un mensaje de error en la consola
    except Exception as e:
        print(f'Error al enviar el correo: {e}')
        raise  # Se lanza una excepción

# Configuración de la ruta para la nueva contraseña


@app.route('/nuevaContra/<Token_Contra>', methods=['GET', 'POST'])
def nuevaContra(Token_Contra):
    try:
        # Se verifica el token y extrae el ID del usuario
        token_data = decode_token(Token_Contra)
        id_usuario = token_data['sub']

        if request.method == 'POST':
            # Se obtiene la nueva contraseña del formulario
            nueva_contra = request.form['nuevac']
            confirmar_contra = request.form['confirmar_nuevac']

            if not nueva_contra or not confirmar_contra:
                flash('Por favor, rellena todos los campos')
                return redirect(url_for('nuevaContra', Token_Contra=Token_Contra))

            # Se verifica si ambas contraseñas coinciden
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

    # En caso de que el token haya expirado se menciona en un mensaje y se redirige a la vista de recuperación
    except ExpiredSignatureError:
        return 'Error: Token ha expirado, solicita uno nuevo'
    # En caso de que ocurra un error inesperado se menciona en un mensaje y se redirige a la vista de recuperación
    except InvalidTokenError:
        return 'Error: Token inválido, solicita uno nuevo'
    except Exception as e:
        return f'Error inesperado: {str(e)}'


def enviar_correo_notificacion(email_usuario, nombre_usuario, modificaciones):
    msg = Message('Notificación de actualización de cuenta',
                  sender='Estadia-AVAO191844<r-emmanuel_n@hotmail.com>',
                  recipients=[email_usuario])
    msg.body = f"Hola {nombre_usuario},\n\nTu cuenta ha sido modificada recientemente con los siguientes cambios:\n\n" + \
               "\n".join(modificaciones) + \
               "\n\nSi no realizaste estos cambios, por favor contacta al administrador."

    Correo.send(msg)


def notificar_nuevo_modelo(email_usuario, nombre_usuario, nombre_modelo, precision, modelo):
    msg = Message('Nuevo Modelo Disponible - Sistema de Detección de Basura',
                  sender='Estadia-AVAO191844<r-emmanuel_n@hotmail.com>',
                  recipients=[email_usuario])

    msg.body = f"""Hola {nombre_usuario},

Se ha generado un nuevo modelo de {modelo} llamado {nombre_modelo}, con una Precisión de {precision} en el Sistema de Detección de Basura en Imágenes Estáticas.
Accede al sistema para utilizarlo en tus proyectos de detección de basura.

Tesis - AVAO191844"""

    Correo.send(msg)
###########################################################################################################
##################################### CONFIGURACIÓN ADMINISTRADOR #########################################
############################################################################################################

# Configuración de la ruta para acceso de Administrador, siendo asegurada por medio de la libreria de "Login_Required"


@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    return render_template('admin/admin.html')


@app.route('/nuevoUsuarioA')
@login_required
def nuevoUsuarioA():
    return render_template('admin/nuevoUsuarioA.html')


@app.route('/tiposBasuraA')
@login_required
def tiposBasuraA():
    return render_template('admin/tiposBasuraA.html')


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
            d.Tecnologia,
            d.Ruta,
            d.idDataSetExp
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


@app.route('/reportesA')
@login_required
def reportesA():
    cursor = BaseDatos.connection.cursor()
    cursor.execute("""
        SELECT
            NombreEvaluacion, TiempoMinYOLO, ErrorYOLO, PrecisionYOLO, SensibilidadYOLO, EspecifidadYOLO, TiempoMinDETR, ErrorDETR, PrecisionDETR, SensibilidadDETR, EspecifidadDETR
        FROM
            evaluacion""")

    evaluaciones = cursor.fetchall()
    cursor.close()
    datos_graficos = [
        {
            'nombre': eval[0],
            'tiempo_yolo': eval[1].total_seconds() / 60 if isinstance(eval[1], timedelta) else float(eval[1]),
            'error_yolo': float(eval[2]) if eval[2] else 0,
            'precision_yolo': float(eval[3]) if eval[3] else 0,
            'sensibilidad_yolo': float(eval[4]) if eval[4] else 0,
            'especifidad_yolo': float(eval[5]) if eval[5] else 0,
            'tiempo_detr': eval[6].total_seconds() / 60 if isinstance(eval[6], timedelta) else float(eval[6]),
            'error_detr': float(eval[7]) if eval[7] else 0,
            'precision_detr': float(eval[8]) if eval[8] else 0,
            'sensibilidad_detr': float(eval[9]) if eval[9] else 0,
            'especifidad_detr': float(eval[10]) if eval[10] else 0
        }
        for eval in evaluaciones]
    return render_template('admin/reportesA.html', evaluaciones=evaluaciones, datos_graficos=datos_graficos)


@app.route('/crudBasuraA')
@login_required
def crudBasuraA():
    cursor = BaseDatos.connection.cursor()
    cursor.execute('SELECT * FROM tiposbasura')
    basuras = cursor.fetchall()
    cursor.close()
    return render_template('admin/tiposBasuraA.html', basuras=basuras)


@app.route('/eliminarBasuraA/<string:tipoBasura>')
def eliminarBasuraA(tipoBasura):
    cursor = BaseDatos.connection.cursor()
    cursor.execute(
        'DELETE FROM tiposbasura WHERE tipoBasura = %s', (tipoBasura,))
    BaseDatos.connection.commit()
    cursor.close()
    flash('Registro de basura eliminado satisfactoriamente')
    return redirect(url_for('crudBasuraA'))


@app.route('/editarBasuraA/<string:tipoBasura>')
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


@app.route('/editarBasuraAdmin/<string:tipoBasura>', methods=['POST'])
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
        cursor.close()
        flash('Tipo de basura actualizado satisfactoriamente')
        return redirect(url_for('crudBasuraA'))


@app.route('/agregarNuevoA', methods=['POST'])
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
        cursor.close()
        flash('Nuevo usuario, guardado satisfactoriamente')
        return redirect(url_for('nuevoUsuarioA'))


@app.route('/agregarBasura', methods=['POST'])
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
        cursor.close()
        flash('Nueva información, guardada satisfactoriamente')
        return redirect(url_for('crudBasuraA'))


@app.route('/crudUsuarioA')
@login_required
def crudUsuarioA():
    cursor = BaseDatos.connection.cursor()
    cursor.execute('SELECT * FROM usuarios')
    usuarios = cursor.fetchall()
    cursor.close()
    return render_template('admin/crudUsuarioA.html', usuarios=usuarios)


@app.route('/eliminarA/<string:correo>')
def eliminarA(correo):
    cursor = BaseDatos.connection.cursor()
    cursor.execute(
        'DELETE FROM usuarios WHERE Correo = %s', (correo,))
    BaseDatos.connection.commit()
    cursor.close()
    flash('Usuario eliminado satisfactoriamente')
    return redirect(url_for('crudUsuarioA'))


@app.route('/editarA/<string:correo>')
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


@app.route('/editarUsuarioA/<string:correo>', methods=['POST'])
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
        cursor.close()

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

        enviar_correo_notificacion(nuevo_correo, nombre, modificaciones)

        flash('Contacto actualizado satisfactoriamente. <br> Modificaciones realizadas:<br>' + '<br>'.join(
            modificaciones))

        return redirect(url_for('crudUsuarioA'))


@app.route('/evaluadorA')
def evaluadorA():
    cursor = BaseDatos.connection.cursor()
    cursor.execute("""
        SELECT
            e.NombreModelo,
            e.Arquitectura,
            e.PorcentajeErr,
            e.Precision,
            e.TiempoHoras,
            e.Pesos,
            u.Nombre AS NombreUsuario
        FROM
            experimentador e
        INNER JOIN
            Usuarios u ON e.idUsuarios = u.idUsuarios
        WHERE
            e.Arquitectura = 'YOLOV5'
    """)

    pesosY = cursor.fetchall()
    cursor.execute("""
        SELECT
            e.NombreModelo,
            e.Arquitectura,
            e.PorcentajeErr,
            e.Precision,
            e.TiempoHoras,
            e.Pesos,
            u.Nombre AS NombreUsuario
        FROM
            experimentador e
        INNER JOIN
            Usuarios u ON e.idUsuarios = u.idUsuarios
        WHERE
            e.Arquitectura = 'Transformer'
    """)

    pesosT = cursor.fetchall()
    cursor.execute("""
        SELECT d.idDataSetPrueba,d.NombreData, d.Formato, d.Cantidad, u.Nombre, tb.TipoBasura,d.Ruta
        FROM
            datasetprueba d
        INNER JOIN
            Usuarios u ON d.idUsuarios = u.idUsuarios
        INNER JOIN
            TiposBasura tb ON d.idTiposBasura = tb.idTiposBasura
    """)

    databasuras = cursor.fetchall()
    cursor.close()
    return render_template('admin/evaluadorA.html', pesosY=pesosY, pesosT=pesosT, databasuras=databasuras)


@app.route('/evaluarA', methods=['POST'])
def evaluarA():
    tipoUsuario = current_user.tipo
    idDataset_seleccionado = request.form.get('datasetId')
    dataset_seleccionado = request.form.get('dataset')
    PesoYolo = request.form.get('PesoY')
    PesoDETR = request.form.get('PesoT')
    nombre_evaluacion = request.form.get('nombre_evaluacion')

    session['idDatasetPrueba'] = idDataset_seleccionado
    session['nombre_evaluacion'] = nombre_evaluacion

    if not nombre_evaluacion or not dataset_seleccionado or not PesoYolo or not PesoDETR:
        if tipoUsuario == "Tester":
            return jsonify({"error": "Todos los campos son obligatorios", "redirect": url_for('evaluadorT')})
        if tipoUsuario == "Administrador":
            return jsonify({"error": "Todos los campos son obligatorios", "redirect": url_for('evaluadorA')})

    print("Peso de YOLO: ", PesoYolo)
    print("Peso de DETR: ", PesoDETR)

    # Crear identificador único para la tarea
    task_id = str(uuid.uuid4())

    if not hasattr(app, 'task_status'):
        app.task_status = {}

    app.task_status[task_id] = {
        "status": "running",
        "mensaje": "Iniciando evaluación...",
        "completado": False,
        "tipoUsuario": tipoUsuario
    }
    directorio_base = os.path.join(
        directorio_script, "Evaluaciones", nombre_evaluacion)

    directorio_yolo = os.path.join(directorio_base, 'YOLO')
    os.makedirs(directorio_yolo, exist_ok=True)

    directorio_detr = os.path.join(directorio_base, 'DETR')
    os.makedirs(directorio_detr, exist_ok=True)

    session['directorio_yolo'] = os.path.join(directorio_yolo, 'exp')
    session['directorio_detr'] = directorio_detr

    print(
        f"Los valores que escojiste son: Dataset: '{dataset_seleccionado}', \nPeso de YOLO: '{PesoYolo}', \nPeso DETR: '{PesoDETR}' \nY los directorios son: \n'{directorio_yolo}',\n'{directorio_detr}'")

    def ejecutarEvaluacion(task_id):
        try:
            app.task_status[task_id]["mensaje"] = "Evaluando con YOLO..."
            print("Iniciando evaluación de YOLO...")

            inicio_yolo = time.time()

            # Esto te da la ruta del intérprete que está ejecutando este código
            ruta_python = sys.executable

# Construir la ruta al script detect.py
            ruta_resultadoYOLO = os.path.join(
                directorio_script, "EvaluarYOLO.py")

            resultado_yolo = subprocess.run([
                ruta_python,
                ruta_resultadoYOLO,
                "--weights", PesoYolo, "--source", dataset_seleccionado, "--guardado", directorio_yolo
            ], shell=True, capture_output=True, text=True, check=True)

            if resultado_yolo.returncode == 0:
                app.task_status[task_id]["mensaje"] = "Evaluación de YOLO completada."
                tiempo_yolo_segundos = time.time() - inicio_yolo
                horas_yolo, resto_segundos = divmod(
                    int(tiempo_yolo_segundos), 3600)
                minutos_yolo, segundos_yolo = divmod(resto_segundos, 60)
                tiempo_yolo_formateado = f"{horas_yolo:02}:{minutos_yolo:02}:{segundos_yolo:02}"

            else:
                app.task_status[task_id]["mensaje"] = "Error al ejecutar YOLO."
                raise Exception(resultado_yolo.stderr)

            app.task_status[task_id]["mensaje"] = "Evaluando con DETR..."

            inicio_detr = time.time()

            ruta_python = sys.executable

            ruta_resultadoDETR = os.path.join(
                directorio_script, "EvaluarDETR.py")

            resultado_detr = subprocess.run([
                ruta_python,
                ruta_resultadoDETR,
                "--weights", PesoDETR, "--source", dataset_seleccionado, "--guardado", directorio_detr
            ], shell=True, capture_output=True, text=True, check=True)

            if resultado_detr.returncode == 0:
                app.task_status[task_id]["mensaje"] = "Evaluación de DETR completada."
                tiempo_detr_segundos = time.time() - inicio_detr
                horas_detr, resto_segundos_detr = divmod(
                    int(tiempo_detr_segundos), 3600)
                minutos_detr, segundos_detr = divmod(resto_segundos_detr, 60)
                tiempo_detr_formateado = f"{horas_detr:02}:{minutos_detr:02}:{segundos_detr:02}"

            else:
                app.task_status[task_id]["mensaje"] = "Error al ejecutar DETR."
                raise Exception(resultado_detr.stderr)

            app.task_status[task_id]["status"] = "completed"
            app.task_status[task_id]["completado"] = True

        except Exception as e:
            app.task_status[task_id]["mensaje"] = str(e)
            app.task_status[task_id]["status"] = "error"

        finally:
            datos_evaluacion = {
                "nombre_evaluacion": nombre_evaluacion,
                "tiempo_ejecucion_yolo": tiempo_yolo_formateado,
                "tiempo_ejecucion_detr": tiempo_detr_formateado
            }

            ruta_json = os.path.join(
                directorio_base, "MetricasEvaluacion.json")

            # Crear directorio si no existe
            os.makedirs(directorio_base, exist_ok=True)
            with open(ruta_json, 'w', encoding='utf-8') as archivo_json:
                json.dump(datos_evaluacion, archivo_json,
                          indent=4, ensure_ascii=False)

            print(f"Archivo JSON creado en: {ruta_json}")

    hilo = threading.Thread(target=ejecutarEvaluacion, args=(task_id,))
    hilo.start()

    return jsonify({"task_id": task_id})


@app.route('/resultadosA')
def resultadosA():
    tipoUsuario = current_user.tipo
    # Directorios de las imágenes
    yolo_dir = session.get('directorio_yolo')
    detr_dir = session.get('directorio_detr')

    directorio_base = os.path.join(directorio_script)

    yolo_relative_dir = os.path.relpath(yolo_dir, directorio_base)
    detr_relative_dir = os.path.relpath(detr_dir, directorio_base)

    print("Directorio Yolo: ", yolo_relative_dir,
          "\n", "Directorio DETR: ", detr_relative_dir)

    if not yolo_dir or not detr_dir:
        flash("No se encontraron directorios de resultados. Por favor, realiza una evaluación primero.")
        if tipoUsuario == "Tester":
            return redirect(url_for('evaluadorT'))
        if tipoUsuario == "Administrador":
            return redirect(url_for('evaluadorA'))

    # Listar las imágenes de ambos directorios
    yolo_images = [os.path.join(yolo_relative_dir, img).replace(
        "\\", "/") for img in os.listdir(yolo_dir) if img.endswith(('.png', '.jpg', '.jpeg'))]
    detr_images = [os.path.join(detr_relative_dir, img).replace(
        "\\", "/") for img in os.listdir(detr_dir) if img.endswith(('.png', '.jpg', '.jpeg'))]

    yolo_images.sort()
    detr_images.sort()

    session['num_imagenes_yolo'] = len(yolo_images)
    session['num_imagenes_detr'] = len(detr_images)

    # Pasar las rutas de imágenes a la plantilla
    if tipoUsuario == "Tester":
        return render_template('test/resultadosT.html', yolo_images=yolo_images, detr_images=detr_images, zip=zip)
    if tipoUsuario == "Administrador":
        return render_template('admin/resultados.html', yolo_images=yolo_images, detr_images=detr_images, zip=zip)


@app.route('/GuardarEvaluacion', methods=['POST'])
def GuardarEvaluacion():
    tipoUsuario = current_user.tipo
    nombre_evaluacion = session.get('nombre_evaluacion')
    idPrueba = session.get('idDatasetPrueba')

    directorio_base = os.path.join(
        directorio_script, "Evaluaciones", nombre_evaluacion)

    if not nombre_evaluacion:
        flash("No se encontró el nombre de la evaluación en la sesión.")
        if tipoUsuario == "Tester":
            return redirect(url_for('evaluadorT'))
        if tipoUsuario == "Administrador":
            return redirect(url_for('evaluadorA'))

    try:
        # Ruta del archivo JSON
        ruta_json = os.path.join(directorio_base, "MetricasEvaluacion.json")
        datos_evaluacion = {}  # Inicializar por si no existe el JSON

        # Cargar el archivo JSON existente (si existe)
        if os.path.exists(ruta_json):
            with open(ruta_json, 'r', encoding='utf-8') as archivo_json:
                datos_evaluacion = json.load(archivo_json)

        num_imagenes_yolo = session.get('num_imagenes_yolo', 0)
        num_imagenes_detr = session.get('num_imagenes_detr', 0)

        # Validar que existen valores
        if num_imagenes_yolo == 0 or num_imagenes_detr == 0:
            flash("Error: No se encontró el número de imágenes en la sesión.")
            return redirect(url_for('resultadosA'))

        # Contadores
        TP_yolo = FN_yolo = FP_yolo = TN_yolo = 0
        TP_detr = FN_detr = FP_detr = TN_detr = 0
        faltan_veredictos = False

        # Procesar cada imagen (usar el número real de imágenes)
        for i in range(1, num_imagenes_yolo + 1):
            veredicto_yolo = request.form.get(f'yolo_veredicto_{i}')
            if not veredicto_yolo:
                faltan_veredictos = True
            else:
                veredicto_yolo = int(veredicto_yolo)
                if veredicto_yolo == 1:
                    TP_yolo += 1
                elif veredicto_yolo == 2:
                    FN_yolo += 1
                elif veredicto_yolo == 3:
                    FP_yolo += 1
                elif veredicto_yolo == 4:
                    TN_yolo += 1

        for i in range(1, num_imagenes_detr + 1):
            veredicto_detr = request.form.get(f'detr_veredicto_{i}')
            if not veredicto_detr:
                faltan_veredictos = True
            else:
                veredicto_detr = int(veredicto_detr)
                if veredicto_detr == 1:
                    TP_detr += 1
                elif veredicto_detr == 2:
                    FN_detr += 1
                elif veredicto_detr == 3:
                    FP_detr += 1
                elif veredicto_detr == 4:
                    TN_detr += 1

        if faltan_veredictos:
            flash("Debes seleccionar todos los veredictos.")
            return redirect(url_for('resultadosA'))

        # Calcular métricas (función mejorada)
        def calcular_metricas(TP, FN, FP, TN):
            total = TP + FN + FP + TN
            precision = TP / (TP + FP) if (TP + FP) > 0 else 0
            sensibilidad = TP / (TP + FN) if (TP + FN) > 0 else 0
            especificidad = TN / (TN + FP) if (TN + FP) > 0 else 0
            error = (FP + FN) / total if total > 0 else 0
            return [precision, error, sensibilidad, especificidad]

        # Aplicar redondeo
        metricas_yolo = [round(
            val * 100, 2) for val in calcular_metricas(TP_yolo, FN_yolo, FP_yolo, TN_yolo)]
        metricas_detr = [round(
            val * 100, 2) for val in calcular_metricas(TP_detr, FN_detr, FP_detr, TN_detr)]

        # Insertar en BD (MEJORA: Usar parámetros para seguridad)
        sql = """INSERT INTO evaluacion (
                    idDataSetPrueba, NombreEvaluacion, 
                    TiempoMinYOLO, ErrorYOLO, PrecisionYOLO, SensibilidadYOLO, EspecifidadYOLO,
                    TiempoMinDETR, ErrorDETR, PrecisionDETR, SensibilidadDETR, EspecifidadDETR
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        valores = (
            idPrueba, nombre_evaluacion,
            datos_evaluacion.get(
                "tiempo_ejecucion_yolo", 0), metricas_yolo[1], metricas_yolo[0], metricas_yolo[2], metricas_yolo[3],
            datos_evaluacion.get(
                "tiempo_ejecucion_detr", 0), metricas_detr[1], metricas_detr[0], metricas_detr[2], metricas_detr[3]
        )

        cursor = BaseDatos.connection.cursor()
        cursor.execute(sql, valores)
        BaseDatos.connection.commit()
        cursor.close()

        flash("¡Evaluación guardada correctamente!")
        if tipoUsuario == "Tester":
            return redirect(url_for('reportesT'))
        if tipoUsuario == "Administrador":
            return redirect(url_for('reportesA'))

    except Exception as e:
        flash(f"Error grave: {str(e)}")
        if tipoUsuario == "Tester":
            return redirect(url_for('reportesT'))
        if tipoUsuario == "Administrador":
            return redirect(url_for('reportesA'))

############################################################################################################
######################################### CONFIGURACIÓN TESTER #############################################
############################################################################################################


@app.route('/tester', methods=['GET', 'POST'])
@login_required
def tester():
    return render_template('test/Tester.html')


@app.route('/experimentadorT')
@login_required
def experimentadorT():
    Usuario = current_user.id
    cursor = BaseDatos.connection.cursor()
    cursor.execute("""
        SELECT
            d.NombreDataExp,
            d.FormatoExp,
            d.Imagenes,
            tb.TipoBasura,
            d.Tecnologia,
            d.Ruta,
            d.idDataSetExp
        FROM
            dataexperiment d
        INNER JOIN
            TiposBasura tb ON d.idTiposBasura = tb.idTiposBasura
        WHERE
            idUsuarios = %s
    """, (Usuario,))

    datas = cursor.fetchall()
    cursor.close()
    return render_template('test/experimentadorT.html', datas=datas)


@app.route('/evaluadorT')
@login_required
def evaluadorT():
    cursor = BaseDatos.connection.cursor()
    cursor.execute("""
        SELECT
            e.NombreModelo,
            e.Arquitectura,
            e.PorcentajeErr,
            e.Precision,
            e.TiempoHoras,
            e.Pesos,
            u.Nombre AS NombreUsuario
        FROM
            experimentador e
        INNER JOIN
            Usuarios u ON e.idUsuarios = u.idUsuarios
        WHERE
            e.Arquitectura = 'YOLOV5'
    """)
    pesosY = cursor.fetchall()

    cursor.execute("""
        SELECT
            e.NombreModelo,
            e.Arquitectura,
            e.PorcentajeErr,
            e.Precision,
            e.TiempoHoras,
            e.Pesos,
            u.Nombre AS NombreUsuario
        FROM
            experimentador e
        INNER JOIN
            Usuarios u ON e.idUsuarios = u.idUsuarios
        WHERE
            e.Arquitectura = 'Transformer'
    """)
    pesosT = cursor.fetchall()

    cursor.execute("""
        SELECT d.idDataSetPrueba,d.NombreData, d.Formato, d.Cantidad, u.Nombre, tb.TipoBasura,d.Ruta
        FROM
            datasetprueba d
        INNER JOIN
            Usuarios u ON d.idUsuarios = u.idUsuarios
        INNER JOIN
            TiposBasura tb ON d.idTiposBasura = tb.idTiposBasura
        WHERE
            u.idUsuarios = %s
    """, (current_user.id,))

    databasuras = cursor.fetchall()
    cursor.close()
    return render_template('test/evaluadorT.html', pesosY=pesosY, pesosT=pesosT, databasuras=databasuras)


@app.route('/reportesT')
@login_required
def reportesT():
    cursor = BaseDatos.connection.cursor()
    cursor.execute("""
        SELECT
            NombreEvaluacion, TiempoMinYOLO, ErrorYOLO, PrecisionYOLO, SensibilidadYOLO, EspecifidadYOLO, TiempoMinDETR, ErrorDETR, PrecisionDETR, SensibilidadDETR, EspecifidadDETR
        FROM
            evaluacion""")

    evaluaciones = cursor.fetchall()
    cursor.close()
    datos_graficos = [
        {
            'nombre': eval[0],
            'tiempo_yolo': eval[1].total_seconds() / 60 if isinstance(eval[1], timedelta) else float(eval[1]),
            'error_yolo': float(eval[2]) if eval[2] else 0,
            'precision_yolo': float(eval[3]) if eval[3] else 0,
            'sensibilidad_yolo': float(eval[4]) if eval[4] else 0,
            'especifidad_yolo': float(eval[5]) if eval[5] else 0,
            'tiempo_detr': eval[6].total_seconds() / 60 if isinstance(eval[6], timedelta) else float(eval[6]),
            'error_detr': float(eval[7]) if eval[7] else 0,
            'precision_detr': float(eval[8]) if eval[8] else 0,
            'sensibilidad_detr': float(eval[9]) if eval[9] else 0,
            'especifidad_detr': float(eval[10]) if eval[10] else 0
        }
        for eval in evaluaciones]
    return render_template('test/reportesT.html', evaluaciones=evaluaciones, datos_graficos=datos_graficos)


@app.route('/crudUsuarioT')
@login_required
def crudUsuarioT():
    return render_template('test/crudUsuarioT.html')


@app.route('/editarUsuarioT/<string:correo>', methods=['POST'])
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
        cursor.close()

        enviar_correo_notificacion_tester(correo, nombre)

        flash('Contacto actualizado satisfactoriamente')
        return redirect(url_for('crudUsuarioT'))


def enviar_correo_notificacion_tester(email_usuario, nombre_usuario):
    msg = Message('Notificación de actualización de cuenta',
                  sender='Estadia-AVAO191844<r-emmanuel_n@hotmail.com>',
                  recipients=[email_usuario])
    msg.body = f"Hola {nombre_usuario}, \n\nTu cuenta ha sido modificada recientemente \n\n Si no realizaste estos cambios, por favor contacta al administrador."

    Correo.send(msg)


@app.route('/CrudDatasetEval')
@login_required
def CrudDatasetEval():
    cursor = BaseDatos.connection.cursor()
    cursor.execute('SELECT TipoBasura FROM tiposBasura')
    tipos = cursor.fetchall()
    cursor.close()
    return render_template('admin/crudDatasetEval.html', tipos=tipos)


@app.route('/CrudDatasetA')
@login_required
def CrudDatasetA():
    cursor = BaseDatos.connection.cursor()
    cursor.execute('SELECT TipoBasura FROM tiposBasura')
    tipos = cursor.fetchall()
    cursor.close()
    return render_template('admin/crudDatasetPruebaA.html', tipos=tipos)


@app.route('/CrudDatasetT')
@login_required
def CrudDatasetT():
    cursor = BaseDatos.connection.cursor()
    cursor.execute('SELECT TipoBasura FROM tiposBasura')
    tipos = cursor.fetchall()
    cursor.close()
    return render_template('test/crudDatasetPruebaT.html', tipos=tipos)


@app.route('/agregarDataset', methods=['POST'])
def agregarDataset():
    tipoUsuario = current_user.tipo
    archivos = request.files.getlist("Dataset[]")
    nombre_dataset = request.form.get('nombreDataset')
    tecnologia = request.form.get('Tecnologia')
    formato = request.form.get('Formato')
    tipo_basura = request.form.get('tipoBasura')

    # Verificar si los campos están vacíos
    if not all([archivos, nombre_dataset, tecnologia, formato, tipo_basura]):
        flash('Por favor, complete todos los campos')
        if tipoUsuario == 'Administador':
            return redirect(url_for('CrudDatasetA'))
        return redirect(url_for('CrudDatasetT'))

    # Realiza la validación del dataset en función de la tecnología
    validacion_fallida = False
    cantidad_total, cantidad_test = 0, 0

    if tecnologia == "YOLO":
        validacion_fallida, mensaje_error, cantidad_total, cantidad_test = validar_estructura_yolo(
            archivos, formato)
    elif tecnologia == "Transformer":
        validacion_fallida, mensaje_error, cantidad_total, cantidad_test = validar_estructura_transformer(
            archivos, formato)

    # Si la validación falla, regresar a la página y mantener los datos
    if validacion_fallida:
        flash(mensaje_error)
        return redirect(url_for('CrudDatasetA'))

    # Guardar los archivos en el directorio configurado
    if archivos:
        ruta = archivos[0]
        if ruta and ruta.filename != '':
            # Extraer la ruta base (directorio) del primer archivo
            ruta_base = os.path.dirname(ruta.filename)

            # Construir la ruta completa donde se almacenará el directorio
            ruta_guardado = os.path.join(
                app.config['UPLOAD_FOLDER'], ruta_base)

            # Si la tecnología es YOLO, agregar la ruta "test/images"
            if tecnologia == "YOLO":
                ruta_test = os.path.join(ruta_guardado, 'test', 'images')

            # Si la tecnología es Transformer, agregar solo la carpeta "test"
            elif tecnologia == "Transformer":
                ruta_test = os.path.join(ruta_guardado, 'test')

    # Guardar los datos en la base de datos
    guardar_dataset(nombre_dataset, ruta_guardado, formato,
                    tecnologia, tipo_basura, cantidad_total, cantidad_test, ruta_test)

    flash(f"El dataset '{nombre_dataset}' ha sido guardado correctamente.")
    return redirect(url_for('experimentadorA'))


def validar_estructura_yolo(archivos, formato):
    # Ruta base donde se encuentran los datasets
    base_datasets = os.path.join(directorio_script, "Datasets")

    ruta = archivos[0]
    ruta_base = os.path.dirname(ruta.filename)
    ruta_guardado = os.path.join(base_datasets, ruta_base)

    # Diccionario para almacenar las rutas de archivos por carpetas para YOLO
    dataset_estructura_yolo = {
        "train": {"labels": [], "images": []},
        "test": {"labels": [], "images": []},
        "valid": {"labels": [], "images": []}
    }

    error_formato = False
    error_carpeta = False
    formato_correcto = True

    # Procesar todos los archivos recibidos
    for archivo in archivos:
        ruta_relativa = archivo.filename

        # Convertir a ruta absoluta agregando la carpeta "Datasets"
        ruta_absoluta = os.path.join(base_datasets, ruta_relativa)

        if 'train/' in ruta_relativa:
            if '/labels/' in ruta_relativa and ruta_relativa.endswith('.txt'):
                dataset_estructura_yolo['train']['labels'].append(
                    ruta_absoluta)
            elif '/images/' in ruta_relativa:
                if ruta_relativa.endswith(formato.lower()):
                    dataset_estructura_yolo['train']['images'].append(
                        ruta_absoluta)
                else:
                    # <-- Depuración
                    print(f"Formato incorrecto en: {ruta_relativa}")
                    error_formato = True
                    formato_correcto = False

        elif 'test/' in ruta_relativa:
            if '/labels/' in ruta_relativa and ruta_relativa.endswith('.txt'):
                dataset_estructura_yolo['test']['labels'].append(ruta_absoluta)
            elif '/images/' in ruta_relativa:
                if ruta_relativa.lower().endswith(formato.lower()):
                    dataset_estructura_yolo['test']['images'].append(
                        ruta_absoluta)
                elif ruta_relativa.lower().endswith('.json'):
                    # Solo para depuración
                    print(f"Ignorando archivo JSON: {ruta_relativa}")
                else:
                    print(f"Formato incorrecto en: {ruta_relativa}")
                    error_formato = True
                    formato_correcto = False

        elif 'valid/' in ruta_relativa:
            if '/labels/' in ruta_relativa and ruta_relativa.endswith('.txt'):
                dataset_estructura_yolo['valid']['labels'].append(
                    ruta_absoluta)
            elif '/images/' in ruta_relativa:
                if ruta_relativa.endswith(formato.lower()):
                    dataset_estructura_yolo['valid']['images'].append(
                        ruta_absoluta)
                else:
                    # <-- Depuración
                    print(f"Formato incorrecto en: {ruta_relativa}")
                    error_formato = True
                    formato_correcto = False

    # Si el formato es incorrecto, regresamos el error
    if error_formato:
        return True, f"Error: No hay ninguna imagen con formato {formato}, Valida nuevamente tu dataset", 0, 0

    # Validar si las carpetas tienen la estructura necesaria
    for carpeta, contenido in dataset_estructura_yolo.items():
        if not contenido['labels'] or not contenido['images']:
            error_carpeta = True

    # Si hay errores en las carpetas, regresamos el error correspondiente
    if error_carpeta:
        return True, f"Error: La carpeta {carpeta} no contiene los archivos necesarios para YOLO", 0, 0

    # Contar imágenes en cada carpeta
    cantidad_train = len(dataset_estructura_yolo['train']['images'])
    cantidad_test = len(dataset_estructura_yolo['test']['images'])
    cantidad_valid = len(dataset_estructura_yolo['valid']['images'])

    # Calcular la cantidad total de imágenes
    cantidad_total = cantidad_train + cantidad_test + cantidad_valid

    # Generar el archivo JSON en la carpeta "test"
    generar_coco_json(dataset_estructura_yolo['test']['images'],
                      dataset_estructura_yolo['test']['labels'], ruta_guardado)

    return False, "", cantidad_total, cantidad_test


def generar_coco_json(imagenes, etiquetas, ruta_base):
    # Ruta para guardar el archivo
    output_json_path = os.path.join(
        ruta_base, "test", "images", "_annotations.coco.json")

    # Inicializar estructura COCO
    coco_format = {
        "images": [],
        "annotations": [],
        "categories": []
    }

    # Agregar la única categoría "Garbage"
    coco_format["categories"].append({
        "id": 0,  # ID único de la categoría
        "name": "Garbage",
        "supercategory": "none"
    })

    # Procesar imágenes y anotaciones
    annotation_id = 1  # ID único para cada anotación
    for img_id, img_path in enumerate(imagenes):
        # Información de la imagen
        img = Image.open(img_path)
        width, height = img.size
        file_name = os.path.basename(img_path)

        coco_format["images"].append({
            "id": img_id,
            "file_name": file_name,
            "height": height,
            "width": width
        })

        # Leer archivo de anotaciones (YOLO)
        label_file = next((etiqueta for etiqueta in etiquetas if os.path.basename(
            etiqueta).split('.')[0] == os.path.splitext(file_name)[0]), None)
        if label_file:
            with open(label_file, 'r') as f:
                for line in f:
                    _, x_center, y_center, bbox_width, bbox_height = map(
                        float, line.strip().split())

                    # Convertir a formato COCO
                    x_min = (x_center - bbox_width / 2) * width
                    y_min = (y_center - bbox_height / 2) * height
                    bbox_width *= width
                    bbox_height *= height

                    coco_format["annotations"].append({
                        "id": annotation_id,
                        "image_id": img_id,
                        "category_id": 0,  # Siempre es "Garbage"
                        "bbox": [x_min, y_min, bbox_width, bbox_height],
                        "area": bbox_width * bbox_height,
                        "segmentation": [],
                        "iscrowd": 0
                    })
                    annotation_id += 1

    # Guardar en un archivo JSON
    with open(output_json_path, 'w') as json_file:
        json.dump(coco_format, json_file, indent=4)

    print(f"Archivo annotations.json generado en {output_json_path}")


def validar_estructura_transformer(archivos, formato):
    # Diccionario para almacenar las rutas de archivos por carpetas para Transformer
    dataset_estructura_transformer = {
        "train": {"images": [], "json": False},
        "test": {"images": [], "json": False},
        "valid": {"images": [], "json": False}
    }

    error_formato = False
    error_carpeta = False
    formato_correcto = True

    # Procesar todos los archivos recibidos
    for archivo in archivos:
        # Obtener la ruta relativa del archivo dentro del directorio
        ruta_relativa = archivo.filename
        # Validación para Transformer
        if 'train/' in ruta_relativa:
            if ruta_relativa.endswith(formato):
                dataset_estructura_transformer['train']['images'].append(
                    ruta_relativa)
            elif ruta_relativa.endswith('.json'):
                dataset_estructura_transformer['train']['json'] = True
            else:
                error_formato = True
                formato_correcto = False

        elif 'test/' in ruta_relativa:
            if ruta_relativa.endswith(formato):
                dataset_estructura_transformer['test']['images'].append(
                    ruta_relativa)
            elif ruta_relativa.endswith('.json'):
                dataset_estructura_transformer['test']['json'] = True
            else:
                error_formato = True
                formato_correcto = False

        elif 'valid/' in ruta_relativa:
            if ruta_relativa.endswith(formato):
                dataset_estructura_transformer['valid']['images'].append(
                    ruta_relativa)
            elif ruta_relativa.endswith('.json'):
                dataset_estructura_transformer['valid']['json'] = True
            else:
                error_formato = True
                formato_correcto = False

    if error_formato:
        return True, f"Error: No hay ninguna imagen con formato {formato}, Valida nuevamente tu dataset", ""

    # Validar si las carpetas tienen la estructura necesaria
    for carpeta, contenido in dataset_estructura_transformer.items():
        if not contenido['images'] or not contenido['json']:
            error_carpeta = True

    # Si hay errores en las carpetas, regresamos el error correspondiente
    if error_carpeta:
        return True, f"Error: La carpeta {carpeta} no contiene los archivos necesarios para Transformer", ""

    # Contar imágenes en cada carpeta
    cantidad_train = len(dataset_estructura_transformer['train']['images'])
    cantidad_test = len(dataset_estructura_transformer['test']['images'])
    cantidad_valid = len(dataset_estructura_transformer['valid']['images'])

    # Calcular la cantidad total de imágenes
    cantidad_total = cantidad_train + cantidad_test + cantidad_valid

    return False, "", cantidad_total, cantidad_test


def guardar_dataset(nombre, ruta, formato, tecnologia, tipo_basura, cantidad_total, cantidad_test, ruta_test):
    usuario_id = current_user.id
    cursor = BaseDatos.connection.cursor()

    cursor.execute(
        "SELECT 1 FROM dataexperiment WHERE NombreDataExp = %s", (nombre,))

    if cursor.fetchone() is not None:
        flash('Ya existe un dataset con ese nombre')
        return redirect(url_for('CrudDatasetA'))

    cursor = BaseDatos.connection.cursor()
    cursor.execute(
        "SELECT idTiposBasura FROM tiposbasura WHERE TipoBasura = %s", (tipo_basura,))
    id_tipo_basura = cursor.fetchone()[0]

    print(usuario_id, id_tipo_basura, nombre, formato,
          cantidad_total, tecnologia, ruta)
    print(usuario_id, id_tipo_basura, nombre, formato,
          cantidad_test, ruta_test)
    try:
        cursor.execute(
            "INSERT INTO dataexperiment (idUsuarios, idTiposBasura, NombreDataExp, FormatoExp, Imagenes, Tecnologia, Ruta) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (usuario_id, id_tipo_basura, nombre, formato,
             cantidad_total, tecnologia, ruta)
        )
        cursor.execute("INSERT INTO datasetprueba (idUsuarios, idTiposBasura, NombreData, Formato, Cantidad, Ruta) "
                       "VALUES (%s, %s, %s, %s, %s, %s)",
                       (usuario_id, id_tipo_basura, nombre, formato,
                        cantidad_test, ruta_test))

        BaseDatos.connection.commit()
    except Exception as e:
        BaseDatos.connection.rollback()
        print(f"Error: {e}")
    finally:
        cursor.close()


@app.route('/eliminarDataset/<string:NombreDataExp>')
def eliminarDataset(NombreDataExp):
    tipoUsuario = current_user.tipo
    cursor = BaseDatos.connection.cursor()
    try:
        cursor.execute(
            'DELETE FROM dataexperiment WHERE NombreDataExp = %s', (NombreDataExp,))

        cursor.execute(
            'DELETE FROM datasetprueba WHERE NombreData = %s', (NombreDataExp,))

        BaseDatos.connection.commit()

        flash('Dataset eliminado satisfactoriamente', 'success')
        if tipoUsuario == 'Administrador':
            return redirect(url_for('experimentadorA'))
        if tipoUsuario == 'Tester':
            return redirect(url_for('experimentadorT'))

    except MySQLdb.IntegrityError as e:
        if e.args[0] == 1451:

            BaseDatos.connection.rollback()

            flash(
                "No se puede eliminar el dataset porque está asociado con unos pesos para evaluación.", "error")
        else:

            BaseDatos.connection.rollback()
            flash("Ocurrió un error al eliminar el dataset. Inténtalo de nuevo.", "error")

        if tipoUsuario == 'Administrador':
            return redirect(url_for('experimentadorA'))
        if tipoUsuario == 'Tester':
            return redirect(url_for('experimentadorT'))

    finally:
        cursor.close()


@app.route('/editarDataset/<string:NombreDataExp>')
def editarDataset(NombreDataExp):
    tipoUsuario = current_user.tipo
    cursor = BaseDatos.connection.cursor()
    sql = "SELECT NombreDataExp FROM dataexperiment WHERE NombreDataExp = %s"
    cursor.execute(sql, (NombreDataExp,))
    dataset = cursor.fetchone()
    Nombre = dataset[0]
    cursor.close()
    if tipoUsuario == 'Administrador':
        return render_template('admin/editarDatasetExpAd.html', nombreDataset=Nombre)
    if tipoUsuario == 'Tester':
        return render_template('test/editarDatasetExpTes.html', nombreDataset=Nombre)


@app.route('/modificarDataset/<string:NombreDataset>', methods=['POST'])
def modificarDataset(NombreDataset):
    if request.method == 'POST':
        tipoUsuario = current_user.tipo
        Nombre = request.form['nombreDataset']

        cursor = BaseDatos.connection.cursor()

        sql = "SELECT * FROM dataexperiment WHERE NombreDataExp = %s"
        cursor.execute(sql, (Nombre,))
        existe = cursor.fetchone()

        if existe:
            flash('Ya existe un dataset con el mismo nombre')
            if tipoUsuario == 'Administrador':
                return redirect(url_for('experimentadorA'))
            if tipoUsuario == 'Tester':
                return redirect(url_for('experimentadorT'))

        sql = """UPDATE dataexperiment SET NombreDataExp = %s WHERE NombreDataExp = %s"""
        cursor.execute(sql, (Nombre, NombreDataset))
        cursor.execute(
            "UPDATE datasetprueba SET NombreData = %s WHERE NombreData = %s", (Nombre, NombreDataset))
        BaseDatos.connection.commit()
        cursor.close()
        flash('Dataset actualizado satisfactoriamente')

        if tipoUsuario == 'Administrador':
            return redirect(url_for('experimentadorA'))
        if tipoUsuario == 'Tester':
            return redirect(url_for('experimentadorT'))


# Configuración del manejo de errores


def status_401(error):
    return redirect(url_for('login'))


def status_404(error):
    return "<h1>Esta página no existe</h1>", 404


# Configuración y ejecución del sistema como el llamado al módulo "configuración"
if __name__ == '__main__':
    app.register_error_handler(401, status_401)
    app.register_error_handler(404, status_404)
    app.run(debug=True)
