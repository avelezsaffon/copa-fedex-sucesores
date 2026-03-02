"""
Motor de cálculo de ranking para Copa Fedex Sucesores
"""

from typing import List, Dict, Tuple
from src.database import (
    get_db, obtener_fechas_torneo, obtener_tabla_puntos,
    DB_PATH
)

TOP_N = 8  # Se toman las 8 mejores fechas de cada jugador

# Datos oficiales - Club de Golf de Manizales (Federacion Colombiana de Golf)
PAR = 72
# Azules-6755
SLOPE_AZULES = 137
CR_AZULES = 71.8
# Blancas-6338
SLOPE_BLANCAS = 128
CR_BLANCAS = 69.4
# Tope de handicap para el torneo
MAX_HCP_TORNEO = 15


def calcular_hcp_cancha(indice: float, slope: int = SLOPE_AZULES, cr: float = CR_AZULES) -> int:
    """Calcula el handicap de cancha segun tabla oficial de la federacion.
    Formula WHS: HCP = Indice * (Slope / 113) + (CR - Par)
    Operaciones reordenadas para minimizar error de punto flotante.
    """
    if indice is None:
        return 0
    hcp = (indice * slope + (cr - PAR) * 113) / 113
    return round(hcp)


def calcular_puntos_con_empates(
    jugadores_ordenados: List[Tuple[int, int, float, float]],
    tabla: List[Dict],
    es_ultimas_cuatro: bool
) -> List[Dict]:
    """
    Calcula puntos manejando empates.

    Args:
        jugadores_ordenados: Lista de (jugador_id, ronda_id, score_neto, handicap)
                             ordenados por score_neto ASC
        tabla: Tabla de puntos completa
        es_ultimas_cuatro: Si es una de las últimas 4 fechas

    Returns:
        Lista de dicts con jugador_id, ronda_id, score_neto, posicion, puntos
    """
    campo_puntos = 'puntos_ultimas_cuatro' if es_ultimas_cuatro else 'puntos_normal'

    puntos_por_pos = {}
    for row in tabla:
        puntos_por_pos[row['posicion']] = row[campo_puntos]

    resultados = []
    i = 0
    n = len(jugadores_ordenados)

    while i < n:
        j = i
        while j < n and jugadores_ordenados[j][2] == jugadores_ordenados[i][2]:
            j += 1

        puntos_grupo = []
        for pos in range(i + 1, j + 1):
            puntos_grupo.append(puntos_por_pos.get(pos, 0.0))

        promedio = sum(puntos_grupo) / len(puntos_grupo) if puntos_grupo else 0.0
        promedio = round(promedio, 2)

        for k in range(i, j):
            jid, rid, score_neto, handicap = jugadores_ordenados[k]
            resultados.append({
                'jugador_id': jid,
                'ronda_id': rid,
                'score_gross': int(score_neto + handicap) if handicap is not None else None,
                'handicap_aplicado': handicap,
                'score_neto': score_neto,
                'posicion': i + 1,
                'puntos': promedio,
            })

        i = j

    return resultados


def recalcular_fecha(db_path: str, fecha_torneo_id: int):
    """
    Recalcula puntos para una fecha basándose en las asignaciones existentes
    en resultados_fecha. Lee los scores de las rondas vinculadas y recalcula
    posiciones y puntos.
    """
    with get_db(db_path) as conn:
        fecha_row = conn.execute(
            'SELECT * FROM fechas_torneo WHERE id = ?', (fecha_torneo_id,)
        ).fetchone()
        if not fecha_row:
            return

        es_ultimas_cuatro = bool(fecha_row['es_ultima_cuatro'])
        fecha_str = fecha_row['fecha']

        # Obtener asignaciones actuales para esta fecha
        asignaciones = conn.execute('''
            SELECT rf.id, rf.jugador_id, rf.ronda_id, j.indice
            FROM resultados_fecha rf
            JOIN jugadores j ON rf.jugador_id = j.id
            WHERE rf.fecha_torneo_id = ?
        ''', (fecha_torneo_id,)).fetchall()

        if not asignaciones:
            conn.execute(
                'UPDATE fechas_torneo SET num_jugadores = 0, valida = 0 WHERE id = ?',
                (fecha_torneo_id,)
            )
            return

        # Para cada asignación, obtener el score de la ronda vinculada
        jugadores_con_score = []
        for asig in asignaciones:
            ronda_id = asig['ronda_id']
            gross = None

            ronda_hcp = None  # handicap de la tarjeta federación

            if ronda_id:
                ronda = conn.execute(
                    'SELECT score_gross, handicap_cancha FROM rondas WHERE id = ?',
                    (ronda_id,)
                ).fetchone()
                if ronda:
                    gross = ronda['score_gross']
                    ronda_hcp = ronda['handicap_cancha']

            # Si no hay ronda vinculada, buscar automáticamente
            if gross is None:
                from datetime import date as dt_date, timedelta
                sabado = dt_date.fromisoformat(fecha_str)
                domingo = sabado + timedelta(days=1)

                ronda = conn.execute('''
                    SELECT id, score_gross, handicap_cancha FROM rondas
                    WHERE jugador_id = ? AND fecha IN (?, ?)
                    ORDER BY fecha ASC
                    LIMIT 1
                ''', (asig['jugador_id'], sabado.isoformat(), domingo.isoformat())).fetchone()

                if ronda:
                    gross = ronda['score_gross']
                    ronda_id = ronda['id']
                    ronda_hcp = ronda['handicap_cancha']
                    # Actualizar la referencia a la ronda
                    conn.execute(
                        'UPDATE resultados_fecha SET ronda_id = ? WHERE id = ?',
                        (ronda_id, asig['id'])
                    )

            # Prioridad handicap: 1) tarjeta federación, 2) cálculo desde indice
            if ronda_hcp is not None:
                handicap = ronda_hcp
            else:
                indice = asig['indice'] or 0
                handicap = calcular_hcp_cancha(indice)
                handicap = min(handicap, MAX_HCP_TORNEO)

            if gross is not None:
                neto = round(gross - handicap, 1)
                jugadores_con_score.append((
                    asig['jugador_id'], ronda_id, neto, handicap
                ))

        if not jugadores_con_score:
            return

        # Ordenar por score neto (menor es mejor)
        jugadores_con_score.sort(key=lambda x: x[2])

        # Obtener tabla de puntos
        tabla = obtener_tabla_puntos(db_path)

        # Calcular puntos con manejo de empates
        resultados = calcular_puntos_con_empates(
            jugadores_con_score, tabla, es_ultimas_cuatro
        )

        # Actualizar resultados existentes (no borrar y recrear, para mantener asignaciones)
        for r in resultados:
            conn.execute('''
                UPDATE resultados_fecha
                SET ronda_id = ?, score_gross = ?, handicap_aplicado = ?,
                    score_neto = ?, posicion = ?, puntos = ?
                WHERE fecha_torneo_id = ? AND jugador_id = ?
            ''', (
                r.get('ronda_id'),
                r.get('score_gross'),
                r.get('handicap_aplicado'),
                r.get('score_neto'),
                r.get('posicion'),
                r.get('puntos'),
                fecha_torneo_id,
                r['jugador_id'],
            ))

        # Actualizar conteo
        num = len(resultados)
        conn.execute(
            'UPDATE fechas_torneo SET num_jugadores = ?, valida = ? WHERE id = ?',
            (num, num >= 2, fecha_torneo_id)
        )


def calcular_ranking_general(db_path: str = DB_PATH) -> List[Dict]:
    """
    Calcula el ranking general: top 8 fechas por jugador, suma de puntos.
    Incluye jugadores sin resultados (para mostrar en lista).
    """
    with get_db(db_path) as conn:
        jugadores = conn.execute(
            'SELECT id, nombre, apellido, indice FROM jugadores ORDER BY apellido'
        ).fetchall()

        ranking = []
        for jugador in jugadores:
            jid = jugador['id']

            resultados = conn.execute('''
                SELECT rf.puntos, rf.posicion, ft.fecha, ft.es_ultima_cuatro
                FROM resultados_fecha rf
                JOIN fechas_torneo ft ON rf.fecha_torneo_id = ft.id
                WHERE rf.jugador_id = ? AND ft.valida = 1 AND rf.puntos IS NOT NULL
                ORDER BY rf.puntos DESC
            ''', (jid,)).fetchall()

            resultados = [dict(r) for r in resultados]

            top_n = resultados[:TOP_N]
            total_puntos = sum(r['puntos'] for r in top_n) if top_n else 0
            fechas_jugadas = len(resultados)

            puntos_por_fecha = {}
            top_n_fechas = set()
            for r in top_n:
                puntos_por_fecha[r['fecha']] = r['puntos']
                top_n_fechas.add(r['fecha'])

            for r in resultados[TOP_N:]:
                puntos_por_fecha[r['fecha']] = r['puntos']

            promedio = round(total_puntos / fechas_jugadas, 2) if fechas_jugadas > 0 else 0

            ranking.append({
                'jugador_id': jid,
                'nombre': jugador['nombre'],
                'apellido': jugador['apellido'],
                'indice': jugador['indice'],
                'total_puntos': round(total_puntos, 2),
                'fechas_jugadas': fechas_jugadas,
                'promedio_puntos': promedio,
                'puntos_por_fecha': puntos_por_fecha,
                'top_n_fechas': top_n_fechas,
            })

    # Ordenar: por puntos (mayor primero), luego por indice (menor primero)
    ranking.sort(key=lambda x: (-x['total_puntos'], x['indice'] or 99))

    for i, r in enumerate(ranking):
        r['posicion'] = i + 1

    return ranking


def recalcular_todo(db_path: str = DB_PATH):
    """Recalcula resultados para todas las fechas y el ranking general."""
    fechas = obtener_fechas_torneo(db_path)
    for fecha in fechas:
        recalcular_fecha(db_path, fecha['id'])
    return calcular_ranking_general(db_path)
