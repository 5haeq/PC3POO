import socket
import json

class ClienteSocket:
    def __init__(self, host="127.0.0.1", puerto=5000):
        self._host = host
        self._puerto = puerto
        self._socket = None
        self._conectado = False

    def conectar(self):
        if not self._conectado:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.settimeout(10)
            self._socket.connect((self._host, self._puerto))
            self._conectado = True

    def desconectar(self):
        if self._conectado:
            self._socket.close()
            self._conectado = False

    def enviar(self, datos):
        try:
            if not self._conectado:
                self.conectar()
            self._socket.send(json.dumps(datos).encode("utf-8"))
        except (socket.error, ConnectionRefusedError) as e:
            raise ConnectionError(f"No se pudo conectar al servidor: {e}")

    def recibir(self):
        try:
            respuesta_bytes = self._socket.recv(4096).decode("utf-8")
            return json.loads(respuesta_bytes)
        except (socket.timeout, ConnectionResetError, json.JSONDecodeError) as e:
            raise ConnectionError(f"Error al recibir datos: {e}")

    def enviar_y_recibir(self, datos):
        self.enviar(datos)
        return self.recibir()
