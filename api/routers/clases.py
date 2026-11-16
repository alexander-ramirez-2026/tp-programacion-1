
from fastapi import APIRouter, Depends, HTTPException, status

from api.auth import require_admin
from api.database import get_connection
from api.models import Clase

router = APIRouter(prefix="/clases", tags=["Clases"])


# BUSCAR UNA CLASE POR ID
def _obtener_clase(cursor, clase_id: int):
    cursor.execute(
        "SELECT * FROM clases WHERE id = %s",
        (clase_id,)
    )
    return cursor.fetchone()


# LISTAR CLASES ACTIVAS
@router.get("")
def listar_clases():
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM clases WHERE cancelada = 0"
        )

        return [dict(fila) for fila in cursor.fetchall()]

    finally:
        conn.close()


# OBTENER UNA CLASE POR ID
# También permite consultar clases canceladas
@router.get("/{clase_id}")
def obtener_clase(clase_id: int):
    conn = get_connection()

    try:
        cursor = conn.cursor()
        clase = _obtener_clase(cursor, clase_id)

        if clase is None:
            raise HTTPException(
                status_code=404,
                detail="Clase no encontrada"
            )

        return dict(clase)

    finally:
        conn.close()


# CREAR UNA CLASE
@router.post("", status_code=status.HTTP_201_CREATED)
def crear_clase(
    clase: Clase,
    role: str = Depends(require_admin)
):
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO clases
                (nombre, instructor, horario, cupo_maximo,
                 edad_minima, edad_maxima)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                clase.nombre,
                clase.instructor,
                clase.horario,
                clase.cupo_maximo,
                clase.edad_minima,
                clase.edad_maxima
            )
        )

        clase_id = cursor.lastrowid
        conn.commit()

        return {
            "id": clase_id,
            "nombre": clase.nombre,
            "instructor": clase.instructor,
            "horario": clase.horario,
            "cupo_maximo": clase.cupo_maximo,
            "edad_minima": clase.edad_minima,
            "edad_maxima": clase.edad_maxima,
            "cancelada": False
        }

    finally:
        conn.close()


# ACTUALIZAR UNA CLASE
@router.put("/{clase_id}")
def actualizar_clase(
    clase_id: int,
    clase: Clase,
    role: str = Depends(require_admin)
):
    conn = get_connection()

    try:
        cursor = conn.cursor()
        existente = _obtener_clase(cursor, clase_id)

        if existente is None:
            raise HTTPException(
                status_code=404,
                detail="Clase no encontrada"
            )

        cursor.execute(
            """
            UPDATE clases
            SET nombre = %s,
                instructor = %s,
                horario = %s,
                cupo_maximo = %s,
                edad_minima = %s,
                edad_maxima = %s
            WHERE id = %s
            """,
            (
                clase.nombre,
                clase.instructor,
                clase.horario,
                clase.cupo_maximo,
                clase.edad_minima,
                clase.edad_maxima,
                clase_id
            )
        )

        conn.commit()

        return {
            "id": clase_id,
            "nombre": clase.nombre,
            "instructor": clase.instructor,
            "horario": clase.horario,
            "cupo_maximo": clase.cupo_maximo,
            "edad_minima": clase.edad_minima,
            "edad_maxima": clase.edad_maxima,
            "cancelada": bool(existente["cancelada"])
        }

    finally:
        conn.close()


# CANCELAR UNA CLASE (BAJA LÓGICA)
@router.delete("/{clase_id}/cancelar")
def cancelar_clase(
    clase_id: int,
    role: str = Depends(require_admin)
):
    conn = get_connection()

    try:
        cursor = conn.cursor()
        existente = _obtener_clase(cursor, clase_id)

        if existente is None:
            raise HTTPException(
                status_code=404,
                detail="Clase no encontrada"
            )

        cursor.execute(
            "UPDATE clases SET cancelada = 1 WHERE id = %s",
            (clase_id,)
        )

        conn.commit()

        return {
            "id": clase_id,
            "mensaje": "Clase cancelada"
        }

    finally:
        conn.close()
