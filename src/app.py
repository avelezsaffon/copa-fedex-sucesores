"""
FastAPI app para Copa Fedex Sucesores
"""

import os
import secrets
import base64

from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware

import json

from src.database import (
    obtener_jugadores, obtener_jugador, obtener_rondas_jugador,
    obtener_fechas_torneo, obtener_fecha_torneo,
    obtener_resultados_fecha, obtener_resultados_jugador,
    obtener_sparkline_jugador, toggle_aplicable, toggle_asignacion,
    obtener_matriz_datos, obtener_fechas_asignadas_jugador, obtener_reporte_semanal,
    toggle_pago, agregar_jugador, eliminar_jugador, obtener_ronda,
    actualizar_ronda_tarjeta, crear_fecha_torneo,
    DB_PATH
)
from src.ranking import (
    calcular_ranking_general, recalcular_todo, calcular_hcp_cancha,
    SLOPE_AZULES, CR_AZULES, SLOPE_BLANCAS, CR_BLANCAS,
)
from src.sync import sync_rondas_jugador, sync_all, auto_detectar_fechas_torneo
from src.fedegolf_collector import FedegolfScoresCollector
from src.chat_agent import chat_responder

from pydantic import BaseModel

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")


ADMIN_PATHS = {"/api/asignar", "/api/jugador", "/api/recalcular"}


def es_ruta_admin(path: str) -> bool:
    """Verifica si la ruta requiere autenticacion de admin."""
    if path in ("/api/asignar", "/api/recalcular", "/api/jugador/agregar", "/api/fechas/generar"):
        return True
    if path.startswith("/api/jugador/") and (path.endswith("/toggle-pago") or path.endswith("/eliminar")):
        return True
    return False


class AdminAuthMiddleware(BaseHTTPMiddleware):
    """Protege solo endpoints de admin con HTTP Basic Auth."""

    async def dispatch(self, request: Request, call_next):
        if not ADMIN_PASSWORD or request.method == "GET":
            return await call_next(request)

        if not es_ruta_admin(request.url.path):
            return await call_next(request)

        # Solo rutas admin requieren autenticacion
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Basic "):
            try:
                decoded = base64.b64decode(auth[6:]).decode("utf-8")
                user, pwd = decoded.split(":", 1)
                if secrets.compare_digest(pwd, ADMIN_PASSWORD):
                    return await call_next(request)
            except Exception:
                pass

        return Response(
            content="Acceso no autorizado",
            status_code=401,
            headers={"WWW-Authenticate": 'Basic realm="Admin"'},
        )


app = FastAPI(title="Copa Fedex Sucesores 2026")
app.add_middleware(AdminAuthMiddleware)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
templates.env.globals["calcular_hcp_cancha"] = calcular_hcp_cancha
templates.env.globals["SLOPE_AZULES"] = SLOPE_AZULES
templates.env.globals["CR_AZULES"] = CR_AZULES
templates.env.globals["SLOPE_BLANCAS"] = SLOPE_BLANCAS
templates.env.globals["CR_BLANCAS"] = CR_BLANCAS


# === Páginas HTML ===

@app.get("/", response_class=HTMLResponse)
async def home_page(request: Request):
    jugadores = obtener_jugadores(DB_PATH)
    ranking = calcular_ranking_general(DB_PATH)
    ranking_map = {r['jugador_id']: r for r in ranking}
    for j in jugadores:
        r = ranking_map.get(j['id'], {})
        j['posicion_ranking'] = r.get('posicion', '-')
        j['total_puntos'] = r.get('total_puntos', 0)
    jugadores.sort(key=lambda x: (
        x['posicion_ranking'] if isinstance(x['posicion_ranking'], int) else 999,
        x.get('indice') or 99
    ))
    return templates.TemplateResponse("home.html", {
        "request": request,
        "jugadores": jugadores,
    })


@app.get("/ranking", response_class=HTMLResponse)
async def ranking_page(request: Request):
    ranking = calcular_ranking_general(DB_PATH)
    # Solo jugadores que han jugado al menos una fecha
    ranking_activo = [r for r in ranking if r['fechas_jugadas'] > 0]
    fechas = obtener_fechas_torneo(DB_PATH)
    # Solo fechas que tienen resultados
    fechas_con_datos = [f for f in fechas if f['num_jugadores'] > 0]
    return templates.TemplateResponse("ranking.html", {
        "request": request,
        "ranking": ranking_activo,
        "fechas": fechas_con_datos,
    })


@app.get("/jugadores", response_class=HTMLResponse)
async def jugadores_page(request: Request):
    jugadores = obtener_jugadores(DB_PATH)
    # Agregar info de ranking a cada jugador
    ranking = calcular_ranking_general(DB_PATH)
    ranking_map = {r['jugador_id']: r for r in ranking}
    for j in jugadores:
        r = ranking_map.get(j['id'], {})
        j['posicion_ranking'] = r.get('posicion', '-')
        j['total_puntos'] = r.get('total_puntos', 0)
        j['fechas_jugadas'] = r.get('fechas_jugadas', 0)
        j['sparkline'] = obtener_sparkline_jugador(DB_PATH, j['id'])
    # Ordenar por ranking (menor posicion primero), luego por indice
    jugadores.sort(key=lambda x: (
        x['posicion_ranking'] if isinstance(x['posicion_ranking'], int) else 999,
        x.get('indice') or 99
    ))
    return templates.TemplateResponse("jugadores.html", {
        "request": request,
        "jugadores": jugadores,
    })


@app.get("/jugador/{jugador_id}", response_class=HTMLResponse)
async def jugador_detalle_page(request: Request, jugador_id: int):
    jugador = obtener_jugador(DB_PATH, jugador_id)
    if not jugador:
        return HTMLResponse("Jugador no encontrado", status_code=404)
    rondas = obtener_rondas_jugador(DB_PATH, jugador_id)
    resultados = obtener_resultados_jugador(DB_PATH, jugador_id)
    fechas_asignadas = obtener_fechas_asignadas_jugador(DB_PATH, jugador_id)

    return templates.TemplateResponse("jugador_detalle.html", {
        "request": request,
        "jugador": jugador,
        "rondas": rondas,
        "resultados": resultados,
        "fechas_asignadas": fechas_asignadas,
    })


@app.get("/fecha/{fecha_id}", response_class=HTMLResponse)
async def fecha_detalle_page(request: Request, fecha_id: int):
    fecha = obtener_fecha_torneo(DB_PATH, fecha_id)
    if not fecha:
        return HTMLResponse("Fecha no encontrada", status_code=404)
    resultados = obtener_resultados_fecha(DB_PATH, fecha_id)
    return templates.TemplateResponse("fecha_detalle.html", {
        "request": request,
        "fecha": fecha,
        "resultados": resultados,
    })


@app.get("/fechas", response_class=HTMLResponse)
async def fechas_matriz_page(request: Request):
    datos = obtener_matriz_datos(DB_PATH)
    # Enriquecer jugadores con ranking y total_puntos
    ranking = calcular_ranking_general(DB_PATH)
    ranking_map = {r['jugador_id']: r for r in ranking}
    jugadores = datos['jugadores']
    for j in jugadores:
        r = ranking_map.get(j['id'], {})
        j['total_puntos'] = r.get('total_puntos', 0)
        j['posicion_ranking'] = r.get('posicion', 999)
    # Ordenar por ranking (menor posicion primero), luego por indice
    jugadores.sort(key=lambda x: (x['posicion_ranking'], x.get('indice') or 99))
    return templates.TemplateResponse("fechas_matriz.html", {
        "request": request,
        "jugadores": jugadores,
        "fechas": datos['fechas'],
        "asignaciones": datos['asignaciones'],
    })


@app.get("/reglas", response_class=HTMLResponse)
async def reglas_page(request: Request):
    return templates.TemplateResponse("reglas.html", {"request": request})


@app.get("/liquidar", response_class=HTMLResponse)
async def liquidar_page(request: Request):
    fechas = obtener_fechas_torneo(DB_PATH)
    return templates.TemplateResponse("liquidar.html", {
        "request": request,
        "fechas": fechas,
    })


@app.get("/reporte", response_class=HTMLResponse)
async def reporte_page(request: Request):
    from src.database import get_db
    # Build data for all jornadas (most recent first)
    jornadas = []
    with get_db(DB_PATH) as conn:
        fechas = conn.execute('''
            SELECT ft.id FROM fechas_torneo ft
            WHERE ft.num_jugadores > 0
            ORDER BY ft.fecha DESC
        ''').fetchall()
    for fecha in fechas:
        datos = obtener_reporte_semanal(DB_PATH, [fecha['id']])
        jornadas.append(datos)

    ranking = calcular_ranking_general(DB_PATH)
    ranking_activo = [r for r in ranking if r['fechas_jugadas'] > 0]
    return templates.TemplateResponse("reporte.html", {
        "request": request,
        "jornadas": jornadas,
        "ranking": ranking_activo,
    })


# === API Endpoints ===

@app.post("/api/ronda/{ronda_id}/toggle")
async def api_toggle_ronda(ronda_id: int):
    new_state = toggle_aplicable(DB_PATH, ronda_id)
    auto_detectar_fechas_torneo(DB_PATH)
    return JSONResponse({"aplicable": new_state})


@app.post("/api/sync/jugador/{jugador_id}")
async def api_sync_jugador(jugador_id: int):
    count = sync_rondas_jugador(DB_PATH, jugador_id)
    return JSONResponse({"nuevas_rondas": count})


@app.post("/api/sync/all")
async def api_sync_all():
    result = sync_all(DB_PATH)
    return JSONResponse(result)


class AsignarRequest(BaseModel):
    jugador_id: int
    fecha_torneo_id: int


@app.post("/api/asignar")
async def api_asignar(req: AsignarRequest):
    asignado = toggle_asignacion(DB_PATH, req.jugador_id, req.fecha_torneo_id)
    return JSONResponse({"asignado": asignado})


@app.post("/api/jugador/{jugador_id}/toggle-pago")
async def api_toggle_pago(jugador_id: int):
    nuevo_estado = toggle_pago(DB_PATH, jugador_id)
    return JSONResponse({"pago": nuevo_estado})


@app.post("/api/recalcular")
async def api_recalcular():
    auto_detectar_fechas_torneo(DB_PATH)
    ranking = recalcular_todo(DB_PATH)
    return JSONResponse({
        "status": "ok",
        "jugadores_en_ranking": len(ranking),
    })


@app.get("/api/ronda/{ronda_id}/hoyos")
async def api_ronda_hoyos(ronda_id: int):
    """Obtiene datos hoyo por hoyo de una ronda. Usa cache en DB o busca en la federacion."""
    ronda = obtener_ronda(DB_PATH, ronda_id)
    if not ronda:
        return JSONResponse({"error": "Ronda no encontrada"}, status_code=404)

    # Si ya tenemos los datos cacheados, devolverlos
    if ronda.get('hoyos_json'):
        return JSONResponse(json.loads(ronda['hoyos_json']))

    # Si no tenemos tarjeta_id, no podemos buscar
    if not ronda.get('tarjeta_id'):
        return JSONResponse({"error": "No hay tarjeta_id para esta ronda"}, status_code=404)

    # Buscar en la federacion
    collector = FedegolfScoresCollector()
    detalle = collector.get_scorecard_detail(ronda['tarjeta_id'])

    if not detalle:
        return JSONResponse({"error": "No se pudo obtener el detalle de la tarjeta"}, status_code=404)

    # Cachear en la DB, incluyendo handicap e indice si están disponibles
    hoyos_str = json.dumps(detalle)
    actualizar_ronda_tarjeta(
        DB_PATH, ronda_id,
        hoyos_json=hoyos_str,
        handicap_cancha=detalle.get('handicap_cancha'),
        indice_al_momento=detalle.get('indice_al_momento'),
    )

    return JSONResponse(detalle)


class AgregarJugadorRequest(BaseModel):
    codigo: str


@app.post("/api/jugador/agregar")
async def api_agregar_jugador(req: AgregarJugadorRequest):
    collector = FedegolfScoresCollector()
    jugador = collector.search_player_by_code(req.codigo)
    if not jugador:
        return JSONResponse({"error": "No se encontro jugador con codigo " + req.codigo}, status_code=404)
    agregar_jugador(DB_PATH, jugador)
    return JSONResponse({
        "nombre": jugador.get("nombre", "") + " " + jugador.get("apellido", ""),
        "codigo": jugador.get("codigo"),
        "indice": jugador.get("indice"),
        "categoria": jugador.get("categoria"),
    })


@app.post("/api/jugador/{jugador_id}/eliminar")
async def api_eliminar_jugador(jugador_id: int):
    jugador = obtener_jugador(DB_PATH, jugador_id)
    if not jugador:
        return JSONResponse({"error": "Jugador no encontrado"}, status_code=404)
    eliminar_jugador(DB_PATH, jugador_id)
    return JSONResponse({
        "status": "ok",
        "nombre": jugador['nombre'] + " " + jugador['apellido'],
    })


class LiquidarRequest(BaseModel):
    fecha: str  # formato YYYY-MM-DD (sabado del fin de semana)


@app.post("/api/liquidar")
async def api_liquidar(req: LiquidarRequest):
    """
    Endpoint de auto-liquidacion: sincroniza, asigna y calcula todo de un golpe.
    1. Sync rondas de todos los jugadores
    2. Detecta quien jugo en Manizales ese fin de semana
    3. Obtiene handicap de la federacion para cada tarjeta
    4. Asigna jugadores a la fecha
    5. Recalcula posiciones y puntos
    """
    from datetime import date as dt_date, timedelta
    from src.database import get_db, guardar_resultados_fecha
    from src.ranking import recalcular_fecha

    sabado_str = req.fecha
    try:
        sabado = dt_date.fromisoformat(sabado_str)
    except ValueError:
        return JSONResponse({"error": "Formato de fecha invalido. Use YYYY-MM-DD"}, status_code=400)

    domingo = sabado + timedelta(days=1)
    log = []

    # Paso 1: Sync
    log.append("Paso 1: Sincronizando rondas...")
    try:
        sync_result = sync_all(DB_PATH)
        log.append(f"  Sincronizados: {sync_result['jugadores_sincronizados']} jugadores, {sync_result['rondas_nuevas']} rondas nuevas")
    except Exception as e:
        log.append(f"  Error en sync: {str(e)}")

    # Paso 2: Buscar/crear fecha del torneo
    with get_db(DB_PATH) as conn:
        fecha_row = conn.execute(
            'SELECT id FROM fechas_torneo WHERE fecha = ?', (sabado_str,)
        ).fetchone()
        if fecha_row:
            fecha_torneo_id = fecha_row['id']
        else:
            cursor = conn.execute(
                'INSERT INTO fechas_torneo (fecha) VALUES (?)', (sabado_str,)
            )
            fecha_torneo_id = cursor.lastrowid
    log.append(f"Paso 2: Fecha torneo ID={fecha_torneo_id} ({sabado_str})")

    # Paso 3: Detectar quien jugo en Manizales este fin de semana
    log.append("Paso 3: Detectando jugadores del fin de semana...")
    with get_db(DB_PATH) as conn:
        rondas_finde = conn.execute('''
            SELECT r.id as ronda_id, r.jugador_id, j.nombre, j.apellido,
                   r.fecha, r.club, r.score_gross, r.tarjeta_id, r.handicap_cancha
            FROM rondas r
            JOIN jugadores j ON r.jugador_id = j.id
            WHERE r.fecha IN (?, ?)
            AND r.club LIKE '%Manizales%'
            AND r.score_gross IS NOT NULL
            AND r.score_gross >= 60
            ORDER BY r.jugador_id, r.fecha
        ''', (sabado_str, domingo.isoformat())).fetchall()
        rondas_finde = [dict(r) for r in rondas_finde]

    if not rondas_finde:
        log.append("  No se encontraron rondas en Manizales para este fin de semana")
        return JSONResponse({"log": log, "error": "No hay rondas para liquidar"})

    # Elegir ronda por jugador: preferir sabado sobre domingo
    mejores = {}
    for r in rondas_finde:
        jid = r['jugador_id']
        if jid not in mejores:
            mejores[jid] = r
        elif r['fecha'] == sabado_str:
            mejores[jid] = r  # Preferir sabado

    log.append(f"  {len(mejores)} jugadores detectados:")
    for jid, r in mejores.items():
        log.append(f"    {r['nombre']} {r['apellido']} | {r['fecha']} | Gross:{r['score_gross']} | HCP:{r['handicap_cancha']}")

    # Paso 4: Obtener handicap de federacion para rondas sin handicap_cancha
    log.append("Paso 4: Obteniendo handicaps de la federacion...")
    import time
    collector = FedegolfScoresCollector()
    for jid, r in mejores.items():
        if r['handicap_cancha'] is None and r['tarjeta_id']:
            try:
                detalle = collector.get_scorecard_detail(r['tarjeta_id'])
                if detalle and detalle.get('handicap_cancha') is not None:
                    with get_db(DB_PATH) as conn:
                        conn.execute(
                            'UPDATE rondas SET handicap_cancha=?, indice_al_momento=? WHERE id=?',
                            (detalle['handicap_cancha'], detalle.get('indice_al_momento'), r['ronda_id'])
                        )
                    r['handicap_cancha'] = detalle['handicap_cancha']
                    log.append(f"    {r['nombre']} {r['apellido']}: HCP={detalle['handicap_cancha']}")
                time.sleep(0.3)
            except Exception as e:
                log.append(f"    Error obteniendo HCP de {r['nombre']}: {str(e)}")

    # Paso 5: Asignar jugadores a la fecha (limpiar asignaciones previas)
    log.append("Paso 5: Asignando jugadores a la fecha...")
    with get_db(DB_PATH) as conn:
        conn.execute('DELETE FROM resultados_fecha WHERE fecha_torneo_id = ?', (fecha_torneo_id,))
        for jid, r in mejores.items():
            conn.execute('''
                INSERT INTO resultados_fecha (fecha_torneo_id, jugador_id, ronda_id, score_gross)
                VALUES (?, ?, ?, ?)
            ''', (fecha_torneo_id, jid, r['ronda_id'], r['score_gross']))
        num = len(mejores)
        conn.execute(
            'UPDATE fechas_torneo SET num_jugadores = ?, valida = ? WHERE id = ?',
            (num, num >= 2, fecha_torneo_id)
        )

    # Paso 6: Recalcular
    log.append("Paso 6: Recalculando posiciones y puntos...")
    recalcular_fecha(DB_PATH, fecha_torneo_id)

    # Paso 7: Leer resultados finales
    resultados_finales = obtener_resultados_fecha(DB_PATH, fecha_torneo_id)
    log.append(f"\nRESULTADOS FECHA {sabado_str}:")
    log.append(f"{'Pos':>3} | {'Jugador':<30} | {'Gross':>5} | {'HCP':>5} | {'Neto':>5} | {'Puntos':>6}")
    log.append("-" * 80)
    for r in resultados_finales:
        log.append(f"{r['posicion']:>3} | {r['nombre']} {r['apellido']:<25} | {r['score_gross'] or '-':>5} | {r['handicap_aplicado'] or '-':>5} | {r['score_neto'] or '-':>5} | {r['puntos'] or 0:>6}")

    return JSONResponse({
        "status": "ok",
        "fecha": sabado_str,
        "fecha_torneo_id": fecha_torneo_id,
        "jugadores": len(mejores),
        "resultados": resultados_finales,
        "log": log,
    })


class ChatRequest(BaseModel):
    mensajes: list[dict]


@app.post("/api/chat")
async def api_chat(req: ChatRequest):
    try:
        respuesta = chat_responder(req.mensajes)
        return JSONResponse({"respuesta": respuesta})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


class GenerarFechasRequest(BaseModel):
    year: int


@app.post("/api/fechas/generar")
async def api_generar_fechas(req: GenerarFechasRequest):
    from datetime import date, timedelta
    start = date(req.year, 1, 1)
    end = date(req.year, 12, 31)
    current = start
    while current.weekday() != 5:  # primer sabado
        current += timedelta(days=1)
    count = 0
    while current <= end:
        # Solo sabados - cada fin de semana es UNA fecha
        crear_fecha_torneo(DB_PATH, current.isoformat(), es_ultima_cuatro=False)
        count += 1
        current += timedelta(days=7)
    return JSONResponse({"status": "ok", "fechas_procesadas": count, "year": req.year})
