"""
Script para extraer scores y buscar jugadores
de la Federación Colombiana de Golf
"""

import requests
import pandas as pd
import json
from datetime import datetime
from bs4 import BeautifulSoup
import time
from typing import List, Dict, Optional


class FedegolfScoresCollector:
    """
    Clase para interactuar con la base de datos de la
    Federación Colombiana de Golf
    """

    def __init__(self):
        self.base_url = "https://federacioncolombianadegolf.com"
        self.search_url = f"{self.base_url}/handicap/"
        self.api_url = "https://servicios.federacioncolombianadegolf.com/apex"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'
        })

    def search_player_by_name(self, name: str) -> List[Dict]:
        """
        Busca un jugador por nombre en la Federación

        Args:
            name: Nombre del jugador a buscar

        Returns:
            Lista de diccionarios con información del jugador
        """
        try:
            # Construir URL de búsqueda
            search_params = {
                'tipo_busqueda': 'nom',
                'termino_busqueda': name
            }

            response = self.session.get(
                self.search_url,
                params=search_params,
                timeout=10
            )

            if response.status_code != 200:
                print(f"Error: Status code {response.status_code}")
                return []

            # Parsear HTML
            soup = BeautifulSoup(response.content, 'html.parser')

            # Buscar tabla de resultados
            players = []
            table = soup.find('table')

            if table:
                rows = table.find_all('tr')[1:]  # Saltar header

                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 5:
                        player = {
                            'codigo': cols[0].text.strip(),
                            'nombre': cols[1].text.strip(),
                            'apellido': cols[2].text.strip(),
                            'categoria': cols[3].text.strip(),
                            'indice': cols[4].text.strip()
                        }
                        players.append(player)

            return players

        except Exception as e:
            print(f"Error en búsqueda de jugador: {str(e)}")
            return []

    def search_player_by_code(self, code: str) -> Optional[Dict]:
        """
        Busca un jugador por código

        Args:
            code: Código del jugador

        Returns:
            Diccionario con información del jugador
        """
        try:
            search_params = {
                'tipo_busqueda': 'cod',
                'termino_busqueda': code
            }

            response = self.session.get(
                self.search_url,
                params=search_params,
                timeout=10
            )

            if response.status_code != 200:
                return None

            soup = BeautifulSoup(response.content, 'html.parser')
            table = soup.find('table')

            if table:
                row = table.find('tr')
                if row:
                    cols = row.find_all('td')
                    if len(cols) >= 5:
                        return {
                            'codigo': cols[0].text.strip(),
                            'nombre': cols[1].text.strip(),
                            'apellido': cols[2].text.strip(),
                            'categoria': cols[3].text.strip(),
                            'indice': cols[4].text.strip()
                        }

            return None

        except Exception as e:
            print(f"Error en búsqueda por código: {str(e)}")
            return None

    def get_player_scores(self, user_id: str) -> List[Dict]:
        """
        Obtiene el histórico de scores de un jugador

        Args:
            user_id: ID del usuario en Salesforce

        Returns:
            Lista de scores
        """
        try:
            # URL del endpoint de histórico
            scores_url = f"{self.api_url}/HistorialJuegoResultadoPp"

            params = {'user': user_id}

            response = self.session.get(
                scores_url,
                params=params,
                timeout=10
            )

            if response.status_code == 200:
                # El contenido es HTML, parsearlo
                soup = BeautifulSoup(response.content, 'html.parser')

                # Buscar tabla de resultados
                scores = []
                table = soup.find('table')

                if table:
                    rows = table.find_all('tr')[1:]  # Saltar header

                    for row in rows:
                        cols = row.find_all('td')
                        if len(cols) >= 7:
                            score = {
                                'fecha': cols[1].text.strip(),
                                'club': cols[2].text.strip(),
                                'cancha': cols[3].text.strip(),
                                'marca': cols[4].text.strip(),
                                'score': cols[5].text.strip(),
                                'diferencial': cols[6].text.strip()
                            }
                            scores.append(score)

                return scores

            return []

        except Exception as e:
            print(f"Error obteniendo scores: {str(e)}")
            return []

    def save_to_csv(self, data: List[Dict], filename: str):
        """
        Guarda datos a un archivo CSV

        Args:
            data: Lista de diccionarios
            filename: Nombre del archivo
        """
        try:
            df = pd.DataFrame(data)
            df.to_csv(filename, index=False, encoding='utf-8')
            print(f"Datos guardados en {filename}")
        except Exception as e:
            print(f"Error guardando CSV: {str(e)}")
