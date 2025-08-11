import time
import requests
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# --- Constantes ---
LOCATION_ID = "4764"
OUTPUT_FILENAME = "latest_weather.json"

def get_weather_data_with_selenium():
    """
    Versión con más diagnósticos para encontrar el punto de fallo.
    """
    print("Iniciando la función para obtener datos...")
    
    # --- Configuración de Selenium ---
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    driver = None # Inicializamos fuera del try
    weather_data = None
    
    try:
        print("Punto 1: Inicializando el driver de Chrome...")
        driver = webdriver.Chrome(options=chrome_options)
        print("✅ Driver de Chrome inicializado.")
        
        # Aumentamos el tiempo de espera para la carga de la página
        driver.set_page_load_timeout(45)

        print(f"Punto 2: Navegando a https://www.smn.gob.ar/ ...")
        driver.get("https://www.smn.gob.ar/")
        print("✅ Navegación completada.")
        print(f"Título de la página cargada: '{driver.title}'") # Imprimimos el título para ver si es la página correcta

        # 3. Espera a que el token se guarde
        token = None
        timeout = 20
        start_time = time.time()
        print("Punto 3: Esperando la generación del token...")
        while time.time() - start_time < timeout:
            token = driver.execute_script("return localStorage.getItem('token');")
            if token:
                print("✅ Token JWT obtenido.")
                break
            time.sleep(1) # Aumentamos la pausa a 1 segundo

        if not token:
            raise Exception("Timeout: No se pudo obtener el token después de esperar.")

        # 4. Usa el token para pedir los datos
        print(f"Punto 4: Usando el navegador para pedir datos de la locación {LOCATION_ID}...")
        js_script = f"""
            const url = 'https://ws1.smn.gob.ar/v1/weather/location/{LOCATION_ID}';
            const token = '{token}';
            const callback = arguments[arguments.length - 1];
            fetch(url, {{ headers: {{ 'Authorization': 'JWT ' + token }} }})
            .then(response => response.json())
            .then(data => callback(data))
            .catch(error => callback({{ error: error.toString() }}));
        """
        result = driver.execute_async_script(js_script)

        if result and "error" in result:
             raise Exception(f"Error en el fetch de JavaScript: {result['error']}")
        
        weather_data = result
        print("✅ Datos del tiempo obtenidos con éxito.")

    except Exception as e:
        # ESTA ES LA LÍNEA MÁS IMPORTANTE PARA LA DEPURACIÓN
        print(f"\n❌ Ocurrió un error con Selenium: {e}\n")
        # Si el driver existe, intentamos sacar una captura para más pistas
        if driver:
            try:
                driver.save_screenshot('error_screenshot.png')
                print("Se guardó una captura de pantalla del error como 'error_screenshot.png'")
            except:
                pass # Ignora si falla la captura
    finally:
        if driver:
            print("Cerrando el driver del navegador.")
            driver.quit()
        
    return weather_data

def save_data_to_file(data):
    # (Esta función no cambia)
    if data:
        print(f"Guardando datos en el archivo '{OUTPUT_FILENAME}'...")
        with open(OUTPUT_FILENAME, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"✅ Archivo '{OUTPUT_FILENAME}' guardado.")
    else:
        print("No se recibieron datos para guardar.")

# --- Ejecución Principal ---
if __name__ == "__main__":
    final_data = get_weather_data_with_selenium()
    if final_data:
        save_data_to_file(final_data)
    else:
        # Este es el mensaje que viste
        print("\nFallo al obtener los datos del tiempo. Revisa el log de arriba para ver el error específico.")
