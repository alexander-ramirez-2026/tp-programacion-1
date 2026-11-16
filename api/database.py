import os
import mysql.connector
from dotenv import load_dotenv

# Buscamos la ruta del archivo y cargamos las variables del .env
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

def get_connection():
    """Crea y devuelve una conexión a la base de datos MySQL."""
    conexion = mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "gimnasio")
    )
    return conexion
