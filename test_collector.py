"""
Script de prueba para el collector de Fedegolf
"""

from src.fedegolf_collector import FedegolfScoresCollector
from src.database import create_database, agregar_jugadores

if __name__ == "__main__":
    # Crear base de datos
    print("Creando base de datos...")
    create_database("data/torneo.db")

    # Crear instancia del collector
    collector = FedegolfScoresCollector()

    # EJEMPLO: Buscar jugador por nombre
    print("\n" + "="*50)
    print("BUSCANDO JUGADOR POR NOMBRE")
    print("="*50)

    jugadores = collector.search_player_by_name("Eduardo Escobar")

    if jugadores:
        print(f"Se encontraron {len(jugadores)} jugador(es):\n")
        for jugador in jugadores[:5]:
            print(f"Código: {jugador['codigo']}")
            print(f"Nombre: {jugador['nombre']} {jugador['apellido']}")
            print(f"Categoría: {jugador['categoria']}")
            print(f"Índice: {jugador['indice']}\n")

        # Agregar a base de datos
        agregar_jugadores("data/torneo.db", jugadores)
    else:
        print("No se encontraron jugadores")
