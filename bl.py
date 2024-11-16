# bl.py
import json
import scraper
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def get_all_stations():
    try:
        with open('stations.json', 'r') as file:
            file_data = json.load(file)
        return {
            'code': 200,
            'result': file_data
        }
    except FileNotFoundError:
        logger.error("stations.json file not found")
        return {
            'code': 500,
            'msg': 'Station data file not found'
        }
    except json.JSONDecodeError:
        logger.error("Error decoding stations.json")
        return {
            'code': 500,
            'msg': 'Error reading station data'
        }

def get_station_by_id(id):
    try:
        with open('stations.json', 'r') as file:
            file_data = json.load(file)
        
        for station in file_data:
            if station['stationId'] == id:
                return {
                    'code': 200,
                    'result': station
                }
        
        return {
            'code': 404,
            'msg': f'No station with ID {id} found'
        }
    except Exception as e:
        logger.error(f"Error in get_station_by_id: {str(e)}")
        return {
            'code': 500,
            'msg': f'Error retrieving station data: {str(e)}'
        }

def get_station_weather(id):
    try:
        # First verify if station exists
        station_info = get_station_by_id(id)
        if station_info['code'] == 404:
            return station_info
        
        data = scraper.get_station_data(id)
        if 'error' in data:
            return {
                'code': data.get('code', 500),
                'msg': data['error']
            }
            
        return {
            'code': 200,
            'result': data
        }
    except Exception as e:
        logger.error(f"Error in get_station_weather: {str(e)}")
        return {
            'code': 500,
            'msg': f'Error retrieving weather data: {str(e)}'
        }

def get_weather_alerts():
    try:
        data = scraper.get_alerts()
        if 'error' in data:
            return {
                'code': data.get('code', 500),
                'msg': data['error']
            }
        return {
            'code': 200,
            'result': data
        }
    except Exception as e:
        logger.error(f"Error in get_weather_alerts: {str(e)}")
        return {
            'code': 500,
            'msg': f'Error retrieving alert data: {str(e)}'
        }

def get_state_alerts(state):
    try:
        data = scraper.get_alerts()
        if 'error' in data:
            return {
                'code': data.get('code', 500),
                'msg': data['error']
            }
        
        # Get alerts for specific state
        state = state.lower()
        state_alerts = data.get('alerts_by_state', {}).get(state, [])
        
        if not state_alerts:
            return {
                'code': 404,
                'msg': f'No alerts found for state: {state}'
            }
        
        return {
            'code': 200,
            'result': {
                'state': state,
                'alerts': state_alerts,
                'total_alerts': len(state_alerts),
                'last_updated': data.get('last_updated')
            }
        }
    except Exception as e:
        logger.error(f"Error in get_state_alerts: {str(e)}")
        return {
            'code': 500,
            'msg': f'Error retrieving state alert data: {str(e)}'
        }

def get_alerts_summary():
    try:
        data = scraper.get_alerts()
        if 'error' in data:
            return {
                'code': data.get('code', 500),
                'msg': data['error']
            }
        
        # Count alerts by level
        alert_levels = {
            'No Warning': 0,
            'Watch': 0,
            'Alert': 0,
            'Warning': 0
        }
        
        for alert in data.get('alerts', []):
            level = alert.get('alert_level', 'Unknown')
            if level in alert_levels:
                alert_levels[level] += 1
        
        summary = {
            'total_alerts': len(data.get('alerts', [])),
            'states_affected': len(data.get('alerts_by_state', {})),
            'alert_levels': alert_levels,
            'last_updated': data.get('last_updated'),
            'timestamp': datetime.now().isoformat()
        }
        
        return {
            'code': 200,
            'result': summary
        }
    except Exception as e:
        logger.error(f"Error in get_alerts_summary: {str(e)}")
        return {
            'code': 500,
            'msg': f'Error retrieving alerts summary: {str(e)}'
        }