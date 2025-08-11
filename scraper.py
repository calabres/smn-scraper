import time
import json
import undetected_chromedriver as uc # Importamos la librería especializada

# --- Constantes ---
LOCATION_ID = "4764"
OUTPUT_FILENAME = "latest_weather.json"

def get_weather_data_with_undetected_browser():
    """
    Usa undetected-chromedriver para superar las protecciones de seguridad (ej: Cloudflare).
    """
    print("Iniciando navegador con undetected-chromedriver...")
    
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    driver = None
    weather_data = None
    
    try:
        # Usamos uc.Chrome() en lugar de webdriver.Chrome()
        driver = uc.Chrome(options=options)
        print("Driver inicializado. Navegando a la página del SMN...")
        
        driver.get("https://www.smn.gob.ar/")
        print(f"Navegación completada. Título: '{driver.title}'")

        # Damos tiempo suficiente para pasar la verificación "Just a moment..."
        print("Esperando 25 segundos para la carga completa y la generación del token...")
        time.sleep(25)
        
        # Obtenemos el token directamente del localStorage
        token = driver.execute_script("return localStorage.getItem('token');")

        if not token:
            raise Exception("No se pudo obtener el token. La página de seguridad podría haber fallado o cambiado.")
        
        print("✅ Token JWT obtenido con éxito.")
        
        # Usamos el mismo navegador para pedir los datos
        print(f"Pidiendo datos para la locación {LOCATION_ID}...")
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

        if result and result.get("error"):
             raise Exception(f"Error al pedir los datos: {result['error']}")
        
        weather_data = result
        print("✅ Datos del tiempo obtenidos.")

    except Exception as e:
        print(f"\n❌ Ocurrió un error: {e}\n")
    finally:
        if driver:
            print("Cerrando el navegador.")
            driver.quit()
            
    return weather_data

def save_data_to_file(data):
    if data:
        print(f"Guardando datos en '{OUTPUT_FILENAME}'...")
        with open(OUTPUT_FILENAME, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"✅ Archivo guardado.")
    else:
        print("No se recibieron datos para guardar.")

# --- Ejecución Principal ---
if __name__ == "__main__":
    final_data = get_weather_data_with_undetected_browser()
    if final_data:
        save_data_to_file(final_data)
    else:
        print("\nEl script finalizó sin obtener datos.")
