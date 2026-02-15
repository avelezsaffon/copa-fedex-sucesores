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
        self.ajax_url = f"{self.base_url}/wp-admin/admin-ajax.php"
        self.api_url = "https://servicios.federacioncolombianadegolf.com/apex"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': '*/*',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'X-Requested-With': 'XMLHttpRequest'
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
            # Datos para AJAX (FormData format)
            data = {
                'action': 'envio_salesforce',
                'type': 'field_value',
                'tipo_busqueda': 'nom',
                'termino_busqueda': name
            }

            response = self.session.post(
                self.ajax_url,
                data=data,
                timeout=10
            )

            if response.status_code != 200:
                print(f"Error: Status code {response.status_code}")
                return []

            # La respuesta es JSON
            try:
                result = response.json()
                if result.get('success') and result.get('data'):
                    busqueda_result = result['data'].get('BusquedaResult', [])

                    players = []
                    for item in busqueda_result:
                        if item.get('Persona'):
                            persona = item['Persona']
                            player = {
                                'codigo': persona.get('CodigoJugador__c', ''),
                                'nombre': persona.get('FirstName', ''),
                                'apellido': persona.get('LastName', ''),
                                'categoria': persona.get('Category__c', ''),
                                'indice': persona.get('Index__c', ''),
                                'salesforce_id': persona.get('Id', ''),
                                'email': persona.get('Email', ''),
                                'club': persona.get('Club__c', '')
                            }
                            players.append(player)

                    return players
            except json.JSONDecodeError:
                print(f"Error: La respuesta no es JSON válido")
                return []

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
            # Datos para AJAX
            data = {
                'action': 'envio_salesforce',
                'type': 'field_value',
                'tipo_busqueda': 'cod',
                'termino_busqueda': code
            }

            response = self.session.post(
                self.ajax_url,
                data=data,
                timeout=10
            )

            if response.status_code != 200:
                return None

            # La respuesta es JSON
            try:
                result = response.json()
                if result.get('success') and result.get('data'):
                    busqueda_result = result['data'].get('BusquedaResult', [])

                    if busqueda_result and len(busqueda_result) > 0:
                        item = busqueda_result[0]
                        if item.get('Persona'):
                            persona = item['Persona']
                            return {
                                'codigo': persona.get('CodigoJugador__c', ''),
                                'nombre': persona.get('FirstName', ''),
                                'apellido': persona.get('LastName', ''),
                                'categoria': persona.get('Category__c', ''),
                                'indice': persona.get('Index__c', ''),
                                'salesforce_id': persona.get('Id', ''),
                                'email': persona.get('Email', ''),
                                'club': persona.get('Club__c', '')
                            }

                return None
            except json.JSONDecodeError:
                print(f"Error: La respuesta no es JSON válido")
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

                # Buscar la tabla correcta (la que tiene el header específico)
                scores = []
                tables = soup.find_all('table')

                for table in tables:
                    rows = table.find_all('tr')
                    if len(rows) < 2:
                        continue

                    # Verificar si es la tabla de scores (tiene el header correcto)
                    header_row = rows[0]
                    headers = [th.text.strip() for th in header_row.find_all(['th', 'td'])]

                    # La tabla correcta tiene estos headers
                    if 'FECHAS DE JUEGO' in headers and 'SCORES GROSS/AJUST' in headers:
                        # Procesar las filas de datos
                        for row in rows[1:]:  # Saltar header
                            cols = row.find_all('td')
                            if len(cols) >= 8:
                                # Columnas: TARJETA, FECHA, CLUB, CANCHA, MARCA, PATRONES, SCORES, DIFERENCIAL
                                score = {
                                    'fecha': cols[1].text.strip(),
                                    'club': cols[2].text.strip(),
                                    'cancha': cols[3].text.strip(),
                                    'marca': cols[4].text.strip(),
                                    'patrones': cols[5].text.strip(),  # CMP/CUR/PAR
                                    'scores': cols[6].text.strip(),    # GROSS/AJUST
                                    'diferencial': cols[7].text.strip()
                                }
                                scores.append(score)
                        break  # Ya encontramos la tabla correcta

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
