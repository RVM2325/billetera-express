# 🇵🇪 Billetera Express - Gestor de Finanzas Personales y Familiar

Una aplicación web completa, ligera y modular para el control de ingresos, gastos y presupuestos personales en Soles (`S/.`), con **soporte multiusuario** para que cada integrante de la familia tenga su propia cuenta privada, todo construido con **Python puro**, **SQLite** y una interfaz moderna con **Tailwind CSS** y **Chart.js**.

---

## 🏗️ Arquitectura y Patrones del Proyecto

El proyecto sigue una arquitectura limpia en capas con autenticación y aislamiento estricto de datos:

```text
GestorFinanzas/
├── app/
│   ├── models.py       # Clases de dominio POO (Usuario, Transaccion, Categoria) con validaciones.
│   ├── security.py     # Criptografía: Hashing seguro (PBKDF2-HMAC-SHA256) y tokens de sesión.
│   ├── database.py     # Capa de datos SQLite (usuarios, sesiones, transacciones con FK y semillas).
│   ├── services.py     # Lógica de negocio, autenticación, control de acceso y métricas financieras.
│   └── server.py       # Servidor HTTP nativo con API RESTful protegida con tokens Bearer.
├── static/
│   ├── index.html      # Dashboard responsivo con modal de autenticación y vista multiusuario.
│   ├── app.js          # Lógica frontend reactiva (Fetch con Auth, gráficos dinámicos, tabs y toasts).
│   └── styles.css      # Estilos personalizados, scrollbars y animaciones.
├── tests/
│   └── test_services.py # Suite de pruebas unitarias (registro, login, aislamiento y autorización).
├── main.py             # Script principal que expone el servidor en la red local (0.0.0.0).
└── README.md           # Documentación del proyecto.
```

---

## ✨ Nuevas Características Multiusuario

* **Cuentas y Perfiles Independientes**: Cada integrante de la familia puede crear su cuenta con su nombre, avatar personalizado (`👨‍💻`, `👩`, `👨`, `👧`, `😎`, etc.) y contraseña.
* **Seguridad Criptográfica**: Las contraseñas nunca se guardan en texto plano; se utiliza **PBKDF2-HMAC-SHA256 con sal aleatoria** (librería estándar de Python, sin dependencias externas).
* **Aislamiento Total de Datos**: El Usuario A jamás puede ver, sumar ni borrar las transacciones o el saldo del Usuario B.
* **Acceso Demo Familiar Integrado**:
  * **Raúl** (`raul` / clave: `123456`)
  * **Mamá** (`mama` / clave: `123456`)
  * **Papá** (`papa` / clave: `123456`)
* **Persistencia de Sesión**: Guarda el token de sesión de forma segura en el navegador para que no tengas que iniciar sesión cada vez que refrescas la página.
* **Compartible en Red Wi-Fi**: Cualquier familiar en la casa puede abrirlo desde su celular o laptop.

---

## 🚀 Cómo Iniciar el Servidor

1. Abre tu terminal y entra a la carpeta:
   ```bash
   cd /home/rvm/GestorFinanzas
   python3 main.py
   ```

2. En la terminal verás las URLs activas:
   * **En tu laptop**: `http://localhost:8000`
   * **En los celulares de tu familia**: `http://<TU_IP_LOCAL>:8000` (aparece indicada en tu terminal)

---

## 🧪 Ejecutar Pruebas Automatizadas

Para validar que la criptografía, los logins y el aislamiento de datos entre usuarios funcionen correctamente:

```bash
cd /home/rvm/GestorFinanzas
python3 -m unittest tests/test_services.py
```
