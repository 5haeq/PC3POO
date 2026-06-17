# Cliente/ui_views.py
import tkinter as tk
from tkinter import messagebox
import socket_client

def mostrar_pantalla_login():
    ventana = tk.Tk()
    ventana.title("Prototipo Zoom - Inicio de Sesión")
    ventana.geometry("300x250")
    ventana.eval('tk::PlaceWindow . center') # Centra la ventana

    tk.Label(ventana, text="Correo electrónico:").pack(pady=(20, 5))
    entrada_correo = tk.Entry(ventana, width=30)
    entrada_correo.pack()

    tk.Label(ventana, text="Contraseña:").pack(pady=(10, 5))
    entrada_clave = tk.Entry(ventana, width=30, show="*")
    entrada_clave.pack()

    def procesar_login():
        correo = entrada_correo.get()
        clave = entrada_clave.get()

        # Validar campos vacíos antes de enviar al servidor [cite: 100]
        if not correo or not clave:
            messagebox.showwarning("Atención", "Por favor, completa todos los campos.")
            return

        # Nos comunicamos con el servidor
        respuesta = socket_client.enviar_peticion_login(correo, clave)

        if respuesta.get("status") == "success":
            messagebox.showinfo("Éxito", f"Bienvenido, {respuesta['nombres']} ({respuesta['rol']})")
            ventana.destroy()
            # AQUI: Llamar a la función que dibuje la Pantalla de Inicio (Fase 3)
        else:
            # Si es incorrecto, mostrar error sin cerrar la aplicación [cite: 103]
            messagebox.showerror("Error de Login", respuesta.get("message"))

    tk.Button(ventana, text="Ingresar", command=procesar_login, width=15).pack(pady=20)
    
    ventana.mainloop()