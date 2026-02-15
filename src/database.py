"""
Funciones para manejo de base de datos SQLite del torneo
"""

import sqlite3
from typing import List, Dict
import pandas as pd


def create_database(db_name: str = "../data/torneo.db"):
    """
    Crea la estructura de base de datos para el torneo
    """
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # Tabla de jugadores
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jugadores (
            id INTEGER PRIMARY KEY,
            codigo INTEGER UNIQUE NOT NULL,
            nombre TEXT NOT NULL,
            apellido TEXT NOT NULL,
            categoria TEXT,
            indice REAL,
            handicap REAL,
            club TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Tabla de scores
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY,
            jugador_id INTEGER NOT NULL,
            fecha DATE NOT NULL,
            club TEXT,
            cancha TEXT,
            marca TEXT,
            score INTEGER,
            diferencial REAL,
            FOREIGN KEY(jugador_id) REFERENCES jugadores(id)
        )
    ''')

    # Tabla de torneos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS torneos (
            id INTEGER PRIMARY KEY,
            nombre TEXT NOT NULL,
            fecha_inicio DATE,
            fecha_fin DATE,
            club TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Tabla de resultados del torneo
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS resultados_torneo (
            id INTEGER PRIMARY KEY,
            torneo_id INTEGER NOT NULL,
            jugador_id INTEGER NOT NULL,
            score_bruto INTEGER,
            score_neto INTEGER,
            posicion INTEGER,
            puntos INTEGER,
            handicap_aplicado REAL,
            FOREIGN KEY(torneo_id) REFERENCES torneos(id),
            FOREIGN KEY(jugador_id) REFERENCES jugadores(id)
        )
    ''')

    # Tabla de ranking anual
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ranking_anual (
            id INTEGER PRIMARY KEY,
            jugador_id INTEGER NOT NULL,
            anio INTEGER NOT NULL,
            puntos_totales INTEGER DEFAULT 0,
            torneos_jugados INTEGER DEFAULT 0,
            FOREIGN KEY(jugador_id) REFERENCES jugadores(id),
            UNIQUE(jugador_id, anio)
        )
    ''')

    conn.commit()
    conn.close()
    print(f"Base de datos '{db_name}' creada correctamente")


def agregar_jugador(db_name: str, jugador: Dict):
    """
    Agrega un jugador a la base de datos
    """
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    try:
        cursor.execute('''
            INSERT INTO jugadores
            (codigo, nombre, apellido, categoria, indice)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            jugador.get('codigo'),
            jugador.get('nombre'),
            jugador.get('apellido'),
            jugador.get('categoria'),
            jugador.get('indice')
        ))
        conn.commit()
        print(f"Jugador {jugador['nombre']} {jugador['apellido']} agregado")
    except sqlite3.IntegrityError:
        print(f"Jugador con código {jugador['codigo']} ya existe")
    finally:
        conn.close()


def agregar_jugadores(db_name: str, jugadores: List[Dict]):
    """
    Agrega múltiples jugadores a la base de datos
    """
    for jugador in jugadores:
        agregar_jugador(db_name, jugador)


def obtener_jugadores(db_name: str) -> List[Dict]:
    """
    Obtiene todos los jugadores de la base de datos
    """
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM jugadores')
    rows = cursor.fetchall()

    jugadores = []
    for row in rows:
        jugadores.append({
            'id': row[0],
            'codigo': row[1],
            'nombre': row[2],
            'apellido': row[3],
            'categoria': row[4],
            'indice': row[5],
            'handicap': row[6],
            'club': row[7]
        })

    conn.close()
    return jugadores


def save_to_sqlite(database: str, table: str, data: List[Dict]):
    """
    Guarda datos a una base de datos SQLite

    Args:
        database: Nombre de la base de datos
        table: Nombre de la tabla
        data: Lista de diccionarios
    """
    try:
        conn = sqlite3.connect(database)
        df = pd.DataFrame(data)
        df.to_sql(table, conn, if_exists='append', index=False)
        conn.close()
        print(f"Datos guardados en {database}/{table}")
    except Exception as e:
        print(f"Error guardando SQLite: {str(e)}")
