"""
Liquidacion Fecha 8 - 2026-04-11 (Sabado)

Proceso:
1. Sincroniza rondas desde la federacion
2. Encuentra rondas de sabado 11 o domingo 12 en Club Manizales
3. Sabado prevalece sobre domingo
4. EXCLUYE a Andres Velez Saffon (jid=12) porque su ronda del domingo no cuenta
5. Obtiene handicap_cancha de la federacion para cada tarjeta
6. Asigna jugadores a Fecha 8 (fecha_torneo_id buscado por fecha)
7. Recalcula puntos

Usage: python3 /app/scripts/liquidate_fecha_8.py
"""
import sqlite3
import sys
import time

sys.path.insert(0, '/app')
from src.ranking import recalcular_fecha
from src.fedegolf_collector import FedegolfScoresCollector
from src.sync import sync_all

DB = '/data/torneo.db'
FECHA_SABADO = '2026-04-11'
FECHA_DOMINGO = '2026-04-12'
EXCLUIR_JUGADOR_IDS = {12}  # Andres Velez Saffon - su ronda del domingo no cuenta


def main():
    # Paso 1: Sync
    print('=== Paso 1: Sync rondas desde federacion ===')
    try:
        result = sync_all(DB)
        print(f"Jugadores: {result['jugadores_sincronizados']}, Rondas nuevas: {result['rondas_nuevas']}")
    except Exception as e:
        print(f'Error en sync: {e}')

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    # Paso 2: Buscar fecha_torneo
    ft = conn.execute(
        "SELECT id FROM fechas_torneo WHERE fecha = ?", (FECHA_SABADO,)
    ).fetchone()
    if not ft:
        cursor = conn.execute(
            "INSERT INTO fechas_torneo (fecha) VALUES (?)", (FECHA_SABADO,)
        )
        fecha_torneo_id = cursor.lastrowid
        conn.commit()
        print(f'Creada fecha_torneo_id={fecha_torneo_id}')
    else:
        fecha_torneo_id = ft['id']
    print(f'\nFecha torneo ID: {fecha_torneo_id}')

    # Paso 3: Mostrar rondas del fin de semana
    print('\n=== Paso 3: Rondas encontradas para el fin de semana ===')
    rondas = conn.execute(
        "SELECT r.id, r.jugador_id, j.nombre, j.apellido, r.fecha, r.score_gross, "
        "r.handicap_cancha, r.tarjeta_id "
        "FROM rondas r JOIN jugadores j ON r.jugador_id=j.id "
        "WHERE r.fecha IN (?, ?) "
        "AND r.club LIKE '%Manizales%' "
        "AND r.score_gross IS NOT NULL "
        "AND r.score_gross >= 60 "
        "ORDER BY r.jugador_id, r.fecha",
        (FECHA_SABADO, FECHA_DOMINGO)
    ).fetchall()

    for r in rondas:
        marker = ''
        if r['jugador_id'] in EXCLUIR_JUGADOR_IDS:
            marker = ' [EXCLUIR]'
        print(f"  id={r['id']} jid={r['jugador_id']} {r['nombre']} {r['apellido']:<25} "
              f"{r['fecha']} G:{r['score_gross']} HCP:{r['handicap_cancha']} t:{r['tarjeta_id']}{marker}")

    # Paso 4: Elegir ronda por jugador (sabado prevalece), excluir jugadores
    mejores = {}
    for r in rondas:
        jid = r['jugador_id']
        if jid in EXCLUIR_JUGADOR_IDS:
            print(f"  -- EXCLUYENDO jid={jid} ({r['nombre']} {r['apellido']}) --")
            continue
        if jid not in mejores:
            mejores[jid] = dict(r)
        elif r['fecha'] == FECHA_SABADO:
            mejores[jid] = dict(r)

    print(f'\n{len(mejores)} jugadores seleccionados:')
    for jid, r in sorted(mejores.items()):
        print(f"  {r['nombre']} {r['apellido']} | {r['fecha']} | G:{r['score_gross']} | "
              f"HCP_cancha:{r['handicap_cancha']} | t:{r['tarjeta_id']}")

    # Paso 5: Obtener handicaps de la federacion
    print('\n=== Paso 5: Obtener handicaps de la federacion ===')
    collector = FedegolfScoresCollector()
    for jid, r in mejores.items():
        if r['handicap_cancha'] is None and r['tarjeta_id']:
            try:
                detail = collector.get_scorecard_detail(r['tarjeta_id'])
                if detail and detail.get('handicap_cancha') is not None:
                    hcp = detail['handicap_cancha']
                    idx = detail.get('indice_al_momento')
                    conn.execute(
                        "UPDATE rondas SET handicap_cancha=?, indice_al_momento=? WHERE id=?",
                        (hcp, idx, r['id'])
                    )
                    r['handicap_cancha'] = hcp
                    print(f"  {r['nombre']} {r['apellido']}: HCP={hcp} indice={idx}")
                else:
                    print(f"  {r['nombre']} {r['apellido']}: SKIP no HCP")
                time.sleep(0.3)
            except Exception as e:
                print(f"  Error {r['nombre']}: {e}")
    conn.commit()

    # Paso 6: Asignar jugadores a la fecha (limpiar previos)
    print('\n=== Paso 6: Asignar jugadores y recalcular ===')
    conn.execute(
        "DELETE FROM resultados_fecha WHERE fecha_torneo_id=?", (fecha_torneo_id,)
    )
    for jid, r in mejores.items():
        conn.execute(
            "INSERT INTO resultados_fecha (fecha_torneo_id, jugador_id, ronda_id, score_gross) "
            "VALUES (?, ?, ?, ?)",
            (fecha_torneo_id, jid, r['id'], r['score_gross'])
        )
    num = len(mejores)
    conn.execute(
        "UPDATE fechas_torneo SET num_jugadores=?, valida=? WHERE id=?",
        (num, num >= 2, fecha_torneo_id)
    )
    conn.commit()

    # Paso 7: Recalcular
    recalcular_fecha(DB, fecha_torneo_id)

    # Paso 8: Mostrar resultados finales
    print('\n=== FECHA 8 (2026-04-11) RESULTADOS ===')
    for r in conn.execute(
        "SELECT rf.posicion, j.nombre, j.apellido, rf.score_gross, rf.handicap_aplicado, "
        "rf.score_neto, rf.puntos, rr.fecha, rr.handicap_cancha FROM resultados_fecha rf "
        "JOIN jugadores j ON rf.jugador_id=j.id "
        "LEFT JOIN rondas rr ON rf.ronda_id=rr.id "
        "WHERE rf.fecha_torneo_id=? ORDER BY rf.posicion",
        (fecha_torneo_id,)
    ).fetchall():
        match = 'OK' if r['handicap_aplicado'] == r['handicap_cancha'] else (
            'CALC' if r['handicap_cancha'] is None else 'MISS'
        )
        print(f"  {r['posicion']:>2} {r['nombre']} {r['apellido']:<25} "
              f"G:{r['score_gross']} HCP:{r['handicap_aplicado']} N:{r['score_neto']} "
              f"Pts:{r['puntos']} ({r['fecha']}) [{match}]")

    conn.close()
    print('\nDone!')


if __name__ == '__main__':
    main()
