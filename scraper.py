import requests
import re
import json
from datetime import datetime

# --- Constantes ---
# La URL ahora apunta al archivo de texto plano
DATA_URL_TEMPLATE = "https://ssl.smn.gob.ar/dpd/descarga_opendata.php?file=observaciones/tiepre{date}.txt"
TARGET_CITY = "San Fernando"
OUTPUT_FILENAME = 'san_fernando_weather.geojson'

def fetch_and_process_data():
    """
    Descarga los datos del SMN, busca San Fernando y genera un GeoJSON.
    """
    # Formatea la fecha actual para construir la URL dinámica (ej: 20250811)
    current_date_str = datetime.now().strftime('%Y%m%d')
    data_url = DATA_URL_TEMPLATE.format(date=current_date_str)
    
    print(f"Descargando datos desde: {data_url}")
    
    try:
        response = requests.get(data_url)
        response.raise_for_status() # Lanza un error si la descarga falla
        
        # El contenido del archivo de texto, decodificado correctamente
        text_data = response.content.decode('latin-1')
        
        print("Datos descargados. Buscando la línea de San Fernando...")
        
        # Itera sobre cada línea del texto
        for line in text_data.splitlines():
            if line.startswith(TARGET_CITY):
                print(f"✅ Línea encontrada: {line}")
                
                # Procesa la línea para extraer los datos
                parts = [p.strip() for p in line.split(';')]
                
                # Estructura del .txt:
                # 0:Localidad; 1:Fecha; 2:Hora; 3:Clima; ...; 8:Viento (Dirección y Velocidad)
                
                fecha_str = parts[1]
                hora_str = parts[2]
                viento_full = parts[8]
                
                # Extraemos la velocidad y dirección del viento
                # Usamos una expresión regular para manejar casos como "Norte  14" o "Calma"
                viento_match = re.match(r'^(.*)\s+(\d+)$', viento_full)
                if viento_match:
                    direccion_viento = viento_match.group(1).strip()
                    velocidad_viento = int(viento_match.group(2))
                else:
                    direccion_viento = viento_full # Si no hay match (ej: "Calma")
                    velocidad_viento = 0
                
                # Crea el objeto GeoJSON
                geojson_feature = {
                    "type": "FeatureCollection",
                    "features": [
                        {
                            "type": "Feature",
                            "geometry": None, # No tenemos coordenadas en este archivo
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
                
                # Guarda el archivo
                with open(OUTPUT_FILENAME, 'w', encoding='utf-8') as f:
                    json.dump(geojson_feature, f, ensure_ascii=False, indent=4)
                
                print(f"Archivo '{OUTPUT_FILENAME}' creado/actualizado con éxito.")
                return # Termina el script una vez que encuentra y procesa la línea
        
        print(f"❌ No se encontró la línea para '{TARGET_CITY}' en el archivo de datos.")

    except requests.exceptions.RequestException as e:
        print(f"❌ Error al descargar el archivo de datos: {e}")
    except Exception as e:
        print(f"❌ Ocurrió un error inesperado al procesar los datos: {e}")

if __name__ == "__main__":
    fetch_and_process_data()
