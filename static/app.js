// Estado global de la aplicación cliente
let usuarioActual = null;
let categorias = [];
let transacciones = [];
let chartGastosInstance = null;
let filtroTipoActual = "todos";

const TOKEN_KEY = "billetera_express_token";

// Elementos del DOM - Auth
const modalAuth = document.getElementById("modal-auth");
const tabLogin = document.getElementById("tab-login");
const tabRegistro = document.getElementById("tab-registro");
const formLogin = document.getElementById("form-login");
const formRegistro = document.getElementById("form-registro");
const loginUsernameInput = document.getElementById("login-username");
const loginPasswordInput = document.getElementById("login-password");
const regNombreInput = document.getElementById("reg-nombre");
const regUsernameInput = document.getElementById("reg-username");
const regPasswordInput = document.getElementById("reg-password");
const btnCerrarSesion = document.getElementById("btn-cerrar-sesion");
const usuarioBadgeContainer = document.getElementById("usuario-badge-container");
const navUserIcono = document.getElementById("nav-user-icono");
const navUserNombre = document.getElementById("nav-user-nombre");
const saludoUsuarioEl = document.getElementById("saludo-usuario");
const btnsDemoLogin = document.querySelectorAll(".btn-demo-login");

// Elementos del DOM - Dashboard
const fechaActualEl = document.getElementById("fecha-actual");
const metricaSaldoEl = document.getElementById("metrica-saldo");
const metricaIngresosEl = document.getElementById("metrica-ingresos");
const metricaGastosEl = document.getElementById("metrica-gastos");
const metricaMovimientosEl = document.getElementById("metrica-movimientos");
const metricaEstadoEl = document.getElementById("metrica-estado");

const formTransaccion = document.getElementById("form-transaccion");
const inputTipo = document.getElementById("input-tipo");
const btnTipoGasto = document.getElementById("btn-tipo-gasto");
const btnTipoIngreso = document.getElementById("btn-tipo-ingreso");
const selectCategoria = document.getElementById("select-categoria");
const inputMonto = document.getElementById("input-monto");
const inputDescripcion = document.getElementById("input-descripcion");
const inputFecha = document.getElementById("input-fecha");

const tablaCuerpo = document.getElementById("tabla-cuerpo");
const tablaVacia = document.getElementById("tabla-vacia");
const buscadorTabla = document.getElementById("buscador-tabla");
const filtrosBtns = document.querySelectorAll(".filtro-btn");
const btnRefrescar = document.getElementById("btn-refrescar");
const listaTopGastos = document.getElementById("lista-top-gastos");
const graficoVacio = document.getElementById("grafico-vacio");
const toastEl = document.getElementById("toast");

// =============================================================================
// UTILIDADES Y HELPERS DE API
// =============================================================================

function obtenerToken() {
  return localStorage.getItem(TOKEN_KEY);
}

function guardarToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

function borrarToken() {
  localStorage.removeItem(TOKEN_KEY);
}

// Wrapper fetch autenticado
async function fetchAutenticado(url, opciones = {}) {
  const token = obtenerToken();
  const headers = {
    "Content-Type": "application/json",
    ...(opciones.headers || {})
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(url, { ...opciones, headers });

  if (res.status === 401) {
    // Sesión expirada o inválida
    borrarToken();
    usuarioActual = null;
    mostrarModalAuth();
    throw new Error("Sesión requerida");
  }

  return res;
}

// Formateador de moneda en Soles
function formatearSoles(monto) {
  return "S/ " + Number(monto).toLocaleString("es-PE", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  });
}

// Notificación flotante Toast
function mostrarToast(mensaje, esError = false) {
  toastEl.textContent = mensaje;
  toastEl.className = `fixed bottom-5 right-5 z-50 transition-all duration-300 pointer-events-none flex items-center gap-2 px-4 py-3 rounded-xl shadow-lg text-sm font-medium text-white ${
    esError ? "bg-rose-600" : "bg-emerald-600"
  }`;
  toastEl.classList.remove("translate-y-20", "opacity-0");

  setTimeout(() => {
    toastEl.classList.add("translate-y-20", "opacity-0");
  }, 3200);
}

// Configurar fecha de hoy
function inicializarFechas() {
  const hoy = new Date();
  const opcionesFecha = { weekday: "long", year: "numeric", month: "short", day: "numeric" };
  const fechaTexto = hoy.toLocaleDateString("es-PE", opcionesFecha);
  if (fechaActualEl) {
    fechaActualEl.textContent = fechaTexto.charAt(0).toUpperCase() + fechaTexto.slice(1);
  }

  const anio = hoy.getFullYear();
  const mes = String(hoy.getMonth() + 1).padStart(2, "0");
  const dia = String(hoy.getDate()).padStart(2, "0");
  inputFecha.value = `${anio}-${mes}-${dia}`;
}

// =============================================================================
// GESTIÓN DE AUTENTICACIÓN Y SESIÓN
// =============================================================================

function mostrarModalAuth(tab = "login") {
  modalAuth.classList.remove("hidden");
  activarTab(tab);
}

function ocultarModalAuth() {
  modalAuth.classList.add("hidden");
}

function activarTab(tab) {
  if (tab === "login") {
    tabLogin.className = "py-2 text-xs font-bold rounded-lg bg-indigo-600 text-white shadow-sm transition-all";
    tabRegistro.className = "py-2 text-xs font-bold rounded-lg text-indigo-300 hover:text-white transition-all";
    formLogin.classList.remove("hidden");
    formRegistro.classList.add("hidden");
  } else {
    tabRegistro.className = "py-2 text-xs font-bold rounded-lg bg-indigo-600 text-white shadow-sm transition-all";
    tabLogin.className = "py-2 text-xs font-bold rounded-lg text-indigo-300 hover:text-white transition-all";
    formRegistro.classList.remove("hidden");
    formLogin.classList.add("hidden");
  }
}

async function verificarSesion() {
  const token = obtenerToken();
  if (!token) {
    mostrarModalAuth("login");
    return;
  }

  try {
    const res = await fetchAutenticado("/api/auth/me");
    if (res.ok) {
      const data = await res.json();
      establecerUsuario(data.usuario);
      await cargarTodo();
    } else {
      mostrarModalAuth("login");
    }
  } catch (err) {
    mostrarModalAuth("login");
  }
}

function establecerUsuario(usuario) {
  usuarioActual = usuario;
  navUserIcono.textContent = usuario.icono || "👤";
  navUserNombre.textContent = usuario.nombre;
  usuarioBadgeContainer.classList.remove("hidden");
  saludoUsuarioEl.innerHTML = `<span>${usuario.icono || "👋"}</span> ¡Hola, ${usuario.nombre}!`;
  ocultarModalAuth();
}

// Login
formLogin.addEventListener("submit", async (e) => {
  e.preventDefault();
  const username = loginUsernameInput.value.trim();
  const password = loginPasswordInput.value;

  try {
    const res = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password })
    });
    const data = await res.json();

    if (res.ok) {
      guardarToken(data.token);
      establecerUsuario(data.usuario);
      mostrarToast(`¡Bienvenido de vuelta, ${data.usuario.nombre}!`);
      formLogin.reset();
      await cargarTodo();
    } else {
      mostrarToast(data.error || "Credenciales incorrectas", true);
    }
  } catch (err) {
    mostrarToast("Error de conexión al iniciar sesión", true);
  }
});

// Registro
formRegistro.addEventListener("submit", async (e) => {
  e.preventDefault();
  const iconoSeleccionado = document.querySelector('input[name="reg-icono"]:checked')?.value || "👤";
  const datos = {
    nombre: regNombreInput.value.trim(),
    username: regUsernameInput.value.trim().toLowerCase(),
    password: regPasswordInput.value,
    icono: iconoSeleccionado
  };

  try {
    const res = await fetch("/api/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(datos)
    });
    const data = await res.json();

    if (res.ok) {
      guardarToken(data.token);
      establecerUsuario(data.usuario);
      mostrarToast(`¡Cuenta creada con éxito! Hola, ${data.usuario.nombre}.`);
      formRegistro.reset();
      await cargarTodo();
    } else {
      mostrarToast(data.error || "No se pudo crear la cuenta", true);
    }
  } catch (err) {
    mostrarToast("Error de conexión al registrar cuenta", true);
  }
});

// Logout
btnCerrarSesion.addEventListener("click", async () => {
  try {
    await fetchAutenticado("/api/auth/logout", { method: "POST" });
  } catch (e) {}
  borrarToken();
  usuarioActual = null;
  usuarioBadgeContainer.classList.add("hidden");
  saludoUsuarioEl.innerHTML = `<span>👋</span> ¡Hola!`;
  mostrarToast("Has cerrado sesión.");
  mostrarModalAuth("login");
});

// Acceso rápido demo familiar
btnsDemoLogin.forEach(btn => {
  btn.addEventListener("click", () => {
    const user = btn.getAttribute("data-user");
    loginUsernameInput.value = user;
    loginPasswordInput.value = "123456";
    formLogin.dispatchEvent(new Event("submit"));
  });
});

tabLogin.addEventListener("click", () => activarTab("login"));
tabRegistro.addEventListener("click", () => activarTab("registro"));

// =============================================================================
// GESTIÓN DE DATOS DEL DASHBOARD
// =============================================================================

function setTipoOperacion(tipo) {
  inputTipo.value = tipo;
  if (tipo === "gasto") {
    btnTipoGasto.className = "tipo-btn py-2 text-xs font-bold rounded-lg shadow-sm bg-rose-600 text-white";
    btnTipoIngreso.className = "tipo-btn py-2 text-xs font-bold rounded-lg text-slate-600 hover:text-slate-900";
  } else {
    btnTipoIngreso.className = "tipo-btn py-2 text-xs font-bold rounded-lg shadow-sm bg-emerald-600 text-white";
    btnTipoGasto.className = "tipo-btn py-2 text-xs font-bold rounded-lg text-slate-600 hover:text-slate-900";
  }
  actualizarOpcionesCategorias();
}

function actualizarOpcionesCategorias() {
  const tipo = inputTipo.value;
  const filtradas = categorias.filter(c => c.tipo === tipo);

  selectCategoria.innerHTML = '<option value="" disabled selected>Selecciona una categoría...</option>';
  filtradas.forEach(c => {
    const opt = document.createElement("option");
    opt.value = c.nombre;
    opt.textContent = `${c.icono} ${c.nombre}`;
    selectCategoria.appendChild(opt);
  });
}

async function cargarCategorias() {
  try {
    const res = await fetch("/api/categorias");
    categorias = await res.json();
    actualizarOpcionesCategorias();
  } catch (err) {
    console.error("Error al cargar categorías:", err);
  }
}

async function cargarResumen() {
  try {
    const res = await fetchAutenticado("/api/resumen");
    const data = await res.json();

    metricaSaldoEl.textContent = formatearSoles(data.saldo_neto);
    metricaIngresosEl.textContent = formatearSoles(data.total_ingresos);
    metricaGastosEl.textContent = formatearSoles(data.total_gastos);
    metricaMovimientosEl.textContent = data.total_movimientos;

    if (data.saldo_neto < 0) {
      metricaSaldoEl.className = "text-2xl sm:text-3xl font-extrabold text-rose-600 tracking-tight";
      metricaEstadoEl.textContent = "⚠️ Balance en déficit";
      metricaEstadoEl.className = "text-xs text-rose-500 font-semibold mt-1";
    } else {
      metricaSaldoEl.className = "text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight";
      metricaEstadoEl.textContent = "✅ Balance saludable";
      metricaEstadoEl.className = "text-xs text-emerald-600 font-semibold mt-1";
    }

    renderizarGraficoYTopGastos(data.gastos_por_categoria, data.total_gastos);
  } catch (err) {
    console.error("Error al cargar resumen:", err);
  }
}

async function cargarTransacciones() {
  try {
    const res = await fetchAutenticado("/api/transacciones");
    transacciones = await res.json();
    renderizarTabla();
  } catch (err) {
    console.error("Error al cargar transacciones:", err);
  }
}

async function cargarTodo() {
  await Promise.all([cargarCategorias(), cargarResumen(), cargarTransacciones()]);
}

// Gráfica de gastos con Chart.js
function renderizarGraficoYTopGastos(gastosCat, totalGastos) {
  if (!gastosCat || gastosCat.length === 0 || totalGastos === 0) {
    graficoVacio.classList.remove("hidden");
    if (chartGastosInstance) {
      chartGastosInstance.destroy();
      chartGastosInstance = null;
    }
    listaTopGastos.innerHTML = '<p class="text-xs text-slate-400 text-center py-6">No hay gastos para clasificar.</p>';
    return;
  }

  graficoVacio.classList.add("hidden");

  const etiquetas = gastosCat.map(g => g.categoria);
  const valores = gastosCat.map(g => g.total);

  const paletaColores = [
    "#ef4444", "#f97316", "#f59e0b", "#6366f1",
    "#8b5cf6", "#ec4899", "#14b8a6", "#06b6d4"
  ];

  const ctx = document.getElementById("grafico-gastos").getContext("2d");
  if (chartGastosInstance) {
    chartGastosInstance.destroy();
  }

  chartGastosInstance = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: etiquetas,
      datasets: [{
        data: valores,
        backgroundColor: paletaColores.slice(0, etiquetas.length),
        borderWidth: 2,
        borderColor: "#ffffff"
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: function(context) {
              const valor = context.parsed;
              const porcentaje = ((valor / totalGastos) * 100).toFixed(1);
              return ` ${context.label}: S/ ${valor.toFixed(2)} (${porcentaje}%)`;
            }
          }
        }
      },
      cutout: "70%"
    }
  });

  // Lista de desglose con barras de porcentaje
  listaTopGastos.innerHTML = "";
  gastosCat.forEach((g, idx) => {
    const color = paletaColores[idx % paletaColores.length];
    const porcentaje = ((g.total / totalGastos) * 100).toFixed(1);

    const item = document.createElement("div");
    item.className = "text-xs space-y-1";
    item.innerHTML = `
      <div class="flex justify-between items-center text-slate-700 font-medium">
        <span class="flex items-center gap-1.5">
          <span class="w-2.5 h-2.5 rounded-full inline-block" style="background-color: ${color}"></span>
          ${g.categoria}
        </span>
        <span class="font-bold text-slate-900">${formatearSoles(g.total)} <span class="text-slate-400 font-normal">(${porcentaje}%)</span></span>
      </div>
      <div class="w-full bg-slate-100 rounded-full h-1.5 overflow-hidden">
        <div class="h-1.5 rounded-full transition-all duration-500" style="width: ${porcentaje}%; background-color: ${color}"></div>
      </div>
    `;
    listaTopGastos.appendChild(item);
  });
}

// Renderizado de tabla de transacciones
function renderizarTabla() {
  const termino = buscadorTabla.value.trim().toLowerCase();

  const filtradas = transacciones.filter(t => {
    const coincideTipo = filtroTipoActual === "todos" || t.tipo === filtroTipoActual;
    const coincideBusqueda = t.descripcion.toLowerCase().includes(termino) ||
                             t.categoria.toLowerCase().includes(termino) ||
                             t.fecha.includes(termino);
    return coincideTipo && coincideBusqueda;
  });

  tablaCuerpo.innerHTML = "";

  if (filtradas.length === 0) {
    tablaVacia.classList.remove("hidden");
    return;
  }

  tablaVacia.classList.add("hidden");

  filtradas.forEach(tx => {
    const esIngreso = tx.tipo === "ingreso";
    const tr = document.createElement("tr");
    tr.className = "fila-transaccion transition-colors";

    tr.innerHTML = `
      <td class="py-3 px-4 font-mono text-xs text-slate-500 whitespace-nowrap">${tx.fecha}</td>
      <td class="py-3 px-4 whitespace-nowrap">
        <span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium ${
          esIngreso ? "bg-emerald-100 text-emerald-800" : "bg-slate-100 text-slate-700"
        }">
          ${esIngreso ? "📈" : "🏷️"} ${tx.categoria}
        </span>
      </td>
      <td class="py-3 px-4 text-slate-800 font-medium">${tx.descripcion}</td>
      <td class="py-3 px-4 text-right whitespace-nowrap font-bold ${
        esIngreso ? "text-emerald-600" : "text-rose-600"
      }">
        ${esIngreso ? "+" : "-"} ${formatearSoles(tx.monto)}
      </td>
      <td class="py-3 px-4 text-center whitespace-nowrap">
        <button onclick="eliminarTransaccion(${tx.id})" title="Eliminar movimiento" class="p-1 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
          </svg>
        </button>
      </td>
    `;
    tablaCuerpo.appendChild(tr);
  });
}

// Eliminar transacción
async function eliminarTransaccion(id) {
  if (!confirm("¿Seguro que deseas eliminar este movimiento?")) {
    return;
  }

  try {
    const res = await fetchAutenticado(`/api/transacciones/${id}`, { method: "DELETE" });
    if (res.ok) {
      mostrarToast("Movimiento eliminado correctamente.");
      await cargarResumen();
      await cargarTransacciones();
    } else {
      const err = await res.json();
      mostrarToast(err.error || "No se pudo eliminar", true);
    }
  } catch (err) {
    mostrarToast("Error de conexión al eliminar", true);
  }
}

// Guardar nueva transacción
formTransaccion.addEventListener("submit", async (e) => {
  e.preventDefault();

  const datos = {
    tipo: inputTipo.value,
    categoria: selectCategoria.value,
    monto: parseFloat(inputMonto.value),
    descripcion: inputDescripcion.value.trim(),
    fecha: inputFecha.value
  };

  if (!datos.categoria) {
    mostrarToast("Por favor selecciona una categoría.", true);
    return;
  }

  try {
    const res = await fetchAutenticado("/api/transacciones", {
      method: "POST",
      body: JSON.stringify(datos)
    });

    if (res.ok) {
      mostrarToast("¡Movimiento registrado con éxito!");
      formTransaccion.reset();
      inicializarFechas();
      setTipoOperacion(datos.tipo);
      await cargarResumen();
      await cargarTransacciones();
    } else {
      const err = await res.json();
      mostrarToast(err.error || "Error al registrar movimiento", true);
    }
  } catch (err) {
    mostrarToast("Error de red al guardar la transacción", true);
  }
});

// Eventos de botones
btnTipoGasto.addEventListener("click", () => setTipoOperacion("gasto"));
btnTipoIngreso.addEventListener("click", () => setTipoOperacion("ingreso"));

filtrosBtns.forEach(btn => {
  btn.addEventListener("click", () => {
    filtrosBtns.forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    filtroTipoActual = btn.getAttribute("data-filtro");
    renderizarTabla();
  });
});

buscadorTabla.addEventListener("input", renderizarTabla);

btnRefrescar.addEventListener("click", async () => {
  if (usuarioActual) {
    await cargarTodo();
    mostrarToast("Datos actualizados.");
  }
});

// Inicialización de la aplicación al cargar el DOM
document.addEventListener("DOMContentLoaded", async () => {
  inicializarFechas();
  setTipoOperacion("gasto");
  await cargarCategorias();
  await verificarSesion();
});
