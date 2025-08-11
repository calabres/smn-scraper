import time
import requests
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# --- Constantes ---
LOCATION_ID = "4764"  # ID para Observatorio Central Buenos Aires (Haedo)
OUTPUT_FILENAME = "latest_weather.json"

def get_jwt_token_with_selenium():
    print("Iniciando navegador en el servidor de GitHub...")
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    driver = webdriver.Chrome(options=chrome_options)
    token = None
    try:
        driver.get("https://www.smn.gob.ar/")
        
        timeout = 20
        start_time = time.time()
        while time.time() - start_time < timeout:
            token = driver.execute_script("return localStorage.getItem('token');")
            if token:
                print("Token JWT obtenido con éxito.")
                break
            time.sleep(0.5)
    finally:
        driver.quit()
        
    return token

def get_smn_weather_data(jwt_token):
    if not jwt_token: return None
    weather_url = f"https://ws1.smn.gob.ar/v1/weather/location/{LOCATION_ID}"
    headers = {'Authorization': f'JWT {jwt_token}'}
    print(f"Pidiendo datos del tiempo para la locación {LOCATION_ID}...")
    try:
        response = requests.get(weather_url, headers=headers)
        response.raise_for_status()
        data = response.json()
        print("Datos del tiempo obtenidos.")
        return data
    except Exception as e:
        print(f"Error al obtener los datos del tiempo: {e}")
        return None

def save_data_to_file(data):
    if data:
        print(f"Guardando datos en el archivo '{OUTPUT_FILENAME}'...")
        # Guardamos el diccionario completo como un JSON legible
        with open(OUTPUT_FILENAME, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"Archivo '{OUTPUT_FILENAME}' guardado con éxito.")
    else:
        print("No hay datos para guardar.")

# --- Ejecución Principal del Script ---
if __name__ == "__main__":
    token = get_jwt_token_with_selenium()
    if token:
        weather_data = get_smn_weather_data(token)
        save_data_to_file(weather_data)
    else:
        print("Fallo al obtener el token. No se pueden obtener los datos del tiempo.")
