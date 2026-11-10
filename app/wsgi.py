"""
Adaptador WSGI estándar para Billetera Express.
Permite desplegar la aplicación en servidores WSGI de producción
(como PythonAnywhere, Gunicorn, uWSGI) usando únicamente la librería estándar.
"""
import json
import os
import re
import mimetypes
from urllib.parse import parse_qs
from .services import FinanzasService

STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
service = FinanzasService()

def application(environ, start_response):
    metodo = environ.get("REQUEST_METHOD", "GET").upper()
    path = environ.get("PATH_INFO", "/")
    if path == "" or path == "/":
        path = "/index.html"

    # CORS Headers básicos
    cors_headers = [
        ("Access-Control-Allow-Origin", "*"),
        ("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS"),
        ("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Session-Token")
    ]

    if metodo == "OPTIONS":
        start_response("204 No Content", cors_headers)
        return [b""]

    # Extraer token de autorización
    auth_header = environ.get("HTTP_AUTHORIZATION", "")
    token = ""
    if auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
    elif "HTTP_X_SESSION_TOKEN" in environ:
        token = environ.get("HTTP_X_SESSION_TOKEN", "").strip()

    usuario_autenticado = service.obtener_usuario_por_token(token) if token else None

    def responder_json(datos, status="200 OK"):
        body = json.dumps(datos, ensure_ascii=False).encode("utf-8")
        headers = [
            ("Content-Type", "application/json; charset=utf-8"),
            ("Content-Length", str(len(body))),
            *cors_headers
        ]
        start_response(status, headers)
        return [body]

    def leer_json_body():
        try:
            length = int(environ.get("CONTENT_LENGTH", 0))
            if length > 0:
                raw = environ["wsgi.input"].read(length).decode("utf-8")
                return json.loads(raw)
        except Exception:
            pass
        return {}

    # -------------------------------------------------------------
    # RUTAS DE LA API REST
    # -------------------------------------------------------------
    if path.startswith("/api/"):
        query = parse_qs(environ.get("QUERY_STRING", ""))

        if path == "/api/categorias" and metodo == "GET":
            return responder_json(service.listar_categorias())

        # Auth
        if path == "/api/auth/register" and metodo == "POST":
            datos = leer_json_body()
            try:
                res = service.registrar_usuario(
                    username=datos.get("username", ""),
                    password=datos.get("password", ""),
                    nombre=datos.get("nombre", ""),
                    icono=datos.get("icono", "👤")
                )
                return responder_json(res, "201 Created")
            except ValueError as e:
                return responder_json({"error": str(e)}, "400 Bad Request")
            except Exception as e:
                return responder_json({"error": str(e)}, "500 Internal Server Error")

        if path == "/api/auth/login" and metodo == "POST":
            datos = leer_json_body()
            try:
                res = service.iniciar_sesion(
                    username=datos.get("username", ""),
                    password=datos.get("password", "")
                )
                return responder_json(res, "200 OK")
            except ValueError as e:
                return responder_json({"error": str(e)}, "400 Bad Request")
            except Exception as e:
                return responder_json({"error": str(e)}, "500 Internal Server Error")

        if path == "/api/auth/logout" and metodo == "POST":
            if token:
                service.cerrar_sesion(token)
            return responder_json({"mensaje": "Sesión cerrada correctamente"})

        if path == "/api/auth/me" and metodo == "GET":
            if not usuario_autenticado:
                return responder_json({"error": "Sesión inválida o expirada"}, "401 Unauthorized")
            return responder_json({"usuario": usuario_autenticado})

        # Rutas protegidas
        if not usuario_autenticado:
            return responder_json({"error": "No autorizado. Inicia sesión primero."}, "401 Unauthorized")

        usuario_id = usuario_autenticado["id"]

        if path == "/api/resumen" and metodo == "GET":
            return responder_json(service.obtener_resumen(usuario_id))

        if path == "/api/transacciones" and metodo == "GET":
            filtro_tipo = query.get("tipo", [None])[0]
            return responder_json(service.listar_transacciones(usuario_id, tipo=filtro_tipo))

        if path == "/api/transacciones" and metodo == "POST":
            datos = leer_json_body()
            try:
                tx = service.registrar_transaccion(datos, usuario_id=usuario_id)
                return responder_json(tx.a_diccionario(), "201 Created")
            except ValueError as e:
                return responder_json({"error": str(e)}, "400 Bad Request")
            except Exception as e:
                return responder_json({"error": str(e)}, "500 Internal Server Error")

        match_del = re.match(r"^/api/transacciones/(\d+)$", path)
        if match_del and metodo == "DELETE":
            tx_id = int(match_del.group(1))
            if service.eliminar_transaccion(tx_id, usuario_id=usuario_id):
                return responder_json({"mensaje": "Transacción eliminada con éxito", "id": tx_id})
            return responder_json({"error": "Transacción no encontrada o sin permiso"}, "404 Not Found")

        return responder_json({"error": "Ruta de API no encontrada"}, "404 Not Found")

    # -------------------------------------------------------------
    # ARCHIVOS ESTÁTICOS
    # -------------------------------------------------------------
    ruta_archivo = os.path.normpath(os.path.join(STATIC_DIR, path.lstrip("/")))
    if not ruta_archivo.startswith(STATIC_DIR) or not os.path.isfile(ruta_archivo):
        start_response("404 Not Found", [("Content-Type", "text/plain")])
        return [b"Archivo no encontrado"]

    mime, _ = mimetypes.guess_type(ruta_archivo)
    mime = mime or "application/octet-stream"

    with open(ruta_archivo, "rb") as f:
        contenido = f.read()

    headers = [
        ("Content-Type", mime),
        ("Content-Length", str(len(contenido))),
        *cors_headers
    ]
    start_response("200 OK", headers)
    return [contenido]
