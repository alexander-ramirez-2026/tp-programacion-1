
/* =========================================
   1. CONFIGURACIÓN GENERAL
========================================= */

const API_URL = "http://127.0.0.1:8000";

let apiKeyActual = "";
let rolActual = "";
let dniSocioEnEdicion = null;

/* =========================================
   2. ELEMENTOS DEL HTML
========================================= */

const loginScreen = document.getElementById("login-screen");
const appScreen = document.getElementById("app-screen");

const loginForm = document.getElementById("login-form");
const apiKeyInput = document.getElementById("api-key");
const loginMessage = document.getElementById("login-message");

const userRole = document.getElementById("user-role");
const logoutButton = document.getElementById("logout-button");

const adminPanel = document.getElementById("admin-panel");
const adminSociosPanel = document.getElementById("admin-socios-panel");
const socioPanel = document.getElementById("socio-panel");
const adminReservationsPanel = document.getElementById("admin-reservations-panel");

const appMessage = document.getElementById("app-message");

const formSocio = document.getElementById("formSocio");
const socioDni = document.getElementById("socioDni");
const socioNombre = document.getElementById("socioNombre");
const socioApellido = document.getElementById("socioApellido");
const socioFecha = document.getElementById("socioFecha");

const btnGuardarSocio = document.getElementById("btnGuardarSocio");
const btnCancelarSocio = document.getElementById("btnCancelarSocio");
const btnConsultarSocios = document.getElementById("btnConsultarSocios");

const resultadoSocios = document.getElementById("resultadoSocios");
const mensajeSocios = document.getElementById("mensajeSocios");

const reservationForm = document.getElementById("create-reservation-form");
const myReservationsForm = document.getElementById("my-reservations-form");
const classSearchForm = document.getElementById("class-search-form");

/* =========================================
   3. NAVEGACIÓN DEL MENÚ LATERAL
========================================= */

const botonesNavegacion = document.querySelectorAll("[data-section]");

const secciones = {
    inicio: document.getElementById("section-inicio"),
    socios: document.getElementById("section-socios"),
    clases: document.getElementById("section-clases"),
    reservas: document.getElementById("section-reservas")
};

const titulosSecciones = {
    inicio: "Inicio",
    socios: "Gestión de socios",
    clases: "Gestión de clases",
    reservas: "Gestión de reservas"
};

function cambiarSeccion(nombreSeccion) {
    if (!secciones[nombreSeccion]) {
        return;
    }

    // Restringir secciones administrativas
    if (
        rolActual !== "admin" &&
        (nombreSeccion === "socios" || nombreSeccion === "clases")
    ) {
        mostrarMensajeApp(
            "No tenés permisos para acceder a esta sección.",
            true
        );

        return;
    }

    // Ocultar todas las secciones
    Object.values(secciones).forEach(function(seccion) {
        seccion.classList.add("hidden");
    });

    // Mostrar la sección seleccionada
    secciones[nombreSeccion].classList.remove("hidden");

    // Cambiar título
    document.getElementById("page-title").textContent =
        titulosSecciones[nombreSeccion];

    // Actualizar botón activo
    botonesNavegacion.forEach(function(boton) {
        boton.classList.toggle(
            "active",
            boton.dataset.section === nombreSeccion
        );
    });

    // Mostrar u ocultar tarjeta de inicio para socios
    const socioHomeCard = document.getElementById("socio-home-card");

    if (socioHomeCard) {
        socioHomeCard.classList.toggle(
            "hidden",
            rolActual === "admin"
        );
    }

    // Consultar datos al entrar en cada sección
    if (nombreSeccion === "socios" && rolActual === "admin") {
        consultarSocios();
    }

    if (nombreSeccion === "clases" && rolActual === "admin") {
        if (typeof consultarClases === "function") {
            consultarClases();
        }
    }
}

// Conectar los botones del menú y los botones de las tarjetas
botonesNavegacion.forEach(function(boton) {
    boton.addEventListener("click", function() {
        cambiarSeccion(boton.dataset.section);
    });
});

/* =========================================
   4. FUNCIONES GENERALES
========================================= */

function mostrarMensajeApp(texto, error) {
    appMessage.textContent = texto;
    appMessage.style.color = error ? "#dc2626" : "#15803d";
}

function mostrarMensajeSocios(texto, error) {
    mensajeSocios.textContent = texto;
    mensajeSocios.style.color = error ? "#dc2626" : "#15803d";
}

function obtenerHeadersApp() {
    return {
        "Content-Type": "application/json",
        "X-API-Key": apiKeyActual
    };
}

/* =========================================
   5. INICIO DE SESIÓN
========================================= */

loginForm.addEventListener("submit", async function(evento) {
    evento.preventDefault();

    const clave = apiKeyInput.value.trim();

    if (clave === "") {
        loginMessage.textContent = "Ingresá tu API Key.";
        return;
    }

    loginMessage.textContent = "Verificando acceso...";

    try {
        const respuesta = await fetch(API_URL + "/socios", {
            headers: {
                "X-API-Key": clave
            }
        });

        if (respuesta.status === 401) {
            throw new Error("API Key incorrecta.");
        }

        if (respuesta.status === 403) {
            const respuestaClases = await fetch(API_URL + "/clases", {
                headers: {
                    "X-API-Key": clave
                }
            });

            if (respuestaClases.status === 401) {
                throw new Error("API Key incorrecta.");
            }

            if (!respuestaClases.ok) {
                throw new Error("No se pudo verificar el acceso.");
            }

            iniciarSesion(clave, "socio");
            return;
        }

        if (!respuesta.ok) {
            throw new Error("No se pudo verificar el acceso.");
        }

        iniciarSesion(clave, "admin");

    } catch (error) {
        loginMessage.textContent = error.message;
    }
});

/* =========================================
   6. INICIAR SESIÓN Y CONFIGURAR ROL
========================================= */

function iniciarSesion(clave, rol) {
    apiKeyActual = clave;
    rolActual = rol;

    loginScreen.classList.add("hidden");
    appScreen.classList.remove("hidden");

    const nombreRol =
        rol === "admin" ? "Administrador" : "Socio";

    userRole.textContent = nombreRol;

    document.getElementById("sidebar-user").textContent = nombreRol;
    document.getElementById("sidebar-role").textContent = "Sesión activa";

    // Mostrar opciones administrativas
    document.querySelectorAll(".admin-nav").forEach(function(elemento) {
        elemento.classList.toggle("hidden", rol !== "admin");
    });

    // Mostrar paneles según el rol
    adminPanel.classList.toggle("hidden", rol !== "admin");
    adminSociosPanel.classList.toggle("hidden", rol !== "admin");
    adminReservationsPanel.classList.toggle("hidden", rol !== "admin");

    socioPanel.classList.remove("hidden");

    // Entregar API Key al módulo de clases
    document.getElementById("apiKey").value = clave;

    loginMessage.textContent = "";

    cambiarSeccion("inicio");

    mostrarMensajeApp("Sesión iniciada correctamente.", false);
}

/* =========================================
   7. CERRAR SESIÓN
========================================= */

logoutButton.addEventListener("click", function() {
    apiKeyActual = "";
    rolActual = "";

    document.getElementById("apiKey").value = "";

    appScreen.classList.add("hidden");
    loginScreen.classList.remove("hidden");

    loginForm.reset();
    limpiarFormularioSocio();

    mostrarMensajeApp("", false);
    loginMessage.textContent = "";

    document.getElementById("resultado-reservas").replaceChildren();
    document.getElementById("results").textContent =
        "Todavía no hay resultados para mostrar.";
});

/* =========================================
   8. GESTIÓN DE SOCIOS
========================================= */

// REGISTRAR O MODIFICAR SOCIO

formSocio.addEventListener("submit", async function(evento) {
    evento.preventDefault();

    if (rolActual !== "admin") {
        mostrarMensajeSocios(
            "No tenés permisos para realizar esta acción.",
            true
        );
        return;
    }

    const dni = socioDni.value.trim();
    const nombre = socioNombre.value.trim();
    const apellido = socioApellido.value.trim();
    const fecha = socioFecha.value;

    if (!dni || !nombre || !apellido || !fecha) {
        mostrarMensajeSocios("Completá todos los campos.", true);
        return;
    }

    const datos = {
        dni: Number(dni),
        nombre: nombre,
        apellido: apellido,
        fecha_nacimiento: fecha
    };

    const editando = dniSocioEnEdicion !== null;

    let url = API_URL + "/socios";
    let metodo = "POST";

    if (editando) {
        url = API_URL + "/socios/" +
            encodeURIComponent(dniSocioEnEdicion);
        metodo = "PUT";
    }

    try {
        const respuesta = await fetch(url, {
            method: metodo,
            headers: obtenerHeadersApp(),
            body: JSON.stringify(datos)
        });

        const resultado = await respuesta.json().catch(function() {
            return {};
        });

        if (!respuesta.ok) {
            throw new Error(
                resultado.detail || "No se pudo guardar el socio."
            );
        }

        mostrarMensajeSocios(
            editando
                ? "Socio actualizado correctamente."
                : "Socio registrado correctamente.",
            false
        );

        limpiarFormularioSocio();
        await consultarSocios();

    } catch (error) {
        mostrarMensajeSocios(error.message, true);
    }
});

// CONSULTAR SOCIOS

async function consultarSocios() {
    if (rolActual !== "admin") {
        return;
    }

    try {
        const respuesta = await fetch(API_URL + "/socios", {
            headers: obtenerHeadersApp()
        });

        const socios = await respuesta.json();

        if (!respuesta.ok) {
            throw new Error(
                socios.detail || "No se pudieron consultar los socios."
            );
        }

        mostrarSocios(socios);

    } catch (error) {
        mostrarMensajeSocios(error.message, true);
    }
}

btnConsultarSocios.addEventListener("click", consultarSocios);

// MOSTRAR SOCIOS

function mostrarSocios(socios) {
    resultadoSocios.replaceChildren();

    if (!Array.isArray(socios) || socios.length === 0) {
        resultadoSocios.textContent = "No hay socios registrados.";
        return;
    }

    const tabla = document.createElement("table");
    const encabezado = document.createElement("tr");

    [
        "DNI",
        "Nombre",
        "Apellido",
        "Fecha de nacimiento",
        "Acciones"
    ].forEach(function(columna) {
        const th = document.createElement("th");
        th.textContent = columna;
        encabezado.appendChild(th);
    });

    tabla.appendChild(encabezado);

    socios.forEach(function(socio) {
        const fila = document.createElement("tr");

        [
            socio.dni,
            socio.nombre,
            socio.apellido,
            socio.fecha_nacimiento
        ].forEach(function(valor) {
            const celda = document.createElement("td");
            celda.textContent = valor ?? "";
            fila.appendChild(celda);
        });

        const acciones = document.createElement("td");

        const btnEditar = document.createElement("button");
        btnEditar.type = "button";
        btnEditar.textContent = "Editar";

        btnEditar.addEventListener("click", function() {
            editarSocio(socio);
        });

        const btnEliminar = document.createElement("button");
        btnEliminar.type = "button";
        btnEliminar.textContent = "Eliminar";
        btnEliminar.className = "secondary-button";

        btnEliminar.addEventListener("click", function() {
            eliminarSocio(socio.dni);
        });

        acciones.appendChild(btnEditar);
        acciones.appendChild(btnEliminar);

        fila.appendChild(acciones);
        tabla.appendChild(fila);
    });

    resultadoSocios.appendChild(tabla);
}

// EDITAR SOCIO

function editarSocio(socio) {
    dniSocioEnEdicion = socio.dni;

    socioDni.value = socio.dni;
    socioDni.disabled = true;

    socioNombre.value = socio.nombre;
    socioApellido.value = socio.apellido;
    socioFecha.value = socio.fecha_nacimiento;

    btnGuardarSocio.textContent = "Guardar cambios";
    btnCancelarSocio.hidden = false;

    mostrarMensajeSocios("Editando los datos del socio.", false);

    formSocio.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });
}

// ELIMINAR SOCIO

async function eliminarSocio(dni) {
    if (rolActual !== "admin") {
        mostrarMensajeSocios(
            "No tenés permisos para eliminar socios.",
            true
        );
        return;
    }

    const confirmar = confirm(
        "¿Estás seguro de que querés eliminar al socio con DNI " +
        dni + "?"
    );

    if (!confirmar) {
        return;
    }

    try {
        const respuesta = await fetch(
            API_URL + "/socios/" + encodeURIComponent(dni),
            {
                method: "DELETE",
                headers: obtenerHeadersApp()
            }
        );

        const resultado = await respuesta.json().catch(function() {
            return {};
        });

        if (!respuesta.ok) {
            throw new Error(
                resultado.detail || "No se pudo eliminar el socio."
            );
        }

        mostrarMensajeSocios("Socio eliminado correctamente.", false);
        await consultarSocios();

    } catch (error) {
        mostrarMensajeSocios(error.message, true);
    }
}

// LIMPIAR FORMULARIO

function limpiarFormularioSocio() {
    formSocio.reset();

    socioDni.disabled = false;
    dniSocioEnEdicion = null;

    btnGuardarSocio.textContent = "Registrar socio";
    btnCancelarSocio.hidden = true;
}

btnCancelarSocio.addEventListener("click", function() {
    limpiarFormularioSocio();
    mostrarMensajeSocios("Edición cancelada.", false);
});

/* =========================================
   9. REGISTRAR RESERVA
========================================= */

reservationForm.addEventListener("submit", async function(evento) {
    evento.preventDefault();

    const dni = document.getElementById("reservation-dni").value.trim();
    const claseId = document.getElementById("reservation-class").value.trim();

    if (!apiKeyActual) {
        mostrarMensajeApp("Primero iniciá sesión.", true);
        return;
    }

    if (!dni || !claseId) {
        mostrarMensajeApp("Completá todos los campos.", true);
        return;
    }

    try {
        const respuesta = await fetch(
            API_URL + "/clases/" +
            encodeURIComponent(claseId) + "/reservas",
            {
                method: "POST",
                headers: obtenerHeadersApp(),
                body: JSON.stringify({
                    socio_dni: Number(dni)
                })
            }
        );

        const resultado = await respuesta.json().catch(function() {
            return {};
        });

        if (!respuesta.ok) {
            throw new Error(
                resultado.detail || "No se pudo registrar la reserva."
            );
        }

        mostrarMensajeApp("Reserva registrada correctamente.", false);
        reservationForm.reset();

    } catch (error) {
        mostrarMensajeApp(error.message, true);
    }
});

/* =========================================
   10. CONSULTAR RESERVAS DE UN SOCIO
========================================= */

myReservationsForm.addEventListener("submit", async function(evento) {
    evento.preventDefault();

    const dni = document.getElementById("socio-dni").value.trim();

    if (!apiKeyActual || !dni) {
        mostrarMensajeApp("Ingresá un DNI válido.", true);
        return;
    }

    try {
        const respuesta = await fetch(
            API_URL + "/socios/" +
            encodeURIComponent(dni) + "/reservas",
            {
                headers: obtenerHeadersApp()
            }
        );

        const reservas = await respuesta.json();

        if (!respuesta.ok) {
            throw new Error(
                reservas.detail || "No se pudieron consultar las reservas."
            );
        }

        mostrarReservas(reservas);

    } catch (error) {
        mostrarMensajeApp(error.message, true);
    }
});

// MOSTRAR RESERVAS DE UN SOCIO

function mostrarReservas(reservas) {
    const contenedor = document.getElementById("resultado-reservas");

    contenedor.replaceChildren();

    if (!Array.isArray(reservas) || reservas.length === 0) {
        contenedor.textContent = "Este socio no tiene reservas.";
        return;
    }

    reservas.forEach(function(reserva) {
        const elemento = document.createElement("div");
        elemento.className = "reservation-item";

        const nombre = document.createElement("h3");
        nombre.textContent = reserva.nombre || "Reserva de clase";

        const horario = document.createElement("p");
        horario.textContent =
            "Horario: " + (reserva.horario || "No disponible");

        const fecha = document.createElement("p");
        fecha.textContent =
            "Fecha de reserva: " +
            (reserva.fecha_reserva || "No disponible");

        elemento.appendChild(nombre);
        elemento.appendChild(horario);
        elemento.appendChild(fecha);

        contenedor.appendChild(elemento);
    });

    mostrarMensajeApp("Reservas consultadas correctamente.", false);
}

/* =========================================
   11. CONSULTAR RESERVAS DE UNA CLASE
   SOLO ADMINISTRADOR
========================================= */

classSearchForm.addEventListener("submit", async function(evento) {
    evento.preventDefault();

    if (rolActual !== "admin") {
        mostrarMensajeApp(
            "Esta opción requiere permisos de administrador.",
            true
        );
        return;
    }

    const claseId = document.getElementById("class-id").value.trim();

    if (!claseId) {
        mostrarMensajeApp("Ingresá el ID de una clase.", true);
        return;
    }

    await consultarReservasClase(claseId);
});

/* =========================================
   12. CARGAR RESERVAS DE UNA CLASE
========================================= */

async function consultarReservasClase(claseId) {
    try {
        const respuesta = await fetch(
            API_URL + "/clases/" +
            encodeURIComponent(claseId) + "/reservas",
            {
                headers: obtenerHeadersApp()
            }
        );

        const reservas = await respuesta.json();

        if (!respuesta.ok) {
            throw new Error(
                reservas.detail ||
                "No se pudieron consultar las reservas."
            );
        }

        const contenedor = document.getElementById("resultado-reservas");

        contenedor.replaceChildren();

        if (!Array.isArray(reservas) || reservas.length === 0) {
            contenedor.textContent = "Esta clase no tiene reservas.";

            mostrarMensajeApp("Consulta realizada correctamente.", false);
            return;
        }

        reservas.forEach(function(reserva) {
            const elemento = document.createElement("div");
            elemento.className = "reservation-item";

            const nombre = document.createElement("h3");
            nombre.textContent =
                (reserva.nombre || "") + " " +
                (reserva.apellido || "");

            const dni = document.createElement("p");
            dni.textContent = "DNI: " + reserva.socio_dni;

            const fecha = document.createElement("p");
            fecha.textContent =
                "Fecha: " +
                (reserva.fecha_reserva || "No disponible");

            const botonCancelar = document.createElement("button");
            botonCancelar.type = "button";
            botonCancelar.textContent = "Cancelar reserva";
            botonCancelar.className = "secondary-button";

            botonCancelar.addEventListener("click", function() {
                cancelarReserva(reserva.id, claseId);
            });

            elemento.appendChild(nombre);
            elemento.appendChild(dni);
            elemento.appendChild(fecha);
            elemento.appendChild(botonCancelar);

            contenedor.appendChild(elemento);
        });

        mostrarMensajeApp(
            "Reservas de la clase consultadas correctamente.",
            false
        );

    } catch (error) {
        mostrarMensajeApp(error.message, true);
    }
}

/* =========================================
   13. CANCELAR RESERVA
   SOLO ADMINISTRADOR
========================================= */

async function cancelarReserva(reservaId, claseId) {
    if (rolActual !== "admin") {
        mostrarMensajeApp(
            "No tenés permisos para cancelar reservas.",
            true
        );
        return;
    }

    const confirmar = confirm(
        "¿Estás seguro de que querés cancelar esta reserva?"
    );

    if (!confirmar) {
        return;
    }

    try {
        const respuesta = await fetch(
            API_URL + "/reservas/" +
            encodeURIComponent(reservaId),
            {
                method: "DELETE",
                headers: obtenerHeadersApp()
            }
        );

        const resultado = await respuesta.json().catch(function() {
            return {};
        });

        if (!respuesta.ok) {
            throw new Error(
                resultado.detail || "No se pudo cancelar la reserva."
            );
        }

        mostrarMensajeApp(
            "Reserva cancelada correctamente. Se liberó el cupo.",
            false
        );

        await consultarReservasClase(claseId);

    } catch (error) {
        mostrarMensajeApp(error.message, true);
    }
}

/* =========================================
   14. CONFIRMACIÓN DE CARGA
========================================= */

console.log("APP.JS CARGADO CORRECTAMENTE");
