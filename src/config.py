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
    DEBUG = True
    MAIL_SERVER = 'smtp-mail.outlook.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = 'r-emmanuel_n@hotmail.com'
    MAIL_PASSWORD = 'exvcpiyrdnmhbpic'
    MAIL_DEFAULT_SENDER = 'Estadia_AVAO191844@Emmanuel.com'


configuracion = {
    'desarrollo': ConfiguracionDesarrollo,
    'codigoR': CodigoRecuperacion
}
