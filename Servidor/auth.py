# Servidor/auth.py
# Importa aquí tu conector (ej. import pyodbc, import psycopg2, import mysql.connector)

def validar_login(correo, clave):
    """
    Se conecta a la BD y verifica las credenciales.
    Devuelve un diccionario con la respuesta estructurada.
    """
    try:
        # AQUI VA TU CONEXIÓN REAL A LA BD. Ejemplo conceptual:
        # conexion = conector.connect("tu_cadena_de_conexion")
        # cursor = conexion.cursor()
        # cursor.execute("SELECT IdUsuario, Nombres, Rol FROM Usuarios WHERE Correo = ? AND PasswordHash = ?", (correo, clave))
        # resultado = cursor.fetchone()
        
        # Simulamos el resultado para que puedas probar la UI inmediatamente
        if correo == "luis@email.com" and clave == "123456":
            # Si es correcto, devolver IdUsuario, Nombres y Rol [cite: 102]
            return {
                "status": "success", 
                "idUsuario": 1, 
                "nombres": "Luis Tasayco", 
                "rol": "Host"
            }
        else:
            # Si es incorrecto, devolver mensaje de error [cite: 103]
            return {
                "status": "error", 
                "message": "Credenciales incorrectas o usuario no existe."
            }
    except Exception as e:
        return {"status": "error", "message": str(e)}