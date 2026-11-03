"""
Tests para el TP Final: API de gestión de un gimnasio.

Requisitos para correr estos tests:
    pip install pytest httpx

Se asume que:
- La API expone las rutas descriptas en la consigna (/socios, /clases,
  /clases/{id}/reservas, /socios/{dni}/reservas, etc.).
- La API corre en http://127.0.0.1:8000 (ajustar BASE_URL si es necesario).
- La base de datos fue cargada desde gimnasio.sql, sin modificaciones de
  esquema (los nombres de tablas y columnas deben coincidir exactamente).
- Existen dos API Keys configuradas en el servidor mediante variables de
  entorno (ADMIN_API_KEY y SOCIO_API_KEY), cuyos valores coinciden con
  ADMIN_API_KEY y SOCIO_API_KEY definidas más abajo en este archivo.

Cómo correr:
    1. Levantar el servidor: uvicorn main:app --reload
    2. En otra terminal: pytest test_final.py -v

Nota: estos tests validan comportamiento observable (códigos de estado,
forma del JSON, relaciones entre clases/socios/reservas), no la
implementación interna. Los datos de prueba se crean y se eliminan
(o se cancelan, en el caso de las clases) dentro de cada test, para no
depender de los datos de ejemplo de gimnasio.sql ni ensuciar la base
entre corridas.
"""

import random
from datetime import date

import httpx
import pytest

import os
from dotenv import load_dotenv

BASE_URL = "http://127.0.0.1:8000"

# Cargar las API Keys desde el .env de la carpeta principal
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

ADMIN_API_KEY = os.getenv("ADMIN_API_KEY")
SOCIO_API_KEY = os.getenv("SOCIO_API_KEY")
INVALID_API_KEY = "esta-key-no-es-ninguna-de-las-dos"

ADMIN_HEADERS = {"X-API-Key": ADMIN_API_KEY}
SOCIO_HEADERS = {"X-API-Key": SOCIO_API_KEY}

def dni_aleatorio() -> int:
    """DNI de prueba, en un rango que no debería chocar con datos reales."""
    return random.randint(90_000_000, 99_999_999)


def fecha_para_edad(anios: int) -> str:
    """
    Devuelve (en formato YYYY-MM-DD) una fecha de nacimiento tal que,
    calculada desde hoy, la persona tenga exactamente `anios` años.
    Se calcula en runtime (no se hardcodea un año) para que los tests
    seiguan siendo válidos sin importar cuándo se corran.
    """
    hoy = date.today()
    try:
        return hoy.replace(year=hoy.year - anios).isoformat()
    except ValueError:
        # Nacidos un 29 de febrero, en un año no bisiesto: corremos un día.
        return hoy.replace(year=hoy.year - anios, day=hoy.day - 1).isoformat()


@pytest.fixture(scope="module")
def client():
    with httpx.Client(base_url=BASE_URL, timeout=10.0) as c:
        yield c


@pytest.fixture()
def socio_factory(client):
    """
    Fixture-factory: permite crear varios socios dentro de un mismo test
    (socio_factory(edad=20), socio_factory(edad=15), ...). Cada socio creado
    se elimina automáticamente al terminar el test.
    """
    creados = []

    def _crear(edad: int = 25, **overrides):
        payload = {
            "dni": dni_aleatorio(),
            "nombre": "Test",
            "apellido": "Alumno",
            "fecha_nacimiento": fecha_para_edad(edad),
        }
        payload.update(overrides)
        response = client.post("/socios", json=payload, headers=ADMIN_HEADERS)
        assert response.status_code == 201, (
            f"No se pudo crear el socio de prueba: {response.status_code} {response.text}"
        )
        socio = response.json()
        creados.append(socio["dni"])
        return socio

    yield _crear

    for dni in creados:
        client.delete(f"/socios/{dni}", headers=ADMIN_HEADERS)


@pytest.fixture()
def clase_factory(client):
    """
    Fixture-factory equivalente a socio_factory, pero para clases. Como no
    existe un DELETE físico de clases, la limpieza se hace cancelándolas.
    """
    creadas = []

    def _crear(**overrides):
        payload = {
            "nombre": "Clase de prueba",
            "instructor": "Instructor Test",
            "horario": "Lunes 08:00 a 09:00",
            "cupo_maximo": 10,
            "edad_minima": None,
            "edad_maxima": None,
        }
        payload.update(overrides)
        response = client.post("/clases", json=payload, headers=ADMIN_HEADERS)
        assert response.status_code == 201, (
            f"No se pudo crear la clase de prueba: {response.status_code} {response.text}"
        )
        clase = response.json()
        creadas.append(clase["id"])
        return clase

    yield _crear

    for clase_id in creadas:
        client.delete(f"/clases/{clase_id}/cancelar", headers=ADMIN_HEADERS)


# ---------------------------------------------------------------------
# Autenticación y permisos
# ---------------------------------------------------------------------

class TestAutenticacion:
    def test_endpoint_admin_sin_key_devuelve_401(self, client):
        response = client.get("/socios")
        assert response.status_code == 401

    def test_endpoint_admin_con_key_invalida_devuelve_401(self, client):
        response = client.get("/socios", headers={"X-API-Key": INVALID_API_KEY})
        assert response.status_code == 401

    def test_endpoint_admin_con_key_de_socio_devuelve_403(self, client):
        # La key es válida, pero el rol "socio" no tiene permiso acá.
        response = client.get("/socios", headers=SOCIO_HEADERS)
        assert response.status_code == 403

    def test_endpoint_publico_no_requiere_key(self, client):
        response = client.get("/clases")
        assert response.status_code == 200


# ---------------------------------------------------------------------
# Socios
# ---------------------------------------------------------------------

class TestSocios:
    def test_crear_socio_devuelve_201(self, client, socio_factory):
        socio = socio_factory()
        assert "dni" in socio
        assert socio["nombre"] == "Test"

    def test_crear_socio_sin_permiso_devuelve_401_o_403(self, client):
        payload = {
            "dni": dni_aleatorio(),
            "nombre": "X",
            "apellido": "Y",
            "fecha_nacimiento": "1990-01-01",
        }
        sin_key = client.post("/socios", json=payload)
        assert sin_key.status_code == 401

        con_key_socio = client.post("/socios", json=payload, headers=SOCIO_HEADERS)
        assert con_key_socio.status_code == 403

    def test_listar_socios_incluye_el_creado(self, client, socio_factory):
        socio = socio_factory()
        response = client.get("/socios", headers=ADMIN_HEADERS)
        assert response.status_code == 200
        dnis = [s["dni"] for s in response.json()]
        assert socio["dni"] in dnis

    def test_obtener_socio_existente(self, client, socio_factory):
        socio = socio_factory()
        response = client.get(f"/socios/{socio['dni']}", headers=ADMIN_HEADERS)
        assert response.status_code == 200
        assert response.json()["nombre"] == "Test"

    def test_obtener_socio_inexistente_devuelve_404(self, client):
        response = client.get("/socios/1", headers=ADMIN_HEADERS)
        assert response.status_code == 404

    def test_actualizar_socio_devuelve_200(self, client, socio_factory):
        socio = socio_factory()
        payload = {
            "dni": socio["dni"],
            "nombre": "Actualizado",
            "apellido": socio["apellido"],
            "fecha_nacimiento": socio["fecha_nacimiento"],
        }
        response = client.put(
            f"/socios/{socio['dni']}", json=payload, headers=ADMIN_HEADERS
        )
        assert response.status_code == 200
        assert response.json()["nombre"] == "Actualizado"

    def test_actualizar_socio_persiste_los_cambios(self, client, socio_factory):
        socio = socio_factory()
        payload = {
            "dni": socio["dni"],
            "nombre": "Actualizado",
            "apellido": socio["apellido"],
            "fecha_nacimiento": socio["fecha_nacimiento"],
        }
        client.put(f"/socios/{socio['dni']}", json=payload, headers=ADMIN_HEADERS)

        response = client.get(f"/socios/{socio['dni']}", headers=ADMIN_HEADERS)
        assert response.json()["nombre"] == "Actualizado"

    def test_actualizar_socio_inexistente_devuelve_404(self, client):
        payload = {
            "dni": 1,
            "nombre": "X",
            "apellido": "Y",
            "fecha_nacimiento": "2000-01-01",
        }
        response = client.put("/socios/1", json=payload, headers=ADMIN_HEADERS)
        assert response.status_code == 404

    def test_eliminar_socio_devuelve_200_o_204(self, client):
        payload = {
            "dni": dni_aleatorio(),
            "nombre": "Borrar",
            "apellido": "Me",
            "fecha_nacimiento": "1990-01-01",
        }
        creado = client.post("/socios", json=payload, headers=ADMIN_HEADERS).json()
        response = client.delete(f"/socios/{creado['dni']}", headers=ADMIN_HEADERS)
        assert response.status_code in (200, 204)

    def test_socio_eliminado_ya_no_se_puede_obtener(self, client):
        payload = {
            "dni": dni_aleatorio(),
            "nombre": "Borrar",
            "apellido": "Me",
            "fecha_nacimiento": "1990-01-01",
        }
        creado = client.post("/socios", json=payload, headers=ADMIN_HEADERS).json()
        client.delete(f"/socios/{creado['dni']}", headers=ADMIN_HEADERS)

        response = client.get(f"/socios/{creado['dni']}", headers=ADMIN_HEADERS)
        assert response.status_code == 404

    def test_eliminar_socio_inexistente_devuelve_404(self, client):
        response = client.delete("/socios/1", headers=ADMIN_HEADERS)
        assert response.status_code == 404


# ---------------------------------------------------------------------
# Clases
# ---------------------------------------------------------------------

class TestClases:
    def test_listar_clases_devuelve_200_y_una_lista(self, client):
        response = client.get("/clases")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_crear_clase_sin_permiso_devuelve_401_o_403(self, client):
        payload = {
            "nombre": "Zumba",
            "instructor": "Vale",
            "horario": "Jueves 20 a 21hs",
            "cupo_maximo": 5,
        }
        sin_key = client.post("/clases", json=payload)
        assert sin_key.status_code == 401

        con_key_socio = client.post("/clases", json=payload, headers=SOCIO_HEADERS)
        assert con_key_socio.status_code == 403

    def test_crear_clase_devuelve_201(self, client, clase_factory):
        clase = clase_factory(nombre="Zumba")
        assert clase["nombre"] == "Zumba"
        assert "id" in clase
        assert not clase["cancelada"]

    def test_clase_creada_aparece_en_el_listado(self, client, clase_factory):
        clase = clase_factory()
        response = client.get("/clases")
        ids = [c["id"] for c in response.json()]
        assert clase["id"] in ids

    def test_obtener_clase_existente(self, client, clase_factory):
        clase = clase_factory(nombre="Pilates")
        response = client.get(f"/clases/{clase['id']}")
        assert response.status_code == 200
        assert response.json()["nombre"] == "Pilates"

    def test_obtener_clase_inexistente_devuelve_404(self, client):
        response = client.get("/clases/999999")
        assert response.status_code == 404

    def test_actualizar_clase_devuelve_200(self, client, clase_factory):
        clase = clase_factory()
        payload = {
            "nombre": "Nombre actualizado",
            "instructor": clase["instructor"],
            "horario": clase["horario"],
            "cupo_maximo": clase["cupo_maximo"],
            "edad_minima": clase["edad_minima"],
            "edad_maxima": clase["edad_maxima"],
        }
        response = client.put(
            f"/clases/{clase['id']}", json=payload, headers=ADMIN_HEADERS
        )
        assert response.status_code == 200
        assert response.json()["nombre"] == "Nombre actualizado"

    def test_actualizar_clase_inexistente_devuelve_404(self, client):
        payload = {
            "nombre": "X",
            "instructor": "Y",
            "horario": "Z",
            "cupo_maximo": 1,
        }
        response = client.put("/clases/999999", json=payload, headers=ADMIN_HEADERS)
        assert response.status_code == 404

    def test_cancelar_clase_sin_permiso_devuelve_401_o_403(self, client, clase_factory):
        clase = clase_factory()
        sin_key = client.delete(f"/clases/{clase['id']}/cancelar")
        assert sin_key.status_code == 401

        con_key_socio = client.delete(
            f"/clases/{clase['id']}/cancelar", headers=SOCIO_HEADERS
        )
        assert con_key_socio.status_code == 403

    def test_cancelar_clase_la_marca_como_cancelada(self, client, clase_factory):
        clase = clase_factory()
        response = client.delete(
            f"/clases/{clase['id']}/cancelar", headers=ADMIN_HEADERS
        )
        assert response.status_code == 200

        detalle = client.get(f"/clases/{clase['id']}").json()
        assert bool(detalle["cancelada"]) is True

    def test_clase_cancelada_no_aparece_en_el_listado_publico(
        self, client, clase_factory
    ):
        clase = clase_factory()
        client.delete(f"/clases/{clase['id']}/cancelar", headers=ADMIN_HEADERS)

        response = client.get("/clases")
        ids = [c["id"] for c in response.json()]
        assert clase["id"] not in ids

    def test_cancelar_clase_inexistente_devuelve_404(self, client):
        response = client.delete("/clases/999999/cancelar", headers=ADMIN_HEADERS)
        assert response.status_code == 404


# ---------------------------------------------------------------------
# Reservas
# ---------------------------------------------------------------------

class TestReservas:
    def test_crear_reserva_devuelve_201(self, client, clase_factory, socio_factory):
        clase = clase_factory(cupo_maximo=5)
        socio = socio_factory(edad=25)

        response = client.post(
            f"/clases/{clase['id']}/reservas",
            json={"socio_dni": socio["dni"]},
            headers=SOCIO_HEADERS,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["clase_id"] == clase["id"]
        assert data["socio_dni"] == socio["dni"]

    def test_crear_reserva_sin_key_devuelve_401(
        self, client, clase_factory, socio_factory
    ):
        clase = clase_factory()
        socio = socio_factory()
        response = client.post(
            f"/clases/{clase['id']}/reservas",
            json={"socio_dni": socio["dni"]},
        )
        assert response.status_code == 401

    def test_crear_reserva_con_key_admin_tambien_funciona(
        self, client, clase_factory, socio_factory
    ):
        clase = clase_factory()
        socio = socio_factory()
        response = client.post(
            f"/clases/{clase['id']}/reservas",
            json={"socio_dni": socio["dni"]},
            headers=ADMIN_HEADERS,
        )
        assert response.status_code == 201

    def test_reservar_clase_inexistente_devuelve_404(self, client, socio_factory):
        socio = socio_factory()
        response = client.post(
            "/clases/999999/reservas",
            json={"socio_dni": socio["dni"]},
            headers=SOCIO_HEADERS,
        )
        assert response.status_code == 404

    def test_reservar_para_socio_inexistente_devuelve_404(
        self, client, clase_factory
    ):
        clase = clase_factory()
        response = client.post(
            f"/clases/{clase['id']}/reservas",
            json={"socio_dni": 1},
            headers=SOCIO_HEADERS,
        )
        assert response.status_code == 404

    def test_reservar_clase_cancelada_devuelve_409(
        self, client, clase_factory, socio_factory
    ):
        clase = clase_factory()
        client.delete(f"/clases/{clase['id']}/cancelar", headers=ADMIN_HEADERS)
        socio = socio_factory()

        response = client.post(
            f"/clases/{clase['id']}/reservas",
            json={"socio_dni": socio["dni"]},
            headers=SOCIO_HEADERS,
        )
        assert response.status_code == 409

    def test_reservar_sin_cupo_devuelve_409(
        self, client, clase_factory, socio_factory
    ):
        clase = clase_factory(cupo_maximo=1)
        socio_1 = socio_factory()
        socio_2 = socio_factory()

        primera = client.post(
            f"/clases/{clase['id']}/reservas",
            json={"socio_dni": socio_1["dni"]},
            headers=SOCIO_HEADERS,
        )
        assert primera.status_code == 201

        segunda = client.post(
            f"/clases/{clase['id']}/reservas",
            json={"socio_dni": socio_2["dni"]},
            headers=SOCIO_HEADERS,
        )
        assert segunda.status_code == 409

    def test_reservar_repetido_devuelve_409(
        self, client, clase_factory, socio_factory
    ):
        clase = clase_factory(cupo_maximo=2)
        socio_1 = socio_factory()

        primera = client.post(
            f"/clases/{clase['id']}/reservas",
            json={"socio_dni": socio_1["dni"]},
            headers=SOCIO_HEADERS,
        )
        assert primera.status_code == 201

        segunda = client.post(
            f"/clases/{clase['id']}/reservas",
            json={"socio_dni": socio_1["dni"]},
            headers=SOCIO_HEADERS,
        )
        assert segunda.status_code == 409

    def test_reservar_sin_cumplir_edad_minima_devuelve_422(
        self, client, clase_factory, socio_factory
    ):
        clase = clase_factory(edad_minima=18)
        socio_menor = socio_factory(edad=15)

        response = client.post(
            f"/clases/{clase['id']}/reservas",
            json={"socio_dni": socio_menor["dni"]},
            headers=SOCIO_HEADERS,
        )
        assert response.status_code == 422

    def test_reservar_cumpliendo_edad_minima_devuelve_201(
        self, client, clase_factory, socio_factory
    ):
        clase = clase_factory(edad_minima=18)
        socio_mayor = socio_factory(edad=25)

        response = client.post(
            f"/clases/{clase['id']}/reservas",
            json={"socio_dni": socio_mayor["dni"]},
            headers=SOCIO_HEADERS,
        )
        assert response.status_code == 201

    def test_reservar_excediendo_edad_maxima_devuelve_422(
        self, client, clase_factory, socio_factory
    ):
        clase = clase_factory(edad_maxima=12)
        socio_grande = socio_factory(edad=20)

        response = client.post(
            f"/clases/{clase['id']}/reservas",
            json={"socio_dni": socio_grande["dni"]},
            headers=SOCIO_HEADERS,
        )
        assert response.status_code == 422

    def test_listar_reservas_de_clase_sin_permiso_devuelve_401_o_403(
        self, client, clase_factory
    ):
        clase = clase_factory()
        sin_key = client.get(f"/clases/{clase['id']}/reservas")
        assert sin_key.status_code == 401

        con_key_socio = client.get(
            f"/clases/{clase['id']}/reservas", headers=SOCIO_HEADERS
        )
        assert con_key_socio.status_code == 403

    def test_listar_reservas_de_clase_incluye_datos_del_socio(
        self, client, clase_factory, socio_factory
    ):
        clase = clase_factory()
        socio = socio_factory()
        client.post(
            f"/clases/{clase['id']}/reservas",
            json={"socio_dni": socio["dni"]},
            headers=SOCIO_HEADERS,
        )

        response = client.get(
            f"/clases/{clase['id']}/reservas", headers=ADMIN_HEADERS
        )
        assert response.status_code == 200
        dnis = [r["dni"] for r in response.json()]
        assert socio["dni"] in dnis

    def test_listar_reservas_de_socio_acepta_key_de_socio(
        self, client, clase_factory, socio_factory
    ):
        clase = clase_factory()
        socio = socio_factory()
        client.post(
            f"/clases/{clase['id']}/reservas",
            json={"socio_dni": socio["dni"]},
            headers=SOCIO_HEADERS,
        )

        response = client.get(
            f"/socios/{socio['dni']}/reservas", headers=SOCIO_HEADERS
        )
        assert response.status_code == 200
        ids_de_clase = [r["clase_id"] for r in response.json()]
        assert clase["id"] in ids_de_clase

    def test_listar_reservas_de_socio_sin_key_devuelve_401(
        self, client, socio_factory
    ):
        socio = socio_factory()
        response = client.get(f"/socios/{socio['dni']}/reservas")
        assert response.status_code == 401
