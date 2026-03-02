# Proceso de Liquidacion de Fechas - Copa Fedex Sucesores 2026

## Resumen

Este documento describe el proceso paso a paso para liquidar (calcular resultados de)
una nueva fecha del torneo Copa Fedex Sucesores 2026. Un agente de IA puede seguir
estas instrucciones para ejecutar el proceso completo.

## Arquitectura

- **App**: FastAPI desplegada en Fly.dev (`copa-fedex-sucesores`)
- **DB**: SQLite en volumen persistente `/data/torneo.db`
- **Datos de jugadores/rondas**: Federacion Colombiana de Golf (scraping)
- **Repo local**: `/Users/andresvelezsaffon/torneo-golf/`
- **Repo GitHub**: `avelezsaffon/copa-fedex-sucesores`
- **URL produccion**: https://copa-fedex-sucesores.fly.dev/

## Reglas del Torneo

- Cada fin de semana = 1 fecha del torneo (sabado es la fecha oficial)
- Si un jugador juega sabado Y domingo, cuenta la tarjeta del **sabado**
- Si solo juega domingo, cuenta esa tarjeta
- Score neto = Score Gross (reportado por la federacion) - Handicap de cancha (de la federacion ese dia)
- **IMPORTANTE**: El handicap se toma directamente de la tarjeta de la federacion para esa ronda. NO se calcula. NO se modifica. NO se aplica tope de 15 al handicap de la federacion.
- Puntos por posicion: 1ro=300, 2do=240, 3ro=190, 4to=150, 5to=120, 6to=100, 7to=90, 8vo=85, 9no=80, 10mo=75, 11=70, 12=65, 13=60...
- Empates: se promedian los puntos de las posiciones empatadas
- Minimo 2 jugadores para que una fecha sea valida
- Ranking general = suma de las mejores 8 fechas de cada jugador
- Ultimas 4 fechas del torneo tienen puntos x1.5

## Datos de la Cancha (Club de Golf de Manizales)

- Par: 72
- Tees Azules: Slope 137, CR 71.8
- Tees Blancas: Slope 128, CR 69.4

## Proceso de Liquidacion Paso a Paso

### 1. Sincronizar rondas desde la Federacion

Esto descarga las rondas nuevas de todos los jugadores.

```bash
# Desde produccion:
curl -X POST https://copa-fedex-sucesores.fly.dev/api/sync/all
```

O via SSH:
```bash
flyctl ssh console -a copa-fedex-sucesores -C "python3 -c \"
import sys; sys.path.insert(0, '/app')
from src.sync import sync_all
result = sync_all('/data/torneo.db')
print(result)
\""
```

### 2. Verificar las rondas del fin de semana

Revisar que rondas se descargaron para el fin de semana en cuestion:

```bash
flyctl ssh console -a copa-fedex-sucesores -C "python3 -c \"
import sqlite3
conn = sqlite3.connect('/data/torneo.db')
# Cambiar las fechas segun el fin de semana
SABADO = '2026-03-07'
DOMINGO = '2026-03-08'
rondas = conn.execute('''
    SELECT r.id, j.nombre, j.apellido, r.fecha, r.club, r.score_gross, r.tarjeta_id
    FROM rondas r JOIN jugadores j ON r.jugador_id = j.id
    WHERE r.fecha IN (?, ?)
    ORDER BY r.fecha, j.apellido
''', (SABADO, DOMINGO)).fetchall()
for r in rondas:
    print(f'{r[1]} {r[2]} | {r[3]} | {r[4]} | Gross:{r[5]} | tarjeta:{r[6]}')
\""
```

**ATENCION**: Las fechas de la federacion a veces vienen con un dia de desfase
(ej: domingo 1 de marzo aparece como 2 de marzo). Si las rondas de Club Manizales
aparecen un dia despues (lunes), corregir con:

```sql
UPDATE rondas SET fecha = 'YYYY-MM-DD_correcto' WHERE fecha = 'YYYY-MM-DD_incorrecto'
AND club LIKE '%Manizales%'
```

### 3. Obtener handicap de la federacion para cada ronda

**CRITICO**: Cada ronda necesita el `handicap_cancha` que la federacion tenia registrado
para esa tarjeta. Esto se obtiene del detalle de la tarjeta (scorecard).

```python
# Ejecutar localmente o via SSH
from src.fedegolf_collector import FedegolfScoresCollector
import sqlite3, time

conn = sqlite3.connect('data/torneo_prod.db')  # o /data/torneo.db en produccion
collector = FedegolfScoresCollector()

# Buscar rondas del fin de semana sin handicap_cancha
rondas = conn.execute('''
    SELECT r.id, r.tarjeta_id, j.nombre, j.apellido
    FROM rondas r JOIN jugadores j ON r.jugador_id = j.id
    WHERE r.tarjeta_id IS NOT NULL AND r.handicap_cancha IS NULL
    AND r.fecha BETWEEN ? AND ?
''', (SABADO, DOMINGO)).fetchall()

for rid, tarjeta, nombre, apellido in rondas:
    detalle = collector.get_scorecard_detail(tarjeta)
    if detalle:
        conn.execute('UPDATE rondas SET handicap_cancha=?, indice_al_momento=? WHERE id=?',
            (detalle.get('handicap_cancha'), detalle.get('indice_al_momento'), rid))
        print(f'{nombre} {apellido}: HCP={detalle.get("handicap_cancha")}')
    time.sleep(0.3)

conn.commit()
```

### 4. Verificar tarjetas incompletas

Revisar si alguna ronda tiene un score sospechosamente bajo (tarjeta incompleta):

```sql
SELECT j.nombre, j.apellido, r.fecha, r.score_gross, r.tarjeta_id
FROM rondas r JOIN jugadores j ON r.jugador_id = j.id
WHERE r.fecha BETWEEN 'SABADO' AND 'DOMINGO'
AND r.score_gross < 60
```

Si un jugador tiene tarjeta incompleta un dia pero completa el otro, usar la completa.
Si ambas son incompletas, NO incluir al jugador en la fecha.

### 5. Asignar jugadores a la fecha del torneo

La fecha del torneo debe existir (se crean automaticamente). Verificar:

```sql
SELECT id, fecha FROM fechas_torneo WHERE fecha = 'SABADO'
```

Asignar cada jugador que jugo ese fin de semana. Si jugo sabado y domingo,
vincular con la ronda del **sabado**:

```python
# Para cada jugador que jugo:
conn.execute('''
    INSERT INTO resultados_fecha (jugador_id, fecha_torneo_id, ronda_id)
    VALUES (?, ?, ?)
''', (jugador_id, fecha_torneo_id, ronda_id_sabado))
```

O usar la API de la app:
```bash
curl -X POST https://copa-fedex-sucesores.fly.dev/api/asignar \
  -H "Content-Type: application/json" \
  -d '{"jugador_id": X, "fecha_torneo_id": Y}'
```

### 6. Recalcular resultados

```python
from src.ranking import recalcular_fecha
recalcular_fecha(db_path, fecha_torneo_id)
```

`recalcular_fecha` hace:
1. Lee el `score_gross` de la ronda vinculada (el que reporta la federacion)
2. Lee el `handicap_cancha` de la ronda (el que tenia la federacion ese dia)
3. Calcula neto = gross - handicap
4. Ordena por neto y asigna puntos segun la tabla, promediando empates

### 7. Verificar resultados

```sql
SELECT rf.posicion, j.nombre, j.apellido, rf.score_gross,
       rf.handicap_aplicado, rf.score_neto, rf.puntos, r.handicap_cancha
FROM resultados_fecha rf
JOIN jugadores j ON rf.jugador_id = j.id
LEFT JOIN rondas r ON rf.ronda_id = r.id
WHERE rf.fecha_torneo_id = ?
ORDER BY rf.posicion
```

**Verificar que `handicap_aplicado` == `handicap_cancha` para todas las filas.**

### 8. Desplegar a produccion

Si se hicieron cambios de codigo:
```bash
cd /Users/andresvelezsaffon/torneo-golf
flyctl deploy
```

Si solo se actualizan datos en la DB de produccion, usar SSH:
```bash
flyctl ssh console -a copa-fedex-sucesores -C "python3 -c \"...\""
```

Para subir archivos a produccion:
```bash
flyctl sftp shell -a copa-fedex-sucesores
> put archivo_local /ruta/remota
```

**NOTA**: La maquina de Fly tiene auto-stop. Hacer `curl` a la URL primero
para despertarla antes de usar SSH/SFTP.

### 9. Crear branch de snapshot

Despues de liquidar, crear un branch con el estado actual:

```bash
git checkout -b fechaX-YYYY-MM-DD
git add -A
git commit -m "Fecha X liquidada - YYYY-MM-DD"
git push origin fechaX-YYYY-MM-DD
git checkout main
```

## Herramientas Clave

- `flyctl` ubicado en `/Users/andresvelezsaffon/.fly/bin/flyctl`
- DB local de trabajo: `data/torneo_prod.db`
- DB produccion: `/data/torneo.db` (en el volumen de Fly)
- Entorno virtual: `venv/` (activar con `source venv/bin/activate`)

## Archivos Principales

| Archivo | Descripcion |
|---------|-------------|
| `src/app.py` | FastAPI app, rutas y endpoints |
| `src/ranking.py` | Motor de calculo: handicap, puntos, empates, ranking |
| `src/sync.py` | Sincronizacion con la federacion |
| `src/database.py` | Capa de datos SQLite |
| `src/fedegolf_collector.py` | Scraper de la federacion |
| `templates/reporte.html` | Pagina de reporte/prensa (cronologia de todas las fechas) |
| `templates/fechas_matriz.html` | Matriz de asignaciones |
| `start.py` | Entrypoint con migraciones de DB |

## Historial de Liquidaciones

### Fecha 1 - 2026-02-21
- **13 jugadores**
- Ganador: Pedro Velez Gomez (Gross 68, HCP 0, Neto 68, 300 pts)
- 2do: Santiago Gonzalez Ossa (Gross 75, HCP 2, Neto 73, 240 pts)
- 3ro empate: Villegas Herrera / Valencia Hoyos (Neto 75, 170 pts c/u)
- Empate masivo a neto 78: Zuluaga, Millan Hoyos, Velez Saffon, Villegas Villegas, Millan Ocampo (86 pts c/u)
- Branch: `fecha2-2026-03-01` (incluye fecha 1 y fecha 2)

### Fecha 2 - 2026-02-28
- **12 jugadores**
- Ganador: Juan Manuel Mideros Barbossa (Gross 74, HCP 7, Neto 67, 300 pts)
- 2do: Juan Pablo Valencia Hoyos (Gross 72, HCP 4, Neto 68, 240 pts)
- 3ro: Pedro Velez Gomez (Gross 71, HCP -1, Neto 72, 190 pts)
- Nota: Mideros tenia tarjeta del domingo con pocos hoyos. Se uso la del sabado.
- Branch: `fecha2-2026-03-01`

### Ranking General (despues de Fecha 2)
1. Velez Gomez - 490 pts
2. Valencia Hoyos - 410 pts
3. Gonzalez Ossa - 375 pts
4. Mideros Barbossa - 360 pts
5. Villegas Herrera - 240 pts
6. Zuluaga Ramirez - 221 pts
7. Villegas Villegas / Velez Saffon - 181 pts
9. Millan Ocampo - 166 pts
10. Millan Hoyos - 151 pts
11. Uribe Jaramillo - 150 pts
12. Perez Quintero - 120 pts (1 fecha)
13. Saenz Merino - 75 pts (1 fecha)
14. Alvarez Antia - 70 pts (1 fecha)
