"""
Script para migrar la base de datos y sembrar datos iniciales.
Ejecutar una vez: python seed_data.py
Para agregar fechas nuevas: python seed_data.py --add-dates 2026
"""

import os
import sys
from datetime import date, timedelta
from src.database import migrate_database, seed_tabla_puntos, crear_fecha_torneo

DB_PATH = os.environ.get("DB_PATH", "data/torneo.db")


def generar_fines_de_semana(start: date, end: date):
    """
    Genera todos los sábados y domingos entre start y end (inclusive).
    """
    current = start
    while current.weekday() != 5:  # 5 = sábado
        current += timedelta(days=1)

    dias = []
    while current <= end:
        dias.append(current)  # sábado
        domingo = current + timedelta(days=1)
        if domingo <= end:
            dias.append(domingo)  # domingo
        current += timedelta(days=7)

    return dias


def agregar_fechas(year: int):
    """Agrega todos los fines de semana de un año al torneo (sin borrar nada)."""
    start = date(year, 1, 1)
    end = date(year, 12, 31)
    dias = generar_fines_de_semana(start, end)

    print(f"=== Agregando {len(dias)} dias de fin de semana de {year} ===")
    for d in dias:
        crear_fecha_torneo(DB_PATH, d.isoformat(), es_ultima_cuatro=False)

    print(f"   Primer dia: {dias[0].isoformat()}")
    print(f"   Ultimo dia: {dias[-1].isoformat()}")
    print(f"   {len(dias)} fechas procesadas (duplicados ignorados)")


def main():
    # Si se pasa --add-dates YEAR, solo agrega fechas sin migrar
    if len(sys.argv) >= 3 and sys.argv[1] == "--add-dates":
        year = int(sys.argv[2])
        agregar_fechas(year)
        return

    print("=== Migrando base de datos ===")
    migrate_database(DB_PATH)

    print("\n=== Sembrando tabla de puntos ===")
    seed_tabla_puntos(DB_PATH)

    print("\n=== Generando fechas de torneo (fines de semana) ===")
    fines = generar_fines_de_semana(date(2026, 2, 21), date(2026, 6, 28))
    # Últimos 4 fines de semana = últimos 8 días (4 sáb + 4 dom)
    ultimos_sabados = [d for d in fines if d.weekday() == 5][-4:]
    ultimos_domingos = [d for d in fines if d.weekday() == 6][-4:]
    ultimas_fechas = set(ultimos_sabados + ultimos_domingos)

    for d in fines:
        es_ultima = d in ultimas_fechas
        crear_fecha_torneo(DB_PATH, d.isoformat(), es_ultima)

    print(f"   {len(fines)} dias de fin de semana creados")
    print(f"   Primer dia: {fines[0].isoformat()}")
    print(f"   Ultimo dia: {fines[-1].isoformat()}")
    print(f"   Ultimas fechas: {sorted(d.isoformat() for d in ultimas_fechas)}")

    print("\n=== Seed completado ===")
    print(f"   Base de datos: {DB_PATH}")
    print("   Luego: uvicorn src.app:app --reload")


if __name__ == "__main__":
    main()
