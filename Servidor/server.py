import socket
import threading
import json

# Configuración del servidor
HOST = '127.0.0.1'  # Localhost para pruebas
PORT = 5000         # Puerto de escucha

def manejar_cliente(conexion, direccion):
    print(f"[NUEVA CONEXIÓN] Cliente conectado desde {direccion}")
    conectado = True
    
    while conectado:
        try:
            # Recibimos el mensaje (esperamos un JSON en formato string)
            datos = conexion.recv(1024).decode('utf-8')
            if not datos:
                break
            
            # Convertimos el string a un diccionario de Python [cite: 137-138]
            mensaje = json.loads(datos)
            tipo_mensaje = mensaje.get("type")
            
            # Evaluamos el protocolo de comunicación [cite: 66, 139]
            if tipo_mensaje == "LOGIN_REQUEST":
                print(f"[*] Intento de login recibido: {mensaje['correo']}")
                
                # AQUI IRÁ LA VALIDACIÓN CON LA BASE DE DATOS MÁS ADELANTE [cite: 140]
                # Por ahora simulamos una respuesta exitosa
                respuesta = {
                    "type": "LOGIN_RESPONSE",
                    "status": "success",
                    "idUsuario": 1,
                    "nombres": "Luis Tasayco",
                    "rol": "Host"
                }
                
                # Enviamos la respuesta de vuelta al cliente [cite: 141]
                conexion.send(json.dumps(respuesta).encode('utf-8'))
                
        except json.JSONDecodeError:
            print("[ERROR] Formato JSON inválido recibido.")
        except ConnectionResetError:
            break

    print(f"[DESCONEXIÓN] Cliente {direccion} se ha desconectado.")
    conexion.close()

def iniciar_servidor():
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # TCP [cite: 22]
    servidor.bind((HOST, PORT))
    servidor.listen()
    print(f"[ESCUCHANDO] Servidor activo en {HOST}:{PORT}")
    
    while True:
        # El servidor espera indefinidamente nuevas conexiones [cite: 133-134]
        conexion, direccion = servidor.accept()
        # Creamos un hilo independiente para cada cliente [cite: 135]
        hilo = threading.Thread(target=manejar_cliente, args=(conexion, direccion))
        hilo.start()
        print(f"[HILOS ACTIVOS] {threading.active_count() - 1}")

if __name__ == "__main__":
    print("[INICIANDO] Levantando servidor...")
    iniciar_servidor()