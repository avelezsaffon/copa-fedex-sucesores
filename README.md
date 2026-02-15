# Torneo de Golf - Sistema de Gestión

Sistema para gestionar torneos locales de golf con integración a la Federación Colombiana de Golf.

## Características

- 🏌️ Búsqueda de jugadores en la Federación Colombiana de Golf
- 📊 Extracción automática de scores
- 🏆 Sistema de ranking anual con puntos por posición
- 📱 Interfaz web responsive (mobile-first)
- 💾 Base de datos SQLite local

## Estructura del Proyecto

```
torneo-golf/
├── src/
│   ├── fedegolf_collector.py  # Scraper de la federación
│   ├── database.py            # Gestión de base de datos
│   └── app.py                 # Web app (próximamente)
├── data/
│   └── torneo.db              # Base de datos SQLite
├── requirements.txt
└── README.md
```

## Instalación

```bash
# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Crear base de datos
python src/database.py
```

## Uso

### Buscar jugadores

```python
from src.fedegolf_collector import FedegolfScoresCollector

collector = FedegolfScoresCollector()

# Buscar por nombre
jugadores = collector.search_player_by_name("Eduardo Escobar")

# Buscar por código
jugador = collector.search_player_by_code("25701")
```

### Gestionar base de datos

```python
from src.database import create_database, agregar_jugador

# Crear base de datos
create_database("data/torneo.db")

# Agregar jugador
agregar_jugador("data/torneo.db", jugador_dict)
```

## Próximos pasos

- [ ] Implementar sistema de puntuación según reglas del Excel
- [ ] Crear web app con FastAPI
- [ ] Interfaz mobile-first para ver resultados
- [ ] Sistema de ranking automático
- [ ] Sincronización automática de scores

## Tecnologías

- Python 3.x
- FastAPI
- SQLite
- BeautifulSoup4
- Pandas
