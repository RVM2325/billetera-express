"""
Módulo de seguridad: Hashing seguro de contraseñas y generación de tokens de sesión.
Usa PBKDF2-HMAC-SHA256 y tokens criptográficos de la librería estándar de Python.
"""
import hashlib
import secrets

def hashear_password(password: str) -> str:
    """Genera un hash seguro con sal aleatoria usando PBKDF2-HMAC-SHA256."""
    salt = secrets.token_hex(16)
    hash_bytes = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000)
    return f"{salt}${hash_bytes.hex()}"

def verificar_password(password: str, hash_almacenado: str) -> bool:
    """Verifica si la contraseña ingresada coincide con el hash almacenado."""
    try:
        partes = hash_almacenado.split("$")
        if len(partes) != 2:
            return False
        salt, hash_real = partes
        hash_candidato = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000).hex()
        return secrets.compare_digest(hash_real, hash_candidato)
    except Exception:
        return False

def generar_token_sesion() -> str:
    """Genera un token seguro y único para identificar la sesión del usuario."""
    return secrets.token_hex(32)
