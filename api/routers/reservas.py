
"""
Gestión de reservas de clases del gimnasio.
"""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from api.auth import require_socio_or_admin, require_admin
from api.database import get_connection


router = APIRouter(tags=["Reservas"])


# MODELO PARA VALIDAR LOS DATOS DE LA RESERVA
class ReservaCreate(BaseModel):
    socio_dni: int = Field(gt=0)


# CALCULAR EDAD DEL SOCIO
def calcular_edad(fecha_nacimiento: date) -> int:
    hoy = date.today()
    edad = hoy.year - fecha_nacimiento.year

    if (hoy.month, hoy.day) < (
        fecha_nacimiento.month,
        fecha_nacimiento.day
    ):
        edad -= 1

    return edad


# ==========================================
# CREAR UNA RESERVA
# ==========================================
@router.post(
    "/clases/{clase_id}/reservas",
    status_code=status.HTTP_201_CREATED
)
def crear_reserva(
    clase_id: int,
    datos: ReservaCreate,
    rol: str = Depends(require_socio_or_admin)
):
    conexion = get_connection()

    try:
        cursor = conexion.cursor()
        socio_dni = datos.socio_dni

        # VERIFICAR QUE LA CLASE EXISTA
        cursor.execute(
            "SELECT * FROM clases WHERE id = ?",
            (clase_id,)
        )

        clase = cursor.fetchone()

        if not clase:
            raise HTTPException(
                status_code=404,
                detail="Clase no encontrada"
            )

        # VERIFICAR QUE LA CLASE NO ESTÉ CANCELADA
        if clase["cancelada"]:
            raise HTTPException(
                status_code=409,
                detail="La clase está cancelada"
            )

        # VERIFICAR QUE EL SOCIO EXISTA
        cursor.execute(
            "SELECT * FROM socios WHERE dni = ?",
            (socio_dni,)
        )

        socio = cursor.fetchone()

        if not socio:
            raise HTTPException(
                status_code=404,
                detail="Socio no encontrado"
            )

        # VERIFICAR QUE NO EXISTA UNA RESERVA REPETIDA
        cursor.execute(
            """
            SELECT COUNT(*) AS cantidad
            FROM reservas
            WHERE clase_id = ? AND socio_dni = ?
            """,
            (clase_id, socio_dni)
        )

        if cursor.fetchone()["cantidad"] > 0:
            raise HTTPException(
                status_code=409,
                detail="El socio ya está reservado en esta clase"
            )

        # VERIFICAR LOS CUPOS DISPONIBLES
        cursor.execute(
            """
            SELECT COUNT(*) AS cantidad
            FROM reservas
            WHERE clase_id = ?
            """,
            (clase_id,)
        )

        reservas_actuales = cursor.fetchone()["cantidad"]

        if reservas_actuales >= clase["cupo_maximo"]:
            raise HTTPException(
                status_code=409,
                detail="No quedan cupos disponibles"
            )

        # CALCULAR LA EDAD DEL SOCIO
        fecha_nacimiento = date.fromisoformat(
            socio["fecha_nacimiento"]
        )

        edad = calcular_edad(fecha_nacimiento)

        # VERIFICAR EDAD MÍNIMA
        if (
            clase["edad_minima"] is not None
            and edad < clase["edad_minima"]
        ):
            raise HTTPException(
                status_code=422,
                detail="El socio no cumple la edad mínima"
            )

        # VERIFICAR EDAD MÁXIMA
        if (
            clase["edad_maxima"] is not None
            and edad > clase["edad_maxima"]
        ):
            raise HTTPException(
                status_code=422,
                detail="El socio supera la edad máxima"
            )

        # REGISTRAR LA RESERVA
        cursor.execute(
            """
            INSERT INTO reservas (clase_id, socio_dni)
            VALUES (?, ?)
            """,
            (clase_id, socio_dni)
        )

        reserva_id = cursor.lastrowid
        conexion.commit()

        return {
            "id": reserva_id,
            "clase_id": clase_id,
            "socio_dni": socio_dni,
            "mensaje": "Reserva creada correctamente"
        }

    except HTTPException:
        raise

    except Exception as exc:
        conexion.rollback()

        raise HTTPException(
            status_code=500,
            detail="Error al crear la reserva"
        ) from exc

    finally:
        conexion.close()


# ==========================================
# CANCELAR UNA RESERVA
# ==========================================
@router.delete("/reservas/{reserva_id}")
def cancelar_reserva(
    reserva_id: int,
    rol: str = Depends(require_admin)
):
    conexion = get_connection()

    try:
        cursor = conexion.cursor()

        # VERIFICAR QUE LA RESERVA EXISTA
        cursor.execute(
            "SELECT * FROM reservas WHERE id = ?",
            (reserva_id,)
        )

        reserva = cursor.fetchone()

        if not reserva:
            raise HTTPException(
                status_code=404,
                detail="Reserva no encontrada"
            )

        # ELIMINAR LA RESERVA
        cursor.execute(
            "DELETE FROM reservas WHERE id = ?",
            (reserva_id,)
        )

        conexion.commit()

        return {
            "id": reserva_id,
            "mensaje": "Reserva cancelada correctamente",
            "cupo_liberado": True
        }

    except HTTPException:
        raise

    except Exception as exc:
        conexion.rollback()

        raise HTTPException(
            status_code=500,
            detail="Error al cancelar la reserva"
        ) from exc

    finally:
        conexion.close()


# ==========================================
# CONSULTAR RESERVAS DE UNA CLASE
# ==========================================
@router.get("/clases/{clase_id}/reservas")
def obtener_reservas_clase(
    clase_id: int,
    rol: str = Depends(require_admin)
):
    conexion = get_connection()

    try:
        cursor = conexion.cursor()

        cursor.execute(
            "SELECT id FROM clases WHERE id = ?",
            (clase_id,)
        )

        if not cursor.fetchone():
            raise HTTPException(
                status_code=404,
                detail="Clase no encontrada"
            )

        cursor.execute(
            """
            SELECT
                r.id,
                r.clase_id,
                r.socio_dni,
                r.fecha_reserva,
                s.dni,
                s.nombre,
                s.apellido
            FROM reservas r
            JOIN socios s ON r.socio_dni = s.dni
            WHERE r.clase_id = ?
            """,
            (clase_id,)
        )

        reservas = cursor.fetchall()

        return [dict(fila) for fila in reservas]

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Error al consultar las reservas"
        ) from exc

    finally:
        conexion.close()


# ==========================================
# CONSULTAR RESERVAS DE UN SOCIO
# ==========================================
@router.get("/socios/{dni}/reservas")
def obtener_reservas_socio(
    dni: int,
    rol: str = Depends(require_socio_or_admin)
):
    conexion = get_connection()

    try:
        cursor = conexion.cursor()

        cursor.execute(
            "SELECT dni FROM socios WHERE dni = ?",
            (dni,)
        )

        if not cursor.fetchone():
            raise HTTPException(
                status_code=404,
                detail="Socio no encontrado"
            )

        cursor.execute(
            """
            SELECT
                r.id,
                r.clase_id,
                r.socio_dni,
                r.fecha_reserva,
                c.nombre,
                c.instructor,
                c.horario
            FROM reservas r
            JOIN clases c ON r.clase_id = c.id
            WHERE r.socio_dni = ?
            """,
            (dni,)
        )

        reservas = cursor.fetchall()

        return [dict(fila) for fila in reservas]

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Error al consultar las reservas"
        ) from exc

    finally:
        conexion.close()
