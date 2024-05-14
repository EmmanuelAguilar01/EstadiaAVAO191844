from Models.entities.Usuario import Usuario, UsuarioIniciado


class ModeloUsuario():

    @classmethod
    def Iniciar(self, BaseDatos, usuario):
        try:
            Cursor = BaseDatos.connection.cursor()
            sql = """SELECT Correo, Contra FROM detector.usuarios WHERE correo = '{}'""".format(
                usuario.correo)
            Cursor.execute(sql)
            row = Cursor.fetchone()
            if row is not None:
                usuario = Usuario(row[0], Usuario.verificar_contra(
                    row[1], usuario.contra),)
                return usuario
            else:
                return None
        except Exception as ex:
            raise Exception(ex)

    @classmethod
    def get_by_id(cls, BaseDatos, idUsuarios):
        try:
            Cursor = BaseDatos.connection.cursor()
            sql = "SELECT idUsuarios,Nombre,Apellido,Correo,Tipo,FechaRegistro, Intereses, Procedencia FROM detector.usuarios WHERE idUsuarios = %s"
            Cursor.execute(sql, (idUsuarios,))
            row = Cursor.fetchone()
            if row is not None:
                usuario_iniciado = UsuarioIniciado(
                    row[0], row[1], row[2], row[3], None, row[4], row[5], row[6], row[7])
                return usuario_iniciado
            else:
                return None
        except Exception as ex:
            raise Exception(ex)
