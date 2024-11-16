# scraper.py
import requests
from bs4 import BeautifulSoup
import urllib3
import logging
import re

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def get_station_data(id):
    try:
        URL = f'https://mausam.imd.gov.in/responsive/stationWiseNowcastGIS.php?id={id}'
        logger.debug(f"Fetching data from URL: {URL}")

        # Add headers to mimic a browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

        session = requests.Session()
        response = session.get(URL, verify=False, headers=headers, timeout=30)
        logger.debug(f"Response status code: {response.status_code}")
        
        if response.status_code != 200:
            return {
                'error': f'Server returned status code {response.status_code}',
                'code': response.status_code
            }

        html_text = response.text
        logger.debug(f"Response length: {len(html_text)}")

        # Log the first part of the response for debugging
        logger.debug(f"Response preview: {html_text[:500]}")

        soup = BeautifulSoup(html_text, 'html.parser')
        
        # Find the main data table
        table = soup.find('table', {'class': 'table'})
        if not table:
            logger.error("No table found in the response")
            return {
                'error': 'Weather data table not found',
                'code': 500
            }

        # Extract data using more robust methods
        def find_value_by_label(label_text):
            try:
                label_cell = soup.find(text=re.compile(label_text, re.IGNORECASE))
                if label_cell:
                    # Try to find the next cell with the value
                    next_cell = label_cell.find_parent('td').find_next_sibling('td')
                    if next_cell:
                        return next_cell.text.strip()
            except Exception as e:
                logger.error(f"Error finding value for {label_text}: {str(e)}")
            return "0"

        def safe_float(value, default=0.0):
            try:
                # Remove any non-numeric characters except decimal point and minus
                cleaned = re.sub(r'[^0-9.-]', '', value)
                return float(cleaned)
            except (ValueError, TypeError):
                return default

        # Extract temperature data
        max_temp = find_value_by_label('Maximum Temperature')
        min_temp = find_value_by_label('Minimum Temperature')
        max_dep = find_value_by_label('Departure from Normal Max')
        min_dep = find_value_by_label('Departure from Normal Min')
        
        # Extract humidity data
        rh_0830 = find_value_by_label('Relative Humidity.*0830')
        rh_1730 = find_value_by_label('Relative Humidity.*1730')

        # Extract astronomical data
        sunrise = find_value_by_label('Sunrise')
        sunset = find_value_by_label('Sunset')
        moonrise = find_value_by_label('Moonrise')
        moonset = find_value_by_label('Moonset')

        # Extract forecast data
        def get_forecast_data(day_number):
            try:
                date_cell = soup.find(text=re.compile(f"Day {day_number}"))
                if date_cell:
                    date_row = date_cell.find_parent('tr')
                    if date_row:
                        cells = date_row.find_all('td')
                        if len(cells) >= 4:
                            return {
                                'day': day_number,
                                'date': cells[0].text.strip(),
                                'min': safe_float(cells[1].text.strip()),
                                'max': safe_float(cells[2].text.strip()),
                                'condition': cells[3].text.strip()
                            }
            except Exception as e:
                logger.error(f"Error getting forecast for day {day_number}: {str(e)}")
            return None

        # Get forecast for 7 days
        forecast = []
        for day in range(1, 8):
            day_forecast = get_forecast_data(day)
            if day_forecast:
                forecast.append(day_forecast)

        if not forecast:
            logger.warning("No forecast data found")

        weather_data = {
            'temperature': {
                'max': {
                    'value': safe_float(max_temp),
                    'departure': safe_float(max_dep)
                },
                'min': {
                    'value': safe_float(min_temp),
                    'departure': safe_float(min_dep)
                }
            },
            'humidity': {
                'morning': safe_float(rh_0830),
                'evening': safe_float(rh_1730)
            },
            'astronomical': {
                'sunrise': sunrise,
                'sunset': sunset,
                'moonrise': moonrise,
                'moonset': moonset
            },
            'forecast': forecast
        }

        logger.debug(f"Successfully extracted weather data: {weather_data}")
        return weather_data

    except requests.Timeout:
        logger.error("Request timed out")
        return {
            'error': 'Request timed out',
            'code': 504
        }
    except requests.RequestException as e:
        logger.error(f"Request error: {str(e)}")
        return {
            'error': f'Network error: {str(e)}',
            'code': 500
        }
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {
            'error': f'Unexpected error: {str(e)}',
            'code': 500
        }
    
    logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def parse_alert_level(color_class):
    """Convert color class to alert level"""
    color_map = {
        'green': 'No Warning',
        'yellow': 'Watch',
        'orange': 'Alert',
        'red': 'Warning'
    }
    # Clean the color class string and match it to our map
    color = color_class.lower().strip()
    for key in color_map:
        if key in color:
            return color_map[key]
    return 'Unknown'

def get_alerts():
    try:
        URL = 'https://mausam.imd.gov.in/responsive/stationWiseNowcastGIS.php'
        logger.debug(f"Fetching alerts from URL: {URL}")

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5'
        }

        session = requests.Session()
        response = session.get(URL, verify=False, headers=headers, timeout=30)
        logger.debug(f"Response status code: {response.status_code}")

        if response.status_code != 200:
            return {
                'error': f'Server returned status code {response.status_code}',
                'code': response.status_code
            }

        html_text = response.text
        soup = BeautifulSoup(html_text, 'html.parser')

        # Find the update time
        update_time = None
        time_div = soup.find('div', string=re.compile(r'Last Updated.*'))
        if time_div:
            update_time = time_div.text.strip()

        # Extract map data
        alerts = []
        script_tags = soup.find_all('script')
        for script in script_tags:
            if not script.string:
                continue
            
            # Look for marker data in different possible formats
            for pattern in [
                r'var\s+markers\s*=\s*(\[.*?\]);',
                r'var\s+points\s*=\s*(\[.*?\]);',
                r'var\s+locations\s*=\s*(\[.*?\]);'
            ]:
                markers_match = re.search(pattern, script.string, re.DOTALL)
                if markers_match:
                    try:
                        # Clean up the JavaScript array to make it valid JSON
                        markers_str = markers_match.group(1)
                        # Quote all keys
                        markers_str = re.sub(r'(\w+):', r'"\1":', markers_str)
                        # Replace single quotes with double quotes
                        markers_str = re.sub(r'\'', '"', markers_str)
                        # Handle any special characters in text
                        markers_str = markers_str.replace('\n', '\\n').replace('\r', '\\r')
                        
                        map_data = json.loads(markers_str)
                        
                        for marker in map_data:
                            alert = {
                                'location': marker.get('location', '').strip(),
                                'state': marker.get('state', '').strip(),
                                'alert_level': marker.get('alertLevel', 'Unknown'),
                                'warning_type': marker.get('warningType', '').strip(),
                                'details': marker.get('description', '').strip(),
                                'valid_time': marker.get('validTime', '').strip(),
                                'coordinates': {
                                    'lat': float(marker.get('lat', 0)),
                                    'lng': float(marker.get('lng', 0))
                                }
                            }
                            
                            # Only add if we have a valid location
                            if alert['location']:
                                alerts.append(alert)
                        
                        break  # Break if we successfully parsed the data
                    except json.JSONDecodeError as e:
                        logger.error(f"Error parsing map data: {e}")
                    except Exception as e:
                        logger.error(f"Error processing marker data: {e}")

        # If no alerts found in map data, try parsing the table
        if not alerts:
            alert_table = soup.find('table', {'class': ['table', 'alert-table']})
            if alert_table:
                rows = alert_table.find_all('tr')
                for row in rows[1:]:  # Skip header row
                    cols = row.find_all('td')
                    if len(cols) >= 3:
                        alert_color = ''
                        # Try to get color from cell background or class
                        for col in cols:
                            background_color = col.get('style', '')
                            if 'background' in background_color.lower():
                                alert_color = background_color
                                break
                        
                        alert = {
                            'location': cols[0].text.strip(),
                            'alert_level': parse_alert_level(alert_color),
                            'warning_type': cols[1].text.strip(),
                            'details': cols[2].text.strip(),
                            'valid_time': cols[3].text.strip() if len(cols) > 3 else None
                        }
                        alerts.append(alert)

        # Group alerts by state
        alerts_by_state = {}
        for alert in alerts:
            state = alert.get('state', 'Unknown')
            if state not in alerts_by_state:
                alerts_by_state[state] = []
            alerts_by_state[state].append(alert)

        result = {
            'last_updated': update_time,
            'alerts': alerts,
            'alerts_by_state': alerts_by_state,
            'total_alerts': len(alerts),
            'states_affected': len(alerts_by_state)
        }

        logger.debug(f"Successfully extracted {len(alerts)} alerts from {len(alerts_by_state)} states")
        return result

    except requests.Timeout:
        logger.error("Request timed out")
        return {
            'error': 'Request timed out',
            'code': 504
        }
    except requests.RequestException as e:
        logger.error(f"Request error: {str(e)}")
        return {
            'error': f'Network error: {str(e)}',
            'code': 500
        }
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {
            'error': f'Unexpected error: {str(e)}',
            'code': 500
        }
