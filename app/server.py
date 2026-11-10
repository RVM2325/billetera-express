"""
Servidor HTTP y API REST con soporte de Autenticación y Control de Acceso.
Sirve archivos estáticos y gestiona rutas protegidas para cada usuario.
"""
import http.server
import json
import os
import re
from urllib.parse import urlparse, parse_qs
from .services import FinanzasService

STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")

class FinanzasRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.service = FinanzasService()
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def _responder_json(self, datos, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Session-Token")
        self.end_headers()
        self.wfile.write(json.dumps(datos, ensure_ascii=False).encode("utf-8"))

    def _obtener_token(self) -> str:
        """Extrae el token del header Authorization o X-Session-Token."""
        auth_header = self.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            return auth_header[7:].strip()
        token_custom = self.headers.get("X-Session-Token", "")
        if token_custom:
            return token_custom.strip()
        return ""

    def _obtener_usuario_autenticado(self):
        """Valida el token y retorna el usuario autenticado o None."""
        token = self._obtener_token()
        if not token:
            return None
        return self.service.obtener_usuario_por_token(token)

    def _leer_cuerpo_json(self):
        longitud = int(self.headers.get("Content-Length", 0))
        if longitud == 0:
            return {}
        cuerpo = self.rfile.read(longitud).decode("utf-8")
        return json.loads(cuerpo)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Session-Token")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        # Rutas públicas
        if path == "/api/categorias":
            categorias = self.service.listar_categorias()
            self._responder_json(categorias)
            return

        # Rutas de autenticación
        if path == "/api/auth/me":
            usuario = self._obtener_usuario_autenticado()
            if not usuario:
                self._responder_json({"error": "Sesión inválida o expirada"}, 401)
                return
            self._responder_json({"usuario": usuario})
            return

        # Rutas de finanzas protegidas por usuario
        if path == "/api/resumen":
            usuario = self._obtener_usuario_autenticado()
            if not usuario:
                self._responder_json({"error": "No autorizado. Inicia sesión primero."}, 401)
                return
            resumen = self.service.obtener_resumen(usuario["id"])
            self._responder_json(resumen)
            return

        elif path == "/api/transacciones":
            usuario = self._obtener_usuario_autenticado()
            if not usuario:
                self._responder_json({"error": "No autorizado. Inicia sesión primero."}, 401)
                return
            tipo_filtro = query.get("tipo", [None])[0]
            transacciones = self.service.listar_transacciones(usuario_id=usuario["id"], tipo=tipo_filtro)
            self._responder_json(transacciones)
            return

        # Si no es API, servir archivos estáticos (index.html, app.js, etc.)
        if path == "/" or path == "":
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # Registro de nuevo usuario
        if path == "/api/auth/register":
            try:
                datos = self._leer_cuerpo_json()
                resultado = self.service.registrar_usuario(
                    username=datos.get("username", ""),
                    password=datos.get("password", ""),
                    nombre=datos.get("nombre", ""),
                    icono=datos.get("icono", "👤")
                )
                self._responder_json(resultado, 201)
            except ValueError as e:
                self._responder_json({"error": str(e)}, 400)
            except Exception as e:
                self._responder_json({"error": f"Error del servidor: {str(e)}"}, 500)
            return

        # Inicio de sesión
        elif path == "/api/auth/login":
            try:
                datos = self._leer_cuerpo_json()
                resultado = self.service.iniciar_sesion(
                    username=datos.get("username", ""),
                    password=datos.get("password", "")
                )
                self._responder_json(resultado, 200)
            except ValueError as e:
                self._responder_json({"error": str(e)}, 400)
            except Exception as e:
                self._responder_json({"error": f"Error del servidor: {str(e)}"}, 500)
            return

        # Cierre de sesión
        elif path == "/api/auth/logout":
            token = self._obtener_token()
            self.service.cerrar_sesion(token)
            self._responder_json({"mensaje": "Sesión cerrada correctamente"})
            return

        # Registrar transacción (Protegida)
        elif path == "/api/transacciones":
            usuario = self._obtener_usuario_autenticado()
            if not usuario:
                self._responder_json({"error": "No autorizado. Inicia sesión primero."}, 401)
                return

            try:
                datos = self._leer_cuerpo_json()
                tx = self.service.registrar_transaccion(datos, usuario_id=usuario["id"])
                self._responder_json(tx.a_diccionario(), 201)
            except ValueError as e:
                self._responder_json({"error": str(e)}, 400)
            except Exception as e:
                self._responder_json({"error": f"Error interno: {str(e)}"}, 500)
            return

        self._responder_json({"error": "Ruta no encontrada"}, 404)

    def do_DELETE(self):
        parsed = urlparse(self.path)
        match = re.match(r"^/api/transacciones/(\d+)$", parsed.path)
        if match:
            usuario = self._obtener_usuario_autenticado()
            if not usuario:
                self._responder_json({"error": "No autorizado. Inicia sesión primero."}, 401)
                return

            transaccion_id = int(match.group(1))
            eliminado = self.service.eliminar_transaccion(transaccion_id, usuario_id=usuario["id"])
            if eliminado:
                self._responder_json({"mensaje": "Transacción eliminada con éxito", "id": transaccion_id})
            else:
                self._responder_json({"error": "Transacción no encontrada o no tienes permiso para borrarla"}, 404)
            return

        self._responder_json({"error": "Ruta no encontrada"}, 404)
