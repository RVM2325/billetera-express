"""
Capa de acceso a datos y gestión de base de datos SQLite con soporte multiusuario.
"""
import sqlite3
import os
from typing import Optional, Union
from .security import hashear_password

DB_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "finanzas.db")

def obtener_conexion(origen: Optional[Union[str, sqlite3.Connection]] = None) -> sqlite3.Connection:
    """Retorna una conexión a SQLite configurada con row_factory para diccionarios."""
    if isinstance(origen, sqlite3.Connection):
        return origen

    path = origen if origen is not None else DB_FILE_PATH
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def inicializar_bd(origen: Optional[Union[str, sqlite3.Connection]] = None):
    """Crea las tablas necesarias y siembra datos iniciales con soporte para cuentas de usuario."""
    conn = obtener_conexion(origen)
    try:
        cursor = conn.cursor()

        # 1. Tabla de usuarios
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                nombre TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                icono TEXT DEFAULT '👤',
                creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 2. Tabla de sesiones activas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sesiones (
                token TEXT PRIMARY KEY,
                usuario_id INTEGER NOT NULL,
                creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE
            );
        """)

        # 3. Tabla de categorías
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categorias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE,
                tipo TEXT NOT NULL CHECK(tipo IN ('ingreso', 'gasto')),
                icono TEXT DEFAULT '🏷️'
            );
        """)

        # 4. Tabla de transacciones vinculadas al usuario
        # Verificamos si existe una versión vieja sin la columna usuario_id
        cursor.execute("PRAGMA table_info(transacciones);")
        columnas = [col["name"] for col in cursor.fetchall()]
        if columnas and "usuario_id" not in columnas:
            cursor.execute("DROP TABLE transacciones;")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transacciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER NOT NULL,
                tipo TEXT NOT NULL CHECK(tipo IN ('ingreso', 'gasto')),
                categoria TEXT NOT NULL,
                monto REAL NOT NULL CHECK(monto > 0),
                descripcion TEXT NOT NULL,
                fecha TEXT NOT NULL,
                FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE
            );
        """)

        # 5. Sembrar categorías iniciales si no existen
        cursor.execute("SELECT COUNT(*) as total FROM categorias;")
        if cursor.fetchone()["total"] == 0:
            categorias_default = [
                ("Sueldo", "ingreso", "💼"),
                ("Freelance", "ingreso", "💻"),
                ("Ventas / Negocio", "ingreso", "📈"),
                ("Otros ingresos", "ingreso", "💵"),
                ("Alimentación", "gasto", "🍔"),
                ("Transporte", "gasto", "🚌"),
                ("Vivienda y Servicios", "gasto", "💡"),
                ("Educación", "gasto", "📚"),
                ("Entretenimiento", "gasto", "🎮"),
                ("Salud", "gasto", "💊"),
                ("Compras personales", "gasto", "🛍️")
            ]
            cursor.executemany(
                "INSERT INTO categorias (nombre, tipo, icono) VALUES (?, ?, ?);",
                categorias_default
            )

        # 6. Sembrar usuarios demo si no existen
        cursor.execute("SELECT COUNT(*) as total FROM usuarios;")
        if cursor.fetchone()["total"] == 0:
            usuarios_demo = [
                ("raul", "Raúl", hashear_password("123456"), "👨‍💻"),
                ("mama", "Mamá", hashear_password("123456"), "👩"),
                ("papa", "Papá", hashear_password("123456"), "👨")
            ]
            cursor.executemany(
                "INSERT INTO usuarios (username, nombre, password_hash, icono) VALUES (?, ?, ?, ?);",
                usuarios_demo
            )

            # Obtener el ID de raul para asociarle sus transacciones iniciales
            cursor.execute("SELECT id FROM usuarios WHERE username = 'raul';")
            raul_id = cursor.fetchone()["id"]

            transacciones_raul = [
                (raul_id, "ingreso", "Sueldo", 3200.00, "Pago de quincena", "2026-11-01"),
                (raul_id, "ingreso", "Freelance", 650.00, "Diseño de landing page", "2026-11-03"),
                (raul_id, "gasto", "Vivienda y Servicios", 450.00, "Servicios luz, agua e internet", "2026-11-04"),
                (raul_id, "gasto", "Alimentación", 185.50, "Compras de la semana en el mercado", "2026-11-05"),
                (raul_id, "gasto", "Transporte", 60.00, "Recarga de tarjeta Metropolitano", "2026-11-06"),
                (raul_id, "gasto", "Educación", 320.00, "Mensualidad curso especialización", "2026-11-07")
            ]
            cursor.executemany(
                """
                INSERT INTO transacciones (usuario_id, tipo, categoria, monto, descripcion, fecha)
                VALUES (?, ?, ?, ?, ?, ?);
                """,
                transacciones_raul
            )

            # Sembrar una transacción de ejemplo para Mamá para comprobar aislamiento
            cursor.execute("SELECT id FROM usuarios WHERE username = 'mama';")
            mama_id = cursor.fetchone()["id"]
            transacciones_mama = [
                (mama_id, "ingreso", "Ventas / Negocio", 1200.00, "Venta por catálogo", "2026-11-02"),
                (mama_id, "gasto", "Alimentación", 250.00, "Supermercado quincena", "2026-11-04")
            ]
            cursor.executemany(
                """
                INSERT INTO transacciones (usuario_id, tipo, categoria, monto, descripcion, fecha)
                VALUES (?, ?, ?, ?, ?, ?);
                """,
                transacciones_mama
            )

        conn.commit()
    finally:
        if not isinstance(origen, sqlite3.Connection):
            conn.close()
