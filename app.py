from flask import Flask, jsonify
import bl
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import waitress
import os
import logging

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Retrieve rate limit values from environment variables
RATE_LIMIT_DAILY = int(os.getenv('RATE_LIMIT_DAILY', 1000))
RATE_LIMIT_HOURLY = int(os.getenv('RATE_LIMIT_HOURLY', 100))

app = Flask(__name__)

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[
        f"{RATE_LIMIT_DAILY} per day",
        f"{RATE_LIMIT_HOURLY} per hour"
    ]
)

limiter.init_app(app)

@app.route('/station/<string:id>')
def get_station(id):
    try:
        logger.debug(f"Station request received for ID: {id}")
        if id == 'all':
            result = bl.get_all_stations()
        else:
            result = bl.get_station_by_id(int(id))
        return jsonify(result), result['code']
    except ValueError:
        return jsonify({
            'code': 400,
            'msg': 'Invalid station ID format'
        }), 400
    except Exception as e:
        logger.error(f"Error in get_station: {str(e)}")
        return jsonify({
            'code': 500,
            'msg': 'Internal server error'
        }), 500

@app.route('/weather/<int:id>')
def get_station_weather(id):
    try:
        logger.debug(f"Weather request received for station ID: {id}")
        result = bl.get_station_weather(id)
        return jsonify(result), result['code']
    except Exception as e:
        logger.error(f"Error in get_station_weather: {str(e)}")
        return jsonify({
            'code': 500,
            'msg': 'Internal server error'
        }), 500

@app.route('/alerts')
def get_all_alerts():
    try:
        logger.debug("Weather alerts request received")
        result = bl.get_weather_alerts()
        return jsonify(result), result['code']
    except Exception as e:
        logger.error(f"Error in get_all_alerts: {str(e)}")
        return jsonify({
            'code': 500,
            'msg': 'Internal server error'
        }), 500

@app.route('/alerts/state/<string:state>')
def get_state_alerts(state):
    try:
        logger.debug(f"Weather alerts request received for state: {state}")
        result = bl.get_state_alerts(state)
        return jsonify(result), result['code']
    except Exception as e:
        logger.error(f"Error in get_state_alerts: {str(e)}")
        return jsonify({
            'code': 500,
            'msg': 'Internal server error'
        }), 500

@app.route('/alerts/summary')
def get_alerts_summary():
    try:
        logger.debug("Weather alerts summary request received")
        result = bl.get_alerts_summary()
        return jsonify(result), result['code']
    except Exception as e:
        logger.error(f"Error in get_alerts_summary: {str(e)}")
        return jsonify({
            'code': 500,
            'msg': 'Internal server error'
        }), 500

if __name__ == '__main__':
    logger.info("Starting weather API server...")
    try:
        waitress.serve(app, host='0.0.0.0', port=1875)
    except Exception as e:
        logger.error(f"Server failed to start: {str(e)}")