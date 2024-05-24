from werkzeug.security import check_password_hash
from flask_login import UserMixin
# Creación de la clase Usuario para su verificacion


class Usuario(UserMixin):
    """Creacion de la clase para un usuario y se verifique en el inicio"""

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

    @classmethod
    def verificar_contra(cls, contraHash, contra):
        """Aplica un hash a la contraseña para seguridad"""
        return check_password_hash(contraHash, contra)
