from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import socios, clases, reservas 

app = FastAPI(
    title="API de gestión de gimnasio",
    version="1.0.0",
)

# El frontend del TP puede ejecutarse desde otro origen.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(socios.router)
app.include_router(clases.router)
app.include_router(reservas.router)

@app.get("/")
def root():
    return {"mensaje": "API de gestión de gimnasio"}
