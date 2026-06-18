import base64
import os
import threading
import tkinter as tk
from tkinter import filedialog, scrolledtext

class PantallaSala(tk.Frame):
    def __init__(self, master, usuario, cliente_socket, codigo_sala, es_host, id_sala, on_salir):
        super().__init__(master)
        self._usuario = usuario
        self._cliente_socket = cliente_socket
        self._codigo_sala = codigo_sala
        self._es_host = es_host
        self._id_sala = id_sala
        self._on_salir = on_salir
        self._file_recv = {}
        self._download_dir = os.path.join(os.path.dirname(__file__), "..", "descargas")
        os.makedirs(self._download_dir, exist_ok=True)
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
                  bg="#2196F3", fg="white").pack(side=tk.RIGHT, padx=(2, 0))
        tk.Button(frame_input, text="📎 Archivo", command=self._enviar_archivo,
                  bg="#9C27B0", fg="white").pack(side=tk.RIGHT, padx=(0, 2))

        tk.Button(self, text="Salir de la Sala", command=self._salir,
                  bg="#f44336", fg="white", font=("Arial", 10)).pack(pady=10)

    def _registrar_callbacks(self):
        self._cliente_socket.registrar_callback("CHAT_MESSAGE", self._recibir_mensaje)
        self._cliente_socket.registrar_callback("FILE_START", self._recibir_file_start)
        self._cliente_socket.registrar_callback("FILE_CHUNK", self._recibir_file_chunk)
        self._cliente_socket.registrar_callback("FILE_END", self._recibir_file_end)
        if self._es_host:
            self._cliente_socket.registrar_callback("WAITING_ROOM_UPDATE", self._nuevo_solicitante)

    def _limpiar_callbacks(self):
        self._cliente_socket.remover_callback("CHAT_MESSAGE")
        self._cliente_socket.remover_callback("FILE_START")
        self._cliente_socket.remover_callback("FILE_CHUNK")
        self._cliente_socket.remover_callback("FILE_END")
        if self._es_host:
            self._cliente_socket.remover_callback("WAITING_ROOM_UPDATE")

    def _nuevo_solicitante(self, msg):
        self.after(0, self._agregar_solicitante, msg["solicitanteId"], msg["solicitanteNombre"])

    def _agregar_solicitante(self, uid, nombre):
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
            self.after(0, self._agregar_mensaje, f"{msg['userName']}: {msg['message']}")

    def _agregar_mensaje(self, texto):
        self._chat_text.config(state=tk.NORMAL)
        self._chat_text.insert(tk.END, texto + "\n")
        self._chat_text.see(tk.END)
        self._chat_text.config(state=tk.DISABLED)

    def _enviar_archivo(self):
        ruta = filedialog.askopenfilename(title="Seleccionar archivo")
        if not ruta:
            return
        nombre = os.path.basename(ruta)
        tamano = os.path.getsize(ruta)
        self._agregar_mensaje(f"📤 Enviando: {nombre} ({tamano} bytes)...")
        threading.Thread(target=self._enviar_archivo_thread, args=(ruta, nombre, tamano), daemon=True).start()

    def _enviar_archivo_thread(self, ruta, nombre, tamano):
        try:
            CHUNK_SIZE = 4096
            with open(ruta, "rb") as f:
                datos = base64.b64encode(f.read()).decode()
            self._cliente_socket.enviar({
                "type": "FILE_START",
                "roomCode": self._codigo_sala,
                "fileName": nombre,
                "fileSize": tamano,
                "userName": self._usuario.nombres
            })
            for i in range(0, len(datos), CHUNK_SIZE):
                self._cliente_socket.enviar({
                    "type": "FILE_CHUNK",
                    "roomCode": self._codigo_sala,
                    "fileName": nombre,
                    "data": datos[i:i + CHUNK_SIZE]
                })
            self._cliente_socket.enviar({
                "type": "FILE_END",
                "roomCode": self._codigo_sala,
                "fileName": nombre
            })
            self.after(0, self._agregar_mensaje, f"✅ Archivo enviado: {nombre}")
        except Exception as e:
            self.after(0, self._agregar_mensaje, f"❌ Error al enviar {nombre}: {e}")

    def _recibir_file_start(self, msg):
        if msg.get("userName") == self._usuario.nombres:
            return
        rid = msg["fileName"]
        self._file_recv[rid] = {
            "name": rid,
            "size": msg["fileSize"],
            "data": "",
            "user": msg["userName"]
        }
        self.after(0, self._agregar_mensaje, f"📥 Recibiendo: {rid} ({msg['fileSize']} bytes) de {msg['userName']}...")

    def _recibir_file_chunk(self, msg):
        nombre = msg.get("fileName")
        if nombre and nombre in self._file_recv:
            self._file_recv[nombre]["data"] += msg["data"]

    def _recibir_file_end(self, msg):
        rid = msg["fileName"]
        info = self._file_recv.pop(rid, None)
        if not info:
            return
        try:
            datos = base64.b64decode(info["data"])
            ruta = os.path.join(self._download_dir, rid)
            with open(ruta, "wb") as f:
                f.write(datos)
            self.after(0, self._agregar_mensaje, f"✅ Archivo recibido: {rid} (guardado en descargas/)")
        except Exception as e:
            self.after(0, self._agregar_mensaje, f"❌ Error al guardar {rid}: {e}")

    def _salir(self):
        self._cliente_socket.enviar({"type": "LEAVE_ROOM", "roomCode": self._codigo_sala})
        self._limpiar_callbacks()
        self._on_salir()
