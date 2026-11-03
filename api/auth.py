
"""
Módulo de autenticación y control de permisos del gimnasio.
"""

import os
from typing import Optional

from dotenv import load_dotenv
from fastapi import Depends, Header, HTTPException


# Obtener la carpeta principal del proyecto
BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

# Cargar las variables del archivo .env
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_PATH)

# Obtener las API Keys
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY")
SOCIO_API_KEY = os.getenv("SOCIO_API_KEY")


def get_role(
    x_api_key: Optional[str] = Header(default=None)
) -> str:
    """Identifica el rol según la API Key recibida."""

    if x_api_key is None:
        raise HTTPException(
            status_code=401,
            detail="API key requerida"
        )

    if ADMIN_API_KEY and x_api_key == ADMIN_API_KEY:
        return "admin"

    if SOCIO_API_KEY and x_api_key == SOCIO_API_KEY:
        return "socio"

    raise HTTPException(
        status_code=401,
        detail="API key inválida"
    )


def require_admin(
    role: str = Depends(get_role)
) -> str:
    """Permite el acceso únicamente al administrador."""

    if role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Esta acción requiere rol admin"
        )

    return role


def require_socio_or_admin(
    role: str = Depends(get_role)
) -> str:
    """Permite el acceso a socios y administradores."""

    if role not in ("socio", "admin"):
        raise HTTPException(
            status_code=403,
            detail="No tiene permisos para esta operación"
        )

    return role
