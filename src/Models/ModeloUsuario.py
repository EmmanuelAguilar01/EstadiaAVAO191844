from Models.entities.Usuario import Usuario


class ModeloUsuario():

    @classmethod
    def Iniciar(self, BaseDatos, correo, contra):
        try:
            Cursor = BaseDatos.connection.cursor()
            sql = """SELECT idUsuarios,Nombre,Apellido,Correo,Contra,Tipo,FechaRegistro, Intereses, Procedencia FROM detector.usuarios WHERE correo = '{}'""".format(
                correo)
            Cursor.execute(sql)
            row = Cursor.fetchone()
            if row is not None:
                usuario = Usuario(row[0], row[1], row[2], row[3], Usuario.verificar_contra(
                    row[4], contra), row[5], row[6], row[7], row[8])
                return usuario
            else:
                return None
        except Exception as ex:
            raise Exception(ex)

    @classmethod
    def get_by_id(cls, BaseDatos, id):
        try:
            Cursor = BaseDatos.connection.cursor()
            sql = "SELECT idUsuarios,Nombre,Apellido,Correo,Tipo,FechaRegistro, Intereses, Procedencia FROM detector.usuarios WHERE idUsuarios = %s"
            Cursor.execute(sql, (id,))
            row = Cursor.fetchone()
            if row is not None:
                usuario_iniciado = Usuario(
                    row[0], row[1], row[2], row[3], None, row[4], row[5], row[6], row[7])
                return usuario_iniciado
            else:
                return None
        except Exception as ex:
            raise Exception(ex)
