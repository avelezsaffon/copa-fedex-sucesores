# Copa Fedex Sucesores 2026

Sistema de gestion del torneo de golf Copa Fedex Sucesores 2026, jugado en el
Club de Golf de Manizales, Colombia. Integra con la Federacion Colombiana de
Golf para obtener scores automaticamente.

## Caracteristicas

- Busqueda de jugadores en la Federacion Colombiana de Golf
- Extraccion automatica de scores de fin de semana
- Sistema de ranking anual con puntos por posicion
- Manejo de empates (promedio de puntos)
- Interfaz web mobile-first
- Agente de IA "El Comisario" para consulta de reglas de golf (RAG sobre reglas USGA/R&A 2023)
- Base de datos SQLite con backups automaticos en JSON

## Reglas del Torneo

- Cada fin de semana = 1 fecha del torneo (sabado es la fecha oficial)
- Si un jugador juega sabado Y domingo, cuenta la tarjeta del sabado
- Si solo juega domingo, cuenta esa tarjeta
- Score neto = Score Gross - Handicap de cancha (de la federacion ese dia)
- Minimo 2 jugadores para que una fecha sea valida
- Ranking general = suma de las mejores 8 fechas de cada jugador
- Ultimas 4 fechas del torneo tienen puntos x1.5
- Puntos por posicion: 1ro=300, 2do=240, 3ro=190, 4to=150, 5to=120, etc.

## Estructura del Proyecto

```
copa-fedex-sucesores/
├── src/
│   ├── app.py                 # FastAPI app, rutas y endpoints
│   ├── database.py            # Capa de datos SQLite
│   ├── ranking.py             # Motor de calculo de puntos
│   ├── sync.py                # Sincronizacion con la federacion
│   ├── fedegolf_collector.py  # Scraper de la federacion
│   ├── chat_agent.py          # Agente "El Comisario"
│   └── rag.py                 # RAG sobre reglas de golf
├── templates/                 # Jinja2 templates
├── static/                    # CSS/JS estatico
├── data/
│   ├── backup/                # Backups JSON (una fuente de respaldo)
│   └── reglas_golf_2023.txt   # Reglas USGA/R&A para el agente
├── scripts/                   # Scripts one-off de liquidacion
├── .github/workflows/         # GitHub Actions (deploy + liquidacion)
├── Dockerfile
├── fly.toml                   # Configuracion de Fly.dev
├── requirements.txt
├── start.py                   # Entrypoint
└── PROCESO_LIQUIDACION.md     # Guia paso a paso para liquidar fechas
```

## Instalacion local

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Crear DB vacia
python start.py
```

## Variables de entorno

- `DB_PATH`: ruta a la base SQLite (default: `data/torneo.db`)
- `ADMIN_PASSWORD`: password para endpoints de admin (opcional, si se define protege /api/asignar, /api/recalcular, etc.)
- `ANTHROPIC_API_KEY`: key de Anthropic para el agente de reglas "El Comisario"

## Stack

- Python 3.11
- FastAPI + Jinja2
- SQLite
- BeautifulSoup4 (scraping)
- Anthropic API (agente de reglas)
- Fly.dev (despliegue)

## Proceso de Liquidacion

Ver [PROCESO_LIQUIDACION.md](PROCESO_LIQUIDACION.md) para el proceso paso a paso
de como liquidar una nueva fecha del torneo.
