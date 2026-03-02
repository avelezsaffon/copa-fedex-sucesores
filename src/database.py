"""
Base de datos SQLite para Copa Fedex Sucesores
"""

import os
import sqlite3
from typing import List, Dict, Optional
from contextlib import contextmanager


DB_PATH = os.environ.get("DB_PATH", "data/torneo.db")


@contextmanager
def get_db(db_path: str = DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def create_database(db_path: str = DB_PATH):
    with get_db(db_path) as conn:
        cursor = conn.cursor()

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
                salesforce_id TEXT,
                pago BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rondas (
                id INTEGER PRIMARY KEY,
                jugador_id INTEGER NOT NULL,
                fecha DATE NOT NULL,
                club TEXT,
                cancha TEXT,
                marca TEXT,
                patrones TEXT,
                score_gross INTEGER,
                score_ajustado INTEGER,
                diferencial REAL,
                aplicable_torneo BOOLEAN DEFAULT 0,
                tarjeta_id TEXT UNIQUE,
                hoyos_json TEXT,
                handicap_cancha INTEGER,
                indice_al_momento REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(jugador_id) REFERENCES jugadores(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fechas_torneo (
                id INTEGER PRIMARY KEY,
                fecha DATE NOT NULL UNIQUE,
                es_ultima_cuatro BOOLEAN DEFAULT 0,
                valida BOOLEAN DEFAULT 1,
                num_jugadores INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS resultados_fecha (
                id INTEGER PRIMARY KEY,
                fecha_torneo_id INTEGER NOT NULL,
                jugador_id INTEGER NOT NULL,
                ronda_id INTEGER,
                score_gross INTEGER,
                handicap_aplicado REAL,
                score_neto REAL,
                posicion INTEGER,
                puntos REAL,
                FOREIGN KEY(fecha_torneo_id) REFERENCES fechas_torneo(id),
                FOREIGN KEY(jugador_id) REFERENCES jugadores(id),
                FOREIGN KEY(ronda_id) REFERENCES rondas(id),
                UNIQUE(fecha_torneo_id, jugador_id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tabla_puntos (
                id INTEGER PRIMARY KEY,
                posicion INTEGER NOT NULL UNIQUE,
                puntos_normal REAL NOT NULL,
                puntos_ultimas_cuatro REAL NOT NULL
            )
        ''')

    print(f"Base de datos '{db_path}' creada correctamente")


def migrate_database(db_path: str = DB_PATH):
    """Elimina tablas viejas y crea el nuevo schema."""
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        # Eliminar tablas viejas
        for table in ['ranking_anual', 'resultados_torneo', 'torneos', 'scores',
                       'resultados_fecha', 'rondas', 'fechas_torneo', 'tabla_puntos']:
            cursor.execute(f'DROP TABLE IF EXISTS {table}')

        # Agregar columnas a jugadores si la tabla existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='jugadores'")
        if cursor.fetchone():
            cursor.execute("PRAGMA table_info(jugadores)")
            columns = [row[1] for row in cursor.fetchall()]
            if 'salesforce_id' not in columns:
                cursor.execute('ALTER TABLE jugadores ADD COLUMN salesforce_id TEXT')
            if 'pago' not in columns:
                cursor.execute('ALTER TABLE jugadores ADD COLUMN pago BOOLEAN DEFAULT 0')

        # Agregar columnas a rondas si la tabla existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='rondas'")
        if cursor.fetchone():
            cursor.execute("PRAGMA table_info(rondas)")
            columns = [row[1] for row in cursor.fetchall()]
            if 'tarjeta_id' not in columns:
                cursor.execute('ALTER TABLE rondas ADD COLUMN tarjeta_id TEXT')
            if 'hoyos_json' not in columns:
                cursor.execute('ALTER TABLE rondas ADD COLUMN hoyos_json TEXT')
            if 'handicap_cancha' not in columns:
                cursor.execute('ALTER TABLE rondas ADD COLUMN handicap_cancha INTEGER')
            if 'indice_al_momento' not in columns:
                cursor.execute('ALTER TABLE rondas ADD COLUMN indice_al_momento REAL')

    create_database(db_path)
    print("Migración completada")


# === Jugadores ===

def obtener_jugadores(db_path: str = DB_PATH) -> List[Dict]:
    with get_db(db_path) as conn:
        rows = conn.execute(
            'SELECT * FROM jugadores ORDER BY apellido, nombre'
        ).fetchall()
        return [dict(row) for row in rows]


def obtener_jugador(db_path: str, jugador_id: int) -> Optional[Dict]:
    with get_db(db_path) as conn:
        row = conn.execute(
            'SELECT * FROM jugadores WHERE id = ?', (jugador_id,)
        ).fetchone()
        return dict(row) if row else None


def agregar_jugador(db_path: str, jugador: Dict):
    with get_db(db_path) as conn:
        try:
            conn.execute('''
                INSERT INTO jugadores (codigo, nombre, apellido, categoria, indice, salesforce_id)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                jugador.get('codigo'),
                jugador.get('nombre'),
                jugador.get('apellido'),
                jugador.get('categoria'),
                jugador.get('indice'),
                jugador.get('salesforce_id')
            ))
        except sqlite3.IntegrityError:
            pass


def toggle_pago(db_path: str, jugador_id: int) -> bool:
    """Toggle pago de un jugador. Retorna nuevo estado."""
    with get_db(db_path) as conn:
        row = conn.execute(
            'SELECT pago FROM jugadores WHERE id = ?', (jugador_id,)
        ).fetchone()
        if not row:
            return False
        new_state = not bool(row['pago'])
        conn.execute(
            'UPDATE jugadores SET pago = ? WHERE id = ?',
            (new_state, jugador_id)
        )
        return new_state


def eliminar_jugador(db_path: str, jugador_id: int):
    """Elimina un jugador y todos sus datos relacionados."""
    with get_db(db_path) as conn:
        conn.execute('DELETE FROM resultados_fecha WHERE jugador_id = ?', (jugador_id,))
        conn.execute('DELETE FROM rondas WHERE jugador_id = ?', (jugador_id,))
        conn.execute('DELETE FROM jugadores WHERE id = ?', (jugador_id,))


def actualizar_jugador(db_path: str, jugador_id: int, data: Dict):
    with get_db(db_path) as conn:
        fields = []
        values = []
        for key in ['categoria', 'indice', 'handicap', 'club', 'salesforce_id']:
            if key in data and data[key] is not None:
                fields.append(f'{key} = ?')
                values.append(data[key])
        if fields:
            values.append(jugador_id)
            conn.execute(
                f'UPDATE jugadores SET {", ".join(fields)} WHERE id = ?',
                values
            )


# === Rondas ===

def guardar_rondas(db_path: str, jugador_id: int, rondas: List[Dict]) -> int:
    """Guarda rondas, retorna cantidad de nuevas insertadas.
    Usa tarjeta_id como clave unica para deduplicar."""
    count = 0
    with get_db(db_path) as conn:
        for ronda in rondas:
            tarjeta_id = ronda.get('tarjeta_id')

            # Si tiene tarjeta_id, verificar si ya existe
            if tarjeta_id:
                existing = conn.execute(
                    'SELECT id FROM rondas WHERE tarjeta_id = ?', (tarjeta_id,)
                ).fetchone()
                if existing:
                    continue  # Ya existe, skip

            try:
                conn.execute('''
                    INSERT INTO rondas
                    (jugador_id, fecha, club, cancha, marca, patrones,
                     score_gross, score_ajustado, diferencial, tarjeta_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    jugador_id,
                    ronda.get('fecha'),
                    ronda.get('club'),
                    ronda.get('cancha'),
                    ronda.get('marca'),
                    ronda.get('patrones'),
                    ronda.get('score_gross'),
                    ronda.get('score_ajustado'),
                    ronda.get('diferencial'),
                    tarjeta_id,
                ))
                count += 1
            except sqlite3.IntegrityError:
                pass  # Duplicado por otra razon, skip
    return count


def obtener_rondas_jugador(db_path: str, jugador_id: int) -> List[Dict]:
    with get_db(db_path) as conn:
        rows = conn.execute('''
            SELECT r.*, ft.fecha as fecha_torneo_str
            FROM rondas r
            LEFT JOIN fechas_torneo ft ON r.fecha = ft.fecha
            WHERE r.jugador_id = ?
            ORDER BY r.fecha DESC
        ''', (jugador_id,)).fetchall()
        return [dict(row) for row in rows]


def obtener_sparkline_jugador(db_path: str, jugador_id: int, limit: int = 15) -> List[float]:
    """Retorna los últimos N diferenciales del jugador para sparkline."""
    with get_db(db_path) as conn:
        rows = conn.execute('''
            SELECT diferencial FROM rondas
            WHERE jugador_id = ? AND diferencial IS NOT NULL
            ORDER BY fecha DESC
            LIMIT ?
        ''', (jugador_id, limit)).fetchall()
        # Retornar en orden cronológico (más viejo primero)
        return [row['diferencial'] for row in reversed(rows)]


def actualizar_ronda_tarjeta(db_path: str, ronda_id: int, tarjeta_id: str = None,
                             hoyos_json: str = None, handicap_cancha: int = None,
                             indice_al_momento: float = None):
    """Actualiza tarjeta_id, hoyos_json, handicap_cancha y/o indice_al_momento de una ronda."""
    with get_db(db_path) as conn:
        if tarjeta_id:
            conn.execute(
                'UPDATE rondas SET tarjeta_id = ? WHERE id = ?',
                (tarjeta_id, ronda_id)
            )
        if hoyos_json:
            conn.execute(
                'UPDATE rondas SET hoyos_json = ? WHERE id = ?',
                (hoyos_json, ronda_id)
            )
        if handicap_cancha is not None:
            conn.execute(
                'UPDATE rondas SET handicap_cancha = ? WHERE id = ?',
                (handicap_cancha, ronda_id)
            )
        if indice_al_momento is not None:
            conn.execute(
                'UPDATE rondas SET indice_al_momento = ? WHERE id = ?',
                (indice_al_momento, ronda_id)
            )


def obtener_ronda(db_path: str, ronda_id: int) -> Optional[Dict]:
    with get_db(db_path) as conn:
        row = conn.execute(
            'SELECT * FROM rondas WHERE id = ?', (ronda_id,)
        ).fetchone()
        return dict(row) if row else None


def toggle_aplicable(db_path: str, ronda_id: int) -> bool:
    """Toggle aplicable_torneo, retorna nuevo estado."""
    with get_db(db_path) as conn:
        row = conn.execute(
            'SELECT aplicable_torneo FROM rondas WHERE id = ?', (ronda_id,)
        ).fetchone()
        if not row:
            return False
        new_state = not bool(row['aplicable_torneo'])
        conn.execute(
            'UPDATE rondas SET aplicable_torneo = ? WHERE id = ?',
            (new_state, ronda_id)
        )
        return new_state


# === Fechas Torneo ===

def obtener_fechas_torneo(db_path: str = DB_PATH) -> List[Dict]:
    with get_db(db_path) as conn:
        rows = conn.execute(
            'SELECT * FROM fechas_torneo ORDER BY fecha'
        ).fetchall()
        return [dict(row) for row in rows]


def obtener_fecha_torneo(db_path: str, fecha_id: int) -> Optional[Dict]:
    with get_db(db_path) as conn:
        row = conn.execute(
            'SELECT * FROM fechas_torneo WHERE id = ?', (fecha_id,)
        ).fetchone()
        return dict(row) if row else None


def crear_fecha_torneo(db_path: str, fecha: str, es_ultima_cuatro: bool = False) -> int:
    with get_db(db_path) as conn:
        try:
            cursor = conn.execute('''
                INSERT INTO fechas_torneo (fecha, es_ultima_cuatro)
                VALUES (?, ?)
            ''', (fecha, es_ultima_cuatro))
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            row = conn.execute(
                'SELECT id FROM fechas_torneo WHERE fecha = ?', (fecha,)
            ).fetchone()
            return row['id']


# === Resultados ===

def guardar_resultados_fecha(db_path: str, fecha_torneo_id: int, resultados: List[Dict]):
    with get_db(db_path) as conn:
        # Limpiar resultados previos de esta fecha
        conn.execute(
            'DELETE FROM resultados_fecha WHERE fecha_torneo_id = ?',
            (fecha_torneo_id,)
        )
        for r in resultados:
            conn.execute('''
                INSERT INTO resultados_fecha
                (fecha_torneo_id, jugador_id, ronda_id, score_gross,
                 handicap_aplicado, score_neto, posicion, puntos)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                fecha_torneo_id,
                r['jugador_id'],
                r.get('ronda_id'),
                r.get('score_gross'),
                r.get('handicap_aplicado'),
                r.get('score_neto'),
                r.get('posicion'),
                r.get('puntos'),
            ))
        # Actualizar num_jugadores y validez (quorum = 2 jugadores)
        num = len(resultados)
        conn.execute('''
            UPDATE fechas_torneo
            SET num_jugadores = ?, valida = ?
            WHERE id = ?
        ''', (num, num >= 2, fecha_torneo_id))


def obtener_resultados_fecha(db_path: str, fecha_torneo_id: int) -> List[Dict]:
    with get_db(db_path) as conn:
        rows = conn.execute('''
            SELECT rf.*, j.nombre, j.apellido
            FROM resultados_fecha rf
            JOIN jugadores j ON rf.jugador_id = j.id
            WHERE rf.fecha_torneo_id = ?
            ORDER BY rf.posicion
        ''', (fecha_torneo_id,)).fetchall()
        return [dict(row) for row in rows]


def obtener_fechas_asignadas_jugador(db_path: str, jugador_id: int) -> List[Dict]:
    """Retorna las fechas del torneo donde este jugador fue asignado, con sus resultados."""
    with get_db(db_path) as conn:
        rows = conn.execute('''
            SELECT rf.*, ft.fecha, ft.es_ultima_cuatro
            FROM resultados_fecha rf
            JOIN fechas_torneo ft ON rf.fecha_torneo_id = ft.id
            WHERE rf.jugador_id = ?
            ORDER BY ft.fecha
        ''', (jugador_id,)).fetchall()
        return [dict(row) for row in rows]


def obtener_resultados_jugador(db_path: str, jugador_id: int) -> List[Dict]:
    with get_db(db_path) as conn:
        rows = conn.execute('''
            SELECT rf.*, ft.fecha, ft.es_ultima_cuatro, ft.valida
            FROM resultados_fecha rf
            JOIN fechas_torneo ft ON rf.fecha_torneo_id = ft.id
            WHERE rf.jugador_id = ? AND ft.valida = 1
            ORDER BY rf.puntos DESC
        ''', (jugador_id,)).fetchall()
        return [dict(row) for row in rows]


# === Tabla de Puntos ===

def obtener_tabla_puntos(db_path: str = DB_PATH) -> List[Dict]:
    with get_db(db_path) as conn:
        rows = conn.execute(
            'SELECT * FROM tabla_puntos ORDER BY posicion'
        ).fetchall()
        return [dict(row) for row in rows]


def obtener_puntos_posicion(db_path: str, posicion: int, es_ultimas_cuatro: bool = False) -> float:
    with get_db(db_path) as conn:
        row = conn.execute(
            'SELECT puntos_normal, puntos_ultimas_cuatro FROM tabla_puntos WHERE posicion = ?',
            (posicion,)
        ).fetchone()
        if row:
            return row['puntos_ultimas_cuatro'] if es_ultimas_cuatro else row['puntos_normal']
        return 0.0


def seed_tabla_puntos(db_path: str = DB_PATH):
    puntos = [
        (1, 300, 450), (2, 240, 370), (3, 190, 300), (4, 150, 250),
        (5, 120, 210), (6, 100, 180), (7, 90, 155), (8, 85, 135),
        (9, 80, 120), (10, 75, 110), (11, 70, 100), (12, 65, 90),
        (13, 60, 85), (14, 57, 80), (15, 56, 75), (16, 55, 70),
        (17, 54, 65), (18, 53, 60), (19, 52, 57), (20, 51, 56),
        (21, 50, 55), (22, 49, 54), (23, 48, 53), (24, 47, 52),
        (25, 46, 51), (26, 45, 50),
    ]
    with get_db(db_path) as conn:
        for pos, normal, ultimas in puntos:
            try:
                conn.execute('''
                    INSERT INTO tabla_puntos (posicion, puntos_normal, puntos_ultimas_cuatro)
                    VALUES (?, ?, ?)
                ''', (pos, normal, ultimas))
            except sqlite3.IntegrityError:
                pass
    print(f"Tabla de puntos sembrada ({len(puntos)} posiciones)")


# === Asignaciones (Matriz) ===

def toggle_asignacion(db_path: str, jugador_id: int, fecha_torneo_id: int) -> bool:
    """
    Toggle: asignar/desasignar un jugador a un fin de semana.
    Retorna True si quedó asignado, False si se desasignó.
    """
    with get_db(db_path) as conn:
        existing = conn.execute('''
            SELECT id FROM resultados_fecha
            WHERE jugador_id = ? AND fecha_torneo_id = ?
        ''', (jugador_id, fecha_torneo_id)).fetchone()

        if existing:
            conn.execute(
                'DELETE FROM resultados_fecha WHERE id = ?',
                (existing['id'],)
            )
            # Actualizar conteo
            num = conn.execute(
                'SELECT COUNT(*) as c FROM resultados_fecha WHERE fecha_torneo_id = ?',
                (fecha_torneo_id,)
            ).fetchone()['c']
            conn.execute(
                'UPDATE fechas_torneo SET num_jugadores = ?, valida = ? WHERE id = ?',
                (num, num >= 2, fecha_torneo_id)
            )
            return False
        else:
            # Buscar ronda del jugador para ese fin de semana (sábado primero, luego domingo)
            fecha_info = conn.execute(
                'SELECT fecha FROM fechas_torneo WHERE id = ?',
                (fecha_torneo_id,)
            ).fetchone()
            if not fecha_info:
                return False

            from datetime import date as dt_date, timedelta
            sabado = dt_date.fromisoformat(fecha_info['fecha'])
            domingo = sabado + timedelta(days=1)

            # Buscar ronda del sábado primero
            ronda = conn.execute('''
                SELECT id, score_gross FROM rondas
                WHERE jugador_id = ? AND fecha = ?
            ''', (jugador_id, sabado.isoformat())).fetchone()

            # Si no hay sábado, buscar domingo
            if not ronda:
                ronda = conn.execute('''
                    SELECT id, score_gross FROM rondas
                    WHERE jugador_id = ? AND fecha = ?
                ''', (jugador_id, domingo.isoformat())).fetchone()

            conn.execute('''
                INSERT INTO resultados_fecha
                (fecha_torneo_id, jugador_id, ronda_id, score_gross,
                 handicap_aplicado, score_neto, posicion, puntos)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                fecha_torneo_id,
                jugador_id,
                ronda['id'] if ronda else None,
                ronda['score_gross'] if ronda else None,
                None, None, None, None
            ))

            # Actualizar conteo
            num = conn.execute(
                'SELECT COUNT(*) as c FROM resultados_fecha WHERE fecha_torneo_id = ?',
                (fecha_torneo_id,)
            ).fetchone()['c']
            conn.execute(
                'UPDATE fechas_torneo SET num_jugadores = ?, valida = ? WHERE id = ?',
                (num, num >= 2, fecha_torneo_id)
            )
            return True


def obtener_reporte_semanal(db_path: str, fecha_torneo_ids: list = None) -> Dict:
    """
    Retorna datos para el reporte de prensa de un fin de semana.
    Si no se pasan IDs, usa las fechas mas recientes que tengan resultados.
    """
    with get_db(db_path) as conn:
        if not fecha_torneo_ids:
            # Obtener las fechas mas recientes con resultados
            fechas = conn.execute('''
                SELECT ft.* FROM fechas_torneo ft
                WHERE ft.num_jugadores > 0
                ORDER BY ft.fecha DESC
                LIMIT 4
            ''').fetchall()
            if not fechas:
                return {'fechas': [], 'resultados_por_fecha': {}, 'otras_canchas': [], 'ranking': []}

            # Agrupar por fin de semana (sab-dom consecutivos)
            from datetime import date as dt_date, timedelta
            fechas = [dict(f) for f in fechas]
            ultimo = dt_date.fromisoformat(fechas[0]['fecha'])
            # Incluir fechas del mismo fin de semana (+-1 dia)
            fecha_torneo_ids = []
            for f in fechas:
                d = dt_date.fromisoformat(f['fecha'])
                if abs((d - ultimo).days) <= 1:
                    fecha_torneo_ids.append(f['id'])
        else:
            fechas = []
            for fid in fecha_torneo_ids:
                f = conn.execute('SELECT * FROM fechas_torneo WHERE id = ?', (fid,)).fetchone()
                if f:
                    fechas.append(dict(f))

        # Resultados por fecha
        resultados_por_fecha = {}
        all_dates = []
        for fid in fecha_torneo_ids:
            rows = conn.execute('''
                SELECT rf.*, j.nombre, j.apellido, j.indice as indice_actual,
                       r.fecha as ronda_fecha, r.diferencial, r.club, r.cancha,
                       r.handicap_cancha, r.indice_al_momento
                FROM resultados_fecha rf
                JOIN jugadores j ON rf.jugador_id = j.id
                LEFT JOIN rondas r ON rf.ronda_id = r.id
                WHERE rf.fecha_torneo_id = ?
                ORDER BY rf.posicion
            ''', (fid,)).fetchall()
            fecha = conn.execute('SELECT * FROM fechas_torneo WHERE id = ?', (fid,)).fetchone()
            resultados_por_fecha[fecha['fecha']] = [dict(r) for r in rows]
            all_dates.append(fecha['fecha'])

        # Rondas en otras canchas esa semana
        if all_dates:
            from datetime import date as dt_date, timedelta
            min_date = min(all_dates)
            max_date = max(all_dates)
            lunes = dt_date.fromisoformat(min_date) - timedelta(days=dt_date.fromisoformat(min_date).weekday())
            domingo = lunes + timedelta(days=6)

            rows = conn.execute('''
                SELECT r.fecha, j.nombre, j.apellido, r.club, r.cancha,
                       r.score_gross, r.diferencial
                FROM rondas r JOIN jugadores j ON r.jugador_id = j.id
                WHERE r.fecha BETWEEN ? AND ?
                AND r.club NOT LIKE '%Manizales%'
                ORDER BY j.apellido, r.fecha
            ''', (lunes.isoformat(), domingo.isoformat())).fetchall()
            otras_canchas = [dict(r) for r in rows]
        else:
            otras_canchas = []

        return {
            'fechas': fechas,
            'resultados_por_fecha': resultados_por_fecha,
            'otras_canchas': otras_canchas,
        }


def obtener_matriz_datos(db_path: str = DB_PATH) -> Dict:
    """
    Retorna los datos para la matriz: jugadores, fechas, y asignaciones con puntos.
    """
    with get_db(db_path) as conn:
        jugadores = conn.execute(
            'SELECT id, nombre, apellido, indice FROM jugadores ORDER BY apellido, nombre'
        ).fetchall()

        fechas = conn.execute(
            'SELECT * FROM fechas_torneo ORDER BY fecha'
        ).fetchall()

        resultados = conn.execute('''
            SELECT rf.jugador_id, rf.fecha_torneo_id, rf.puntos, rf.posicion, rf.score_neto
            FROM resultados_fecha rf
        ''').fetchall()

        # Crear mapa de asignaciones: {(jugador_id, fecha_id): {puntos, posicion, ...}}
        asignaciones = {}
        for r in resultados:
            key = f"{r['jugador_id']}_{r['fecha_torneo_id']}"
            asignaciones[key] = {
                'puntos': r['puntos'],
                'posicion': r['posicion'],
                'score_neto': r['score_neto'],
            }

        return {
            'jugadores': [dict(j) for j in jugadores],
            'fechas': [dict(f) for f in fechas],
            'asignaciones': asignaciones,
        }
