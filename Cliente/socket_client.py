# Cliente/socket_client.py
import socket
import json
import threading

HOST = '127.0.0.1'
PORT = 5000

cliente_socket = None
callback_ui = None

def conectar_servidor(ui_callback_func):
    global cliente_socket, callback_ui
    callback_ui = ui_callback_func
    cliente_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cliente_socket.connect((HOST, PORT))
    
    hilo_escucha = threading.Thread(target=escuchar_servidor, daemon=True)
    hilo_escucha.start()

def escuchar_servidor():
    global cliente_socket, callback_ui
    while True:
        try:
            datos = cliente_socket.recv(2048).decode('utf-8')
            if not datos:
                break
            mensaje = json.loads(datos)
            if callback_ui:
                callback_ui(mensaje)
        except:
            break

def enviar_mensaje(mensaje_dict):
    global cliente_socket
    if cliente_socket:
        try:
            cliente_socket.send(json.dumps(mensaje_dict).encode('utf-8'))
        except Exception as e:
            print(f"[ERROR RED] No se pudo despachar el mensaje: {e}")