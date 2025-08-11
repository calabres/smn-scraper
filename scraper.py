import time
import os
import zipfile
import csv
import requests
from datetime import datetime, timedelta
import undetected_chromedriver as uc
import json

# --- Constantes ---
URL_SMN = "https://www.smn.gob.ar/observaciones"
LOCATION_ID = 4750  # ID para San Fernando
API_URL_TARGET = f"https://ws1.smn.gob.ar/v1/history/weather/location/{LOCATION_ID}"
OUTPUT_FILENAME = 'ultimo_registro_smn.csv'

def create_proxy_extension(host, port, user, password):
    """Helper para crear una extensión de Chrome que maneja el proxy con autenticación."""
    manifest_json = """
    {
        "version": "1.0.0", "manifest_version": 2, "name": "Chrome Proxy",
        "permissions": ["proxy", "tabs", "unlimitedStorage", "storage", "<all_urls>", "webRequest", "webRequestBlocking"],
        "background": { "scripts": ["background.js"] }, "minimum_chrome_version":"22.0.0"
    }
    """
    background_js = f"""
    var config = {{
        mode: "fixed_servers",
        rules: {{
            singleProxy: {{ scheme: "http", host: "{host}", port: parseInt({port}) }},
            bypassList: ["localhost"]
        }}
    }};
    chrome.proxy.settings.set({{value: config, scope: "regular"}}, function() {{}});
    function callbackFn(details) {{
        return {{ authCredentials: {{ username: "{user}", password: "{password}" }} }};
    }}
    chrome.webRequest.onAuthRequired.addListener(callbackFn, {{urls: ["<all_urls>"]}}, ['blocking']);
    """
    proxy_extension_zip = 'proxy_extension.zip'
    with zipfile.ZipFile(proxy_extension_zip, 'w') as zf:
        zf.writestr("manifest.json", manifest_json)
        zf.writestr("background.js", background_js)
    return proxy_extension_zip

def run_scraper_with_proxy():
    """Función principal que ejecuta todo el proceso de scraping."""
    
    # 1. OBTENER TOKEN USANDO EL NAVEGADOR A TRAVÉS DEL PROXY
    print("Iniciando el proceso de scraping a través de un proxy residencial...")
    proxy_host = os.environ.get("PROXY_HOST")
    proxy_port = os.environ.get("PROXY_PORT")
    proxy_user = os.environ.get("PROXY_USER")
    proxy_pass = os.environ.get("PROXY_PASS")

    if not all([proxy_host, proxy_port, proxy_user, proxy_pass]):
        print("❌ Error: Faltan las credenciales del proxy en los secretos de GitHub.")
        return

    proxy_extension_file = create_proxy_extension(proxy_host, proxy_port, proxy_user, proxy_pass)
    
    options = uc.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_extension(proxy_extension_file)
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

    driver = uc.Chrome(options=options, version_main=138)
    
    token = None
    try:
        print("Navegando al SMN a través del proxy...")
        driver.get(URL_SMN)
        print("Esperando 25 segundos para la carga completa...")
        time.sleep(25)

        print("Analizando los logs de red para encontrar el token...")
        logs = driver.get_log('performance')
        for log in logs:
            message = json.loads(log['message'])['message']
            if message['method'] == 'Network.requestWillBeSent':
                headers = message['params']['request'].get('headers', {})
                if 'Authorization' in headers and 'JWT' in headers['Authorization']:
                    token = headers['Authorization'].split('JWT ')[1]
                    break
        
        if token:
            print("✅ Token obtenido con éxito a través del proxy.")
        else:
            print("❌ No se pudo encontrar el token en los logs de red.")
            return # Salimos si no hay token
    finally:
        print("Cerrando el navegador.")
        driver.quit()

    if not token:
        print("\nFinalizando script. No se pudo obtener un token.")
        return

    # 2. USAR EL TOKEN PARA PEDIR LOS DATOS Y GUARDAR EL CSV
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
            
            with open(OUTPUT_FILENAME, 'w', newline='', encoding='utf-8') as archivo_csv:
                escritor_csv = csv.writer(archivo_csv)
                encabezado = [
                    'fecha', 'hora', 'temperatura_C', 'sensacion_termica', 'humedad', 'presion', 
                    'visibilidad_km', 'descripcion_clima', 'viento_direccion', 
                    'viento_velocidad_kmh', 'viento_deg'
                ]
                escritor_csv.writerow(encabezado)
                
                fecha_hora_obj = datetime.fromisoformat(ultimo_registro['date'])
                fila_datos = [
                    fecha_hora_obj.strftime('%Y-%m-%d'), fecha_hora_obj.strftime('%H:%M:%S'),
                    ultimo_registro.get('temperature'), ultimo_registro.get('feels_like'),
                    ultimo_registro.get('humidity'), ultimo_registro.get('pressure'),
                    ultimo_registro.get('visibility'), ultimo_registro.get('weather', {}).get('description'),
                    ultimo_registro.get('wind', {}).get('direction'), ultimo_registro.get('wind', {}).get('speed'),
                    ultimo_registro.get('wind', {}).get('deg')
                ]
                escritor_csv.writerow(fila_datos)

            print(f"\n✅ ¡Éxito! Archivo '{OUTPUT_FILENAME}' creado con el último registro.")
        else:
            print("❌ La respuesta de la API no contenía una lista de registros.")
            
    except Exception as e:
        print(f"❌ Ocurrió un error inesperado al obtener o guardar los datos: {e}")

if __name__ == "__main__":
    run_scraper_with_proxy()
