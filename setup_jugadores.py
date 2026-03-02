"""
Script para agregar los jugadores del torneo y consultar sus rondas
"""

import os
import time
from src.fedegolf_collector import FedegolfScoresCollector
from src.database import create_database, agregar_jugador

DB_PATH = os.environ.get("DB_PATH", "data/torneo.db")

# Lista de jugadores inscritos
JUGADORES_INSCRITOS = [
    {"nombre": "Felipe Uribe", "codigo": "16960"},
    {"nombre": "Juan Carlos Perez", "codigo": "22932"},
    {"nombre": "Juan Felipe Robleda", "codigo": None},  # Sin código
    {"nombre": "Juan Felipe Villegas", "codigo": "12349"},
    {"nombre": "Julian Gomez Hoyos", "codigo": "4228"},
    {"nombre": "Mateo Gaviria", "codigo": "16585"},
    {"nombre": "Nicolas Gallo", "codigo": "3749"},
    {"nombre": "Palomo", "codigo": "12634"},
    {"nombre": "Pedro Velez Gomez", "codigo": "13470"},
    {"nombre": "Sebastian Alvarez", "codigo": "21236"},
    {"nombre": "Camilo Millan", "codigo": "7016"},
    {"nombre": "Juan Pablo Valencia", "codigo": "11709"},
    {"nombre": "Santiago Gonzales", "codigo": "4620"},
    {"nombre": "Andres Velez Saffon", "codigo": "16089"},
]


def verificar_y_agregar_jugadores():
    """
    Verifica la información de cada jugador en la federación
    y los agrega a la base de datos
    """
    # Crear base de datos
    print("📊 Creando base de datos...")
    create_database(DB_PATH)

    collector = FedegolfScoresCollector()
    jugadores_encontrados = []

    print("\n" + "="*60)
    print("🔍 VERIFICANDO JUGADORES EN LA FEDERACIÓN")
    print("="*60)

    for jugador_info in JUGADORES_INSCRITOS:
        nombre = jugador_info["nombre"]
        codigo = jugador_info["codigo"]

        print(f"\n🏌️  Buscando: {nombre} (Código: {codigo or 'N/A'})")
        print("-" * 60)

        if not codigo:
            print(f"⚠️  Sin código de federación - buscar manualmente")
            # Intentar buscar por nombre
            resultados = collector.search_player_by_name(nombre.split()[0])
            if resultados:
                print(f"   Posibles coincidencias encontradas:")
                for r in resultados[:3]:
                    print(f"   - {r['nombre']} {r['apellido']} (Código: {r['codigo']})")
            continue

        # Buscar por código
        jugador = collector.search_player_by_code(codigo)

        if jugador:
            print(f"✅ Encontrado: {jugador['nombre']} {jugador['apellido']}")
            print(f"   Categoría: {jugador['categoria']}")
            print(f"   Índice: {jugador['indice']}")

            jugadores_encontrados.append(jugador)

            # Agregar a base de datos
            agregar_jugador(DB_PATH, jugador)
        else:
            print(f"❌ No se encontró jugador con código {codigo}")

        time.sleep(0.5)  # Delay para no saturar el servidor

    return jugadores_encontrados


def consultar_rondas_jugadores(codigos_jugadores: list):
    """
    Consulta las rondas recientes de los jugadores
    Nota: Necesitamos el user_id de Salesforce, no solo el código
    """
    collector = FedegolfScoresCollector()

    print("\n" + "="*60)
    print("📋 CONSULTANDO RONDAS DE JUGADORES")
    print("="*60)
    print("\n⚠️  IMPORTANTE: Para obtener scores necesitamos el user_id de Salesforce")
    print("    El scraper actual busca por código de federación.")
    print("    Necesitamos expandir el scraper para obtener el user_id.\n")

    # Por ahora, solo mostramos cómo buscar jugadores
    for codigo in codigos_jugadores[:3]:  # Probar con los primeros 3
        print(f"\n🔍 Código: {codigo}")
        jugador = collector.search_player_by_code(codigo)
        if jugador:
            print(f"   ✅ {jugador['nombre']} {jugador['apellido']}")
            # TODO: Necesitamos extraer el user_id para consultar scores
        time.sleep(0.5)


if __name__ == "__main__":
    # Paso 1: Verificar y agregar jugadores
    jugadores = verificar_y_agregar_jugadores()

    print("\n" + "="*60)
    print(f"📊 RESUMEN: {len(jugadores)} jugadores verificados y agregados")
    print("="*60)

    # Paso 2: Intentar consultar rondas
    codigos = [j["codigo"] for j in jugadores if j.get("codigo")]
    if codigos:
        consultar_rondas_jugadores(codigos)
