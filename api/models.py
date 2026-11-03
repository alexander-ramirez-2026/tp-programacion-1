from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field

class Clase(BaseModel):
    nombre: str = Field(..., max_length=100)
    instructor: str = Field(..., max_length=100)
    horario: str = Field(..., max_length=50)
    cupo_maximo: int
    edad_minima: Optional[int] = None
    edad_maxima: Optional[int] = None

class Socio(BaseModel):
    dni: int
    nombre: str
    apellido: str
    fecha_nacimiento: date

class Reserva(BaseModel):
    id: Optional[int] = None
    clase_id: int
    socio_dni: int
    fecha_reserva: Optional[datetime] = None
