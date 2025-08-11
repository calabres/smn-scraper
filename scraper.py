import requests
import json
import re
from datetime import datetime

def crear_geojson_smn():
    """
    Se conecta al link de OpenData del SMN con la fecha actual, 
    busca los datos de San Fernando y los guarda en un archivo GeoJSON.
    """
    # --- 1. CONFIGURACIÓN (con fecha dinámica) ---
    # La fecha se insertará automáticamente
    URL_TEMPLATE = "https://ssl.smn.gob.ar/dpd/descarga_opendata.php?file=observaciones/tiepre{date}.txt"
    ESTACION_OBJETIVO = "San Fernando"
    COORDENADAS = [-58.56, -34.44] # Longitud, Latitud
    OUTPUT_FILENAME = "san_fernando_weather.geojson"

    # Genera la fecha actual en el formato YYYYMMDD que necesita la URL
    fecha_actual_str = datetime.now().strftime('%Y%m%d')
    url_smn = URL_TEMPLATE.format(date=fecha_actual_str)
    
    # Cabecera para simular ser un navegador
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': 'https://www.smn.gob.ar/' # Añadimos Referer por si acaso
    }

    # --- 2. OBTENCIÓN DE DATOS ---
    print(f"Descargando datos desde: {url_smn}")
    try:
        respuesta = requests.get(url_smn, headers=headers)
        respuesta.raise_for_status()
        # Usamos latin-1 que es el encoding correcto para este archivo
        datos_texto = respuesta.content.decode('latin-1')
    except requests.exceptions.RequestException as e:
        print(f"❌ Error al conectar con la URL del SMN: {e}")
        return

    # --- 3. BÚSQUEDA Y PROCESAMIENTO ---
    linea_encontrada = None
    for linea in datos_texto.strip().split('\n'):
        if linea.strip().startswith(ESTACION_OBJETIVO):
            linea_encontrada = linea.strip()
            print(f"✅ Línea encontrada: {linea_encontrada}")
            break

    if not linea_encontrada:
        print(f"No se encontró la estación '{ESTACION_OBJETIVO}' en el archivo de hoy.")
        return

    # --- 4. EXTRACCIÓN Y CONSTRUCCIÓN DEL GEOJSON ---
    try:
        partes = [p.strip() for p in linea_encontrada.split(';')]
        viento_texto = partes[8]
        
        if viento_texto.lower() == 'calma':
            direccion_viento = 'Calma'
            velocidad_viento_kmh = 0
        else:
            viento_partes = viento_texto.rsplit(' ', 1)
            direccion_viento = viento_partes[0].strip()
            velocidad_viento_kmh = int(viento_partes[1])

        propiedades = {
            "estacion": partes[0], "fecha": partes[1], "hora": partes[2],
            "cielo": partes[3], "visibilidad_km": partes[4],
            "temperatura_c": float(partes[5]), "humedad_porc": int(partes[7]),
            "direccion_viento": direccion_viento, "velocidad_viento_kmh": velocidad_viento_kmh,
            "presion_hpa": float(re.findall(r"[\d\.]+", partes[9])[0])
        }

        geojson_resultado = {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": COORDENADAS},
                "properties": propiedades
            }]
        }
        
        # --- 5. GUARDAR EN ARCHIVO ---
        with open(OUTPUT_FILENAME, 'w', encoding='utf-8') as f:
            json.dump(geojson_resultado, f, indent=2, ensure_ascii=False)
        print(f"✅ Archivo '{OUTPUT_FILENAME}' guardado con éxito.")

    except (ValueError, IndexError) as e:
        print(f"❌ Error al procesar los datos de la línea '{linea_encontrada}': {e}")

# --- EJECUCIÓN ---
if __name__ == "__main__":
    crear_geojson_smn()
