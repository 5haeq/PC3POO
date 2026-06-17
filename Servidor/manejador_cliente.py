import json
import threading
from Servidor.protocolo import Protocolo
from Servidor.auth_service import AuthService
from Servidor.base_datos import BaseDatos

class ManejadorCliente:
    def __init__(self, servidor, conexion, direccion):
        self._servidor = servidor
        self._conexion = conexion
        self._direccion = direccion
        self._auth_service = AuthService()
        self._usuario_actual = None
        self._sala_actual = None
        self._conectado = True

    def iniciar(self):
        print(f"[NUEVA CONEXIÓN] Cliente conectado desde {self._direccion}")
        while self._conectado:
            try:
                datos = self._conexion.recv(4096).decode("utf-8")
                if not datos:
                    break
                mensaje = json.loads(datos)
                self._procesar_mensaje(mensaje)
            except json.JSONDecodeError:
                print("[ERROR] Formato JSON inválido recibido")
            except ConnectionResetError:
                break
            except Exception as e:
                print(f"[ERROR] {e}")
                break
        print(f"[DESCONEXIÓN] Cliente {self._direccion} se ha desconectado")
        self._conexion.close()

    def _procesar_mensaje(self, mensaje):
        tipo = mensaje.get("type")
        if tipo == Protocolo.LOGIN_REQUEST:
            self._manejar_login(mensaje)
        elif tipo == Protocolo.CREATE_ROOM:
            self._manejar_crear_sala(mensaje)
        elif tipo == Protocolo.JOIN_ROOM_REQUEST:
            self._manejar_unirse_sala(mensaje)
        elif tipo == Protocolo.CHAT_MESSAGE:
            self._manejar_chat(mensaje)

    def _manejar_login(self, mensaje):
        respuesta = self._auth_service.validar_login(
            mensaje.get("correo", ""),
            mensaje.get("clave", "")
        )
        respuesta["type"] = Protocolo.LOGIN_RESPONSE
        if respuesta["status"] == "success":
            self._usuario_actual = {
                "idUsuario": respuesta["idUsuario"],
                "nombres": respuesta["nombres"],
                "rol": respuesta["rol"]
            }
        self._enviar(respuesta)

    def _manejar_crear_sala(self, mensaje):
        try:
            bd = BaseDatos()
            conexion = bd.conectar()
            cursor = conexion.cursor()
            cursor.execute(
                "INSERT INTO Salas (CodigoSala, Nombre, IdHost) VALUES (?, ?, ?)",
                (mensaje["codigo"], mensaje["nombre"], mensaje["idHost"])
            )
            conexion.commit()
            self._enviar({"type": "CREATE_ROOM", "status": "success", "codigo": mensaje["codigo"]})
        except Exception as e:
            self._enviar({"type": "CREATE_ROOM", "status": "error", "message": str(e)})

    def _manejar_unirse_sala(self, mensaje):
        try:
            bd = BaseDatos()
            conexion = bd.conectar()
            cursor = conexion.cursor()
            cursor.execute(
                "SELECT IdSala, IdHost FROM Salas WHERE CodigoSala = ? AND Estado = 'Activa'",
                (mensaje["codigo"],)
            )
            sala = cursor.fetchone()
            if not sala:
                self._enviar({"type": "JOIN_ROOM_REQUEST", "status": "error",
                              "message": "Sala no encontrada o inactiva."})
                return
            cursor.execute(
                "INSERT INTO SolicitudesSala (IdSala, IdUsuario) VALUES (?, ?)",
                (sala["IdSala"], mensaje["idUsuario"])
            )
            conexion.commit()
            self._enviar({"type": "JOIN_ROOM_REQUEST", "status": "success",
                          "idSala": sala["IdSala"]})
        except Exception as e:
            self._enviar({"type": "JOIN_ROOM_REQUEST", "status": "error", "message": str(e)})

    def _manejar_chat(self, mensaje):
        print(f"[CHAT] {mensaje.get('userName')}: {mensaje.get('message')}")
        self._servidor.reenviar_a_sala(mensaje.get("roomCode"), mensaje, self)

    def _enviar(self, datos):
        try:
            self._conexion.send(json.dumps(datos).encode("utf-8"))
        except Exception as e:
            print(f"[ERROR] No se pudo enviar mensaje: {e}")
            self._conectado = False
