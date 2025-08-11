import requests
import re
import json
from datetime import datetime

# --- Constantes ---
DATA_URL_TEMPLATE = "https://ssl.smn.gob.ar/dpd/descarga_opendata.php?file=observaciones/tiepre{date}.txt"
TARGET_CITY = "San Fernando"
OUTPUT_FILENAME = 'san_fernando_weather.geojson'

def fetch_and_process_data():
    """
    Descarga los datos del SMN, busca San Fernando y genera un GeoJSON.
    """
    current_date_str = datetime.now().strftime('%Y%m%d')
    data_url = DATA_URL_TEMPLATE.format(date=current_date_str)
    
    # --- INICIO DE LA CORRECCIÓN FINAL ---
    # Añadimos un set de headers completo para simular un navegador real,
    # incluyendo el importante 'Referer'.
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'es-ES,es;q=0.9',
        'Referer': 'https://www.smn.gob.ar/' # Le decimos al servidor que venimos de su página principal.
    }
    # --- FIN DE LA CORRECCIÓN FINAL ---
    
    print(f"Descargando datos desde: {data_url}")
    
    try:
        # Hacemos la petición incluyendo el set completo de headers
        response = requests.get(data_url, headers=headers)
        response.raise_for_status()
        
        text_data = response.content.decode('latin-1')
        
        print("Datos descargados. Buscando la línea de San Fernando...")
        
        for line in text_data.splitlines():
            if line.startswith(TARGET_CITY):
                print(f"✅ Línea encontrada: {line}")
                
                parts = [p.strip() for p in line.split(';')]
                
                fecha_str = parts[1]
                hora_str = parts[2]
                viento_full = parts[8]
                
                viento_match = re.match(r'^(.*)\s+(\d+)$', viento_full)
                if viento_match:
                    direccion_viento = viento_match.group(1).strip()
                    velocidad_viento = int(viento_match.group(2))
                else:
                    direccion_viento = viento_full
                    velocidad_viento = 0
                
                geojson_feature = {
                    "type": "FeatureCollection",
                    "features": [
                        {
                            "type": "Feature",
                            "geometry": None,
                            "properties": {
                                "localidad": parts[0],
                                "fecha": fecha_str,
                                "hora": hora_str,
                                "velocidad_viento_kmh": velocidad_viento,
                                "direccion_viento": direccion_viento
                            }
                        }
                    ]
                }
                
                with open(OUTPUT_FILENAME, 'w', encoding='utf-8') as f:
                    json.dump(geojson_feature, f, ensure_ascii=False, indent=4)
                
                print(f"Archivo '{OUTPUT_FILENAME}' creado/actualizado con éxito.")
                return
        
        print(f"❌ No se encontró la línea para '{TARGET_CITY}' en el archivo de datos.")

    except requests.exceptions.RequestException as e:
        print(f"❌ Error al descargar el archivo de datos: {e}")
    except Exception as e:
        print(f"❌ Ocurrió un error inesperado al procesar los datos: {e}")

if __name__ == "__main__":
    fetch_and_process_data()
