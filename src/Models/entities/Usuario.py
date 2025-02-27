#Se importan las librerias para el hash de la contraseña y el login
from werkzeug.security import check_password_hash
from flask_login import UserMixin

# Creación de la clase Usuario para su verificacion
class Usuario(UserMixin):
    #Se inicializan los atributos de la clase

    def __init__(self, id, nombre, apellido, correo, contra, tipo, fechaRegistro, intereses, procedencia) -> None:
        self.id = id
        self.nombre = nombre
        self.apellido = apellido
        self.correo = correo
        self.contra = contra
        self.tipo = tipo
        self.fechaRegistro = fechaRegistro
        self.intereses = intereses
        self.procedencia = procedencia

    #Se crea el metodo de la clase para poder verificar la contraseña con el hash
    @classmethod
    def verificar_contra(cls, contraHash, contra):
        """Aplica un hash a la contraseña para seguridad"""
        return check_password_hash(contraHash, contra)

    #Se crea el metodo de la clase para poder recuperar la contraseña
    @classmethod
    def RecuperacionContrasena(self, id, correo, contra) -> None:
        self.id = id
        self.correo = correo
        self.contra = contra
