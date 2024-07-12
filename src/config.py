class Configuracion:
    SECRET_KEY = 'iGGTCXBKtWn0eun'
    JWT_SECRET_KEY = 'pD0_]ea5*.A8q"yJ:pr>'

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
    MAIL_SERVER = 'smtp.gmail.net'
    MAIL_PORT = 465
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
    MAIL_USERNAME = 'emmanuel.agva@gmail.com'
    MAIL_PASSWORD = 'uvdo dcck clve mjvh'


configuracion = {
    'desarrollo': ConfiguracionDesarrollo,
    'codigoR': CodigoRecuperacion
}
