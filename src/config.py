class Configuracion:
    SECRET_KEY = 'iGGTCXBKtWn0eun'

# Configuración para la conexion de la base de datos


class ConfiguracionDesarrollo(Configuracion):
    """Configuracion para la conexion a la base de datos"""
    DEBUG = True
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = ''
    MYSQL_DB = 'detector'


# Configuración para un servidor web y la recuperación de contraseña
class CodigoRecuperacion(Configuracion):
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'emmanuel.agva@gmail.com'
    MAIL_PASSWORD = 'uvdodcckclvemjvh'
    MAIL_DEFAULT_SENDER = 'EstadiaAVAO191844@gmail.com'


configuracion = {
    'desarrollo': ConfiguracionDesarrollo,
    'codigoR': CodigoRecuperacion
}
