# Cliente/socket_client.py
import socket
import json

HOST = '127.0.0.1'
PORT = 5000

def enviar_peticion_login(correo, clave):
    cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        cliente.connect((HOST, PORT))
        
        peticion_login = {
            "type": "LOGIN_REQUEST",
            "correo": correo,
            "clave": clave
        }
        
        cliente.send(json.dumps(peticion_login).encode('utf-8'))
        
        # Esperamos y devolvemos la respuesta del servidor [cite: 84]
        respuesta_bytes = cliente.recv(1024).decode('utf-8')
        return json.loads(respuesta_bytes)
        
    except ConnectionRefusedError:
        return {"status": "error", "message": "No se pudo conectar al servidor."}
    finally:
        cliente.close()