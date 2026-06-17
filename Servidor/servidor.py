import socket
import threading
from Servidor.manejador_cliente import ManejadorCliente
from Servidor.base_datos import BaseDatos

class Servidor:
    def __init__(self, host="0.0.0.0", puerto=5000):
        self._host = host
        self._puerto = puerto
        self._socket = None
        self._activo = False
        self._clientes = []
        self._salas = {}

    def iniciar(self):
        bd = BaseDatos()
        bd.inicializar()

        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.bind((self._host, self._puerto))
        self._socket.listen()
        self._activo = True
        print(f"[INICIANDO] Servidor activo en {self._host}:{self._puerto}")

        while self._activo:
            try:
                conexion, direccion = self._socket.accept()
                manejador = ManejadorCliente(self, conexion, direccion)
                self._clientes.append(manejador)
                hilo = threading.Thread(target=manejador.iniciar, daemon=True)
                hilo.start()
                print(f"[HILOS ACTIVOS] {threading.active_count() - 1}")
            except OSError:
                break

    def detener(self):
        self._activo = False
        if self._socket:
            self._socket.close()

    def reenviar_a_sala(self, codigo_sala, mensaje, emisor=None):
        for cliente in self._clientes:
            if cliente._sala_actual == codigo_sala and cliente != emisor:
                cliente._enviar(mensaje)

if __name__ == "__main__":
    servidor = Servidor()
    try:
        servidor.iniciar()
    except KeyboardInterrupt:
        print("\n[DETENIENDO] Servidor detenido por el usuario")
        servidor.detener()
