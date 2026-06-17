# Cliente/ui_views.py
import tkinter as tk
from tkinter import messagebox
import socket_client

class AppZoom(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Prototipo Académico Tipo Zoom")
        self.geometry("420x380")
        self.eval('tk::PlaceWindow . center')
        
        self.user_id = None
        self.user_name = None
        self.user_rol = None
        
        self.container = tk.Frame(self)
        self.container.pack(fill="both", expand=True)
        
        # Conectar el socket y pasar el manejador de eventos visuales
        socket_client.conectar_servidor(self.procesar_mensaje_servidor)
        self.mostrar_pantalla(PantallaLogin)

    def mostrar_pantalla(self, clase_frame, *args):
        for child in self.container.winfo_children():
            child.destroy()
        frame = clase_frame(self.container, self, *args)
        frame.pack(fill="both", expand=True)

    def procesar_mensaje_servidor(self, mensaje):
        # Sincroniza la llegada de datos del hilo de red con el hilo principal de Tkinter
        self.after(0, self._mapear_evento, mensaje)

    def _mapear_evento(self, mensaje):
        tipo = mensaje.get("type")
        
        if tipo == "LOGIN_RESPONSE":
            if mensaje.get("status") == "success":
                self.user_id = mensaje["idUsuario"]
                self.user_name = mensaje["nombres"]
                self.user_rol = mensaje["rol"]
                self.mostrar_pantalla(PantallaInicio)
            else:
                messagebox.showerror("Error de acceso", mensaje.get("message"))
                
        elif tipo == "ROOM_CREATED":
            self.mostrar_pantalla(PantallaPanelHost, mensaje["roomCode"])
            
        elif tipo == "WAIT_FOR_HOST":
            self.mostrar_pantalla(PantallaSalaEspera)
            
        elif tipo == "WAITING_ROOM_UPDATE":
            for child in self.container.winfo_children():
                if isinstance(child, PantallaPanelHost):
                    child.agregar_a_espera(mensaje["userIdPendiente"], mensaje["nombresPendiente"])
                    
        elif tipo == "ROOM_JOINED":
            messagebox.showinfo("Acceso aprobado", "El anfitrión ha permitido tu ingreso.")
            self.mostrar_pantalla(PantallaReunion, mensaje["roomCode"])
            
        elif tipo == "ROOM_REJECTED":
            messagebox.showwarning("Acceso denegado", "Tu solicitud de ingreso fue rechazada.")
            self.mostrar_pantalla(PantallaInicio)

class PantallaLogin(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        tk.Label(self, text="Control de Acceso", font=("Arial", 14, "bold")).pack(pady=20)
        
        tk.Label(self, text="Correo Electrónico:").pack(pady=5)
        self.ent_correo = tk.Entry(self, width=32)
        self.ent_correo.pack()
        
        tk.Label(self, text="Contraseña:").pack(pady=5)
        self.ent_clave = tk.Entry(self, width=32, show="*")
        self.ent_clave.pack()
        
        tk.Button(self, text="Conectar", width=16, bg="lightgray", command=self.solicitar_login).pack(pady=25)

    def solicitar_login(self):
        correo = self.ent_correo.get().strip()
        clave = self.ent_clave.get().strip()
        if not correo or not clave:
            messagebox.showwarning("Validación", "Complete los campos obligatorios.")
            return
        socket_client.enviar_mensaje({"type": "LOGIN_REQUEST", "correo": correo, "clave": clave})

class PantallaInicio(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        tk.Label(self, text=f"Sesión activa: {self.controller.user_name}", font=("Arial", 10, "italic"), fg="blue").pack(pady=10)
        
        # Bloque de creación de salas [cite: 20]
        tk.Label(self, text="Sección Anfitrión", font=("Arial", 12, "bold")).pack(pady=10)
        self.ent_sala_crear = tk.Entry(self, width=22)
        self.ent_sala_crear.pack()
        self.ent_sala_crear.insert(0, "UNI-2026")
        tk.Button(self, text="Crear Sala Nueva", bg="lightblue", command=self.crear_sala).pack(pady=5)
        
        # Bloque de acceso a salas [cite: 20]
        tk.Label(self, text="Sección Invitado", font=("Arial", 12, "bold")).pack(pady=10)
        self.ent_sala_unirse = tk.Entry(self, width=22)
        self.ent_sala_unirse.pack()
        tk.Button(self, text="Solicitar Ingreso", bg="lightgreen", command=self.solicitar_ingreso).pack(pady=5)

    def crear_sala(self):
        codigo = self.ent_sala_crear.get().strip()
        if codigo:
            socket_client.enviar_mensaje({"type": "CREATE_ROOM", "roomCode": codigo, "userId": self.controller.user_id})

    def solicitar_ingreso(self):
        codigo = self.ent_sala_unirse.get().strip()
        if codigo:
            socket_client.enviar_mensaje({
                "type": "JOIN_ROOM_REQUEST", 
                "roomCode": codigo, 
                "userId": self.controller.user_id,
                "userName": self.controller.user_name
            })

class PantallaSalaEspera(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        tk.Label(self, text="Sala de Espera Virtual", font=("Arial", 14, "bold"), fg="darkorange").pack(pady=40)
        tk.Label(self, text="Solicitud enviada al host.\nPor favor, espera en esta pantalla hasta ser admitido...", font=("Arial", 11)).pack(pady=10)

class PantallaPanelHost(tk.Frame):
    def __init__(self, parent, controller, room_code):
        super().__init__(parent)
        self.controller = controller
        self.room_code = room_code
        
        tk.Label(self, text=f"Administración de Sala: {self.room_code}", font=("Arial", 12, "bold")).pack(pady=10)
        tk.Label(self, text="Solicitudes en sala de espera:").pack(pady=5)
        
        self.box_pendientes = tk.Listbox(self, width=42, height=8)
        self.box_pendientes.pack(pady=5)
        
        self.mapa_ids = [] # Mapeo de índices de la lista gráfica con IDs reales de usuarios
        
        frame_controles = tk.Frame(self)
        frame_controles.pack(pady=15)
        tk.Button(frame_controles, text="Admitir", bg="lightgreen", width=12, command=lambda: self.responder("accept")).pack(side="left", padx=10)
        tk.Button(frame_controles, text="Rechazar", bg="lightpink", width=12, command=lambda: self.responder("reject")).pack(side="left", padx=10)

    def agregar_a_espera(self, id_usuario, nombre):
        self.box_pendientes.insert(tk.END, f"{nombre} (ID: {id_usuario})")
        self.mapa_ids.append(id_usuario)

    def responder(self, accion):
        seleccion = self.box_pendientes.curselection()
        if not seleccion:
            return
        idx = seleccion[0]
        id_pendiente = self.mapa_ids[idx]
        
        # Despachar decisión al servidor central
        socket_client.enviar_mensaje({
            "type": "ADMIT_USER",
            "userIdPendiente": id_pendiente,
            "action": accion
        })
        
        self.box_pendientes.delete(idx)
        self.mapa_ids.pop(idx)
        
        if accion == "accept":
            # Redirigir al Host de inmediato a la pantalla de la reunión activa
            self.controller.mostrar_pantalla(PantallaReunion, self.room_code)

class PantallaReunion(tk.Frame):
    def __init__(self, parent, controller, room_code):
        super().__init__(parent)
        tk.Label(self, text=f"Reunión Activa: {room_code}", font=("Arial", 14, "bold"), fg="green").pack(pady=30)
        tk.Label(self, text="✓ Canal de comunicación de salas validado.\n\nFase 3 completada con éxito.\nEl socket queda abierto para la transmisión de Chat y Video.", font=("Arial", 11)).pack(pady=10)