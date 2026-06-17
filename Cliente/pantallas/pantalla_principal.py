import tkinter as tk
from tkinter import messagebox, ttk
import random
import string

class PantallaPrincipal(tk.Frame):
    def __init__(self, master, usuario, cliente_socket, on_cerrar_sesion):
        super().__init__(master)
        self._usuario = usuario
        self._cliente_socket = cliente_socket
        self._on_cerrar_sesion = on_cerrar_sesion
        self._crear_widgets()

    def _crear_widgets(self):
        tk.Label(self, text=f"Bienvenido, {self._usuario.nombres}",
                 font=("Arial", 14, "bold")).pack(pady=(20, 5))
        tk.Label(self, text=f"Rol: {self._usuario.rol}",
                 font=("Arial", 10)).pack(pady=(0, 20))

        frame_botones = tk.Frame(self)
        frame_botones.pack()

        tk.Button(frame_botones, text="Crear Sala", command=self._crear_sala,
                  width=20, font=("Arial", 11), bg="#2196F3", fg="white").pack(pady=5)
        tk.Button(frame_botones, text="Unirse a Sala", command=self._unirse_sala,
                  width=20, font=("Arial", 11), bg="#FF9800", fg="white").pack(pady=5)
        tk.Button(frame_botones, text="Cerrar Sesión", command=self._on_cerrar_sesion,
                  width=20, font=("Arial", 11), bg="#f44336", fg="white").pack(pady=(20, 5))

    def _crear_sala(self):
        codigo = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        respuesta = self._cliente_socket.enviar_y_recibir({
            "type": "CREATE_ROOM",
            "nombre": f"Sala de {self._usuario.nombres}",
            "codigo": codigo,
            "idHost": self._usuario.id_usuario
        })
        if respuesta.get("status") == "success":
            messagebox.showinfo("Sala Creada",
                                f"Sala creada exitosamente.\nCódigo: {codigo}")
        else:
            messagebox.showerror("Error", respuesta.get("message", "Error al crear sala"))

    def _unirse_sala(self):
        ventana = tk.Toplevel(self)
        ventana.title("Unirse a Sala")
        ventana.geometry("300x150")
        ventana.transient(self)
        ventana.grab_set()

        tk.Label(ventana, text="Código de la sala:", font=("Arial", 10)).pack(pady=(20, 5))
        entrada = tk.Entry(ventana, width=20, font=("Arial", 12))
        entrada.pack()
        entrada.focus()

        def unirse():
            codigo = entrada.get().strip()
            if not codigo:
                messagebox.showwarning("Atención", "Ingresa un código de sala.")
                return
            respuesta = self._cliente_socket.enviar_y_recibir({
                "type": "JOIN_ROOM_REQUEST",
                "codigo": codigo,
                "idUsuario": self._usuario.id_usuario
            })
            if respuesta.get("status") == "success":
                messagebox.showinfo("Solicitud Enviada",
                                    "Solicitud enviada. Espera a que el host te admita.")
                ventana.destroy()
            else:
                messagebox.showerror("Error", respuesta.get("message", "Error al unirse"))

        tk.Button(ventana, text="Unirse", command=unirse,
                  width=15, font=("Arial", 10), bg="#4CAF50", fg="white").pack(pady=15)
