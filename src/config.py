class Configuracion:
    SECRET_KEY = 'iGGTCXBKtWn0eun'


class ConfiguracionDesarrollo(Configuracion):
    """Configuracion para la conexion a la base de datos"""
    DEBUG = True
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = ''
    MYSQL_DB = 'detector'


configuracion = {
    'desarrollo': ConfiguracionDesarrollo
}
