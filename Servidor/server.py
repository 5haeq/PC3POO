# Servidor/server.py
import socket
import threading
import json
import auth

HOST = '127.0.0.1'
PORT = 5000

# Diccionario global de sesiones activas: { idUsuario: socket_conexion }
clientes_conectados = {}

def manejar_cliente(conexion, direccion):
    print(f"[CONEXIÓN] Nueva conexión establecida desde {direccion}")
    id_usuario_actual = None
    
    while True:
        try:
            datos = conexion.recv(2048).decode('utf-8')
            if not datos:
                break
            
            mensaje = json.loads(datos)
            tipo = mensaje.get("type")
            
            if tipo == "LOGIN_REQUEST":
                res = auth.validar_login(mensaje["correo"], mensaje["clave"])
                if res["status"] == "success":
                    id_usuario_actual = res["data"]["id"]
                    clientes_conectados[id_usuario_actual] = conexion
                    respuesta = {
                        "type": "LOGIN_RESPONSE",
                        "status": "success",
                        "idUsuario": id_usuario_actual,
                        "nombres": res["data"]["nombre"],
                        "rol": res["data"]["rol"]
                    }
                else:
                    respuesta = {"type": "LOGIN_RESPONSE", "status": "error", "message": res["message"]}
                conexion.send(json.dumps(respuesta).encode('utf-8'))
                
            elif tipo == "CREATE_ROOM":
                auth.registrar_sala(mensaje["roomCode"], mensaje["userId"])
                respuesta = {"type": "ROOM_CREATED", "status": "success", "roomCode": mensaje["roomCode"]}
                conexion.send(json.dumps(respuesta).encode('utf-8'))
                
            elif tipo == "JOIN_ROOM_REQUEST":
                res = auth.registrar_solicitud(mensaje["roomCode"], mensaje["userId"], mensaje["userName"])
                if res["status"] == "success":
                    # 1. Notificar al invitado que su estado pasó a espera [cite: 20]
                    respuesta_invitado = {"type": "WAIT_FOR_HOST", "status": "pending"}
                    conexion.send(json.dumps(respuesta_invitado).encode('utf-8'))
                    
                    # 2. Notificar en tiempo real al Host si se encuentra en red 
                    id_host = res["id_host"]
                    if id_host in clientes_conectados:
                        notif_host = {
                            "type": "WAITING_ROOM_UPDATE",
                            "userIdPendiente": mensaje["userId"],
                            "nombresPendiente": mensaje["userName"]
                        }
                        clientes_conectados[id_host].send(json.dumps(notif_host).encode('utf-8'))
                else:
                    respuesta = {"type": "ROOM_REJECTED", "message": res["message"]}
                    conexion.send(json.dumps(respuesta).encode('utf-8'))
                    
            elif tipo == "ADMIT_USER":
                id_pendiente = mensaje["userIdPendiente"]
                accion = mensaje["action"] # "accept" o "reject"
                res = auth.actualizar_solicitud(id_pendiente, accion)
                
                if res["status"] == "success":
                    if id_pendiente in clientes_conectados:
                        tipo_notif = "ROOM_JOINED" if accion == "accept" else "ROOM_REJECTED"
                        notif_invitado = {"type": tipo_notif, "roomCode": res["sala"]}
                        clientes_conectados[id_pendiente].send(json.dumps(notif_invitado).encode('utf-8'))
                        
        except (ConnectionResetError, json.JSONDecodeError):
            break

    # Limpieza al desconectar el cliente
    if id_usuario_actual in clientes_conectados:
        del clientes_conectados[id_usuario_actual]
    print(f"[DESCONEXIÓN] El cliente {direccion} ha cerrado la sesión.")
    conexion.close()

def iniciar_servidor():
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind((HOST, PORT))
    servidor.listen()
    print(f"[ESCUCHANDO] Servidor de salas activo en {HOST}:{PORT}")
    
    while True:
        conexion, direccion = servidor.accept()
        hilo = threading.Thread(target=manejar_cliente, args=(conexion, direccion))
        hilo.start()

if __name__ == "__main__":
    iniciar_servidor()