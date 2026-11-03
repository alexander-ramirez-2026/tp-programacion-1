
-- Base de datos del gimnasio para SQLite

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS socios (
    dni INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL,
    apellido TEXT NOT NULL,
    fecha_nacimiento TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS clases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    instructor TEXT NOT NULL,
    horario TEXT NOT NULL,
    cupo_maximo INTEGER NOT NULL,
    edad_minima INTEGER,
    edad_maxima INTEGER,
    cancelada INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS reservas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    clase_id INTEGER NOT NULL,
    socio_dni INTEGER NOT NULL,
    fecha_reserva TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (clase_id) REFERENCES clases(id)
        ON DELETE CASCADE,

    FOREIGN KEY (socio_dni) REFERENCES socios(dni)
        ON DELETE CASCADE
);
