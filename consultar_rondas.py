"""
Script para consultar las rondas de los jugadores del torneo
"""

from src.fedegolf_collector import FedegolfScoresCollector
import sqlite3
from datetime import datetime, timedelta

def obtener_jugadores_db():
    """Obtiene todos los jugadores de la base de datos"""
    conn = sqlite3.connect("data/torneo.db")
    cursor = conn.cursor()

    cursor.execute('''
        SELECT codigo, nombre, apellido
        FROM jugadores
        ORDER BY apellido, nombre
    ''')

    jugadores = cursor.fetchall()
    conn.close()

    return jugadores


def consultar_rondas_recientes(num_jugadores=5):
    """
    Consulta las rondas recientes de los jugadores
    """
    collector = FedegolfScoresCollector()

    # Obtener jugadores de la DB
    jugadores = obtener_jugadores_db()

    print("="*80)
    print(f"📊 CONSULTANDO RONDAS DE {min(num_jugadores, len(jugadores))} JUGADORES")
    print("="*80)

    for i, (codigo, nombre, apellido) in enumerate(jugadores[:num_jugadores]):
        print(f"\n🏌️  {nombre} {apellido} (Código: {codigo})")
        print("-" * 80)

        # Buscar jugador para obtener salesforce_id
        jugador_info = collector.search_player_by_code(str(codigo))

        if jugador_info and jugador_info.get('salesforce_id'):
            salesforce_id = jugador_info['salesforce_id']
            print(f"   Salesforce ID: {salesforce_id}")
            print(f"   Email: {jugador_info.get('email', 'N/A')}")

            # Obtener scores
            scores = collector.get_player_scores(salesforce_id)

            if scores:
                print(f"\n   ✅ {len(scores)} rondas encontradas:")
                print(f"   {'Fecha':<12} {'Club':<25} {'Score':<8} {'Diferencial':<12}")
                print(f"   {'-'*70}")

                for score in scores[:10]:  # Mostrar últimas 10 rondas
                    fecha = score.get('fecha', '')[:10]
                    club = score.get('club', '')[:24]
                    score_val = score.get('score', '')
                    diff = score.get('diferencial', '')
                    print(f"   {fecha:<12} {club:<25} {score_val:<8} {diff:<12}")
            else:
                print(f"   ⚠️  No se encontraron rondas")
        else:
            print(f"   ❌ No se pudo obtener información del jugador")


if __name__ == "__main__":
    # Consultar primeros 5 jugadores
    consultar_rondas_recientes(num_jugadores=5)

    print("\n" + "="*80)
    print("💡 Para consultar todos los jugadores, edita el parámetro num_jugadores")
    print("="*80)
