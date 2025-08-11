import time
import csv
import requests
from datetime import datetime, timedelta
import undetected_chromedriver as uc
import json

# --- Constantes del script ---
URL_SMN = "https://www.smn.gob.ar/observaciones"
LOCATION_ID = 4750
API_URL_TARGET = f"https://ws1.smn.gob.ar/v1/history/weather/location/{LOCATION_ID}"
NOMBRE_ARCHIVO_CSV = 'ultimo_registro_smn.csv'

def main():
    """Función principal que ejecuta todo el proceso de scraping."""
    print("Iniciando navegador en modo invisible (headless)...")
    
    options = uc.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

    # Forzamos la v138 para que coincida con el navegador de GitHub Actions
    driver = uc.Chrome(options=options, version_main=138)
    
    token = None
    try:
        print(f"Navegando a {URL_SMN}...")
        driver.get(URL_SMN)
        print("Página cargada. Esperando 25 segundos...")
        time.sleep(25)
        
        print("Analizando logs de red para buscar el token...")
        logs = driver.get_log('performance')
        for log in logs:
            message = json.loads(log['message'])['message']
            if message['method'] == 'Network.requestWillBeSent':
                headers = message['params']['request'].get('headers', {})
                if 'Authorization' in headers and 'JWT' in headers['Authorization']:
                    token = headers['Authorization'].split('JWT ')[1]
                    break
        
        if token:
            print("✅ Token obtenido con éxito.")
        else:
            print("❌ No se pudo encontrar el token en los logs. Probablemente la página de seguridad bloqueó la carga.")
            # Imprimimos el título para confirmar si nos quedamos en la página de bloqueo
            print(f"Título final de la página: '{driver.title}'")
            return # Salimos si no hay token
    finally:
        print("Cerrando el navegador.")
        driver.quit()

    if not token:
        return

    # --- Parte 2: Usar el token para pedir los datos y guardar el CSV ---
    print("\nUsando el token para pedir los últimos registros...")
    headers = {'Authorization': f'JWT {token}'}
    params = {
        'start': (datetime.now() - timedelta(days=1)).astimezone().isoformat(),
        'end': datetime.now().astimezone().isoformat()
    }

    try:
        response = requests.get(API_URL_TARGET, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        
        if data.get('list'):
            ultimo_registro = data['list'][-1]
            with open(NOMBRE_ARCHIVO_CSV, 'w', newline='', encoding='utf-8') as f:
                escritor_csv = csv.writer(f)
                escritor_csv.writerow(['fecha', 'hora', 'temperatura_C', 'sensacion_termica', 'humedad', 'presion', 'visibilidad_km', 'descripcion_clima', 'viento_direccion', 'viento_velocidad_kmh', 'viento_deg'])
                fecha_hora_obj = datetime.fromisoformat(ultimo_registro['date'])
                escritor_csv.writerow([
                    fecha_hora_obj.strftime('%Y-%m-%d'), fecha_hora_obj.strftime('%H:%M:%S'),
                    ultimo_registro.get('temperature'), ultimo_registro.get('feels_like'),
                    ultimo_registro.get('humidity'), ultimo_registro.get('pressure'),
                    ultimo_registro.get('visibility'), ultimo_registro.get('weather', {}).get('description'),
                    ultimo_registro.get('wind', {}).get('direction'), ultimo_registro.get('wind', {}).get('speed'),
                    ultimo_registro.get('wind', {}).get('deg')
                ])
            print(f"\n✅ ¡Éxito! Archivo '{NOMBRE_ARCHIVO_CSV}' creado.")
        else:
            print("❌ La respuesta de la API no contenía una lista de registros.")
    except Exception as e:
        print(f"❌ Ocurrió un error al obtener o guardar los datos: {e}")

if __name__ == "__main__":
    main()
