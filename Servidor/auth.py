# Servidor/auth.py

# Simulación de las tablas de la base de datos para control de estados
usuarios_db = {
    "luis@email.com": {"clave": "123456", "id": 1, "nombre": "Luis Tasayco", "rol": "Host"},
    "invitado@email.com": {"clave": "123456", "id": 2, "nombre": "Juan Perez", "rol": "Usuario"}
}

# Almacenamiento en memoria para el prototipo de salas y solicitudes [cite: 20]
salas_db = {}         # Estructura: { codigo_sala: id_host }
solicitudes_db = {}   # Estructura: { id_usuario: {"sala": codigo_sala, "nombre": nombre, "estado": "Pendiente"} }

def validar_login(correo, clave):
    if correo in usuarios_db and usuarios_db[correo]["clave"] == clave:
        return {"status": "success", "data": usuarios_db[correo]}
    return {"status": "error", "message": "Credenciales incorrectas."}

def registrar_sala(codigo, id_host):
    salas_db[codigo] = id_host
    return {"status": "success", "roomCode": codigo}

def registrar_solicitud(codigo, id_usuario, nombre_usuario):
    if codigo not in salas_db:
        return {"status": "error", "message": "La sala especificada no existe."}
    solicitudes_db[id_usuario] = {"sala": codigo, "nombre": nombre_usuario, "estado": "Pendiente"}
    return {"status": "success", "id_host": salas_db[codigo]}

def actualizar_solicitud(id_usuario, accion):
    if id_usuario in solicitudes_db:
        estado = "Aceptado" if accion == "accept" else "Rechazado"
        solicitudes_db[id_usuario]["estado"] = estado
        return {"status": "success", "sala": solicitudes_db[id_usuario]["sala"]}
    return {"status": "error", "message": "Solicitud no encontrada."}