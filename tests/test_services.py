"""
Pruebas unitarias para los modelos, servicios y sistema de autenticación multiusuario.
"""
import unittest
import sqlite3
from app.database import inicializar_bd
from app.services import FinanzasService

class TestFinanzasMultiusuario(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        inicializar_bd(self.conn)
        self.service = FinanzasService(self.conn)

    def tearDown(self):
        self.conn.close()

    def test_registro_e_inicio_sesion(self):
        # 1. Registrar usuario nuevo
        reg = self.service.registrar_usuario(
            username="carlos",
            password="mipassword123",
            nombre="Carlos Vía",
            icono="😎"
        )
        self.assertIn("token", reg)
        self.assertEqual(reg["usuario"]["username"], "carlos")
        self.assertEqual(reg["usuario"]["nombre"], "Carlos Vía")

        # 2. Iniciar sesión con credenciales correctas
        login = self.service.iniciar_sesion("carlos", "mipassword123")
        self.assertIsNotNone(login["token"])

        # 3. Validar token
        user = self.service.obtener_usuario_por_token(login["token"])
        self.assertIsNotNone(user)
        self.assertEqual(user["username"], "carlos")

    def test_login_credenciales_invalidas(self):
        # Contraseña errónea
        with self.assertRaises(ValueError):
            self.service.iniciar_sesion("raul", "password_incorrecto")

        # Usuario no existente
        with self.assertRaises(ValueError):
            self.service.iniciar_sesion("no_existo", "123456")

    def test_aislamiento_de_datos_entre_usuarios(self):
        """Comprueba que el Usuario A no pueda ver las transacciones ni balances del Usuario B."""
        login_raul = self.service.iniciar_sesion("raul", "123456")
        login_mama = self.service.iniciar_sesion("mama", "123456")

        raul_id = login_raul["usuario"]["id"]
        mama_id = login_mama["usuario"]["id"]

        # Insertar transacción específica para Raúl
        tx_raul = self.service.registrar_transaccion({
            "tipo": "gasto",
            "categoria": "Entretenimiento",
            "monto": 80.0,
            "descripcion": "Cine con amigos",
            "fecha": "2026-11-09"
        }, usuario_id=raul_id)

        # Insertar transacción específica para Mamá
        tx_mama = self.service.registrar_transaccion({
            "tipo": "gasto",
            "categoria": "Salud",
            "monto": 150.0,
            "descripcion": "Consulta médica",
            "fecha": "2026-11-09"
        }, usuario_id=mama_id)

        # Transacciones de Raúl
        txs_raul = self.service.listar_transacciones(usuario_id=raul_id)
        descripciones_raul = [t["descripcion"] for t in txs_raul]
        self.assertIn("Cine con amigos", descripciones_raul)
        self.assertNotIn("Consulta médica", descripciones_raul)

        # Transacciones de Mamá
        txs_mama = self.service.listar_transacciones(usuario_id=mama_id)
        descripciones_mama = [t["descripcion"] for t in txs_mama]
        self.assertIn("Consulta médica", descripciones_mama)
        self.assertNotIn("Cine con amigos", descripciones_mama)

    def test_proteccion_eliminar_transaccion_ajena(self):
        """Comprueba que un usuario no pueda eliminar una transacción de otro."""
        login_raul = self.service.iniciar_sesion("raul", "123456")
        login_mama = self.service.iniciar_sesion("mama", "123456")

        raul_id = login_raul["usuario"]["id"]
        mama_id = login_mama["usuario"]["id"]

        # Transacción de Raúl
        tx_raul = self.service.registrar_transaccion({
            "tipo": "ingreso",
            "categoria": "Freelance",
            "monto": 300.0,
            "descripcion": "Asesoría web",
            "fecha": "2026-11-09"
        }, usuario_id=raul_id)

        # Mamá intenta eliminar la transacción de Raúl -> debe retornar False
        eliminado_por_mama = self.service.eliminar_transaccion(tx_raul.id, usuario_id=mama_id)
        self.assertFalse(eliminado_por_mama)

        # Raúl sí la puede eliminar -> debe retornar True
        eliminado_por_raul = self.service.eliminar_transaccion(tx_raul.id, usuario_id=raul_id)
        self.assertTrue(eliminado_por_raul)

    def test_cerrar_sesion(self):
        login = self.service.iniciar_sesion("raul", "123456")
        token = login["token"]
        self.assertTrue(self.service.cerrar_sesion(token))
        # El token ya no debe ser válido
        user = self.service.obtener_usuario_por_token(token)
        self.assertIsNone(user)

if __name__ == "__main__":
    unittest.main()
