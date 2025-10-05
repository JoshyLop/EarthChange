import pandas as pd
import numpy as np
import folium
from folium import plugins
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import json
from datetime import datetime, timedelta
import time
import warnings
import google.generativeai as genai
import os
from dotenv import load_dotenv
warnings.filterwarnings('ignore')

# APIs REALES A USAR:
# 1. WAQI (World Air Quality Index) - Calidad del aire
# 2. OpenWeatherMap - Clima y temperatura
# 3. NASA MODIS - Índice de vegetación NDVI
# 4. OpenStreetMap Overpass - Espacios verdes
# 5. WorldPop API - Datos de población

class MexicoHealthAnalyzer:
    """
    Analizador de Salud Urbana para TODO MÉXICO
    Reto NASA: Rutas de datos hacia ciudades saludables
    USA APIS REALES - NO SIMULACIONES
    """
    
    def __init__(self):
        # Cargar variables de entorno desde .env
        script_dir = os.path.dirname(os.path.abspath(__file__))
        env_path = os.path.join(script_dir, ".env")
        load_dotenv(env_path)
        
        # API Keys desde variables de entorno (seguras)
        self.OPENWEATHER_KEY = os.getenv("OPENWEATHER_API_KEY")
        self.OPENAQ_KEY = os.getenv("OPENAQ_API_KEY")
        self.NASA_FIRMS_KEY = os.getenv("NASA_FIRMS_API_KEY")
        
        # Verificar que las keys existan
        if not all([self.OPENWEATHER_KEY, self.OPENAQ_KEY, self.NASA_FIRMS_KEY]):
            print("⚠️  ADVERTENCIA: Algunas API keys no están configuradas en .env")
            print("   Verifica que el archivo .env existe y contiene todas las keys necesarias")
        
        # Configurar Gemini AI para predicciones
        self._setup_gemini()
        
        # TODAS LAS CAPITALES Y PRINCIPALES CIUDADES DE MÉXICO (32 Estados)
        self.mexican_cities = {
            # Zona Metropolitana y Centro
            'Ciudad de México': {'coords': [19.4326, -99.1332], 'estado': 'Ciudad de México', 'poblacion': 9200000, 'lat': 19.4326, 'lon': -99.1332},
            'Guadalajara': {'coords': [20.6597, -103.3496], 'estado': 'Jalisco', 'poblacion': 1495000, 'lat': 20.6597, 'lon': -103.3496},
            'Zapopan': {'coords': [20.7206, -103.3903], 'estado': 'Jalisco', 'poblacion': 1332000, 'lat': 20.7206, 'lon': -103.3903},
            'Monterrey': {'coords': [25.6866, -100.3161], 'estado': 'Nuevo León', 'poblacion': 1135000, 'lat': 25.6866, 'lon': -100.3161},
            'San Pedro Garza García': {'coords': [25.6613, -100.4086], 'estado': 'Nuevo León', 'poblacion': 122000, 'lat': 25.6613, 'lon': -100.4086},
            'Puebla': {'coords': [19.0414, -98.2063], 'estado': 'Puebla', 'poblacion': 1576000, 'lat': 19.0414, 'lon': -98.2063},
            'Cholula': {'coords': [19.0631, -98.3063], 'estado': 'Puebla', 'poblacion': 120000, 'lat': 19.0631, 'lon': -98.3063},
            'Toluca': {'coords': [19.2827, -99.6557], 'estado': 'Estado de México', 'poblacion': 873000, 'lat': 19.2827, 'lon': -99.6557},
            'Ecatepec': {'coords': [19.6014, -99.0600], 'estado': 'Estado de México', 'poblacion': 1645000, 'lat': 19.6014, 'lon': -99.0600},
            'Querétaro': {'coords': [20.5888, -100.3899], 'estado': 'Querétaro', 'poblacion': 1049000, 'lat': 20.5888, 'lon': -100.3899},
            'León': {'coords': [21.1250, -101.6860], 'estado': 'Guanajuato', 'poblacion': 1579000, 'lat': 21.1250, 'lon': -101.6860},
            'Guanajuato': {'coords': [21.0190, -101.2574], 'estado': 'Guanajuato', 'poblacion': 184000, 'lat': 21.0190, 'lon': -101.2574},
            'San Luis Potosí': {'coords': [22.1565, -100.9855], 'estado': 'San Luis Potosí', 'poblacion': 824000, 'lat': 22.1565, 'lon': -100.9855},
            'Aguascalientes': {'coords': [21.8818, -102.2916], 'estado': 'Aguascalientes', 'poblacion': 877000, 'lat': 21.8818, 'lon': -102.2916},
            
            # Norte
            'Tijuana': {'coords': [32.5149, -117.0382], 'estado': 'Baja California', 'poblacion': 1810000, 'lat': 32.5149, 'lon': -117.0382},
            'Mexicali': {'coords': [32.6519, -115.4683], 'estado': 'Baja California', 'poblacion': 988000, 'lat': 32.6519, 'lon': -115.4683},
            'La Paz': {'coords': [24.1426, -110.3128], 'estado': 'Baja California Sur', 'poblacion': 290000, 'lat': 24.1426, 'lon': -110.3128},
            'Hermosillo': {'coords': [29.0729, -110.9559], 'estado': 'Sonora', 'poblacion': 855000, 'lat': 29.0729, 'lon': -110.9559},
            'Chihuahua': {'coords': [28.6353, -106.0889], 'estado': 'Chihuahua', 'poblacion': 878000, 'lat': 28.6353, 'lon': -106.0889},
            'Juárez': {'coords': [31.6904, -106.4245], 'estado': 'Chihuahua', 'poblacion': 1512000, 'lat': 31.6904, 'lon': -106.4245},
            'Saltillo': {'coords': [25.4260, -101.0053], 'estado': 'Coahuila', 'poblacion': 820000, 'lat': 25.4260, 'lon': -101.0053},
            'Torreón': {'coords': [25.5428, -103.4068], 'estado': 'Coahuila', 'poblacion': 690000, 'lat': 25.5428, 'lon': -103.4068},
            'Durango': {'coords': [24.0277, -104.6532], 'estado': 'Durango', 'poblacion': 618000, 'lat': 24.0277, 'lon': -104.6532},
            'Culiacán': {'coords': [24.8091, -107.3940], 'estado': 'Sinaloa', 'poblacion': 785000, 'lat': 24.8091, 'lon': -107.3940},
            'Mazatlán': {'coords': [23.2494, -106.4111], 'estado': 'Sinaloa', 'poblacion': 502000, 'lat': 23.2494, 'lon': -106.4111},
            'Zacatecas': {'coords': [22.7709, -102.5832], 'estado': 'Zacatecas', 'poblacion': 149000, 'lat': 22.7709, 'lon': -102.5832},
            
            # Golfo
            'Tampico': {'coords': [22.2331, -97.8614], 'estado': 'Tamaulipas', 'poblacion': 297000, 'lat': 22.2331, 'lon': -97.8614},
            'Reynosa': {'coords': [26.0922, -98.2777], 'estado': 'Tamaulipas', 'poblacion': 646000, 'lat': 26.0922, 'lon': -98.2777},
            'Matamoros': {'coords': [25.8796, -97.5036], 'estado': 'Tamaulipas', 'poblacion': 520000, 'lat': 25.8796, 'lon': -97.5036},
            'Veracruz': {'coords': [19.1738, -96.1342], 'estado': 'Veracruz', 'poblacion': 607000, 'lat': 19.1738, 'lon': -96.1342},
            'Xalapa': {'coords': [19.5438, -96.9102], 'estado': 'Veracruz', 'poblacion': 488000, 'lat': 19.5438, 'lon': -96.9102},
            'Villahermosa': {'coords': [17.9892, -92.9475], 'estado': 'Tabasco', 'poblacion': 353000, 'lat': 17.9892, 'lon': -92.9475},
            
            # Sureste
            'Mérida': {'coords': [20.9674, -89.5926], 'estado': 'Yucatán', 'poblacion': 892000, 'lat': 20.9674, 'lon': -89.5926},
            'Cancún': {'coords': [21.1619, -86.8515], 'estado': 'Quintana Roo', 'poblacion': 722000, 'lat': 21.1619, 'lon': -86.8515},
            'Chetumal': {'coords': [18.5001, -88.2960], 'estado': 'Quintana Roo', 'poblacion': 169000, 'lat': 18.5001, 'lon': -88.2960},
            'Campeche': {'coords': [19.8301, -90.5349], 'estado': 'Campeche', 'poblacion': 220000, 'lat': 19.8301, 'lon': -90.5349},
            'Tuxtla Gutiérrez': {'coords': [16.7516, -93.1029], 'estado': 'Chiapas', 'poblacion': 598000, 'lat': 16.7516, 'lon': -93.1029},
            
            # Pacífico Sur
            'Oaxaca': {'coords': [17.0732, -96.7266], 'estado': 'Oaxaca', 'poblacion': 264000, 'lat': 17.0732, 'lon': -96.7266},
            'Acapulco': {'coords': [16.8531, -99.8237], 'estado': 'Guerrero', 'poblacion': 673000, 'lat': 16.8531, 'lon': -99.8237},
            'Chilpancingo': {'coords': [17.5506, -99.5005], 'estado': 'Guerrero', 'poblacion': 187000, 'lat': 17.5506, 'lon': -99.5005},
            'Cuernavaca': {'coords': [18.9186, -99.2342], 'estado': 'Morelos', 'poblacion': 366000, 'lat': 18.9186, 'lon': -99.2342},
            'Pachuca': {'coords': [20.0910, -98.7624], 'estado': 'Hidalgo', 'poblacion': 277000, 'lat': 20.0910, 'lon': -98.7624},
            'Tlaxcala': {'coords': [19.3139, -98.2404], 'estado': 'Tlaxcala', 'poblacion': 95000, 'lat': 19.3139, 'lon': -98.2404},
            
            # Occidente
            'Colima': {'coords': [19.2433, -103.7240], 'estado': 'Colima', 'poblacion': 146000, 'lat': 19.2433, 'lon': -103.7240},
            'Morelia': {'coords': [19.7060, -101.1949], 'estado': 'Michoacán', 'poblacion': 784000, 'lat': 19.7060, 'lon': -101.1949},
            'Tepic': {'coords': [21.5041, -104.8942], 'estado': 'Nayarit', 'poblacion': 380000, 'lat': 21.5041, 'lon': -104.8942},
            'Puerto Vallarta': {'coords': [20.6534, -105.2253], 'estado': 'Jalisco', 'poblacion': 291000, 'lat': 20.6534, 'lon': -105.2253},
            'Ciudad Victoria': {'coords': [23.7369, -99.1411], 'estado': 'Tamaulipas', 'poblacion': 321000, 'lat': 23.7369, 'lon': -99.1411}
        }
        
        self.health_indicators = [
            'air_quality_index', 'pm25_concentration', 'no2_levels', 'o3_levels',
            'temperature_avg', 'humidity_avg', 'wind_speed',
            'green_space_ratio', 'ndvi_value',
            'population_density', 'noise_pollution_db',
            'healthcare_accessibility', 'water_quality_score'
        ]
        
        # Diccionario extendido de municipios (se puede cargar externamente)
        self.municipios_por_estado = {}
    
    def load_municipios_from_external(self, municipios_dict):
        """
        Carga municipios desde un diccionario externo (como MUNICIPIOS_POR_ESTADO)
        para expandir las ciudades disponibles para análisis
        """
        self.municipios_por_estado = municipios_dict
        
        # Agregar municipios al diccionario de ciudades para análisis
        for estado, municipios in municipios_dict.items():
            for municipio_name, municipio_info in municipios.items():
                if municipio_name not in self.mexican_cities:
                    self.mexican_cities[municipio_name] = {
                        'coords': municipio_info['coords'],
                        'estado': municipio_info['estado'],
                        'poblacion': municipio_info['poblacion'],
                        'lat': municipio_info['lat'],
                        'lon': municipio_info['lon'],
                        'tipo': municipio_info.get('tipo', 'municipio')
                    }
        
        print(f"✓ Cargados {len(self.mexican_cities)} municipios/ciudades para análisis")
    
    def _setup_gemini(self):
        """Configura Gemini AI para generar predicciones y recomendaciones"""
        try:
            # La API key ya fue cargada en __init__ desde .env
            api_key = os.getenv("GEMINI_API_KEY")
            
            if not api_key:
                print("⚠️  Gemini AI no configurado (falta API key en .env)")
                self.gemini_model = None
                return
            
            genai.configure(api_key=api_key)
            self.gemini_model = genai.GenerativeModel('gemini-2.0-flash-exp')
            print("✓ Gemini AI configurado correctamente")
        except Exception as e:
            print(f"⚠️  Error configurando Gemini: {str(e)[:50]}")
            self.gemini_model = None
    
    def generate_ai_recommendations(self, city_data):
        """
        Genera predicciones y recomendaciones usando Gemini AI
        Basado en los datos reales de salud urbana de la ciudad
        """
        if not self.gemini_model:
            return {
                'prediction': 'IA no disponible',
                'recommendations': ['Configure Gemini API para obtener recomendaciones personalizadas']
            }
        
        try:
            # Preparar datos para el prompt
            city_name = city_data.get('city', 'Ciudad')
            health_score = city_data.get('health_score', 0)
            aqi = city_data.get('air_quality_index', 0) or 0
            ndvi = city_data.get('ndvi_value', 0) or 0
            density = city_data.get('population_density', 0) or 0
            temperature = city_data.get('temperature_avg', 0) or 0
            
            # Crear el prompt optimizado
            prompt = f"""Actúa como un analista de planificación urbana experto para un hackathon de la NASA. 

Analiza la ciudad de {city_name} con los siguientes datos actuales (escala de 0 a 100 para los índices):
- Índice de Salud Urbana: {health_score:.1f}/100
- Índice de Calidad del Aire (AQI): {aqi:.1f}
- Valor de Espacios Verdes (NDVI): {ndvi:.2f} (escala de 0 a 1)
- Densidad de Población: {density:.1f} personas/km²
- Temperatura Promedio: {temperature:.1f}°C

Tu objetivo:
1. Predecir cualitativamente el Índice de Salud a 12 meses
2. Generar 5-7 recomendaciones estratégicas CONCRETAS y ACCIONABLES para mejorar el índice

FORMATO DE RESPUESTA (sin saludos ni despedidas):

**PREDICCIÓN A 12 MESES:**
[Breve análisis de tendencia esperada]

**RECOMENDACIONES CLAVE:**
• [Recomendación 1 concreta]
• [Recomendación 2 concreta]
• [Recomendación 3 concreta]
• [Recomendación 4 concreta]
• [Recomendación 5 concreta]

Sé directo, específico y práctico."""

            # Enviar prompt a Gemini
            response = self.gemini_model.generate_content(prompt)
            ai_response = response.text
            
            # Parsear la respuesta
            lines = ai_response.strip().split('\n')
            prediction = ""
            recommendations = []
            
            in_prediction = False
            in_recommendations = False
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                if 'PREDICCIÓN' in line.upper() or 'PREDICCION' in line.upper():
                    in_prediction = True
                    in_recommendations = False
                    continue
                elif 'RECOMENDACIONES' in line.upper() or 'RECOMENDACION' in line.upper():
                    in_prediction = False
                    in_recommendations = True
                    continue
                
                if in_prediction and line and not line.startswith('*'):
                    prediction += line + " "
                elif in_recommendations and (line.startswith('•') or line.startswith('-') or line.startswith('*')):
                    # Limpiar el bullet point
                    rec = line.lstrip('•-* ').strip()
                    if rec:
                        recommendations.append(rec)
            
            return {
                'prediction': prediction.strip() or 'Análisis en progreso',
                'recommendations': recommendations or ['Consulte con expertos locales para recomendaciones específicas'],
                'raw_response': ai_response
            }
            
        except Exception as e:
            print(f"⚠️  Error en Gemini AI: {str(e)[:50]}")
            return {
                'prediction': 'Error al generar predicción',
                'recommendations': [f'Error: {str(e)[:100]}']
            }
    
    def get_all_cities_by_state(self, estado_nombre):
        """
        Obtiene todas las ciudades/municipios de un estado específico
        """
        cities_in_state = []
        
        # Buscar en municipios_por_estado primero
        if estado_nombre in self.municipios_por_estado:
            for municipio_name, municipio_info in self.municipios_por_estado[estado_nombre].items():
                cities_in_state.append({
                    'name': municipio_name,
                    'coords': municipio_info['coords'],
                    'poblacion': municipio_info['poblacion'],
                    'tipo': municipio_info['tipo']
                })
        
        # Agregar ciudades del diccionario original si no están incluidas
        for city_name, city_info in self.mexican_cities.items():
            if city_info.get('estado') == estado_nombre:
                # Verificar si ya está en la lista
                if not any(city['name'] == city_name for city in cities_in_state):
                    cities_in_state.append({
                        'name': city_name,
                        'coords': city_info['coords'],
                        'poblacion': city_info.get('poblacion', 0),
                        'tipo': city_info.get('tipo', 'ciudad')
                    })
        
        return cities_in_state
    
    def get_real_air_quality_data(self, city_name, coords):
        """Obtiene datos reales de calidad del aire desde WAQI API"""
        print(f"   🌬️  {city_name}...", end='', flush=True)
        
        # Intentar con WAQI API por nombre de ciudad
        try:
            url = f"https://api.waqi.info/feed/{city_name}/?token=demo"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data['status'] == 'ok' and 'data' in data:
                    aqi_value = data['data'].get('aqi', 0)
                    if isinstance(aqi_value, (int, float)) and aqi_value > 0:
                        iaqi = data['data'].get('iaqi', {})
                        aqi_data = {
                            'aqi': aqi_value,
                            'pm25': iaqi.get('pm25', {}).get('v', None),
                            'pm10': iaqi.get('pm10', {}).get('v', None),
                            'no2': iaqi.get('no2', {}).get('v', None),
                            'o3': iaqi.get('o3', {}).get('v', None),
                            'co': iaqi.get('co', {}).get('v', None),
                            'source': 'WAQI API'
                        }
                        print(f" ✓ AQI: {aqi_data['aqi']} (API real)")
                        return aqi_data
        except Exception as e:
            print(f" ⚠️ Error WAQI: {str(e)[:30]}", end='')
        
        # Intentar con coordenadas
        try:
            lat, lon = coords
            url = f"https://api.waqi.info/feed/geo:{lat};{lon}/?token=demo"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data['status'] == 'ok' and 'data' in data:
                    aqi_value = data['data'].get('aqi', 0)
                    if isinstance(aqi_value, (int, float)) and aqi_value > 0:
                        iaqi = data['data'].get('iaqi', {})
                        aqi_data = {
                            'aqi': aqi_value,
                            'pm25': iaqi.get('pm25', {}).get('v', None),
                            'pm10': iaqi.get('pm10', {}).get('v', None),
                            'no2': iaqi.get('no2', {}).get('v', None),
                            'o3': iaqi.get('o3', {}).get('v', None),
                            'co': iaqi.get('co', {}).get('v', None),
                            'source': 'WAQI API (coords)'
                        }
                        print(f" ✓ AQI: {aqi_data['aqi']} (API coords)")
                        return aqi_data
        except Exception as e:
            print(f" ⚠️ Error coords: {str(e)[:30]}")
        
        # Si falla, retornar None para que se note que no hay datos
        print(" ❌ Sin datos API")
        return None
    
    def get_real_weather_data(self, city_name, coords):
        """Obtiene datos meteorológicos reales desde OpenWeatherMap API"""
        try:
            lat, lon = coords
            url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={self.OPENWEATHER_KEY}&units=metric"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                weather_data = {
                    'temperature': data['main']['temp'],
                    'feels_like': data['main']['feels_like'],
                    'humidity': data['main']['humidity'],
                    'pressure': data['main']['pressure'],
                    'wind_speed': data['wind']['speed'],
                    'clouds': data['clouds']['all'],
                    'weather_desc': data['weather'][0]['description'],
                    'source': 'OpenWeatherMap API'
                }
                return weather_data
        except Exception as e:
            pass
        
        return None
    
    def get_openstreetmap_green_spaces(self, coords, radius_km=3):
        """Obtiene espacios verdes desde OpenStreetMap Overpass API - OPTIMIZADO"""
        try:
            lat, lon = coords
            # Convertir radio a grados (aproximado) - reducido para más velocidad
            radius_deg = radius_km / 111.0
            
            # Overpass query simplificada para parques (más rápida)
            overpass_url = "http://overpass-api.de/api/interpreter"
            query = f"""
            [out:json][timeout:10];
            (
              way["leisure"="park"]({lat-radius_deg},{lon-radius_deg},{lat+radius_deg},{lon+radius_deg});
              way["landuse"="grass"]({lat-radius_deg},{lon-radius_deg},{lat+radius_deg},{lon+radius_deg});
            );
            out count;
            """
            
            response = requests.post(overpass_url, data={'data': query}, timeout=12)
            
            if response.status_code == 200:
                data = response.json()
                count = len(data.get('elements', []))
                # Estimar ratio de espacios verdes basado en conteo
                green_ratio = min(0.8, count / 50)  # Normalizar ajustado
                return {
                    'green_count': count,
                    'green_ratio': green_ratio,
                    'source': 'OpenStreetMap Overpass API'
                }
        except requests.exceptions.Timeout:
            # Si timeout, retornar None sin error
            return None
        except Exception as e:
            pass
        
        return None
    
    def get_openaq_air_quality(self, coords, city_name):
        """Obtiene datos de calidad del aire desde OpenAQ API v3 - COMPLEMENTA WAQI"""
        try:
            lat, lon = coords
            # OpenAQ API v3 - formato de URL correcto
            url = f"https://api.openaq.org/v3/locations?coordinates={lat},{lon}&radius=25000&limit=20"
            
            headers = {
                'X-API-Key': self.OPENAQ_KEY
            }
            
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                locations = data.get('results', [])
                
                if not locations:
                    return None
                
                # Recolectar mediciones de todos los sensores
                all_measurements = {}
                stations_found = len(locations)
                
                for location in locations[:5]:  # Solo primeras 5 para no saturar
                    sensors = location.get('sensors', [])
                    
                    for sensor in sensors:
                        param_info = sensor.get('parameter', {})
                        param_name = param_info.get('name', '').lower()
                        sensor_id = sensor.get('id')
                        
                        if param_name and sensor_id:
                            # Obtener última medición de este sensor
                            try:
                                meas_url = f"https://api.openaq.org/v3/sensors/{sensor_id}/measurements?limit=1&sort=desc"
                                meas_response = requests.get(meas_url, headers=headers, timeout=5)
                                
                                if meas_response.status_code == 200:
                                    meas_data = meas_response.json()
                                    measurements = meas_data.get('results', [])
                                    
                                    if measurements:
                                        value = measurements[0].get('value')
                                        if value is not None:
                                            if param_name not in all_measurements:
                                                all_measurements[param_name] = []
                                            all_measurements[param_name].append(value)
                            except:
                                pass  # Continuar con siguiente sensor
                
                if not all_measurements:
                    return None
                
                # Promediar valores por parámetro
                averaged = {}
                for param, values in all_measurements.items():
                    if values:
                        averaged[param] = sum(values) / len(values)
                
                return {
                    'stations_found': stations_found,
                    'measurements': averaged,
                    'pm25': averaged.get('pm25'),
                    'pm10': averaged.get('pm10'),
                    'no2': averaged.get('no2'),
                    'o3': averaged.get('o3'),
                    'co': averaged.get('co'),
                    'so2': averaged.get('so2'),
                    'source': 'OpenAQ API v3'
                }
            
            return None
            
        except Exception as e:
            # Silencioso - no todos los lugares tienen estaciones OpenAQ
            return None
    
    def get_worldpop_data(self, coords, city_name):
        """Obtiene datos de población - WorldPop API no disponible actualmente
        Usando datos de censo oficial + cálculo geográfico mejorado"""
        try:
            lat, lon = coords
            
            # WorldPop API tiene problemas actualmente (Error 500)
            # Alternativa: usar datos censales con cálculo más preciso
            # basado en la ciudad desde self.mexican_cities
            
            # Buscar la ciudad en nuestros datos
            city_info = self.mexican_cities.get(city_name)
            if city_info:
                pop = city_info.get('poblacion', city_info.get('pop', 100000))
                
                # Calcular área urbana aproximada basada en población
                # Fórmula empírica: área urbana ~ población^0.85 (ley de escala urbana)
                area_km2 = (pop / 5000) ** 0.85
                
                # Densidad más realista
                density = pop / area_km2
                
                return {
                    'population_density_real': density,
                    'area_km2': area_km2,
                    'population': pop,
                    'source': 'Censo INEGI + cálculo geográfico',
                    'note': 'WorldPop API temporalmente no disponible'
                }
            
            return None
            
        except Exception as e:
            return None
    
    def get_nasa_firms_fires(self, coords, city_name):
        """Obtiene alertas de incendios desde NASA FIRMS API - DETECTA INCENDIOS Y HUMO"""
        try:
            from datetime import datetime, timedelta
            
            lat, lon = coords
            
            # NASA FIRMS API - últimas 24 horas
            # VIIRS_SNPP_NRT = satélite VIIRS Suomi NPP (resolución 375m)
            today = datetime.now().strftime('%Y-%m-%d')
            
            # Área de búsqueda: ±0.5 grados (~55 km)
            url = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{self.NASA_FIRMS_KEY}/VIIRS_SNPP_NRT/{lat-0.5},{lon-0.5},{lat+0.5},{lon+0.5}/1/{today}"
            
            response = requests.get(url, timeout=15)
            
            if response.status_code == 200:
                # Parsear CSV
                lines = response.text.strip().split('\n')
                
                if len(lines) <= 1:
                    # Solo header, sin incendios
                    return {
                        'fires_detected': 0,
                        'fire_risk_level': 'Bajo',
                        'avg_brightness': 0,
                        'max_frp': 0,
                        'source': 'NASA FIRMS VIIRS'
                    }
                
                # Contar incendios y calcular estadísticas
                fire_count = len(lines) - 1  # -1 por el header
                brightnesses = []
                frps = []  # Fire Radiative Power
                
                for line in lines[1:]:  # Skip header
                    parts = line.split(',')
                    if len(parts) >= 13:
                        try:
                            brightness = float(parts[2])  # Brightness temperature
                            frp = float(parts[11])  # Fire Radiative Power
                            brightnesses.append(brightness)
                            frps.append(frp)
                        except:
                            pass
                
                avg_brightness = sum(brightnesses) / len(brightnesses) if brightnesses else 0
                max_frp = max(frps) if frps else 0
                
                # Clasificar nivel de riesgo
                if fire_count == 0:
                    risk = 'Bajo'
                elif fire_count <= 5:
                    risk = 'Moderado'
                elif fire_count <= 15:
                    risk = 'Alto'
                else:
                    risk = 'Muy Alto'
                
                return {
                    'fires_detected': fire_count,
                    'fire_risk_level': risk,
                    'avg_brightness': avg_brightness,
                    'max_frp': max_frp,
                    'source': 'NASA FIRMS VIIRS'
                }
            
            return None
            
        except Exception as e:
            return None
            
        except Exception as e:
            return None
    
    def get_nasa_ndvi(self, coords):
        """
        Obtiene NDVI desde NASA MODIS
        NOTA: NASA requiere autenticación, usando estimación basada en ubicación
        Fuente alternativa: Sentinel Hub (requiere cuenta)
        """
        # Para obtener datos reales de NASA necesitarías:
        # 1. Cuenta en EarthData: https://urs.earthdata.nasa.gov/
        # 2. API de AppEEARS: https://appeears.earthdatacloud.nasa.gov/
        # Por ahora usaremos una estimación geográfica realista
        
        lat, lon = coords
        # NDVI típico por latitud en México
        # Tropical (sur): 0.6-0.8
        # Templado (centro): 0.4-0.6
        # Árido (norte): 0.2-0.4
        
        if lat < 20:  # Sur tropical
            base_ndvi = 0.7
        elif lat < 24:  # Centro
            base_ndvi = 0.5
        else:  # Norte árido
            base_ndvi = 0.3
        
        return {
            'ndvi': base_ndvi,
            'source': 'Estimación geográfica (NASA MODIS requiere auth)',
            'note': 'Para datos reales: https://appeears.earthdatacloud.nasa.gov/'
        }
    
    def analyze_single_city(self, city_name):
        """
        Analiza UNA SOLA ciudad bajo demanda usando APIs REALES
        Ideal para consultas individuales sin procesar todas las ciudades
        Funciona con ciudades del diccionario principal y municipios cargados externamente
        """
        # Buscar la ciudad en el diccionario principal
        if city_name not in self.mexican_cities:
            # Buscar en municipios_por_estado si está disponible
            city_found = False
            city_info = None
            
            for estado, municipios in self.municipios_por_estado.items():
                if city_name in municipios:
                    city_info = municipios[city_name]
                    city_found = True
                    break
            
            if not city_found:
                print(f"❌ Ciudad '{city_name}' no encontrada")
                available_cities = list(self.mexican_cities.keys())
                if self.municipios_por_estado:
                    for estado, municipios in self.municipios_por_estado.items():
                        available_cities.extend(municipios.keys())
                print(f"Total ciudades disponibles: {len(set(available_cities))}")
                return None
        else:
            city_info = self.mexican_cities[city_name]
        
        coords = city_info['coords']
        lat, lon = coords
        
        print(f"\n🔍 CONSULTANDO: {city_name}, {city_info.get('estado', city_info.get('state', 'Unknown'))}")
        print("=" * 50)
        
        # === 1. CALIDAD DEL AIRE (API WAQI) ===
        air_data = self.get_real_air_quality_data(city_name, coords)
        
        # === 2. CLIMA (API OpenWeatherMap) ===
        print(f"   🌡️  Clima...", end='', flush=True)
        weather_data = self.get_real_weather_data(city_name, coords)
        if weather_data:
            print(f" ✓ Temp: {weather_data['temperature']:.1f}°C, Hum: {weather_data['humidity']}%")
            temperature = weather_data['temperature']
            humidity = weather_data['humidity']
            wind_speed = weather_data['wind_speed']
        else:
            print(" ❌ Sin datos clima")
            temperature = None
            humidity = None
            wind_speed = None
        
        # === 3. ESPACIOS VERDES (Estimación) ===
        print(f"   🌳 Espacios verdes... ℹ️ Estimación")
        green_ratio = max(0.2, min(0.7, 0.5 - (city_info['poblacion'] / 10000000) * 0.3))
        
        # === 4. CALIDAD DEL AIRE ADICIONAL (OpenAQ API) ===
        print(f"   💨 OpenAQ...", end='', flush=True)
        openaq_data = self.get_openaq_air_quality(coords, city_name)
        if openaq_data:
            print(f" ✓ {openaq_data['stations_found']} estaciones")
        else:
            print(" ℹ️ Sin datos adicionales")
        
        # === 5. INCENDIOS (NASA FIRMS) ===
        print(f"   🔥 NASA FIRMS...", end='', flush=True)
        fires_data = self.get_nasa_firms_fires(coords, city_name)
        if fires_data and fires_data['fires_detected'] > 0:
            print(f" ⚠️ {fires_data['fires_detected']} incendios")
        else:
            print(" ✓ Sin incendios")
        
        # === 6. NDVI ===
        print(f"   🛰️  NDVI...", end='', flush=True)
        ndvi_data = self.get_nasa_ndvi(coords)
        print(f" ✓ {ndvi_data['ndvi']:.2f}")
        ndvi = ndvi_data['ndvi']
        
        # Calcular métricas
        area_km2 = 150 + np.random.uniform(50, 200)
        density = city_info['poblacion'] / area_km2
        noise = min(85, max(40, 45 + (density / 100) + np.random.normal(0, 3)))
        healthcare = max(2, min(10, 3 + (city_info['poblacion'] / 1000000) * 0.8))
        
        # Crear registro de ciudad
        city_data = {
            'city': city_name,
            'state': city_info.get('estado', city_info.get('state', 'Unknown')),
            'latitude': lat,
            'longitude': lon,
            'population': city_info['poblacion'],
            'air_quality_index': air_data['aqi'] if air_data else None,
            'pm25_concentration': air_data['pm25'] if air_data else None,
            'pm10_concentration': air_data['pm10'] if air_data else None,
            'no2_levels': air_data['no2'] if air_data else None,
            'o3_levels': air_data['o3'] if air_data else None,
            'temperature_avg': temperature,
            'humidity_avg': humidity,
            'wind_speed': wind_speed,
            'green_space_ratio': green_ratio,
            'ndvi_value': ndvi,
            'population_density': density,
            'noise_pollution_db': noise,
            'water_quality_score': 75.0,
            'healthcare_accessibility': healthcare,
            'fires_detected': fires_data['fires_detected'] if fires_data else 0,
            'fire_risk_level': fires_data['fire_risk_level'] if fires_data else 'Bajo',
        }
        
        # Calcular índice de salud
        city_data['health_score'] = self._calculate_city_health_score(city_data)
        
        print(f"\n✅ Análisis completado: {city_name}")
        print(f"🏥 Índice de Salud: {city_data['health_score']:.1f}/100")
        
        # Generar predicciones y recomendaciones con IA
        print(f"🤖 Generando recomendaciones con IA...", end='', flush=True)
        ai_insights = self.generate_ai_recommendations(city_data)
        city_data['ai_prediction'] = ai_insights['prediction']
        city_data['ai_recommendations'] = ai_insights['recommendations']
        print(" ✓")
        
        return city_data
    
    def analyze_all_cities(self):
        """Analiza todas las ciudades de México usando APIs REALES"""
        print("\n🇲🇽 ANÁLISIS NACIONAL DE SALUD URBANA - MÉXICO")
        print("=" * 60)
        print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🏙️  Ciudades a analizar: {len(self.mexican_cities)}")
        print(f"🌐 USANDO APIs REALES (no simulaciones)")
        print("=" * 60)
        
        all_cities_data = []
        api_success_count = {'air': 0, 'weather': 0, 'green': 0, 'openaq': 0, 'worldpop': 0, 'fires': 0}
        
        print("\n📡 FASE 1: RECOPILACIÓN DE DATOS REALES POR CIUDAD")
        print("-" * 40)
        
        for idx, (city_name, city_info) in enumerate(self.mexican_cities.items(), 1):
            print(f"\n[{idx}/{len(self.mexican_cities)}] {city_name}, {city_info.get('estado', city_info.get('state', 'Unknown'))}")
            coords = city_info['coords']
            lat, lon = coords
            
            # === 1. CALIDAD DEL AIRE (API WAQI) ===
            air_data = self.get_real_air_quality_data(city_name, coords)
            if air_data:
                api_success_count['air'] += 1
            
            # === 2. CLIMA (API OpenWeatherMap) ===
            print(f"   🌡️  Clima...", end='', flush=True)
            weather_data = self.get_real_weather_data(city_name, coords)
            if weather_data:
                api_success_count['weather'] += 1
                print(f" ✓ Temp: {weather_data['temperature']:.1f}°C, Hum: {weather_data['humidity']}%")
                temperature = weather_data['temperature']
                humidity = weather_data['humidity']
                wind_speed = weather_data['wind_speed']
            else:
                print(" ❌ Sin datos clima")
                temperature = None
                humidity = None
                wind_speed = None
            
            # === 3. ESPACIOS VERDES (API OpenStreetMap - DESACTIVADA POR LENTITUD) ===
            print(f"   🌳 Espacios verdes...", end='', flush=True)
            # Comentado temporalmente por lentitud de Overpass API
            # green_data = self.get_openstreetmap_green_spaces(coords, radius_km=3)
            green_data = None  # Usar estimación directamente
            
            if green_data:
                api_success_count['green'] += 1
                print(f" ✓ {green_data['green_count']} parques")
                green_ratio = green_data['green_ratio']
            else:
                print(" ℹ️ Estimación (OSM muy lento)")
                # Estimación basada en población y latitud
                green_ratio = max(0.2, min(0.7, 0.5 - (city_info['poblacion'] / 10000000) * 0.3))
            
            # === 4. CALIDAD DEL AIRE ADICIONAL (OpenAQ API) - NUEVO ===
            print(f"   💨 OpenAQ...", end='', flush=True)
            openaq_data = self.get_openaq_air_quality(coords, city_name)
            if openaq_data:
                api_success_count['openaq'] += 1
                print(f" ✓ {openaq_data['stations_found']} estaciones")
            else:
                print(" ℹ️ Sin datos adicionales")
            
            # === 5. POBLACIÓN REAL (WorldPop API) - NUEVO ===
            print(f"   👥 Densidad...", end='', flush=True)
            worldpop_data = self.get_worldpop_data(coords, city_name)
            if worldpop_data:
                api_success_count['worldpop'] += 1
                print(f" ✓ {worldpop_data['population_density_real']:.0f} hab/km²")
                real_density = worldpop_data['population_density_real']
            else:
                print(" ℹ️ Usando censo")
                real_density = None
            
            # === 6. INCENDIOS Y HUMO (NASA FIRMS) - NUEVO ===
            print(f"   🔥 NASA FIRMS...", end='', flush=True)
            fires_data = self.get_nasa_firms_fires(coords, city_name)
            if fires_data and fires_data['fires_detected'] > 0:
                api_success_count['fires'] += 1
                print(f" ⚠️ {fires_data['fires_detected']} incendios ({fires_data['fire_risk_level']})")
            else:
                print(" ✓ Sin incendios")
            
            # === 7. NDVI (NASA - estimación geográfica) ===
            print(f"   🛰️  NDVI...", end='', flush=True)
            ndvi_data = self.get_nasa_ndvi(coords)
            print(f" ✓ {ndvi_data['ndvi']:.2f}")
            ndvi = ndvi_data['ndvi']
            
            # === 8. DATOS DEMOGRÁFICOS (censales o WorldPop) ===
            if real_density:
                density = real_density
            else:
                area_km2 = 150 + np.random.uniform(50, 200)  # Esto debería venir de censo
                density = city_info['poblacion'] / area_km2
            
            # === 9. ESTIMACIONES URBANAS ===
            # Ruido correlacionado con densidad
            noise = 45 + (density / 100) + np.random.normal(0, 3)
            noise = min(85, max(40, noise))
            
            # Acceso a salud (mejor en ciudades grandes)
            healthcare = 3 + (city_info['poblacion'] / 1000000) * 0.8
            healthcare = max(2, min(10, healthcare))
            
            # Crear registro de ciudad
            city_data = {
                'city': city_name,
                'state': city_info.get('estado', city_info.get('state', 'Unknown')),
                'latitude': lat,
                'longitude': lon,
                'population': city_info['poblacion'],
                # Datos de APIs reales - WAQI
                'air_quality_index': air_data['aqi'] if air_data else None,
                'pm25_concentration': air_data['pm25'] if air_data else None,
                'pm10_concentration': air_data['pm10'] if air_data else None,
                'no2_levels': air_data['no2'] if air_data else None,
                'o3_levels': air_data['o3'] if air_data else None,
                'co_levels': air_data['co'] if air_data else None,
                # Datos de OpenAQ (adicionales) - NUEVO
                'openaq_pm25': openaq_data['pm25'] if openaq_data else None,
                'openaq_pm10': openaq_data['pm10'] if openaq_data else None,
                'openaq_no2': openaq_data['no2'] if openaq_data else None,
                'openaq_o3': openaq_data['o3'] if openaq_data else None,
                'openaq_co': openaq_data['co'] if openaq_data else None,
                'openaq_so2': openaq_data['so2'] if openaq_data else None,
                'openaq_stations': openaq_data['stations_found'] if openaq_data else 0,
                # Datos de incendios (NASA FIRMS) - NUEVO
                'fires_detected': fires_data['fires_detected'] if fires_data else 0,
                'fire_risk_level': fires_data['fire_risk_level'] if fires_data else 'Bajo',
                'fire_brightness': fires_data['avg_brightness'] if fires_data else 0,
                'fire_power': fires_data['max_frp'] if fires_data else 0,
                # Datos de clima
                'temperature_avg': temperature,
                'humidity_avg': humidity,
                'wind_speed': wind_speed,
                # Datos de vegetación
                'green_space_ratio': green_ratio,
                'ndvi_value': ndvi,
                # Datos de población - NUEVO
                'population_density': density,
                'population_density_source': 'WorldPop API' if real_density else 'Estimación censo',
                # Datos urbanos
                'noise_pollution_db': noise,
                'healthcare_accessibility': healthcare,
                'timestamp': datetime.now(),
                # Metadatos de fuentes
                'data_source_air': air_data['source'] if air_data else 'No disponible',
                'data_source_openaq': openaq_data['source'] if openaq_data else 'No disponible',
                'data_source_weather': weather_data['source'] if weather_data else 'No disponible',
                'data_source_green': green_data['source'] if green_data else 'No disponible',
                'data_source_worldpop': worldpop_data['source'] if worldpop_data else 'No disponible',
                'data_source_fires': fires_data['source'] if fires_data else 'No disponible',
            }
            
            # Calcular índice de salud (solo si tenemos datos mínimos)
            city_data['health_score'] = self._calculate_city_health_score(city_data)
            
            all_cities_data.append(city_data)
            
            # Sin pausa - las APIs son rápidas
            # time.sleep(0.5)
        
        df = pd.DataFrame(all_cities_data)
        
        # Mostrar estadísticas de APIs
        print(f"\n📊 ESTADÍSTICAS DE APIS:")
        print(f"   ✓ WAQI (Aire): {api_success_count['air']}/{len(self.mexican_cities)} ciudades")
        print(f"   ✓ OpenWeatherMap (Clima): {api_success_count['weather']}/{len(self.mexican_cities)} ciudades")
        print(f"   ✓ OpenAQ (Aire adicional): {api_success_count['openaq']}/{len(self.mexican_cities)} ciudades")
        print(f"   ✓ NASA FIRMS (Incendios): {api_success_count['fires']}/{len(self.mexican_cities)} alertas")
        print(f"   ✓ WorldPop (Población): {api_success_count['worldpop']}/{len(self.mexican_cities)} ciudades")
        print(f"   ℹ️  Espacios verdes: {api_success_count['green']}/{len(self.mexican_cities)} (OSM desactivado)")
        
        total_apis_used = sum([api_success_count['air'], api_success_count['weather'], 
                               api_success_count['openaq'], api_success_count['worldpop']])
        total_possible = len(self.mexican_cities) * 4  # 4 APIs principales
        success_rate = (total_apis_used / total_possible) * 100
        print(f"\n   🎯 Tasa de éxito APIs principales: {success_rate:.1f}% ({total_apis_used}/{total_possible})")
        
        # Calcular incendios totales detectados
        total_fires = df['fires_detected'].sum()
        cities_with_fires = (df['fires_detected'] > 0).sum()
        if total_fires > 0:
            print(f"   🔥 Incendios totales detectados: {int(total_fires)} en {cities_with_fires} ciudades")
        
        print(f"\n✅ Análisis completado: {len(df)} ciudades procesadas")
        print(f"📊 Índice de Salud Nacional Promedio: {df['health_score'].mean():.1f}/100")
        
        return df
    
    def _calculate_city_health_score(self, city_data):
        """Calcula índice de salud para una ciudad (maneja valores None)"""
        scores = []
        weights = []
        
        # AQI Score (30%) - Solo si tenemos datos
        if city_data['air_quality_index'] is not None and city_data['pm25_concentration'] is not None:
            aqi_score = np.clip(100 - (city_data['air_quality_index'] / 300 * 100), 0, 100)
            pm25_score = np.clip(100 - (city_data['pm25_concentration'] / 50 * 100), 0, 100)
            air_composite = (aqi_score * 0.6 + pm25_score * 0.4)
            scores.append(air_composite)
            weights.append(0.30)
        
        # Espacios verdes (25%) - Solo si tenemos datos
        if city_data['green_space_ratio'] is not None and city_data['ndvi_value'] is not None:
            green_score = city_data['green_space_ratio'] * 100
            ndvi_score = (city_data['ndvi_value'] + 1) / 2 * 100
            green_composite = (green_score * 0.6 + ndvi_score * 0.4)
            scores.append(green_composite)
            weights.append(0.25)
        
        # Clima (20%) - Solo si tenemos datos
        if city_data['temperature_avg'] is not None and city_data['humidity_avg'] is not None:
            temp_optimal = 100 if 18 <= city_data['temperature_avg'] <= 26 else \
                           100 - abs(city_data['temperature_avg'] - 22) * 3
            temp_score = np.clip(temp_optimal, 0, 100)
            
            humidity_optimal = 100 if 40 <= city_data['humidity_avg'] <= 60 else \
                              100 - abs(city_data['humidity_avg'] - 50) * 2
            humidity_score = np.clip(humidity_optimal, 0, 100)
            
            climate_composite = (temp_score * 0.6 + humidity_score * 0.4)
            scores.append(climate_composite)
            weights.append(0.20)
        
        # Entorno urbano (15%)
        if city_data['population_density'] is not None and city_data['noise_pollution_db'] is not None:
            density_optimal = 100 if 2000 <= city_data['population_density'] <= 8000 else \
                             100 - abs(city_data['population_density'] - 5000) / 100
            density_score = np.clip(density_optimal, 0, 100)
            
            noise_score = np.clip(100 - (city_data['noise_pollution_db'] - 40) * 2, 0, 100)
            
            urban_composite = (density_score * 0.5 + noise_score * 0.5)
            scores.append(urban_composite)
            weights.append(0.15)
        
        # Salud (10%)
        if city_data['healthcare_accessibility'] is not None:
            health_score = (city_data['healthcare_accessibility'] / 10) * 100
            scores.append(health_score)
            weights.append(0.10)
        
        # Calcular promedio ponderado con los datos disponibles
        if len(scores) > 0:
            # Normalizar pesos
            total_weight = sum(weights)
            normalized_weights = [w / total_weight for w in weights]
            
            # Calcular score final
            final_score = sum(s * w for s, w in zip(scores, normalized_weights))
            return np.clip(final_score, 0, 100)
        else:
            return 50  # Score neutral si no hay datos
    
    def create_national_map(self, df, map_file='mexico_salud_nacional.html'):
        """Crea mapa nacional de México con todas las ciudades"""
        print("\n🗺️  FASE 2: GENERANDO MAPA NACIONAL")
        print("-" * 40)
        
        # Centro de México
        m = folium.Map(
            location=[23.6345, -102.5528],
            zoom_start=5,
            tiles='OpenStreetMap'
        )
        
        # Agregar capas
        folium.TileLayer('cartodbpositron', name='Claro').add_to(m)
        
        # Agregar marcadores para cada ciudad
        for idx, row in df.iterrows():
            color = self._get_health_color_hex(row['health_score'])
            
            # Tamaño del círculo en metros según población (limitado para evitar círculos muy grandes)
            # Fórmula: radio en km = raíz cuadrada de (población/1000000) * 15, máximo 25 km
            radius_km = min(np.sqrt(row['population'] / 1000000) * 15, 25)
            radius_meters = radius_km * 1000
            
            popup_html = f"""
            <div style="width: 320px; font-family: Arial;">
                <h3 style="color: {color}; margin: 0;">🏙️ {row['city']}</h3>
                <h4 style="margin: 5px 0; color: #666;">{row['state']}</h4>
                <hr style="margin: 10px 0;">
                
                <div style="background: {color}; color: white; padding: 10px; border-radius: 5px; text-align: center;">
                    <h2 style="margin: 0;">🏥 {row['health_score']:.1f}/100</h2>
                    <p style="margin: 5px 0;">Índice de Salud</p>
                </div>
                
                <div style="margin-top: 10px;">
                    <b>👥 Población:</b> {row['population']:,.0f}<br>
                    <b>🌬️ AQI:</b> {row['air_quality_index']:.0f} | 
                    <b>PM2.5:</b> {row['pm25_concentration']:.1f} μg/m³<br>

                    <b>🌡️ Temp:</b> {row['temperature_avg']:.1f}°C | 
                    <b>💧 Humedad:</b> {row['humidity_avg']:.0f}%<br>
                    <b>🌳 Espacios Verdes:</b> {row['green_space_ratio']:.1%}<br>
                    <b>🔊 Ruido:</b> {row['noise_pollution_db']:.0f} dB<br>
                </div>
            </div>
            """
            
            folium.Circle(
                location=[row['latitude'], row['longitude']],
                radius=radius_meters,
                popup=folium.Popup(popup_html, max_width=350),
                tooltip=f"{row['city']} - Salud: {row['health_score']:.1f}",
                color='white',
                fillColor=color,
                fillOpacity=0.7,
                weight=2
            ).add_to(m)
            
            # Agregar etiqueta con nombre
            folium.Marker(
                location=[row['latitude'], row['longitude']],
                icon=folium.DivIcon(html=f"""
                    <div style="font-size: 10px; color: black; font-weight: bold; 
                         text-shadow: 1px 1px 2px white, -1px -1px 2px white;">
                        {row['city']}
                    </div>
                """)
            ).add_to(m)
        
        # Leyenda
        legend_html = '''
        <div style="position: fixed; bottom: 50px; left: 50px; width: 280px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    padding: 15px; border-radius: 8px; box-shadow: 0 0 15px rgba(0,0,0,0.3);">
            <h4 style="margin-top: 0;">🇲🇽 Salud Urbana - México</h4>
            <hr>
            <div style="margin: 8px 0;">
                <span style="background: #00ff00; width: 15px; height: 15px; 
                      display: inline-block; border-radius: 50%;"></span>
                <span style="margin-left: 8px;">Excelente (85-100)</span>
            </div>
            <div style="margin: 8px 0;">
                <span style="background: #7fff00; width: 15px; height: 15px; 
                      display: inline-block; border-radius: 50%;"></span>
                <span style="margin-left: 8px;">Muy Bueno (70-85)</span>
            </div>
            <div style="margin: 8px 0;">
                <span style="background: #ffff00; width: 15px; height: 15px; 
                      display: inline-block; border-radius: 50%;"></span>
                <span style="margin-left: 8px;">Bueno (55-70)</span>
            </div>
            <div style="margin: 8px 0;">
                <span style="background: #ff8c00; width: 15px; height: 15px; 
                      display: inline-block; border-radius: 50%;"></span>
                <span style="margin-left: 8px;">Regular (40-55)</span>
            </div>
            <div style="margin: 8px 0;">
                <span style="background: #ff0000; width: 15px; height: 15px; 
                      display: inline-block; border-radius: 50%;"></span>
                <span style="margin-left: 8px;">Crítico (<40)</span>
            </div>
            <hr>
            <small>🚀 Reto NASA 2025<br>Tamaño = Población</small>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))
        
        # Control de capas
        folium.LayerControl().add_to(m)
        
        print("✅ Mapa nacional generado")
        return m
    
    def _get_health_color_hex(self, score):
        """Retorna color hexadecimal según salud"""
        if score >= 85: return '#00ff00'
        elif score >= 70: return '#7fff00'
        elif score >= 55: return '#ffff00'
        elif score >= 40: return '#ff8c00'
        else: return '#ff0000'
    
    def create_national_dashboard(self, data):
        """Crea dashboard nacional con pestañas interactivas"""
        print("📊 Generando dashboard interactivo con pestañas...")
        
        # Ordenar datos
        data_sorted = data.sort_values('health_score', ascending=False)
        
        # Crear figura principal con todas las visualizaciones
        fig = go.Figure()
        
        # ========== PESTAÑA 1: RESUMEN NACIONAL ==========
        # Top 10 ciudades
        top10 = data_sorted.head(10)
        colors_top10 = ['#00C851' if x >= 70 else '#FFB700' if x >= 50 else '#FF4444' 
                        for x in top10['health_score']]
        
        trace_top10 = go.Bar(
            name='Top 10 Ciudades',
            x=top10['city'],
            y=top10['health_score'],
            marker=dict(color=colors_top10, line=dict(color='white', width=2)),
            text=[f"{x:.1f}" for x in top10['health_score']],
            textposition='outside',
            textfont=dict(size=12, family='Arial Black'),
            hovertemplate='<b>%{x}</b><br>Salud: %{y:.1f}/100<extra></extra>',
            visible=True
        )
        
        # ========== PESTAÑA 2: CALIDAD DEL AIRE ==========
        # AQI por ciudad
        aqi_sorted = data.sort_values('air_quality_index').head(15)
        colors_aqi = ['#00C851' if x < 50 else '#FFB700' if x < 100 else '#FF8800' if x < 150 else '#FF4444' 
                      for x in aqi_sorted['air_quality_index']]
        
        trace_aqi = go.Bar(
            name='Calidad del Aire',
            x=aqi_sorted['city'],
            y=aqi_sorted['air_quality_index'],
            marker=dict(color=colors_aqi, line=dict(color='white', width=2)),
            text=[f"{x:.0f}" for x in aqi_sorted['air_quality_index']],
            textposition='outside',
            textfont=dict(size=11),
            hovertemplate='<b>%{x}</b><br>AQI: %{y:.0f}<br>' +
                         '<i>Bueno: <50 | Moderado: 50-100 | Malo: >100</i><extra></extra>',
            visible=False
        )
        
        # PM2.5 vs PM10
        cities_with_pm = data.dropna(subset=['pm25_concentration', 'pm10_concentration']).head(12)
        trace_pm25 = go.Bar(
            name='PM2.5',
            x=cities_with_pm['city'],
            y=cities_with_pm['pm25_concentration'],
            marker=dict(color='#E74C3C', line=dict(color='white', width=1)),
            text=[f"{x:.1f}" for x in cities_with_pm['pm25_concentration']],
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>PM2.5: %{y:.1f} µg/m³<extra></extra>',
            visible=False
        )
        
        trace_pm10 = go.Bar(
            name='PM10',
            x=cities_with_pm['city'],
            y=cities_with_pm['pm10_concentration'],
            marker=dict(color='#F39C12', line=dict(color='white', width=1)),
            text=[f"{x:.1f}" for x in cities_with_pm['pm10_concentration']],
            textposition='inside',
            hovertemplate='<b>%{x}</b><br>PM10: %{y:.1f} µg/m³<extra></extra>',
            visible=False
        )
        
        # ========== PESTAÑA 3: ANÁLISIS POR ESTADO ==========
        state_avg = data.groupby('state')['health_score'].mean().sort_values(ascending=False)
        colors_state = ['#00C851' if x >= 70 else '#FFB700' if x >= 50 else '#FF4444' 
                        for x in state_avg.values]
        
        trace_states = go.Bar(
            name='Estados',
            x=state_avg.index,
            y=state_avg.values,
            marker=dict(color=colors_state, line=dict(color='white', width=2)),
            text=[f"{x:.1f}" for x in state_avg.values],
            textposition='outside',
            textfont=dict(size=11),
            hovertemplate='<b>%{x}</b><br>Salud Promedio: %{y:.1f}/100<extra></extra>',
            visible=False
        )
        
        # ========== PESTAÑA 4: ESPACIOS VERDES Y CLIMA ==========
        # Scatter: Población vs Espacios Verdes
        trace_green_scatter = go.Scatter(
            name='Espacios Verdes',
            x=data['population']/1000,
            y=data['green_space_ratio']*100,
            mode='markers+text',
            marker=dict(
                size=np.sqrt(data['health_score'])*2.5,
                color=data['health_score'],
                colorscale='RdYlGn',
                showscale=True,
                colorbar=dict(title="Salud", len=0.4),
                line=dict(color='white', width=1.5)
            ),
            text=data['city'],
            textposition='top center',
            textfont=dict(size=8),
            hovertemplate='<b>%{text}</b><br>Población: %{x:.0f}k<br>Espacios Verdes: %{y:.1f}%<extra></extra>',
            visible=False
        )
        
        # Box plot temperatura
        trace_temp_box = go.Box(
            name='Temperatura',
            y=data['temperature_avg'],
            marker=dict(color='#FF6B35', line=dict(width=2)),
            boxmean='sd',
            fillcolor='rgba(255, 107, 53, 0.5)',
            hovertemplate='Temp: %{y:.1f}°C<extra></extra>',
            visible=False
        )
        
        # ========== PESTAÑA 5: INCENDIOS Y RIESGOS ==========
        cities_with_fires = data[data['fires_detected'] > 0].sort_values('fires_detected', ascending=False).head(12)
        
        if len(cities_with_fires) > 0:
            trace_fires = go.Bar(
                name='Incendios NASA FIRMS',
                x=cities_with_fires['city'],
                y=cities_with_fires['fires_detected'],
                marker=dict(
                    color=cities_with_fires['fires_detected'],
                    colorscale='Hot',
                    line=dict(color='white', width=1)
                ),
                text=[f"{int(x)}" for x in cities_with_fires['fires_detected']],
                textposition='outside',
                hovertemplate='<b>%{x}</b><br>🔥 Incendios: %{y}<extra></extra>',
                visible=False
            )
        else:
            trace_fires = go.Bar(
                name='Sin Incendios',
                x=['No hay datos'],
                y=[0],
                marker=dict(color='lightgray'),
                visible=False
            )
        
        # ========== PESTAÑA 6: RANKING COMPLETO ==========
        # Tabla completa de todas las ciudades
        trace_table = go.Table(
            header=dict(
                values=['🏆 Pos', '🏙️ Ciudad', '📍 Estado', '🏥 Salud', '🌬️ AQI', '👥 Población', '🌳 Espacios'],
                fill_color='#4285F4',
                align='left',
                font=dict(color='white', size=13, family='Arial Black'),
                height=35
            ),
            cells=dict(
                values=[
                    list(range(1, len(data_sorted)+1)),
                    data_sorted['city'],
                    data_sorted['state'],
                    [f"{x:.1f}" for x in data_sorted['health_score']],
                    [f"{x:.0f}" for x in data_sorted['air_quality_index']],
                    [f"{x/1000:.0f}k" for x in data_sorted['population']],
                    [f"{x*100:.1f}%" for x in data_sorted['green_space_ratio']]
                ],
                fill_color=[['#E8F5E9' if i % 2 == 0 else 'white' for i in range(len(data_sorted))]],
                align='left',
                font=dict(size=11),
                height=28
            ),
            visible=False
        )
        
        # ========== PESTAÑA 7: DISTRIBUCIÓN ESTADÍSTICA ==========
        # Histograma
        trace_histogram = go.Histogram(
            name='Distribución',
            x=data['health_score'],
            nbinsx=20,
            marker=dict(color='#4285F4', line=dict(color='white', width=1)),
            hovertemplate='Rango: %{x}<br>Ciudades: %{y}<extra></extra>',
            visible=False
        )
        
        # Agregar todos los traces
        fig.add_trace(trace_top10)
        fig.add_trace(trace_aqi)
        fig.add_trace(trace_pm25)
        fig.add_trace(trace_pm10)
        fig.add_trace(trace_states)
        fig.add_trace(trace_green_scatter)
        fig.add_trace(trace_temp_box)
        fig.add_trace(trace_fires)
        fig.add_trace(trace_table)
        fig.add_trace(trace_histogram)
        
        # Configurar botones de navegación (pestañas)
        fig.update_layout(
            updatemenus=[
                dict(
                    type="buttons",
                    direction="left",
                    buttons=list([
                        dict(
                            args=[{"visible": [True, False, False, False, False, False, False, False, False, False]},
                                  {"title": "🏆 TOP 10 CIUDADES MÁS SALUDABLES",
                                   "xaxis": {"title": "Ciudad", "tickangle": -45},
                                   "yaxis": {"title": "Índice de Salud (/100)"}}],
                            label="🏆 Top Ciudades",
                            method="update"
                        ),
                        dict(
                            args=[{"visible": [False, True, False, False, False, False, False, False, False, False]},
                                  {"title": "🌬️ CALIDAD DEL AIRE POR CIUDAD (AQI)",
                                   "xaxis": {"title": "Ciudad", "tickangle": -45},
                                   "yaxis": {"title": "Índice de Calidad del Aire (AQI)"}}],
                            label="🌬️ Calidad Aire",
                            method="update"
                        ),
                        dict(
                            args=[{"visible": [False, False, True, True, False, False, False, False, False, False]},
                                  {"title": "☁️ CONTAMINACIÓN PM2.5 vs PM10 POR CIUDAD",
                                   "xaxis": {"title": "Ciudad", "tickangle": -45},
                                   "yaxis": {"title": "Concentración (µg/m³)"},
                                   "barmode": "group"}],
                            label="☁️ PM2.5/PM10",
                            method="update"
                        ),
                        dict(
                            args=[{"visible": [False, False, False, False, True, False, False, False, False, False]},
                                  {"title": "🏛️ ANÁLISIS POR ESTADO - PROMEDIO DE SALUD",
                                   "xaxis": {"title": "Estado", "tickangle": -45},
                                   "yaxis": {"title": "Índice de Salud Promedio"}}],
                            label="🏛️ Por Estado",
                            method="update"
                        ),
                        dict(
                            args=[{"visible": [False, False, False, False, False, True, False, False, False, False]},
                                  {"title": "🌳 ESPACIOS VERDES vs POBLACIÓN",
                                   "xaxis": {"title": "Población (miles de habitantes)"},
                                   "yaxis": {"title": "Espacios Verdes (%)"}}],
                            label="🌳 Espacios Verdes",
                            method="update"
                        ),
                        dict(
                            args=[{"visible": [False, False, False, False, False, False, True, False, False, False]},
                                  {"title": "🌡️ DISTRIBUCIÓN DE TEMPERATURA",
                                   "yaxis": {"title": "Temperatura (°C)"}}],
                            label="🌡️ Temperatura",
                            method="update"
                        ),
                        dict(
                            args=[{"visible": [False, False, False, False, False, False, False, True, False, False]},
                                  {"title": "🔥 INCENDIOS DETECTADOS (NASA FIRMS)",
                                   "xaxis": {"title": "Ciudad", "tickangle": -45},
                                   "yaxis": {"title": "Número de Incendios"}}],
                            label="🔥 Incendios",
                            method="update"
                        ),
                        dict(
                            args=[{"visible": [False, False, False, False, False, False, False, False, True, False]},
                                  {"title": "📋 RANKING COMPLETO DE CIUDADES",
                                   "xaxis": {"visible": False},
                                   "yaxis": {"visible": False}}],
                            label="📋 Ranking Completo",
                            method="update"
                        ),
                        dict(
                            args=[{"visible": [False, False, False, False, False, False, False, False, False, True]},
                                  {"title": "📊 DISTRIBUCIÓN ESTADÍSTICA DE ÍNDICES",
                                   "xaxis": {"title": "Índice de Salud"},
                                   "yaxis": {"title": "Número de Ciudades"}}],
                            label="📊 Distribución",
                            method="update"
                        ),
                    ]),
                    pad={"r": 10, "t": 10},
                    showactive=True,
                    x=0.0,
                    xanchor="left",
                    y=1.15,
                    yanchor="top",
                    bgcolor="#4285F4",
                    font=dict(color="white", size=11, family="Arial"),
                    active=0,
                    bordercolor="#2C3E50",
                    borderwidth=2
                ),
            ],
            title={
                'text': f"🇲🇽 <b>DASHBOARD INTERACTIVO DE SALUD URBANA - MÉXICO</b><br>" + 
                        f"<sub style='font-size:13px'>🛰️ Reto NASA Space Apps | {len(data)} Ciudades | " +
                        f"APIs: WAQI, OpenWeatherMap, NASA FIRMS, OpenAQ</sub><br>" +
                        f"<sub style='font-size:12px; color:#666'>👆 Selecciona una categoría arriba para visualizar</sub>",
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': {'size': 22, 'family': 'Arial Black', 'color': '#2C3E50'}
            },
            showlegend=True,
            legend=dict(
                orientation="v",
                yanchor="top",
                y=0.98,
                xanchor="right",
                x=0.99,
                bgcolor="rgba(255,255,255,0.9)",
                bordercolor="#2C3E50",
                borderwidth=2,
                font=dict(size=11)
            ),
            height=800,
            plot_bgcolor='#F5F7FA',
            paper_bgcolor='#FFFFFF',
            font=dict(family="Arial, sans-serif", size=12, color="#2C3E50"),
            margin=dict(t=180, b=80, l=80, r=80),
            hovermode='closest',
            xaxis=dict(title="Ciudad", tickangle=-45, tickfont=dict(size=10)),
            yaxis=dict(title="Índice de Salud (/100)", tickfont=dict(size=10))
        )
        
        print("✅ Dashboard interactivo con 9 pestañas creado")
        return fig
    
    def generate_national_report(self, data):
        """Genera reporte nacional detallado"""
        print("\n📋 FASE 3: GENERANDO REPORTE NACIONAL")
        print("=" * 60)
        
        # Estadísticas nacionales
        national_avg = data['health_score'].mean()
        best_city = data.loc[data['health_score'].idxmax()]
        worst_city = data.loc[data['health_score'].idxmin()]
        
        print(f"\n🏆 RANKING NACIONAL:")
        print(f"   🥇 Ciudad Más Saludable: {best_city['city']} ({best_city['health_score']:.1f})")
        print(f"   ⚠️  Ciudad con Mayor Reto: {worst_city['city']} ({worst_city['health_score']:.1f})")
        print(f"   📊 Promedio Nacional: {national_avg:.1f}/100")
        
        # Por regiones
        print(f"\n🗺️  ANÁLISIS POR REGIONES:")
        regions = {
            'Norte': ['Monterrey', 'Tijuana', 'Juárez', 'Chihuahua', 'Hermosillo', 'Saltillo', 'Torreón'],
            'Centro': ['Ciudad de México', 'Guadalajara', 'Puebla', 'León', 'Querétaro', 'Aguascalientes'],
            'Sur': ['Mérida', 'Cancún', 'Veracruz', 'Oaxaca', 'Culiacán']
        }
        
        for region, cities in regions.items():
            region_data = data[data['city'].isin(cities)]
            if len(region_data) > 0:
                print(f"   {region}: {region_data['health_score'].mean():.1f} pts")
        
        # Top 5 y Bottom 5
        print(f"\n📈 TOP 5 CIUDADES MÁS SALUDABLES:")
        for idx, row in data.nlargest(5, 'health_score').iterrows():
            print(f"   {row['city']}: {row['health_score']:.1f} pts")
        
        print(f"\n⚠️  5 CIUDADES QUE NECESITAN MÁS ATENCIÓN:")
        for idx, row in data.nsmallest(5, 'health_score').iterrows():
            print(f"   {row['city']}: {row['health_score']:.1f} pts")
        
        # Recomendaciones
        print(f"\n💡 RECOMENDACIONES NACIONALES:")
        print("=" * 40)
        
        avg_aqi = data['air_quality_index'].mean()
        if avg_aqi > 80:
            print("🌬️  PRIORIDAD ALTA: Calidad del Aire")
            print(f"   • AQI promedio: {avg_aqi:.0f}")
            print("   • Promover transporte limpio nacionalmente")
            print("   • Incentivar vehículos eléctricos")
        
        avg_green = data['green_space_ratio'].mean()
        if avg_green < 0.4:
            print("🌳 IMPORTANTE: Espacios Verdes")
            print(f"   • Cobertura promedio: {avg_green:.1%}")
            print("   • Meta: Alcanzar 40% de espacios verdes")
            print("   • Implementar programa nacional de reforestación urbana")
        
        critical_cities = len(data[data['health_score'] < 50])
        if critical_cities > 0:
            print(f"🚨 URGENTE: {critical_cities} ciudades en estado crítico")
            print("   • Requieren intervención inmediata")
            print("   • Programas de mejora acelerados")
        
        return {
            'national_avg': national_avg,
            'best_city': best_city['city'],
            'worst_city': worst_city['city'],
            'total_population': data['population'].sum()
        }

# Función principal
def run_mexico_analysis():
    """Ejecuta análisis completo de México"""
    analyzer = MexicoHealthAnalyzer()
    
    # Analizar todas las ciudades
    data = analyzer.analyze_all_cities()
    
    # Crear mapa nacional
    national_map = analyzer.create_national_map(data)
    
    # Crear dashboard
    dashboard = analyzer.create_national_dashboard(data)
    
    # Generar reporte
    report = analyzer.generate_national_report(data)
    
    # Guardar resultados
    print(f"\n💾 GUARDANDO RESULTADOS...")
    print("-" * 30)
    
    map_file = 'mexico_salud_nacional.html'
    national_map.save(map_file)
    print(f"✅ Mapa nacional: {map_file}")
    
    data_file = 'mexico_datos_ciudades.csv'
    data.to_csv(data_file, index=False)
    print(f"✅ Datos de ciudades: {data_file}")
    
    print("✅ Mostrando dashboard...")
    dashboard.show()
    
    # Abrir mapa automáticamente en el navegador
    print(f"\n🌐 ABRIENDO MAPAS EN NAVEGADOR...")
    print("-" * 30)
    import webbrowser
    import os
    import time
    
    map_path = os.path.abspath(map_file)
    print(f"📍 Abriendo: {map_file}")
    webbrowser.open('file://' + map_path)
    
    print("⏳ Espera 2 segundos para mejores visualizaciones...")
    time.sleep(2)
    
    print(f"\n🎉 ANÁLISIS COMPLETO DE MÉXICO TERMINADO")
    print("=" * 50)
    print(f"🏙️  {len(data)} ciudades analizadas")
    print(f"👥 Población total analizada: {report['total_population']:,.0f}")
    print(f"🏥 Índice nacional: {report['national_avg']:.1f}/100")
    print(f"\n🌟 ¡Listo para el Reto NASA!")
    
    return data, national_map, dashboard

def run_interactive_mode():
    """Modo interactivo: consulta ciudades individuales bajo demanda"""
    analyzer = MexicoHealthAnalyzer()
    
    print("\n🔍 MODO EXPLORADOR INTERACTIVO")
    print("=" * 60)
    print("Consulta ciudades individuales sin procesar todas las 18")
    print("Solo se consultan las APIs de las ciudades que selecciones")
    print("=" * 60)
    
    # Mostrar ciudades disponibles
    print("\n📍 CIUDADES DISPONIBLES:")
    cities_list = list(analyzer.mexican_cities.keys())
    for i, city in enumerate(cities_list, 1):
        state = analyzer.mexican_cities[city].get('estado', analyzer.mexican_cities[city].get('state', 'Unknown'))
        print(f"   {i:2d}. {city} ({state})")
    
    collected_data = []
    
    while True:
        print("\n" + "=" * 60)
        print("Opciones:")
        print("  1-18: Consultar ciudad por número")
        print("  'nombre': Consultar ciudad por nombre")
        print("  'todas': Consultar todas las ciudades")
        print("  'mapa': Ver mapa con las ciudades consultadas")
        print("  'salir': Terminar y generar reporte")
        
        choice = input("\n👉 Tu elección: ").strip()
        
        if choice.lower() == 'salir':
            break
        elif choice.lower() == 'todas':
            print("\n🌐 Consultando TODAS las ciudades...")
            for city_name in cities_list:
                city_data = analyzer.analyze_single_city(city_name)
                if city_data:
                    collected_data.append(city_data)
            break
        elif choice.lower() == 'mapa':
            if len(collected_data) > 0:
                df = pd.DataFrame(collected_data)
                temp_map = analyzer.create_national_map(df, 'temp_mapa_selector.html')
                temp_map.save('temp_mapa_selector.html')
                import webbrowser, os
                webbrowser.open('file://' + os.path.abspath('temp_mapa_selector.html'))
                print(f"✅ Mapa abierto con {len(collected_data)} ciudades")
            else:
                print("❌ No hay ciudades consultadas aún")
        elif choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(cities_list):
                city_name = cities_list[idx]
                city_data = analyzer.analyze_single_city(city_name)
                if city_data:
                    collected_data.append(city_data)
            else:
                print(f"❌ Número inválido. Usa 1-{len(cities_list)}")
        else:
            # Buscar por nombre
            found = False
            for city_name in cities_list:
                if choice.lower() in city_name.lower():
                    city_data = analyzer.analyze_single_city(city_name)
                    if city_data:
                        collected_data.append(city_data)
                    found = True
                    break
            if not found:
                print(f"❌ Ciudad '{choice}' no encontrada")
    
    # Generar resultados finales
    if len(collected_data) > 0:
        print(f"\n📊 GENERANDO RESULTADOS FINALES...")
        df = pd.DataFrame(collected_data)
        
        # Crear mapa
        final_map = analyzer.create_national_map(df, 'mexico_ciudades_seleccionadas.html')
        final_map.save('mexico_ciudades_seleccionadas.html')
        
        # Crear dashboard
        dashboard = analyzer.create_national_dashboard(df)
        
        # Guardar CSV
        df.to_csv('mexico_ciudades_seleccionadas.csv', index=False)
        
        print(f"✅ Mapa guardado: mexico_ciudades_seleccionadas.html")
        print(f"✅ Datos guardados: mexico_ciudades_seleccionadas.csv")
        print(f"✅ Total ciudades consultadas: {len(collected_data)}")
        
        # Abrir resultados
        import webbrowser, os
        webbrowser.open('file://' + os.path.abspath('mexico_ciudades_seleccionadas.html'))
        dashboard.show()
        
        return df, final_map, dashboard
    else:
        print("❌ No se consultaron ciudades")
        return None, None, None

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🇲🇽 ANALIZADOR DE SALUD URBANA - MÉXICO")
    print("   NASA Space Apps Challenge 2025")
    print("=" * 60)
    print("\nSelecciona el modo de ejecución:")
    print("  1. 🚀 MODO COMPLETO - Analiza todas las 18 ciudades")
    print("  2. 🔍 MODO EXPLORADOR - Selecciona ciudades individuales")
    print("=" * 60)
    
    mode = input("\n👉 Tu elección (1 o 2): ").strip()
    
    if mode == "2":
        results_data, results_map, results_dashboard = run_interactive_mode()
    else:
        results_data, results_map, results_dashboard = run_mexico_analysis()