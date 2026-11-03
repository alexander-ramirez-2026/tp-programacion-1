
const API_URL_CLASES = "http://127.0.0.1:8000";

// ELEMENTOS DEL HTML
const formulario = document.getElementById("formClase");
const resultado = document.getElementById("resultadoClases");
const mensaje = document.getElementById("mensaje");

const campoId = document.getElementById("claseId");
const campoNombre = document.getElementById("nombre");
const campoInstructor = document.getElementById("instructor");
const campoHorario = document.getElementById("horario");
const campoCupo = document.getElementById("cupo");
const campoEdadMinima = document.getElementById("edadMinima");
const campoEdadMaxima = document.getElementById("edadMaxima");

const apiKey = document.getElementById("apiKey");

const btnConsultar = document.getElementById("btnConsultar");
const btnCancelarEdicion = document.getElementById("btnCancelarEdicion");
const btnGuardar = document.getElementById("btnGuardar");

const tituloFormulario = document.getElementById("tituloFormulario");

// OBTENER HEADERS
function obtenerHeaders() {
    return {
        "Content-Type": "application/json",
        "X-API-Key": apiKey.value.trim()
    };
}

// VERIFICAR ACCESO
function verificarAdministrador() {
    if (!apiKey.value.trim()) {
        mostrarMensaje("Primero tenés que iniciar sesión.", true);
        return false;
    }

    return true;
}

// MOSTRAR MENSAJES
function mostrarMensaje(texto, error = false) {
    mensaje.textContent = texto;
    mensaje.style.color = error ? "#dc2626" : "#15803d";
}

// CONSULTAR CLASES
async function consultarClases() {
    try {
        if (!verificarAdministrador()) return;

        const respuesta = await fetch(`${API_URL}/clases`);

        const clases = await respuesta.json();

        if (!respuesta.ok) {
            throw new Error(clases.detail || "No se pudieron consultar las clases.");
        }

        resultado.replaceChildren();

        if (clases.length === 0) {
            resultado.textContent = "No hay clases disponibles.";
            return;
        }

        const tabla = document.createElement("table");

        const encabezado = document.createElement("tr");

        [
            "ID",
            "Nombre",
            "Instructor",
            "Horario",
            "Cupo",
            "Edad mínima",
            "Edad máxima",
            "Acciones"
        ].forEach(texto => {
            const th = document.createElement("th");
            th.textContent = texto;
            encabezado.appendChild(th);
        });

        tabla.appendChild(encabezado);

        clases.forEach(clase => {
            const fila = document.createElement("tr");

            [
                clase.id,
                clase.nombre,
                clase.instructor,
                clase.horario,
                clase.cupo_maximo,
                clase.edad_minima ?? "-",
                clase.edad_maxima ?? "-"
            ].forEach(valor => {
                const celda = document.createElement("td");
                celda.textContent = valor;
                fila.appendChild(celda);
            });

            const acciones = document.createElement("td");

            const btnEditar = document.createElement("button");
            btnEditar.textContent = "Editar";
            btnEditar.type = "button";
            btnEditar.addEventListener("click", () => editarClase(clase));

            const btnCancelar = document.createElement("button");
            btnCancelar.textContent = "Cancelar clase";
            btnCancelar.type = "button";
            btnCancelar.addEventListener("click", () => cancelarClase(clase.id));

            acciones.appendChild(btnEditar);
            acciones.appendChild(document.createTextNode(" "));
            acciones.appendChild(btnCancelar);

            fila.appendChild(acciones);
            tabla.appendChild(fila);
        });

        resultado.appendChild(tabla);

        mostrarMensaje("Clases consultadas correctamente.");

    } catch (error) {
        mostrarMensaje(error.message, true);
    }
}

// REGISTRAR O ACTUALIZAR CLASE
formulario.addEventListener("submit", async function(evento) {
    evento.preventDefault();

    if (!verificarAdministrador()) return;

    const datos = {
        nombre: campoNombre.value.trim(),
        instructor: campoInstructor.value.trim(),
        horario: campoHorario.value.trim(),
        cupo_maximo: Number(campoCupo.value),
        edad_minima: campoEdadMinima.value === ""
            ? null
            : Number(campoEdadMinima.value),
        edad_maxima: campoEdadMaxima.value === ""
            ? null
            : Number(campoEdadMaxima.value)
    };

    const id = campoId.value;

    const url = id
        ? `${API_URL}/clases/${id}`
        : `${API_URL}/clases`;

    const metodo = id ? "PUT" : "POST";

    try {
        const respuesta = await fetch(url, {
            method: metodo,
            headers: obtenerHeaders(),
            body: JSON.stringify(datos)
        });

        const resultadoApi = await respuesta.json().catch(() => ({}));

        if (!respuesta.ok) {
            throw new Error(
                resultadoApi.detail || "No se pudo guardar la clase."
            );
        }

        mostrarMensaje(
            id
                ? "Clase actualizada correctamente."
                : "Clase registrada correctamente."
        );

        limpiarFormulario();
        consultarClases();

    } catch (error) {
        mostrarMensaje(error.message, true);
    }
});

// CARGAR DATOS PARA EDITAR
function editarClase(clase) {
    if (!verificarAdministrador()) return;

    campoId.value = clase.id;
    campoNombre.value = clase.nombre;
    campoInstructor.value = clase.instructor;
    campoHorario.value = clase.horario;
    campoCupo.value = clase.cupo_maximo;
    campoEdadMinima.value = clase.edad_minima ?? "";
    campoEdadMaxima.value = clase.edad_maxima ?? "";

    tituloFormulario.textContent = "Editar clase";
    btnGuardar.textContent = "Guardar cambios";
    btnCancelarEdicion.hidden = false;

    mostrarMensaje("Modificá los datos de la clase.");
}

// CANCELAR CLASE
async function cancelarClase(id) {
    if (!verificarAdministrador()) return;

    if (!confirm("¿Estás seguro de que querés cancelar esta clase?")) {
        return;
    }

    try {
        const respuesta = await fetch(
            `${API_URL}/clases/${id}/cancelar`,
            {
                method: "DELETE",
                headers: obtenerHeaders()
            }
        );

        const resultadoApi = await respuesta.json().catch(() => ({}));

        if (!respuesta.ok) {
            throw new Error(
                resultadoApi.detail || "No se pudo cancelar la clase."
            );
        }

        mostrarMensaje("Clase cancelada correctamente.");

        limpiarFormulario();
        consultarClases();

    } catch (error) {
        mostrarMensaje(error.message, true);
    }
}

// LIMPIAR FORMULARIO
function limpiarFormulario() {
    formulario.reset();
    campoId.value = "";

    tituloFormulario.textContent = "Registrar clase";
    btnGuardar.textContent = "Registrar clase";
    btnCancelarEdicion.hidden = true;
}

// CANCELAR EDICIÓN
btnCancelarEdicion.addEventListener("click", function() {
    limpiarFormulario();
    mostrarMensaje("Edición cancelada.");
});

// BOTÓN CONSULTAR
btnConsultar.addEventListener("click", consultarClases);
