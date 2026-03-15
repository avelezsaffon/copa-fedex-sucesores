"""
Entrypoint: inicializa la DB si no existe y arranca el servidor.
"""

import os
import sqlite3
import subprocess
import sys

DB_PATH = os.environ.get("DB_PATH", "data/torneo.db")


def db_has_tables():
    """Verifica si la DB tiene las tablas necesarias."""
    if not os.path.exists(DB_PATH):
        return False
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='jugadores'")
        result = cursor.fetchone()
        conn.close()
        return result is not None
    except Exception:
        return False


def init_db():
    """Crea la DB con schema y datos iniciales si no existe."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    if db_has_tables():
        print(f"DB existente con tablas: {DB_PATH}")
        # Migracion: agregar columnas nuevas si faltan
        from src.database import get_db
        with get_db(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(jugadores)")
            columns = [row[1] for row in cursor.fetchall()]
            if 'pago' not in columns:
                cursor.execute('ALTER TABLE jugadores ADD COLUMN pago BOOLEAN DEFAULT 0')
                print("  Columna pago agregada")

            cursor.execute("PRAGMA table_info(rondas)")
            columns = [row[1] for row in cursor.fetchall()]
            if 'tarjeta_id' not in columns:
                cursor.execute('ALTER TABLE rondas ADD COLUMN tarjeta_id TEXT')
                print("  Columna tarjeta_id agregada")
            if 'hoyos_json' not in columns:
                cursor.execute('ALTER TABLE rondas ADD COLUMN hoyos_json TEXT')
                print("  Columna hoyos_json agregada")
            if 'handicap_cancha' not in columns:
                cursor.execute('ALTER TABLE rondas ADD COLUMN handicap_cancha INTEGER')
                print("  Columna handicap_cancha agregada")
            if 'indice_al_momento' not in columns:
                cursor.execute('ALTER TABLE rondas ADD COLUMN indice_al_momento REAL')
                print("  Columna indice_al_momento agregada")

            # Migrar tabla rondas: quitar UNIQUE(jugador_id, fecha, club)
            # para permitir multiples rondas por dia en el mismo club
            auto_idx = cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND name='sqlite_autoindex_rondas_1'"
            ).fetchone()
            if auto_idx:
                print("  Migrando tabla rondas (quitando UNIQUE viejo)...")
                cursor.execute("PRAGMA foreign_keys = OFF")
                cursor.execute('''
                    CREATE TABLE rondas_new (
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
                # Copy data - include handicap_cancha/indice_al_momento if they exist
                old_cols = [r[1] for r in cursor.execute('PRAGMA table_info(rondas)').fetchall()]
                base_cols = 'id, jugador_id, fecha, club, cancha, marca, patrones, score_gross, score_ajustado, diferencial, aplicable_torneo, tarjeta_id, hoyos_json'
                extra = ''
                if 'handicap_cancha' in old_cols:
                    extra += ', handicap_cancha'
                else:
                    extra += ', NULL'
                if 'indice_al_momento' in old_cols:
                    extra += ', indice_al_momento'
                else:
                    extra += ', NULL'
                cursor.execute(f'''
                    INSERT INTO rondas_new
                    SELECT {base_cols}{extra}, created_at
                    FROM rondas
                ''')
                cursor.execute("DROP TABLE rondas")
                cursor.execute("ALTER TABLE rondas_new RENAME TO rondas")
                cursor.execute("PRAGMA foreign_keys = ON")
                print("  Tabla rondas migrada: UNIQUE ahora es por tarjeta_id")

        # Migrar fechas DD/MM/YYYY a ISO YYYY-MM-DD
        from src.sync import migrar_fechas_iso
        migrated = migrar_fechas_iso(DB_PATH)
        if migrated > 0:
            print(f"  {migrated} fechas migradas a formato ISO")
        return

    # DB no existe o esta vacia - borrar archivo corrupto si existe
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"DB vacia eliminada: {DB_PATH}")

    print(f"Creando DB: {DB_PATH}")

    # Ejecutar seed
    from seed_data import main as seed_main
    seed_main()

    # Setup de jugadores se ejecuta manualmente: python setup_jugadores.py
    # No se ejecuta en el arranque porque requiere conexion a la federacion
    print("  Setup jugadores: ejecutar manualmente con 'python setup_jugadores.py'")


if __name__ == "__main__":
    init_db()
    # Arrancar uvicorn
    port = os.environ.get("PORT", "8080")
    subprocess.run([
        sys.executable, "-m", "uvicorn",
        "src.app:app",
        "--host", "0.0.0.0",
        "--port", port,
    ])
