
import os
from api.database import get_connection

# Buscar el archivo gimnasio.sql
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SQL_PATH = os.path.join(BASE_DIR, "gimnasio.sql")


def inicializar_db():
    conexion = get_connection()

    try:
        with open(SQL_PATH, "r", encoding="utf-8") as archivo:
            script_sql = archivo.read()

        conexion.executescript(script_sql)
        conexion.commit()

        print("Base de datos inicializada correctamente.")

    finally:
        conexion.close()


if __name__ == "__main__":
    inicializar_db()
