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
                                'categoria': persona.get('Categoria__c', ''),
                                'indice': persona.get('Indice__c', ''),
                                'salesforce_id': persona.get('Id', ''),
                                'email': persona.get('Email', ''),
                                'club': persona.get('FCG_Club_Federado__c', '')
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
                                'categoria': persona.get('Categoria__c', ''),
                                'indice': persona.get('Indice__c', ''),
                                'salesforce_id': persona.get('Id', ''),
                                'email': persona.get('Email', ''),
                                'club': persona.get('FCG_Club_Federado__c', '')
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
            Lista de scores con tarjeta_id incluido
        """
        try:
            # URL del endpoint de histórico
            scores_url = f"{self.api_url}/HistorialJuegoResultadoPp"

            params = {'user': user_id}

            response = self.session.get(
                scores_url,
                params=params,
                timeout=15
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
                                # Extraer tarjeta_id del link en la primera columna
                                tarjeta_id = None
                                link = cols[0].find('a')
                                if link and link.get('href'):
                                    href = link['href']
                                    # Formato: /apex/TarjetaJuegoWebPp?id=a16Ua000006pE3tIAE
                                    if 'id=' in href:
                                        tarjeta_id = href.split('id=')[-1]

                                # Columnas: TARJETA, FECHA, CLUB, CANCHA, MARCA, PATRONES, SCORES, DIFERENCIAL
                                score = {
                                    'tarjeta_id': tarjeta_id,
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

    def get_scorecard_detail(self, tarjeta_id: str) -> Optional[Dict]:
        """
        Obtiene el detalle hoyo por hoyo de una tarjeta.

        Args:
            tarjeta_id: ID de la tarjeta en Salesforce

        Returns:
            Diccionario con datos hoyo por hoyo
        """
        try:
            url = f"{self.api_url}/TarjetaJuegoWebPp"
            params = {'id': tarjeta_id}

            response = self.session.get(url, params=params, timeout=15)

            if response.status_code != 200:
                return None

            soup = BeautifulSoup(response.content, 'html.parser')
            tables = soup.find_all('table')

            if len(tables) < 2:
                return None

            # Extraer datos del header (primera tabla): handicap, indice, marca, etc.
            header_info = {}
            header_table = tables[0]
            header_text = header_table.get_text(separator='\n', strip=True)
            lines = header_text.split('\n')
            for i, line in enumerate(lines):
                line = line.strip()
                # El valor puede estar después del ':' o en la línea siguiente
                if 'ndicap:' in line:
                    val = line.split(':')[-1].strip()
                    if not val and i + 1 < len(lines):
                        val = lines[i + 1].strip()
                    try:
                        header_info['handicap_cancha'] = int(val)
                    except (ValueError, IndexError):
                        pass
                elif line.startswith('Indice:'):
                    val = line.split(':')[-1].strip()
                    if not val and i + 1 < len(lines):
                        val = lines[i + 1].strip()
                    try:
                        header_info['indice_al_momento'] = float(val)
                    except (ValueError, IndexError):
                        pass
                elif line.startswith('Marca:'):
                    val = line.split(':')[-1].strip()
                    if not val and i + 1 < len(lines):
                        val = lines[i + 1].strip()
                    header_info['marca'] = val

            # La tabla del scorecard tiene filas: HOYO, PAR, VENTAJA, SCORE, AJUSTADO
            scorecard_table = None
            for table in tables:
                rows = table.find_all('tr')
                if len(rows) >= 4:
                    first_cells = [td.text.strip() for td in rows[0].find_all(['th', 'td'])]
                    # La primera fila debe tener los números de hoyo
                    if any('1' == c for c in first_cells[:5]):
                        scorecard_table = table
                        break
                    # O puede tener "HOYO" como header
                    header_text = ' '.join(first_cells).upper()
                    if 'HOYO' in header_text or '1' in first_cells:
                        scorecard_table = table
                        break

            if not scorecard_table:
                return None

            rows = scorecard_table.find_all('tr')
            if len(rows) < 4:
                return None

            def parse_row(row):
                return [td.text.strip() for td in row.find_all(['th', 'td'])]

            row_data = [parse_row(r) for r in rows]

            # Identificar rows por su first cell
            hoyos = {}
            for rd in row_data:
                if not rd:
                    continue
                label = rd[0].upper().strip()
                values = rd[1:]
                if 'HOYO' in label or label == '':
                    hoyos['hoyo'] = values
                elif 'PAR' in label:
                    hoyos['par'] = values
                elif 'VENTAJA' in label or 'HCP' in label:
                    hoyos['ventaja'] = values
                elif 'SCORE' == label or 'SCORE' in label and 'AJUST' not in label:
                    hoyos['score'] = values
                elif 'AJUST' in label:
                    hoyos['ajustado'] = values

            if 'score' not in hoyos:
                # Try another approach: rows in order are typically HOYO, PAR, VENTAJA, SCORE, AJUSTADO
                if len(row_data) >= 5:
                    hoyos = {
                        'hoyo': row_data[0][1:],
                        'par': row_data[1][1:],
                        'ventaja': row_data[2][1:],
                        'score': row_data[3][1:],
                        'ajustado': row_data[4][1:],
                    }

            if 'score' not in hoyos:
                return None

            # Parse into structured hole-by-hole data
            result = {'hoyos': [], 'out': {}, 'in': {}, 'total': {}}
            result.update(header_info)

            score_vals = hoyos.get('score', [])
            par_vals = hoyos.get('par', [])
            ventaja_vals = hoyos.get('ventaja', [])
            ajustado_vals = hoyos.get('ajustado', [])

            for i in range(min(len(score_vals), 22)):
                val = score_vals[i].strip()
                par_val = par_vals[i].strip() if i < len(par_vals) else ''
                vent_val = ventaja_vals[i].strip() if i < len(ventaja_vals) else ''
                aj_val = ajustado_vals[i].strip() if i < len(ajustado_vals) else ''

                # Positions: 0-8 = holes 1-9, 9 = OUT, 10-17 = holes 10-17, 18 = hole 18?
                # Actually: 0-8 = holes 1-9, 9 = OUT, 10-17 = holes 10-17, 18 = IN, 19 = TOTAL
                # Or: 0-8 = holes 1-9, 9 = OUT, 10-18 = holes 10-18, 19 = IN, 20 = TOTAL

                hoyo_num = None
                hoyo_labels = hoyos.get('hoyo', [])
                if i < len(hoyo_labels):
                    lbl = hoyo_labels[i].strip().upper()
                    if lbl == 'OUT':
                        result['out'] = {'par': par_val, 'score': val, 'ajustado': aj_val}
                        continue
                    elif lbl == 'IN':
                        result['in'] = {'par': par_val, 'score': val, 'ajustado': aj_val}
                        continue
                    elif lbl == 'TOTAL':
                        result['total'] = {'par': par_val, 'score': val, 'ajustado': aj_val}
                        continue
                    else:
                        try:
                            hoyo_num = int(lbl)
                        except ValueError:
                            continue

                if hoyo_num:
                    result['hoyos'].append({
                        'hoyo': hoyo_num,
                        'par': int(par_val) if par_val.isdigit() else None,
                        'ventaja': int(vent_val) if vent_val.isdigit() else None,
                        'score': int(val) if val.isdigit() else None,
                        'ajustado': int(aj_val) if aj_val.isdigit() else None,
                    })

            return result

        except Exception as e:
            print(f"Error obteniendo detalle de tarjeta: {str(e)}")
            return None

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
