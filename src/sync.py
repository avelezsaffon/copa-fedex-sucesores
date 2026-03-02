"""
Sincronización de datos con la Federación Colombiana de Golf
"""

import time
import re
from typing import Optional
from src.fedegolf_collector import FedegolfScoresCollector
from src.database import (
    get_db, obtener_jugadores, obtener_jugador,
    actualizar_jugador, guardar_rondas, crear_fecha_torneo,
    DB_PATH
)


def parse_scores(scores_str: str):
    """
    Parsea el campo scores de la federación.
    Formato típico: "85/82" (gross/ajustado)
    """
    if not scores_str:
        return None, None
    parts = scores_str.strip().split('/')
    try:
        gross = int(parts[0].strip()) if len(parts) >= 1 and parts[0].strip() else None
        ajustado = int(parts[1].strip()) if len(parts) >= 2 and parts[1].strip() else None
        return gross, ajustado
    except (ValueError, IndexError):
        return None, None


def parse_diferencial(dif_str: str) -> Optional[float]:
    """Parsea el diferencial a float."""
    if not dif_str:
        return None
    try:
        cleaned = re.sub(r'[^\d.\-]', '', dif_str.strip())
        return float(cleaned) if cleaned else None
    except ValueError:
        return None


def normalizar_fecha(fecha_str: str) -> str:
    """
    Convierte fecha DD/MM/YYYY a formato ISO YYYY-MM-DD.
    Si ya está en ISO o no se puede parsear, retorna el original.
    """
    if not fecha_str:
        return fecha_str
    # Ya es ISO?
    if re.match(r'^\d{4}-\d{2}-\d{2}$', fecha_str.strip()):
        return fecha_str.strip()
    # DD/MM/YYYY?
    m = re.match(r'^(\d{1,2})/(\d{1,2})/(\d{4})$', fecha_str.strip())
    if m:
        return f"{m.group(3)}-{m.group(2).zfill(2)}-{m.group(1).zfill(2)}"
    return fecha_str.strip()


def sync_jugador_info(db_path: str, jugador_id: int) -> bool:
    """
    Actualiza información del jugador desde la federación.
    Retorna True si se actualizó.
    """
    jugador = obtener_jugador(db_path, jugador_id)
    if not jugador or not jugador.get('codigo'):
        return False

    collector = FedegolfScoresCollector()
    info = collector.search_player_by_code(str(jugador['codigo']))

    if not info:
        return False

    # Convertir indice a float
    indice = None
    raw_indice = info.get('indice')
    if raw_indice:
        try:
            indice = float(raw_indice)
        except (ValueError, TypeError):
            pass

    actualizar_jugador(db_path, jugador_id, {
        'categoria': info.get('categoria') or None,
        'indice': indice,
        'handicap': indice,  # Usar indice como handicap por defecto
        'club': info.get('club') or None,
        'salesforce_id': info.get('salesforce_id'),
    })

    return True


def sync_rondas_jugador(db_path: str, jugador_id: int) -> int:
    """
    Sincroniza rondas de un jugador desde la federación.
    Retorna cantidad de rondas nuevas.
    """
    jugador = obtener_jugador(db_path, jugador_id)
    if not jugador:
        return 0

    # Obtener salesforce_id (necesario para consultar scores)
    sf_id = jugador.get('salesforce_id')
    if not sf_id:
        # Intentar obtenerlo primero
        if sync_jugador_info(db_path, jugador_id):
            jugador = obtener_jugador(db_path, jugador_id)
            sf_id = jugador.get('salesforce_id')

    if not sf_id:
        print(f"No se pudo obtener salesforce_id para {jugador['nombre']}")
        return 0

    collector = FedegolfScoresCollector()
    scores_raw = collector.get_player_scores(sf_id)

    if not scores_raw:
        return 0

    # Parsear y preparar rondas
    rondas = []
    for score in scores_raw:
        gross, ajustado = parse_scores(score.get('scores', ''))
        diferencial = parse_diferencial(score.get('diferencial', ''))

        rondas.append({
            'fecha': normalizar_fecha(score.get('fecha', '')),
            'club': score.get('club', ''),
            'cancha': score.get('cancha', ''),
            'marca': score.get('marca', ''),
            'patrones': score.get('patrones', ''),
            'score_gross': gross,
            'score_ajustado': ajustado,
            'diferencial': diferencial,
            'tarjeta_id': score.get('tarjeta_id'),
        })

    count = guardar_rondas(db_path, jugador_id, rondas)
    return count


def sync_all(db_path: str = DB_PATH) -> dict:
    """
    Sincroniza info y rondas de todos los jugadores.
    Retorna resumen.
    """
    jugadores = obtener_jugadores(db_path)
    total_nuevas = 0
    jugadores_sincronizados = 0

    for jugador in jugadores:
        jid = jugador['id']
        codigo = jugador.get('codigo')
        if not codigo:
            continue

        print(f"Sincronizando {jugador['nombre']} {jugador['apellido']}...")

        # Sync info
        sync_jugador_info(db_path, jid)

        # Sync rondas
        nuevas = sync_rondas_jugador(db_path, jid)
        total_nuevas += nuevas
        jugadores_sincronizados += 1

        time.sleep(0.5)  # No saturar el servidor

    return {
        'jugadores_sincronizados': jugadores_sincronizados,
        'rondas_nuevas': total_nuevas,
    }


def migrar_fechas_iso(db_path: str = DB_PATH) -> int:
    """
    Migra fechas de DD/MM/YYYY a ISO YYYY-MM-DD en la tabla rondas.
    Retorna cantidad de filas actualizadas.
    """
    count = 0
    with get_db(db_path) as conn:
        rows = conn.execute('SELECT id, fecha FROM rondas').fetchall()
        for row in rows:
            nueva = normalizar_fecha(row['fecha'])
            if nueva != row['fecha']:
                conn.execute(
                    'UPDATE rondas SET fecha = ? WHERE id = ?',
                    (nueva, row['id'])
                )
                count += 1
    return count


def auto_detectar_fechas_torneo(db_path: str = DB_PATH):
    """
    Para rondas marcadas como aplicables, crea fechas_torneo
    si no existen. Cada fin de semana = 1 fecha (el sabado).
    Si una ronda es domingo, se mapea al sabado anterior.
    """
    from datetime import date as dt_date, timedelta
    with get_db(db_path) as conn:
        fechas = conn.execute('''
            SELECT DISTINCT fecha FROM rondas
            WHERE aplicable_torneo = 1
        ''').fetchall()

    sabados_vistos = set()
    for row in fechas:
        d = dt_date.fromisoformat(row['fecha'])
        # Si es domingo (weekday=6), usar el sabado anterior
        if d.weekday() == 6:
            d = d - timedelta(days=1)
        fecha_sabado = d.isoformat()
        if fecha_sabado not in sabados_vistos:
            sabados_vistos.add(fecha_sabado)
            crear_fecha_torneo(db_path, fecha_sabado)
