"""
One-off fix: delete spurious Perez Quintero round on 2026-04-04 and use Sunday 2026-04-05 round.
Usage: python3 /app/scripts/fix_perez_fecha7.py
"""
import sqlite3
import sys
sys.path.insert(0, '/app')
from src.ranking import recalcular_fecha
from src.fedegolf_collector import FedegolfScoresCollector

DB = '/data/torneo.db'
FECHA_TORNEO_ID = 13  # 2026-04-04
PEREZ_ID = 1


def main():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    print('=== Perez rondas abril (antes) ===')
    for r in conn.execute(
        "SELECT id, fecha, score_gross, handicap_cancha, tarjeta_id FROM rondas "
        "WHERE jugador_id=? AND fecha LIKE '2026-04%' ORDER BY fecha",
        (PEREZ_ID,)
    ).fetchall():
        print(f"  id={r['id']} {r['fecha']} G:{r['score_gross']} HCP:{r['handicap_cancha']} t:{r['tarjeta_id']}")

    # Delete the spurious Saturday round (G:77)
    spurious = conn.execute(
        "SELECT id FROM rondas WHERE jugador_id=? AND fecha='2026-04-04' AND score_gross=77",
        (PEREZ_ID,)
    ).fetchone()
    if spurious:
        sid = spurious['id']
        print(f'\nDeleting resultado_fecha for ronda {sid}')
        conn.execute("DELETE FROM resultados_fecha WHERE ronda_id=?", (sid,))
        print(f'Deleting ronda {sid}')
        conn.execute("DELETE FROM rondas WHERE id=?", (sid,))
        conn.commit()
    else:
        print('\nRonda spurious not found (maybe already deleted)')

    # Also delete any existing Perez resultado on Fecha 7 (in case it references something else)
    conn.execute(
        "DELETE FROM resultados_fecha WHERE fecha_torneo_id=? AND jugador_id=?",
        (FECHA_TORNEO_ID, PEREZ_ID)
    )
    conn.commit()

    # Get Sunday round
    sunday = conn.execute(
        "SELECT id, score_gross, handicap_cancha, tarjeta_id FROM rondas "
        "WHERE jugador_id=? AND fecha='2026-04-05' AND club LIKE '%Manizales%'",
        (PEREZ_ID,)
    ).fetchone()

    if not sunday:
        print('ERROR: No Sunday round found for Perez')
        return

    print(f"\nSunday ronda: id={sunday['id']} G:{sunday['score_gross']} HCP:{sunday['handicap_cancha']}")

    # Try to get handicap from federation if missing
    if sunday['handicap_cancha'] is None and sunday['tarjeta_id']:
        try:
            col = FedegolfScoresCollector()
            detail = col.get_scorecard_detail(sunday['tarjeta_id'])
            if detail and detail.get('handicap_cancha') is not None:
                hcp = detail['handicap_cancha']
                idx = detail.get('indice_al_momento')
                conn.execute(
                    "UPDATE rondas SET handicap_cancha=?, indice_al_momento=? WHERE id=?",
                    (hcp, idx, sunday['id'])
                )
                conn.commit()
                print(f"Handicap obtained from federation: {hcp} (indice: {idx})")
        except Exception as e:
            print(f"Error getting handicap: {e}")

    # Insert Perez into Fecha 7 with Sunday round
    conn.execute(
        "INSERT INTO resultados_fecha (fecha_torneo_id, jugador_id, ronda_id, score_gross) "
        "VALUES (?, ?, ?, ?)",
        (FECHA_TORNEO_ID, PEREZ_ID, sunday['id'], sunday['score_gross'])
    )
    conn.commit()
    print(f"Inserted Perez into Fecha 7 with ronda {sunday['id']}")

    # Recalculate
    recalcular_fecha(DB, FECHA_TORNEO_ID)
    print('Recalculated Fecha 7')

    # Show final results
    print('\n=== FECHA 7 FINAL ===')
    for r in conn.execute(
        "SELECT rf.posicion, j.nombre, j.apellido, rf.score_gross, rf.handicap_aplicado, "
        "rf.score_neto, rf.puntos, rr.fecha FROM resultados_fecha rf "
        "JOIN jugadores j ON rf.jugador_id=j.id "
        "LEFT JOIN rondas rr ON rf.ronda_id=rr.id "
        "WHERE rf.fecha_torneo_id=? ORDER BY rf.posicion",
        (FECHA_TORNEO_ID,)
    ).fetchall():
        print(f"  {r['posicion']:>2} {r['nombre']} {r['apellido']} G:{r['score_gross']} "
              f"HCP:{r['handicap_aplicado']} N:{r['score_neto']} Pts:{r['puntos']} ({r['fecha']})")

    conn.close()
    print('\nDone!')


if __name__ == '__main__':
    main()
