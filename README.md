# Programación I - 2do1ra DS - 2026

Este es el trabajo práctico final del taller. Integra todos los contenidos
vistos: CRUD completo, persistencia en MySQL, CORS y consumo desde un frontend
en JavaScript, y autenticación básica con roles.

La entrega de este TP es obligatoria para poder aprobar el taller. Quienes no
entreguen el TP no podrán presentarse a rendir el examen parcial del 2do
cuatrimestre, ya que el parcial estará basado en la solución que cada equipo
genere.

El TP se realiza en equipos de 2, 3 o 4 integrantes. Es necesario que publiquen
en gitea el código que resuelve esta consigna. Ese código es un requisito para
rendir el parcial, pero *no* forma parte de la calificación. La evaluación
se basará en las explicaciones que cada estudiante pueda dar del código, y en
la implementación de pequeños cambios solicitados como consignas del parcial.
La calificación es individual.

La consigna es construir una API REST para gestionar las clases de un gimnasio,
sus socios, y las reservas que estos hacen a cada clase.

La base de datos ya está diseñada y se entrega junto con esta consigna (archivo
`gimnasio.sql`), para que todos los grupos trabajen sobre el mismo esquema. Los
nombres de tablas y columnas deben respetarse tal cual están definidos ahí,
porque los tests van a validar contra ellos.

----

## Modelo de datos

### `socios`

Representa a los socios del gimnasio.

| Columna | Tipo | Notas |
|---|---|---|
| `dni` | `INT` | Clave primaria |
| `nombre` | `VARCHAR(100)` | |
| `apellido` | `VARCHAR(100)` | |
| `fecha_nacimiento` | `DATE` | Se usa para calcular la edad al momento de reservar |

### `clases`

| Columna | Tipo | Notas |
|---|---|---|
| `id` | `INT` | Clave primaria, autoincremental |
| `nombre` | `VARCHAR(100)` | |
| `instructor` | `VARCHAR(100)` | Solo el nombre, como "Ana", o "Juan" |
| `horario` | `VARCHAR(50)` | Un string como "Martes 18 a 19hs" |
| `cupo_maximo` | `INT` | |
| `edad_minima` | `INT`, admite `NULL` | Sin restricción si es `NULL` |
| `edad_maxima` | `INT`, admite `NULL` | Sin restricción si es `NULL` |
| `cancelada` | `BOOLEAN` | Para "bajas lógicas" |

### `reservas`

| Columna | Tipo | Notas |
|---|---|---|
| `id` | `INT` | Clave primaria, autoincremental |
| `clase_id` | `INT` | Clave foránea a `clases(id)` |
| `socio_dni` | `INT` | Clave foránea a `socios(dni)` |
| `fecha_reserva` | `TIMESTAMP` | Se completa sola (`DEFAULT CURRENT_TIMESTAMP`) |

---

## Reglas de negocio

Estas reglas **no** se resuelven en SQL: se validan en Python, dentro de tus
endpoints, después de consultar los datos necesarios.

### Baja lógica de una clase

Cancelar una clase **no la borra** de la base de datos: se marca `cancelada =
TRUE`. Esto es intencional, para no perder el historial de reservas asociado a
esa clase.

- El listado general de clases (`GET /clases`) debe devolver, por defecto, solo
  las clases con `cancelada = FALSE`.
- Una clase cancelada no debe admitir nuevas reservas (aunque tenga cupo
  disponible).

### Cupo máximo

Antes de crear una reserva, hay que verificar que la cantidad de reservas ya
existentes para esa clase sea menor a su `cupo_maximo`. Si el cupo está
completo, la API debe rechazar la reserva (te sugerimos `409 Conflict`, código
que no usamos antes en el curso, pero que es el estándar HTTP para "la
operación no se puede completar por el estado actual del recurso").

### Reservas repetidas

Un socio no debería poder reservar dos veces una misma clase.

### Restricción de edad

Si `edad_minima` y/o `edad_maxima` **no** son `NULL`, hay que calcular la edad
de la persona (a partir de su `fecha_nacimiento`) y verificar que esté dentro
del rango antes de permitir la reserva. Si no cumple, la API debe rechazar la
reserva (con `422 Unprocessable Entity`, ya que el problema está en los
datos de la solicitud).

> Nota: calcular una edad a partir de dos fechas no es algo que hayamos visto
> explícitamente. Alcanza con restar el año de `fecha_nacimiento`
> al año actual, ajustando si todavía no pasó el cumpleaños en el año en curso.
> El módulo `datetime` de Python trae todo lo necesario para esto. La función
> ya está resuelta en la consigna.

---

## Autenticación y permisos

La autenticación será limitada, no vamos a saber *quién* usa el sistema.
Manejaremos dos API keys: una para socios del gimnasio y otra para
administradores.

| Rol | Variable de entorno sugerida | Puede hacer |
|---|---|---|
| Admin   | `ADMIN_API_KEY` | CRUD completo de `clases` y `socios`; consultar reservas de cualquier clase o socio |
| Socio   | `SOCIO_API_KEY` | Crear y consultar reservas |
| Público | Sin API key     | Consultar clases |

### Cómo responder según el caso

- Si **no** es un endpoint público, el header `X-API-Key` **no está presente**,
o no coincide con ninguna de las dos keys válidas → `401 Unauthorized`.
- Si el header **sí es una key válida**, pero corresponde a un rol sin permiso
para esa acción (por ejemplo, la key de socio intentando hacer un `POST
/clases`) → `403 Forbidden`.

`403` es un código que no usamos antes. A diferencia de `401` (que
significa "no sé quién sos" o "tus credenciales no son válidas"), `403`
significa "sé quién sos, pero no tenés permiso para hacer esto".

### Limitación conocida (y aceptada) de este mecanismo

Como la key de socio es la misma para todos los socios, la API no puede saber
*qué* socio particular está haciendo cada pedido, solo sabe que quien llama
*es* un socio. Esto significa, por ejemplo, que técnicamente cualquiera con la
key de socio podría crear una reserva a nombre del DNI de otra persona. No hace
falta resolver esto: es una limitación esperada de trabajar con API Keys fijas
en lugar de un sistema de usuarios con login, que está fuera del alcance de
este taller.

---

## Endpoints

A continuación se detalla cada endpoint junto con la/s consulta/s SQL que
serán necesarias. Se dan resueltas porque el objetivo del curso no es que
aprendamos a escribir SQL desde cero, sino que sepamos ejecutarlo correctamente
desde Python (con parámetros seguros, manejo de errores, y traducción a
respuestas HTTP).

### Socios — requiere rol **admin**

| Endpoint | Query |
|---|---|
| `GET /socios` | `SELECT * FROM socios` |
| `GET /socios/{dni}` | `SELECT * FROM socios WHERE dni = %s` |
| `POST /socios` | `INSERT INTO socios (dni, nombre, apellido, fecha_nacimiento) VALUES (%s, %s, %s, %s)` |
| `PUT /socios/{dni}` | `UPDATE socios SET nombre = %s, apellido = %s, fecha_nacimiento = %s WHERE dni = %s` |
| `DELETE /socios/{dni}` | `DELETE FROM socios WHERE dni = %s` |

Para `GET /socios/{dni}`, `PUT` y `DELETE`: si la consulta no encuentra a la
persona, hay que devolver `404`.

### Clases

Estos endpoints ya vienen hechos, a modo de ejemplo.

| Endpoint | Rol | Query |
|---|---|---|
| `GET /clases` | Público | `SELECT * FROM clases WHERE cancelada = FALSE` |
| `GET /clases/{id}` | Público | `SELECT * FROM clases WHERE id = %s` |
| `POST /clases` | Admin | `INSERT INTO clases (nombre, instructor, horario, cupo_maximo, edad_minima, edad_maxima) VALUES (%s, %s, %s, %s, %s, %s)` |
| `PUT /clases/{id}` | Admin | `UPDATE clases SET nombre = %s, instructor = %s, horario = %s, cupo_maximo = %s, edad_minima = %s, edad_maxima = %s WHERE id = %s` |
| `DELETE /clases/{id}/cancelar` | Admin | `UPDATE clases SET cancelada = TRUE WHERE id = %s` |

Notemos que "eliminar" una clase, en este TP, nunca ejecuta un `DELETE` sobre
`clases`: siempre se resuelve con el `UPDATE` de la baja lógica. Usaremos el
método DELETE de HTTP, pero no haremos una query SQL DELETE, sino un UPDATE.

Para `GET /clases/{id}`, `PUT` y `DELETE /cancelar`: si no se encuentra la
clase, devolvemos `404`.

### Reservas

**`POST /clases/{id}/reservas`**: rol **socio** o **admin**

Antes de insertar la reserva, tenemos que hacer cuatro consultas:

```sql
SELECT cupo_maximo, edad_minima, edad_maxima, cancelada FROM clases WHERE id = %s
```

```sql
SELECT COUNT(*) AS cantidad FROM reservas WHERE clase_id = %s
```

```sql
SELECT fecha_nacimiento FROM socios WHERE dni = %s
```

```sql
"SELECT COUNT(*) AS cantidad FROM reservas WHERE clase_id = %s AND socio_dni = %s"
```

Con esos cuatro resultados, aplicamos en Python las reglas de negocio (clase
cancelada, cupo, edad, reserva repetida) que detallamos más arriba. Si todo es
válido, insertamos la reserva:

```sql
INSERT INTO reservas (clase_id, socio_dni) VALUES (%s, %s)
```

Códigos de respuesta esperados: `201` si se crea, `404` si la clase o la
persona no existen, `409` si no hay cupo o si la reserva está repetida, `422`
si no cumple la restricción de edad.

**`GET /clases/{id}/reservas`**: rol **admin**

```sql
SELECT reservas.id, reservas.fecha_reserva, socios.dni, socios.nombre, socios.apellido
FROM reservas
JOIN socios ON reservas.socio_dni = socios.dni
WHERE reservas.clase_id = %s
```

**`GET /socios/{dni}/reservas`** — rol **socio** o **admin**

```sql
SELECT reservas.id, reservas.fecha_reserva, clases.id AS clase_id, clases.nombre, clases.instructor, clases.horario
FROM reservas
JOIN clases ON reservas.clase_id = clases.id
WHERE reservas.socio_dni = %s
```

---

## Frontend

Todos los estudiantes deben implementar el **backend completo**: todos los
endpoints, reglas de negocio y permisos detallados arriba.

El alcance del **frontend**, en cambio, depende de la situación de cada
estudiante con las unidades de javascript:

- **Quienes ya aprobaron las unidades de JavaScript** (1er cuatrimestre): solo
  tienen que construir la parte del frontend correspondiente al **CRUD de
clases** (listar, crear, editar y cancelar clases), consumiendo la propia API
con la key de admin. No es necesario que implementen las pantallas de reservas.

- **Quienes no aprobaron el primer cuatrimestre** tienen que construir el
  frontend completo, incluyendo además de lo anterior:
  - Listado de clases disponibles (vista pública, sin key).
  - Formulario para reservar un lugar en una clase, indicando el DNI de la
    persona (usando la key de socio).
  - Vista para consultar, dado un DNI, las clases reservadas por ese socio
    (usando la key de socio o de admin).

- **Si hay integrantes del equipo que aprobaron el primer cuatrimestre y otros
que no**, el grupo deberá hacer el frontend completo, pero los commits de la
parte que corresponde al primer cuatrimestre deben estar _firmados_ por los/las
estudiantes que correspondan.

En ambos casos, el frontend debe ser HTML + CSS + JavaScript vanilla (sin
frameworks), y debe consumir la API real vía `fetch` (no se aceptan datos
simulados o _hardcodeados_ en el HTML).

El código CSS **no** será evaluado en el examen.

---

## Entregables

Todo el trabajo debe estar en un repositorio de Gitea. Debe ser **un solo
repositorio** para el grupo, en donde _aproximadamente_ cada integrante
contribuya con la misma cantidad de código. El repositorio debe incluir:

1. **Código fuente completo del backend** (en Python/FastAPI), implementando el
   100% de los endpoints de esta consigna.
2. **Frontend**, con el alcance que corresponda según la situación de cada
   estudiante (ver sección anterior). Si ningún integrante del equipo tiene
pendiente el primer cuatrimestre, por favor aclarenlo explícitamente en el
`README.md`.
3. **`requirements.txt`** con las dependencias del backend.
4. Reemplazar este **`README.md`** por otro que incluya:
   - Nombre y apellido de cada integrante del equipo.
   - Instrucciones para "levantar" el proyecto de punta a punta (variables de
     entorno necesarias (pueden crear un archivo `.env.example` con variables de
entorno "falsas"), cómo cargar `gimnasio.sql`, cómo correr el backend, cómo
abrir el frontend).
   - Los valores que usaste para `ADMIN_API_KEY` y `SOCIO_API_KEY`, o cómo
     configurarlos, de forma que puedan probarse sin depender de tu entorno
local.
   - Una aclaración explícita de qué alcance de frontend implementaron
     (completo o solo CRUD de clases) y por qué.

No hace falta entregar `gimnasio.sql`: es el mismo para todos los grupos y se
adjunta a esta consigna.

---

## Tests

Van a recibir un archivo `tests_backend.py` (usando `pytest` + `httpx`) que valida
el comportamiento de cada API contra esta consigna. **Aprobar el trabajo
práctico requiere que la totalidad de estos tests pasen**, corriendo `pytest
tests_backend.py` contra el proyecto levantado desde cero, con la base de datos
cargada exactamente desde `gimnasio.sql` sin modificaciones.

Algunas consideraciones sobre estos tests:

- Validan comportamiento observable: códigos de estado, forma del JSON de
  respuesta, y que las reglas de negocio (cupo, edad, baja lógica, permisos por
rol) se respeten. No exigen una implementación interna particular.
- Van a tener acceso a una porción de ejemplo de estos tests antes de la
  entrega final, para poder validar el formato de tus respuestas con
anticipación. Los tests completos corren recién sobre la entrega definitiva.
- Como el esquema de base de datos es común a todos, no hay margen para que los
  tests fallen por diferencias de nombres de tablas o columnas: cualquier
falla en ese sentido indica un error en la implementación, es poco probable que
fallen una ambigüedad de la consigna. De todos modos, se puede consultar ante
cualquier duda.

Un trabajo que no pase el 100% de los tests no se considera apto para ser
evaluado en la instancia de examen final.

---

## Fecha de entrega

Viernes 23/10/2026 (no tenemos clase ese día, pero es la fecha límite para 
dejar el código publicado en Gitea).

---

## Cómo empezar el trabajo

## Requisitos

- Python 3.10 o superior.
- MySQL/MariaDB compatible con el script `gimnasio.sql`.

### 1. Crear la base de datos

Desde MySQL:

```bash
mysql -u tu_usuario -p < gimnasio.sql
```

El script crea la base `gimnasio` y carga los datos de ejemplo.

### 2. Crear el entorno virtual

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Configurar variables de entorno

Copiar `.env.example` como `.env` y completar los datos de conexión:

```bash
cd api
cp .env.example .env
```

La aplicación lee automáticamente el archivo `.env`.

### 4. Ejecutar

```bash
# Ubicados en la carpeta api
uvicorn main:app --reload
```

La API queda disponible en:

- `http://127.0.0.1:8000`
- Documentación Swagger: `http://127.0.0.1:8000/docs`

### API keys

Ejemplo:

- `ADMIN_API_KEY=admin-key-de-prueba`
- `SOCIO_API_KEY=socio-key-de-prueba`

Las operaciones protegidas reciben la key mediante:

```text
X-API-Key: admin-key-de-prueba
```

o:

```text
X-API-Key: socio-key-de-prueba
```

### 5. Correr los tests

En cualquier momento, podemos correr los tests si se dan las siguientes
condiciones:

- Nos ubicamos en la carpeta "raíz" del proyecto
- Tenemos el entorno virtual activado
- Tenemos la API funcionando con uvicorn

Corremos los tests con este comando:

```bash
python -m pytest tests_backend.py -v
```

Si ves que los tests fallan, no hay problema: eso nos indica que hay puntos de
la consigna que todavía no se cumplen. Pueden correr los tests todas las veces
que hagan falta.

Para que el TP esté aprobado es indispensable que los tests pasen; pero el hecho
de que pasen los tests no garantiza que el trabajo estará aprobado.

---

### Roles

- Público: `GET /clases` y `GET /clases/{id}`
- Socio: crear reservas y consultar reservas de un socio
- Admin: CRUD de socios y clases, además de consultas de reservas

### Estructura de archivos

```text
gimnasio.sql
README.md
README_original.md
requirements.txt
tests_backend.py
api/
├── main.py
├── database.py
├── auth.py
├── models.py
└── routers/
    ├── socios.py
    ├── clases.py
    └── reservas.py
```
