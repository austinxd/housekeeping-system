"""
Forecast PDF Parser Service.
Extrae datos de forecast desde PDFs de Protel.
"""
import re
from datetime import datetime, date
from typing import Dict, List, Any, Optional
import pdfplumber


class ForecastPDFParser:
    """
    Parsea PDFs de forecast de ocupación hotelera.
    Extrae: fechas, salidas (departures), llegadas (arrivals), ocupadas (occupied).
    """

    # Meses en español y francés
    MONTHS = {
        'enero': 1, 'janvier': 1, 'january': 1, 'jan': 1, 'ene': 1,
        'febrero': 2, 'février': 2, 'february': 2, 'feb': 2, 'fév': 2,
        'marzo': 3, 'mars': 3, 'march': 3, 'mar': 3,
        'abril': 4, 'avril': 4, 'april': 4, 'abr': 4, 'avr': 4, 'apr': 4,
        'mayo': 5, 'mai': 5, 'may': 5,
        'junio': 6, 'juin': 6, 'june': 6, 'jun': 6,
        'julio': 7, 'juillet': 7, 'july': 7, 'jul': 7,
        'agosto': 8, 'août': 8, 'august': 8, 'ago': 8, 'aug': 8,
        'septiembre': 9, 'septembre': 9, 'september': 9, 'sep': 9, 'sept': 9,
        'octubre': 10, 'octobre': 10, 'october': 10, 'oct': 10,
        'noviembre': 11, 'novembre': 11, 'november': 11, 'nov': 11,
        'diciembre': 12, 'décembre': 12, 'december': 12, 'dic': 12, 'déc': 12, 'dec': 12,
    }

    def __init__(self):
        self.year = datetime.now().year

    def parse_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        Parsea un PDF de forecast y extrae los datos.

        Args:
            pdf_path: Ruta al archivo PDF

        Returns:
            Dict con week_start y forecast data
        """
        with pdfplumber.open(pdf_path) as pdf:
            full_text = ""
            tables = []

            for page in pdf.pages:
                text = page.extract_text() or ""
                full_text += text + "\n"

                # Extraer tablas
                page_tables = page.extract_tables()
                if page_tables:
                    tables.extend(page_tables)

        # Intentar parsear el texto primero (más confiable para este formato)
        result = self._parse_text(full_text)
        if result and result.get('forecast') and len(result.get('forecast', [])) >= 7:
            return result

        # Si el texto no funcionó, intentar extraer de tablas
        if tables:
            result = self._parse_tables(tables, full_text)
            if result and result.get('forecast'):
                return result

        # Último intento: texto
        return self._parse_text(full_text)

    def _parse_tables(self, tables: List, full_text: str) -> Optional[Dict[str, Any]]:
        """Extrae datos de las tablas del PDF."""
        forecast_data = []

        for table in tables:
            if not table or len(table) < 2:
                continue

            # Buscar las filas de encabezados (pueden ser 1 o 2 filas)
            # La tabla típica tiene:
            # Fila 0: ['DATE', 'CHAMBRES', ..., 'ARRIVÉES', ..., 'DÉPARTS', ...]
            # Fila 1: ['', 'Libres', '%', 'Occupées', '%', '%', '#', 'Pers.', '#', 'Pers.', ...]
            header_rows = []
            data_start_idx = 0

            for i, row in enumerate(table):
                if not row:
                    continue
                row_text = ' '.join(str(c).lower() for c in row if c)

                # Si tiene palabras clave de encabezado, es fila de encabezado
                if any(kw in row_text for kw in ['date', 'chambre', 'arriv', 'départ', 'occup', 'libres', 'pers']):
                    header_rows.append(row)
                    data_start_idx = i + 1
                else:
                    # Primera fila sin palabras clave = inicio de datos
                    break

            # Combinar información de encabezados para mapear columnas
            col_map = self._map_columns_multi(header_rows)

            # Procesar filas de datos
            for row in table[data_start_idx:]:
                if not row:
                    continue

                cells = [str(cell).strip() if cell else "" for cell in row]
                day_data = self._extract_row_data_mapped(cells, col_map)
                if day_data:
                    forecast_data.append(day_data)

        if forecast_data:
            # Ordenar por fecha
            forecast_data.sort(key=lambda x: x['date'])

            # Determinar week_start (primer lunes)
            first_date = forecast_data[0]['date']
            week_start = self._get_monday(first_date)

            return {
                'week_start': week_start.isoformat(),
                'forecast': [
                    {
                        'departures': d['departures'],
                        'arrivals': d['arrivals'],
                        'occupied': d['occupied'],
                    }
                    for d in forecast_data
                ],
                'raw_data': forecast_data,
            }

        return None

    def _map_columns_multi(self, header_rows: List[List]) -> Dict[str, int]:
        """Mapea las columnas combinando múltiples filas de encabezado."""
        col_map = {
            'date': 0,
            'occupied': None,
            'arrivals': None,
            'departures': None,
        }

        if not header_rows:
            return col_map

        # Estructura conocida del PDF de Protel:
        # Fila 0: ['DATE', 'CHAMBRES', None, None, None, 'LITS', 'ARRIVÉES', None, 'DÉPARTS', None, 'PRÉSENTS', ...]
        # Fila 1: ['', 'Libres', '%', 'Occupées', '%', '%', '#', 'Pers.', '#', 'Pers.', '#', 'Pers.', ...]
        #
        # Índices de datos:
        # - Occupées = índice 3
        # - Arrivées # = índice 6 (bajo 'ARRIVÉES')
        # - Départs # = índice 8 (bajo 'DÉPARTS')

        # Buscar en fila 0: posición de ARRIVÉES y DÉPARTS
        arrivals_group_idx = None
        departures_group_idx = None

        for row in header_rows:
            for i, cell in enumerate(row):
                cell_lower = str(cell).lower() if cell else ""

                if 'arriv' in cell_lower and arrivals_group_idx is None:
                    arrivals_group_idx = i
                if ('départ' in cell_lower or 'depart' in cell_lower) and departures_group_idx is None:
                    departures_group_idx = i
                # Buscar 'Occupées' en la segunda fila de encabezado
                if 'occup' in cell_lower and col_map['occupied'] is None:
                    col_map['occupied'] = i

        # Si encontramos los grupos, el # está en la primera columna del grupo
        if arrivals_group_idx is not None:
            col_map['arrivals'] = arrivals_group_idx
        if departures_group_idx is not None:
            col_map['departures'] = departures_group_idx

        return col_map

    def _map_columns(self, header_row: List) -> Dict[str, int]:
        """Mapea las columnas del encabezado a sus índices (método legacy)."""
        return self._map_columns_multi([header_row] if header_row else [])

    def _extract_row_data_mapped(self, cells: List[str], col_map: Dict[str, int]) -> Optional[Dict[str, Any]]:
        """Extrae datos de una fila usando el mapeo de columnas."""
        if not cells:
            return None

        # Buscar fecha en la primera celda
        date_found = self._parse_date(cells[0]) if cells else None

        if not date_found:
            return None

        # Extraer valores usando el mapeo de columnas
        def get_first_number(cell_idx):
            """Obtiene el primer número de una celda."""
            if cell_idx is None or cell_idx >= len(cells):
                return 0
            nums = re.findall(r'\d+', cells[cell_idx])
            return int(nums[0]) if nums else 0

        # Si no tenemos mapeo, usar heurística basada en la estructura conocida del PDF
        # Estructura: DATE | Libres | % | Occupées | % | % | #Arr | Pers | #Dep | Pers | #Pres | Pers | ...
        # Índices:      0  |   1    | 2 |    3     | 4 | 5 |  6   |  7   |  8   |  9   |  10   |  11  | ...

        occupied = 0
        arrivals = 0
        departures = 0

        if col_map['occupied'] is not None:
            occupied = get_first_number(col_map['occupied'])
        if col_map['arrivals'] is not None:
            arrivals = get_first_number(col_map['arrivals'])
        if col_map['departures'] is not None:
            departures = get_first_number(col_map['departures'])

        # Si no se mapearon columnas, usar posiciones fijas basadas en estructura estándar
        if occupied == 0 and arrivals == 0 and departures == 0:
            # Estructura típica del PDF:
            # [0]=fecha, [1]=libres, [2]=%, [3]=occupées, [4]=%, [5]=%, [6]=arr#, [7]=arrPers, [8]=dep#, [9]=depPers, [10]=pres#
            if len(cells) >= 11:
                occupied = get_first_number(3)   # Occupées
                arrivals = get_first_number(6)   # Arrivées #
                departures = get_first_number(8) # Départs #

        # Validar que tenemos datos razonables
        if occupied == 0 and arrivals == 0 and departures == 0:
            return None

        return {
            'date': date_found,
            'departures': departures,
            'arrivals': arrivals,
            'occupied': occupied,
        }

    def _extract_row_data(self, cells: List[str]) -> Optional[Dict[str, Any]]:
        """Extrae datos de una fila de tabla (método legacy)."""
        # Usar el nuevo método con mapeo vacío
        return self._extract_row_data_mapped(cells, {
            'date': 0,
            'occupied': None,
            'arrivals': None,
            'departures': None,
        })

    def _parse_text(self, text: str) -> Dict[str, Any]:
        """Parsea el texto del PDF para extraer datos."""
        lines = text.split('\n')
        forecast_data = []

        # Patrón para líneas con datos de Protel/hotel
        # Formato: "lun., 12.01.2026 15 34,88 28 65,12 33,75 3 6 3 6 28 54 ..."
        # Días de la semana en francés/español
        day_names = r'(?:lun|mar|mer|jeu|ven|sam|dim|mi[eé]|s[aá]b|dom)\.'

        for line in lines:
            # Buscar líneas que empiecen con día de la semana
            if not re.match(day_names, line.lower().strip()):
                continue

            # Extraer fecha (formato: dd.mm.yyyy o dd/mm/yyyy)
            date_match = re.search(r'(\d{1,2})[./](\d{1,2})[./](\d{4})', line)
            if not date_match:
                continue

            try:
                day = int(date_match.group(1))
                month = int(date_match.group(2))
                year = int(date_match.group(3))
                row_date = date(year, month, day)
            except ValueError:
                continue

            # Remover la fecha del texto para facilitar extracción
            line_without_date = line[date_match.end():]

            # Extraer números separados por espacios (no decimales)
            # Los valores enteros están separados por espacios, los decimales por coma o punto
            # Primero normalizar: reemplazar comas decimales por puntos
            clean_line = re.sub(r'(\d),(\d)', r'\1.\2', line_without_date)

            # Separar por espacios y extraer números
            parts = clean_line.split()
            numbers = []
            for part in parts:
                # Si es un número entero (sin punto decimal), agregarlo
                if re.match(r'^\d+$', part):
                    num = int(part)
                    if num < 1000:  # Filtrar números financieros grandes
                        numbers.append(num)
                # Si es decimal, ignorarlo (porcentajes)

            # Estructura esperada:
            # libres, occupée, arr#, arrPers, dep#, depPers, pres#, presPers
            # Índices: 0=libres, 1=occupée, 2=arr#, 3=arrPers, 4=dep#, 5=depPers, 6=pres#, 7=presPers

            if len(numbers) >= 8:
                arrivals = numbers[2]    # Arrivées #
                departures = numbers[4]  # Départs #
                occupied = numbers[6]    # Présents # (habitaciones ocupadas)

                forecast_data.append({
                    'date': row_date,
                    'departures': departures,
                    'arrivals': arrivals,
                    'occupied': occupied,
                })

        if forecast_data:
            # Ordenar y determinar week_start
            forecast_data.sort(key=lambda x: x['date'])
            first_date = forecast_data[0]['date']
            week_start = self._get_monday(first_date)

            return {
                'week_start': week_start.isoformat(),
                'forecast': [
                    {
                        'departures': d['departures'],
                        'arrivals': d['arrivals'],
                        'occupied': d['occupied'],
                    }
                    for d in forecast_data[:7]  # Solo 7 días
                ],
                'raw_data': forecast_data[:7],
            }

        return {'error': 'No se pudieron extraer datos del PDF'}

    def _parse_date(self, text: str) -> Optional[date]:
        """Intenta parsear una fecha del texto."""
        if not text:
            return None

        original_text = text
        text = text.lower().strip()

        # Primero intentar formato: "Lun 12/01" o "Mar 13/01" (día_semana + día/mes)
        # Esto es común en reportes hoteleros
        day_name_pattern = r'^(?:lun|mar|mi[eé]|jue|vie|s[aá]b|dom|mon|tue|wed|thu|fri|sat|sun)\s+'
        if re.match(day_name_pattern, text, re.IGNORECASE):
            # Remover el nombre del día para evitar confusión con meses
            text_without_dayname = re.sub(day_name_pattern, '', text, flags=re.IGNORECASE)
            # Ahora parsear día/mes
            match = re.search(r'(\d{1,2})[/\-](\d{1,2})(?:[/\-](\d{2,4}))?', text_without_dayname)
            if match:
                day = int(match.group(1))
                month = int(match.group(2))
                year = int(match.group(3)) if match.group(3) else self.year
                if year < 100:
                    year += 2000
                try:
                    return date(year, month, day)
                except ValueError:
                    pass

        # Formato: "12/01/2026" o "12-01-2026" (sin nombre de día)
        match = re.search(r'(\d{1,2})[/\-](\d{1,2})(?:[/\-](\d{2,4}))?', text)
        if match:
            day = int(match.group(1))
            month = int(match.group(2))
            year = int(match.group(3)) if match.group(3) else self.year
            if year < 100:
                year += 2000
            try:
                return date(year, month, day)
            except ValueError:
                pass

        # Formato: "12 enero" o "12 jan" (día + nombre de mes)
        for month_name, month_num in self.MONTHS.items():
            # Solo buscar si el nombre del mes aparece como palabra completa
            if re.search(r'\b' + month_name + r'\b', text):
                day_match = re.search(r'(\d{1,2})', text)
                if day_match:
                    day = int(day_match.group(1))
                    try:
                        return date(self.year, month_num, day)
                    except ValueError:
                        pass

        return None

    def _build_date(self, day: int, month: int = None) -> date:
        """Construye una fecha a partir del día."""
        if month is None:
            month = datetime.now().month
        return date(self.year, month, day)

    def _get_monday(self, d: date) -> date:
        """Obtiene el lunes de la semana de la fecha dada."""
        return d - __import__('datetime').timedelta(days=d.weekday())
