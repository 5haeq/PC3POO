import tkinter as tk
from tkinter import scrolledtext

class PantallaSala(tk.Frame):
    def __init__(self, master, usuario, cliente_socket, codigo_sala, es_host, id_sala, on_salir):
        super().__init__(master)
        self._usuario = usuario
        self._cliente_socket = cliente_socket
        self._codigo_sala = codigo_sala
        self._es_host = es_host
        self._id_sala = id_sala
        self._on_salir = on_salir
        self._crear_widgets()
        self._registrar_callbacks()

    def _crear_widgets(self):
        tk.Label(self, text=f"Sala: {self._codigo_sala}",
                 font=("Arial", 12, "bold")).pack(pady=(10, 5))

        frame_principal = tk.Frame(self)
        frame_principal.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        if self._es_host:
            frame_izq = tk.Frame(frame_principal, width=200)
            frame_izq.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 5))
            frame_izq.pack_propagate(False)

            tk.Label(frame_izq, text="Sala de Espera",
                     font=("Arial", 10, "bold")).pack(pady=(0, 5))
            self._lista_espera = tk.Listbox(frame_izq, height=10)
            self._lista_espera.pack(fill=tk.BOTH, expand=True)

            frame_botones = tk.Frame(frame_izq)
            frame_botones.pack(fill=tk.X, pady=5)
            tk.Button(frame_botones, text="Admitir", command=self._admitir,
                      bg="#4CAF50", fg="white", width=8).pack(side=tk.LEFT, padx=2)
            tk.Button(frame_botones, text="Rechazar", command=self._rechazar,
                      bg="#f44336", fg="white", width=8).pack(side=tk.LEFT, padx=2)

            self._solicitantes = {}

            frame_chat = tk.Frame(frame_principal)
            frame_chat.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        else:
            frame_chat = frame_principal

        tk.Label(frame_chat, text="Chat", font=("Arial", 10, "bold")).pack()
        self._chat_text = scrolledtext.ScrolledText(frame_chat, height=15, state=tk.DISABLED)
        self._chat_text.pack(fill=tk.BOTH, expand=True)

        frame_input = tk.Frame(frame_chat)
        frame_input.pack(fill=tk.X, pady=5)
        self._entrada_msg = tk.Entry(frame_input)
        self._entrada_msg.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self._entrada_msg.bind("<Return>", lambda e: self._enviar_mensaje())
        tk.Button(frame_input, text="Enviar", command=self._enviar_mensaje,
                  bg="#2196F3", fg="white").pack(side=tk.RIGHT, padx=(5, 0))

        tk.Button(self, text="Salir de la Sala", command=self._salir,
                  bg="#f44336", fg="white", font=("Arial", 10)).pack(pady=10)

    def _registrar_callbacks(self):
        self._cliente_socket.registrar_callback("CHAT_MESSAGE", self._recibir_mensaje)
        if self._es_host:
            self._cliente_socket.registrar_callback("WAITING_ROOM_UPDATE", self._nuevo_solicitante)

    def _limpiar_callbacks(self):
        self._cliente_socket.remover_callback("CHAT_MESSAGE")
        if self._es_host:
            self._cliente_socket.remover_callback("WAITING_ROOM_UPDATE")

    def _nuevo_solicitante(self, msg):
        uid = msg["solicitanteId"]
        nombre = msg["solicitanteNombre"]
        self._solicitantes[uid] = {"nombre": nombre}
        self._lista_espera.insert(tk.END, f"{nombre} (ID: {uid})")

    def _admitir(self):
        sel = self._lista_espera.curselection()
        if not sel:
            return
        texto = self._lista_espera.get(sel[0])
        uid = int(texto.split("ID: ")[1].rstrip(")"))
        self._cliente_socket.enviar({
            "type": "ADMIT_USER",
            "idSala": self._id_sala,
            "idUsuario": uid
        })
        self._lista_espera.delete(sel[0])
        self._solicitantes.pop(uid, None)

    def _rechazar(self):
        sel = self._lista_espera.curselection()
        if not sel:
            return
        texto = self._lista_espera.get(sel[0])
        uid = int(texto.split("ID: ")[1].rstrip(")"))
        self._cliente_socket.enviar({
            "type": "REJECT_USER",
            "idSala": self._id_sala,
            "idUsuario": uid
        })
        self._lista_espera.delete(sel[0])
        self._solicitantes.pop(uid, None)

    def _enviar_mensaje(self):
        texto = self._entrada_msg.get().strip()
        if not texto:
            return
        self._cliente_socket.enviar({
            "type": "CHAT_MESSAGE",
            "roomCode": self._codigo_sala,
            "userName": self._usuario.nombres,
            "message": texto
        })
        self._agregar_mensaje(f"Tú: {texto}")
        self._entrada_msg.delete(0, tk.END)

    def _recibir_mensaje(self, msg):
        if msg.get("userName") != self._usuario.nombres:
            self._agregar_mensaje(f"{msg['userName']}: {msg['message']}")

    def _agregar_mensaje(self, texto):
        self._chat_text.config(state=tk.NORMAL)
        self._chat_text.insert(tk.END, texto + "\n")
        self._chat_text.see(tk.END)
        self._chat_text.config(state=tk.DISABLED)

    def _salir(self):
        self._cliente_socket.enviar({"type": "LEAVE_ROOM", "roomCode": self._codigo_sala})
        self._limpiar_callbacks()
        self._on_salir()
