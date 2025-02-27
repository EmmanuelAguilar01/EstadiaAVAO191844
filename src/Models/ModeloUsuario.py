#Se importa el objeto Usuario para hacer uso de sus metodos
from Models.entities.Usuario import Usuario

#Se crea la clase de ModeloUsuario para hacer uso de los metodos de la clase Usuario
class ModeloUsuario():

    @classmethod
    #Se crea el metodo Iniciar para hacer uso de la base de datos y verificar si el usuario existe
    def Iniciar(self, BaseDatos, correo, contra):
        try:
            #Se hace la conexon con la base de datos
            Cursor = BaseDatos.connection.cursor()
            #Se define la consulta para verificar si el usuario existe
            sql = """SELECT idUsuarios,Nombre,Apellido,Correo,Contra,Tipo,FechaRegistro, Intereses, Procedencia FROM detector.usuarios WHERE correo = '{}'""".format(
                correo)
            #Se ejecuta la consulta
            Cursor.execute(sql)
            #Se obtiene el resultado de la consulta y se guarda en la variable row
            row = Cursor.fetchone()
            #Se verifica si row no es nulo
            if row is not None:
                #Se crea un objeto de la clase Usuario con los datos obtenidos de la consulta
                usuario = Usuario(row[0], row[1], row[2], row[3], Usuario.verificar_contra(
                    row[4], contra), row[5], row[6], row[7], row[8])
                #Se retorna el objeto usuario
                return usuario
            else:
                #Si no se encuentra el usuario se retorna None
                return None
        except Exception as ex:
            raise Exception(ex)

    #Se crea el metodo de registro para hacer uso de la base de datos y registrar un nuevo usuario
    @classmethod
    def get_by_id(cls, BaseDatos, id):
        try:
            #Se hace la conexion con la base de datos
            Cursor = BaseDatos.connection.cursor()
            #Se define la consulta para obtener los datos del usuario
            sql = "SELECT idUsuarios,Nombre,Apellido,Correo,Tipo,FechaRegistro, Intereses, Procedencia FROM detector.usuarios WHERE idUsuarios = %s"
            #Se ejecuta la consulta
            Cursor.execute(sql, (id,))
            #Se obtiene el resultado de la consulta y se guarda en la variable row
            row = Cursor.fetchone()
            #Se verifica si row no es nulo
            if row is not None:
                #Se crea un objeto de la clase Usuario con los datos obtenidos de la consulta
                usuario_iniciado = Usuario(
                    row[0], row[1], row[2], row[3], None, row[4], row[5], row[6], row[7])
                #Se retorna el objeto usuario
                return usuario_iniciado
            else:
                #Si no se encuentra el usuario se retorna None
                return None
        except Exception as ex:
            raise Exception(ex)
    
    #Se crea un metodo para recuperar la contraseña del usuario
    @classmethod
    def recuperacion(cls, BaseDatos, id):
        try:
            #Se hace la conexion con la base de datos
            Cursor = BaseDatos.connection.cursor()
            #Se define la consulta para recuperar la contraseña del usuario
            sql = "SELECT idUsuarios,Correo,Contra FROM detector.usuarios WHERE Correo = %s"
            #Se ejecuta la consulta
            Cursor.execute(sql, (id,))
            #Se obtiene el resultado de la consulta y se guarda en la variable row
            row = Cursor.fetchone()
            #Se verifica si row no es nulo
            if row is not None:
                #Se crea un objeto de la clase Usuario con los datos obtenidos de la consulta para recuperar la contraseña
                recuperacion_C = Usuario.RecuperacionContrasena(
                    row[0], row[1], row[2])
                #Se retorna el objeto recuperacion_C
                return recuperacion_C
            else:
                #Si no se encuentra el usuario se retorna None
                return None
        except Exception as ex:
            raise Exception(ex)
