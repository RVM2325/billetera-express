#!/usr/bin/env python3
"""
Punto de entrada principal para Billetera Express.
Inicializa la base de datos y arranca el servidor web local.
"""
import os
import socket
from http.server import HTTPServer
from app.database import inicializar_bd
from app.server import FinanzasRequestHandler

DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = int(os.environ.get("PORT", 8000))

def obtener_ip_local() -> str:
    """Detecta la IP local de la máquina en la red Wi-Fi/LAN."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"

def buscar_puerto_disponible(host: str, puerto_inicio: int) -> int:
    """Busca el primer puerto disponible a partir de puerto_inicio."""
    puerto = puerto_inicio
    while puerto < puerto_inicio + 100:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex((host, puerto)) != 0:
                return puerto
            puerto += 1
    return puerto_inicio

def main():
    print("=" * 60)
    print("🇵🇪 Billetera Express - Gestor Financiero Personal")
    print("=" * 60)
    print("⚙️  Inicializando base de datos SQLite...")
    inicializar_bd()
    print("✅ Base de datos lista con categorías y datos de prueba.")

    ip_red = obtener_ip_local()
    puerto = buscar_puerto_disponible("0.0.0.0", DEFAULT_PORT)
    servidor = HTTPServer((DEFAULT_HOST, puerto), FinanzasRequestHandler)

    print(f"\n🚀 Servidor web activo y listo para compartir:")
    print(f"   💻 Desde esta PC:      http://localhost:{puerto}")
    print(f"   📱 Desde celulares/PC: http://{ip_red}:{puerto} (en el mismo Wi-Fi)")
    print(f"\n📌 Presiona Ctrl + C para detener el servidor.\n")
    print("-" * 60)

    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Apagando el servidor con calma...")
        servidor.server_close()
        print("👋 ¡Listo! Servidor detenido correctamente.")

if __name__ == "__main__":
    main()
