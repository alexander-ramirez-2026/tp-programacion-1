
from fastapi import APIRouter, Depends, HTTPException, status
from mysql.connector import Error as IntegrityError

from api.auth import require_admin
from api.database import get_connection
from api.models import Socio

router = APIRouter(prefix="/socios", tags=["Socios"])


# LISTAR TODOS LOS SOCIOS
@router.get("")
def obtener_socios(rol: str = Depends(require_admin)):
    conexion = get_connection()

    try:
        cursor = conexion.cursor()
        cursor.execute("SELECT * FROM socios")

        return [dict(fila) for fila in cursor.fetchall()]

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Error al consultar socios"
        )

    finally:
        conexion.close()


# OBTENER UN SOCIO POR DNI
@router.get("/{dni}")
def obtener_socio(dni: int, rol: str = Depends(require_admin)):
    conexion = get_connection()

    try:
        cursor = conexion.cursor()

        cursor.execute(
            "SELECT * FROM socios WHERE dni = %s",
            (dni,)
        )

        resultado = cursor.fetchone()

        if resultado is None:
            raise HTTPException(
                status_code=404,
                detail="Socio no encontrado"
            )

        return dict(resultado)

    finally:
        conexion.close()


# CREAR UN SOCIO
@router.post("", status_code=status.HTTP_201_CREATED)
def crear_socio(datos: Socio, rol: str = Depends(require_admin)):
    conexion = get_connection()

    try:
        cursor = conexion.cursor()

        query = """
            INSERT INTO socios (dni, nombre, apellido, fecha_nacimiento)
            VALUES (%s, %s, %s, %s)
        """

        cursor.execute(query, (
            datos.dni,
            datos.nombre,
            datos.apellido,
            datos.fecha_nacimiento.isoformat()
        ))

        conexion.commit()

        return {
            "dni": datos.dni,
            "nombre": datos.nombre,
            "apellido": datos.apellido,
            "fecha_nacimiento": datos.fecha_nacimiento.isoformat()
        }

    except IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="El DNI ya está registrado"
        )

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Error al crear socio"
        )

    finally:
        conexion.close()


# ACTUALIZAR UN SOCIO
@router.put("/{dni}")
def actualizar_socio(
    dni: int,
    datos: Socio,
    rol: str = Depends(require_admin)
):
    conexion = get_connection()

    try:
        cursor = conexion.cursor()

        cursor.execute(
            "SELECT dni FROM socios WHERE dni = %s",
            (dni,)
        )

        if cursor.fetchone() is None:
            raise HTTPException(
                status_code=404,
                detail="Socio no encontrado"
            )

        query = """
            UPDATE socios
            SET nombre = %s, apellido = %s, fecha_nacimiento = %s
            WHERE dni = %s
        """

        cursor.execute(query, (
            datos.nombre,
            datos.apellido,
            datos.fecha_nacimiento.isoformat(),
            dni
        ))

        conexion.commit()

        return {
            "dni": dni,
            "nombre": datos.nombre,
            "apellido": datos.apellido,
            "fecha_nacimiento": datos.fecha_nacimiento.isoformat()
        }

    finally:
        conexion.close()


# ELIMINAR UN SOCIO
@router.delete("/{dni}")
def eliminar_socio(dni: int, rol: str = Depends(require_admin)):
    conexion = get_connection()

    try:
        cursor = conexion.cursor()

        cursor.execute(
            "DELETE FROM socios WHERE dni = %s",
            (dni,)
        )

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail="Socio no encontrado"
            )

        conexion.commit()

        return {
            "mensaje": "Socio eliminado correctamente"
        }

    except IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="No se puede eliminar el socio porque tiene reservas registradas."
        )

    finally:
        conexion.close()
