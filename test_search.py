"""
Script de prueba para investigar el scraper
"""

from src.fedegolf_collector import FedegolfScoresCollector

collector = FedegolfScoresCollector()

print("="*60)
print("TEST 1: Buscar por nombre 'Andres Velez'")
print("="*60)
jugadores = collector.search_player_by_name("Andres Velez")
print(f"Resultados: {len(jugadores)}")
for j in jugadores[:5]:
    print(f"  - {j['nombre']} {j['apellido']} | Código: {j['codigo']} | Índice: {j['indice']}")

print("\n" + "="*60)
print("TEST 2: Buscar por código '16089'")
print("="*60)
jugador = collector.search_player_by_code("16089")
if jugador:
    print(f"✅ Encontrado: {jugador}")
else:
    print("❌ No encontrado")

print("\n" + "="*60)
print("TEST 3: Buscar por nombre 'Uribe'")
print("="*60)
jugadores = collector.search_player_by_name("Uribe")
print(f"Resultados: {len(jugadores)}")
for j in jugadores[:5]:
    print(f"  - {j['nombre']} {j['apellido']} | Código: {j['codigo']} | Índice: {j['indice']}")
