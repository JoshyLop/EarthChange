"""
MAPA INTERACTIVO DE MÉXICO - Navegación Jerárquica Estado → Ciudades
Sistema de dos niveles: 
1. Selecciona un estado para explorar
2. Elige una ciudad/municipio para consultar APIs en tiempo real
"""

from flask import Flask, render_template, jsonify, request, send_from_directory
from mexico_health_analyzer import MexicoHealthAnalyzer
from mexico_data import ESTADOS_MEXICO, MUNICIPIOS_POR_ESTADO
import json
import os

app = Flask(__name__, static_folder='.')
analyzer = MexicoHealthAnalyzer()

# Datos de estados y municipios importados desde mexico_data.py
# ESTADOS_MEXICO y MUNICIPIOS_POR_ESTADO ahora se importan del módulo mexico_data

# Cargar municipios en el analyzer para análisis extendido
analyzer.load_municipios_from_external(MUNICIPIOS_POR_ESTADO)

@app.route('/health')
def health_check():
    """Health check endpoint para Render"""
    return {'status': 'healthy', 'service': 'NASA Earth Change'}, 200

@app.route('/')
def index():
    """Página principal con mapa interactivo jerárquico"""
    # Crear diccionario completo de todas las ciudades/municipios
    all_cities_dict = {}
    
    # Agregar ciudades del analyzer (excluyendo estados ya definidos en MUNICIPIOS_POR_ESTADO)
    estados_definidos = set(MUNICIPIOS_POR_ESTADO.keys())
    
    for city_name, city_info in analyzer.mexican_cities.items():
        estado = city_info.get('estado', city_info.get('state', 'Unknown'))
        # Solo agregar si el estado NO está en MUNICIPIOS_POR_ESTADO
        if estado not in estados_definidos:
            # Usar clave única con estado para evitar conflictos
            clave_unica = f"{city_name}, {estado}"
            all_cities_dict[clave_unica] = {
                'coords': city_info['coords'],
                'estado': estado,
                'poblacion': city_info.get('pop', city_info.get('poblacion', 0)),
                'lat': city_info['coords'][0],
                'lon': city_info['coords'][1],
                'tipo': city_info.get('tipo', 'ciudad'),
                'nombre': city_name  # Agregar nombre original para el frontend
            }
    
    # Agregar todos los municipios de MUNICIPIOS_POR_ESTADO (prioridad completa)
    for estado, municipios in MUNICIPIOS_POR_ESTADO.items():
        for municipio_name, municipio_info in municipios.items():
            # Usar clave única con estado para evitar conflictos
            clave_unica = f"{municipio_name}, {estado}"
            all_cities_dict[clave_unica] = {
                'coords': municipio_info['coords'],
                'estado': municipio_info['estado'],
                'poblacion': municipio_info['poblacion'],
                'lat': municipio_info['lat'],
                'lon': municipio_info['lon'],
                'tipo': municipio_info.get('tipo', 'municipio'),
                'nombre': municipio_name  # Agregar nombre original para el frontend
            }
    
    return render_template('interactive_map.html', 
                         estados=ESTADOS_MEXICO,
                         cities=all_cities_dict)

@app.route('/img/<path:filename>')
def serve_image(filename):
    """Servir archivos de la carpeta img"""
    return send_from_directory('img', filename)

@app.route('/api/analyze_city', methods=['POST'])
def analyze_city():
    """API endpoint para analizar una ciudad bajo demanda"""
    data = request.get_json()
    city_name = data.get('city_name')
    
    # Buscar la ciudad en ambos diccionarios
    city_found = False
    
    # Primero buscar en MUNICIPIOS_POR_ESTADO
    for estado, municipios in MUNICIPIOS_POR_ESTADO.items():
        if city_name in municipios:
            city_found = True
            break
    
    # Si no se encuentra, buscar en el analyzer tradicional
    if not city_found and city_name not in analyzer.mexican_cities:
        return jsonify({'error': 'Ciudad no encontrada'}), 404
    
    print(f"\n🔍 Consultando APIs para: {city_name}")
    
    try:
        # Analizar ciudad individual
        city_data = analyzer.analyze_single_city(city_name)
        
        if city_data:
            # Adaptar formato para el frontend
            response_data = {
                'air_quality': {
                    'aqi': city_data.get('air_quality_index', 0),
                    'status': get_aqi_status(city_data.get('air_quality_index', 0)),
                    'pm25': city_data.get('pm25_concentration'),
                    'pm10': city_data.get('pm10_concentration')
                },
                'weather': {
                    'temperatura': city_data.get('temperature_avg'),
                    'humedad': city_data.get('humidity_avg')
                },
                'fires': city_data.get('fires_detected', 0),
                'vegetation': {
                    'ndvi_promedio': city_data.get('ndvi_value', 0),
                    'cobertura_verde': int(city_data.get('ndvi_value', 0) * 100)
                },
                'health_score': city_data.get('health_score', 0),
                'ai_insights': {
                    'prediction': city_data.get('ai_prediction', 'No disponible'),
                    'recommendations': city_data.get('ai_recommendations', [])
                }
            }
            
            return jsonify({
                'success': True,
                'data': response_data
            })
        else:
            return jsonify({'error': 'No se pudo analizar la ciudad'}), 500
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

def get_aqi_status(aqi):
    """Convierte AQI en status legible"""
    if aqi <= 50:
        return 'Bueno'
    elif aqi <= 100:
        return 'Moderado'
    elif aqi <= 150:
        return 'Malo'
    elif aqi <= 200:
        return 'Muy Malo'
    elif aqi <= 300:
        return 'Peligroso'
    else:
        return 'Muy Peligroso'

@app.route('/api/estado/<estado_nombre>')
def get_cities_by_state(estado_nombre):
    """Obtiene información y ciudades de un estado específico"""
    
    # Información del estado
    estado_info = ESTADOS_MEXICO.get(estado_nombre)
    if not estado_info:
        return jsonify({'error': 'Estado no encontrado'}), 404
    
    # Municipios del estado desde MUNICIPIOS_POR_ESTADO
    municipios_in_state = []
    if estado_nombre in MUNICIPIOS_POR_ESTADO:
        for municipio_name, municipio_info in MUNICIPIOS_POR_ESTADO[estado_nombre].items():
            municipios_in_state.append({
                'name': municipio_name,
                'lat': municipio_info['lat'],
                'lon': municipio_info['lon'],
                'poblacion': municipio_info['poblacion'],  # Consistente con 'poblacion'
                'estado': municipio_info['estado'],
                'tipo': municipio_info['tipo'],
                'coords': municipio_info['coords']
            })
    
    # También incluir ciudades del analyzer si no están en el diccionario completo
    municipios_agregados = set(m['name'] for m in municipios_in_state)
    for name, info in analyzer.mexican_cities.items():
        if (info.get('estado') == estado_nombre or info.get('state') == estado_nombre) and name not in municipios_agregados:
            municipios_in_state.append({
                'name': name,
                'lat': info['coords'][0],
                'lon': info['coords'][1],
                'poblacion': info.get('pop', info.get('poblacion', 0)),
                'estado': info.get('estado', info.get('state', estado_nombre)),
                'tipo': info.get('tipo', 'ciudad'),
                'coords': info['coords']
            })
    
    return jsonify({
        'estado': estado_nombre,
        'info': {
            'capital': estado_info.get('capital'),
            'poblacion': estado_info.get('poblacion'),
            'superficie': estado_info.get('superficie'),
            'descripcion': estado_info.get('info')
        },
        'municipios': municipios_in_state,
        'count': len(municipios_in_state)
    })

@app.route('/api/cities')
def get_cities():
    """Obtiene lista de ciudades disponibles de todos los estados"""
    cities_data = []
    
    # Obtener ciudades del diccionario completo MUNICIPIOS_POR_ESTADO
    for estado, municipios in MUNICIPIOS_POR_ESTADO.items():
        for municipio_name, municipio_info in municipios.items():
            cities_data.append({
                'name': municipio_name,
                'estado': municipio_info['estado'],  # Usamos 'estado' en lugar de 'state'
                'lat': municipio_info['lat'],
                'lon': municipio_info['lon'],
                'poblacion': municipio_info['poblacion'],  # Usamos 'poblacion' en lugar de 'pop'
                'tipo': municipio_info['tipo'],
                'coords': municipio_info['coords']
            })
    
    # También agregar las ciudades del analyzer para compatibilidad (evitando duplicados)
    municipios_agregados = set(cities_data[i]['name'] for i in range(len(cities_data)))
    for name, info in analyzer.mexican_cities.items():
        if name not in municipios_agregados:
            cities_data.append({
                'name': name,
                'estado': info.get('state', info.get('estado', 'No especificado')),
                'lat': info['coords'][0],
                'lon': info['coords'][1],
                'poblacion': info.get('pop', info.get('poblacion', 0)),
                'tipo': info.get('tipo', 'ciudad'),
                'coords': info['coords']
            })
    
    return jsonify({
        'total_municipios': len(cities_data),
        'municipios': cities_data
    })

if __name__ == '__main__':
    # Configuración para despliegue en producción
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    
    print("\n" + "=" * 60)
    print("🗺️  MAPA INTERACTIVO DE SALUD URBANA - MÉXICO")
    print("=" * 60)
    
    if debug:
        print("🌐 Servidor iniciando en modo DESARROLLO")
        print(f"🔗 URL Local: http://127.0.0.1:{port}")
    else:
        print("🌐 Servidor iniciando en modo PRODUCCIÓN")
        print(f"🔗 Puerto: {port}")
    
    print("👆 Haz clic en las ciudades del mapa para consultar datos")
    print("🛑 Presiona Ctrl+C para detener el servidor")
    print("=" * 60 + "\n")
    
    app.run(debug=debug, host=host, port=port)
