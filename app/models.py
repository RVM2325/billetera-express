"""
Modelos de dominio para el Gestor de Finanzas con soporte multiusuario.
Implementa clases POO con validación de datos y tipado.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Usuario:
    id: Optional[int]
    username: str
    nombre: str
    icono: str = "👤"
    password_hash: Optional[str] = None
    creado_en: Optional[str] = None

    def __post_init__(self):
        self.username = self.username.strip().lower()
        self.nombre = self.nombre.strip()
        if not self.username or len(self.username) < 3:
            raise ValueError("El usuario debe tener al menos 3 caracteres.")
        if not self.nombre:
            raise ValueError("El nombre no puede estar vacío.")

    def a_perfil(self) -> dict:
        """Devuelve el perfil seguro sin hashes ni contraseñas."""
        return {
            "id": self.id,
            "username": self.username,
            "nombre": self.nombre,
            "icono": self.icono
        }

@dataclass
class Categoria:
    id: Optional[int]
    nombre: str
    tipo: str  # 'ingreso' o 'gasto'
    icono: str = "🏷️"

    def __post_init__(self):
        if self.tipo not in ("ingreso", "gasto"):
            raise ValueError("El tipo de categoría debe ser 'ingreso' o 'gasto'.")
        self.nombre = self.nombre.strip()
        if not self.nombre:
            raise ValueError("El nombre de la categoría no puede estar vacío.")

@dataclass
class Transaccion:
    id: Optional[int]
    usuario_id: int
    tipo: str  # 'ingreso' o 'gasto'
    categoria: str
    monto: float
    descripcion: str
    fecha: str  # Formato YYYY-MM-DD

    def __post_init__(self):
        if self.usuario_id is None or self.usuario_id <= 0:
            raise ValueError("La transacción debe pertenecer a un usuario válido.")
        if self.tipo not in ("ingreso", "gasto"):
            raise ValueError("El tipo debe ser 'ingreso' o 'gasto'.")
        if self.monto <= 0:
            raise ValueError("El monto debe ser un número positivo mayor a 0.")
        self.descripcion = self.descripcion.strip()
        if not self.descripcion:
            raise ValueError("La descripción no puede estar vacía.")
        if not self.fecha:
            self.fecha = datetime.now().strftime("%Y-%m-%d")
        else:
            try:
                datetime.strptime(self.fecha, "%Y-%m-%d")
            except ValueError:
                raise ValueError("La fecha debe tener el formato YYYY-MM-DD.")

    def a_diccionario(self) -> dict:
        return {
            "id": self.id,
            "usuario_id": self.usuario_id,
            "tipo": self.tipo,
            "categoria": self.categoria,
            "monto": round(self.monto, 2),
            "descripcion": self.descripcion,
            "fecha": self.fecha
        }
