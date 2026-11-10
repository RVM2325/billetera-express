"""
Capa de Servicios y Lógica de Negocio con soporte Multiusuario.
Gestiona autenticación, sesiones, control de acceso y cálculo de métricas financieras por usuario.
"""
import sqlite3
from typing import List, Dict, Any, Optional, Union
from .database import obtener_conexion
from .models import Transaccion, Categoria, Usuario
from .security import hashear_password, verificar_password, generar_token_sesion

class FinanzasService:
    def __init__(self, origen: Optional[Union[str, sqlite3.Connection]] = None):
        self.origen = origen

    def _ejecutar(self, callback):
        """Ejecuta una operación en la base de datos de forma segura."""
        if isinstance(self.origen, sqlite3.Connection):
            return callback(self.origen)
        else:
            with obtener_conexion(self.origen) as conn:
                return callback(conn)

    # -------------------------------------------------------------
    # SERVICIOS DE AUTENTICACIÓN Y USUARIOS
    # -------------------------------------------------------------

    def registrar_usuario(self, username: str, password: str, nombre: str, icono: str = "👤") -> Dict[str, Any]:
        """Registra un nuevo usuario con contraseña hasheada y retorna su sesión."""
        u = Usuario(id=None, username=username, nombre=nombre, icono=icono or "👤")
        if not password or len(password) < 4:
            raise ValueError("La contraseña debe tener al menos 4 caracteres.")

        pwd_hash = hashear_password(password)

        def operacion(conn):
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM usuarios WHERE username = ?;", (u.username,))
            if cursor.fetchone():
                raise ValueError("El nombre de usuario ya está en uso. Elige otro.")

            cursor.execute(
                """
                INSERT INTO usuarios (username, nombre, password_hash, icono)
                VALUES (?, ?, ?, ?);
                """,
                (u.username, u.nombre, pwd_hash, u.icono)
            )
            usuario_id = cursor.lastrowid

            token = generar_token_sesion()
            cursor.execute(
                "INSERT INTO sesiones (token, usuario_id) VALUES (?, ?);",
                (token, usuario_id)
            )
            conn.commit()

            return {
                "token": token,
                "usuario": {
                    "id": usuario_id,
                    "username": u.username,
                    "nombre": u.nombre,
                    "icono": u.icono
                }
            }

        return self._ejecutar(operacion)

    def iniciar_sesion(self, username: str, password: str) -> Dict[str, Any]:
        """Valida credenciales y genera un nuevo token de sesión."""
        username_limpio = (username or "").strip().lower()
        if not username_limpio or not password:
            raise ValueError("Debes ingresar usuario y contraseña.")

        def operacion(conn):
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, username, nombre, password_hash, icono FROM usuarios WHERE username = ?;",
                (username_limpio,)
            )
            fila = cursor.fetchone()
            if not fila or not verificar_password(password, fila["password_hash"]):
                raise ValueError("Usuario o contraseña incorrectos.")

            usuario_id = fila["id"]
            token = generar_token_sesion()
            cursor.execute(
                "INSERT INTO sesiones (token, usuario_id) VALUES (?, ?);",
                (token, usuario_id)
            )
            conn.commit()

            return {
                "token": token,
                "usuario": {
                    "id": usuario_id,
                    "username": fila["username"],
                    "nombre": fila["nombre"],
                    "icono": fila["icono"]
                }
            }

        return self._ejecutar(operacion)

    def cerrar_sesion(self, token: str) -> bool:
        """Elimina el token de sesión de la base de datos."""
        if not token:
            return False

        def operacion(conn):
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sesiones WHERE token = ?;", (token,))
            conn.commit()
            return cursor.rowcount > 0

        return self._ejecutar(operacion)

    def obtener_usuario_por_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verifica un token y retorna los datos del usuario autenticado."""
        if not token:
            return None

        def operacion(conn):
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT u.id, u.username, u.nombre, u.icono
                FROM sesiones s
                JOIN usuarios u ON s.usuario_id = u.id
                WHERE s.token = ?;
                """,
                (token,)
            )
            fila = cursor.fetchone()
            return dict(fila) if fila else None

        return self._ejecutar(operacion)

    # -------------------------------------------------------------
    # SERVICIOS DE MOVIMIENTOS FINANCIEROS (AISLADOS POR USUARIO)
    # -------------------------------------------------------------

    def registrar_transaccion(self, datos: Dict[str, Any], usuario_id: int) -> Transaccion:
        """Crea y persiste una nueva transacción asociada al usuario autenticado."""
        tx = Transaccion(
            id=None,
            usuario_id=usuario_id,
            tipo=str(datos.get("tipo", "")).lower(),
            categoria=str(datos.get("categoria", "")),
            monto=float(datos.get("monto", 0)),
            descripcion=str(datos.get("descripcion", "")),
            fecha=str(datos.get("fecha", ""))
        )

        def operacion(conn):
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO transacciones (usuario_id, tipo, categoria, monto, descripcion, fecha)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (tx.usuario_id, tx.tipo, tx.categoria, tx.monto, tx.descripcion, tx.fecha)
            )
            tx.id = cursor.lastrowid
            conn.commit()
            return tx

        return self._ejecutar(operacion)

    def listar_transacciones(self, usuario_id: int, tipo: Optional[str] = None, limite: int = 50) -> List[Dict[str, Any]]:
        """Devuelve el historial ordenado de transacciones exclusivas del usuario."""
        def operacion(conn):
            cursor = conn.cursor()
            if tipo in ("ingreso", "gasto"):
                cursor.execute(
                    """
                    SELECT id, usuario_id, tipo, categoria, monto, descripcion, fecha
                    FROM transacciones
                    WHERE usuario_id = ? AND tipo = ?
                    ORDER BY fecha DESC, id DESC
                    LIMIT ?
                    """,
                    (usuario_id, tipo, limite)
                )
            else:
                cursor.execute(
                    """
                    SELECT id, usuario_id, tipo, categoria, monto, descripcion, fecha
                    FROM transacciones
                    WHERE usuario_id = ?
                    ORDER BY fecha DESC, id DESC
                    LIMIT ?
                    """,
                    (usuario_id, limite)
                )
            filas = cursor.fetchall()
            return [dict(f) for f in filas]

        return self._ejecutar(operacion)

    def eliminar_transaccion(self, transaccion_id: int, usuario_id: int) -> bool:
        """Elimina una transacción garantizando que pertenezca al usuario solicitante."""
        def operacion(conn):
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM transacciones WHERE id = ? AND usuario_id = ?;",
                (transaccion_id, usuario_id)
            )
            conn.commit()
            return cursor.rowcount > 0

        return self._ejecutar(operacion)

    def obtener_resumen(self, usuario_id: int) -> Dict[str, Any]:
        """Calcula el balance general y métricas exclusivas del usuario."""
        def operacion(conn):
            cursor = conn.cursor()

            # Totales de ingresos y gastos del usuario
            cursor.execute("""
                SELECT
                    COALESCE(SUM(CASE WHEN tipo = 'ingreso' THEN monto ELSE 0 END), 0) AS total_ingresos,
                    COALESCE(SUM(CASE WHEN tipo = 'gasto' THEN monto ELSE 0 END), 0) AS total_gastos,
                    COUNT(*) AS cantidad_transacciones
                FROM transacciones
                WHERE usuario_id = ?;
            """, (usuario_id,))
            fila_totales = cursor.fetchone()
            total_ingresos = round(fila_totales["total_ingresos"], 2)
            total_gastos = round(fila_totales["total_gastos"], 2)
            saldo_neto = round(total_ingresos - total_gastos, 2)
            cantidad = fila_totales["cantidad_transacciones"]

            # Desglose de gastos por categoría
            cursor.execute("""
                SELECT categoria, ROUND(SUM(monto), 2) as total, COUNT(*) as cantidad
                FROM transacciones
                WHERE usuario_id = ? AND tipo = 'gasto'
                GROUP BY categoria
                ORDER BY total DESC;
            """, (usuario_id,))
            gastos_categoria = [dict(r) for r in cursor.fetchall()]

            # Desglose de ingresos por categoría
            cursor.execute("""
                SELECT categoria, ROUND(SUM(monto), 2) as total, COUNT(*) as cantidad
                FROM transacciones
                WHERE usuario_id = ? AND tipo = 'ingreso'
                GROUP BY categoria
                ORDER BY total DESC;
            """, (usuario_id,))
            ingresos_categoria = [dict(r) for r in cursor.fetchall()]

            return {
                "total_ingresos": total_ingresos,
                "total_gastos": total_gastos,
                "saldo_neto": saldo_neto,
                "total_movimientos": cantidad,
                "gastos_por_categoria": gastos_categoria,
                "ingresos_por_categoria": ingresos_categoria
            }

        return self._ejecutar(operacion)

    def listar_categorias(self) -> List[Dict[str, Any]]:
        """Obtiene el catálogo de categorías disponibles con sus iconos."""
        def operacion(conn):
            cursor = conn.cursor()
            cursor.execute("SELECT id, nombre, tipo, icono FROM categorias ORDER BY nombre ASC;")
            return [dict(r) for r in cursor.fetchall()]

        return self._ejecutar(operacion)
