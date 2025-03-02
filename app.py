import streamlit as st
from datetime import datetime
import pytz
import time
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import logging
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Set page configuration
st.set_page_config(
    page_title="Welcome App",
    page_icon="🤖",
    layout="wide"
)

# Custom CSS for styling with rainbow background animation
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(
            45deg,
            #ff0000,
            #ff7f00,
            #ffff00,
            #00ff00,
            #0000ff,
            #4b0082,
            #8f00ff
        );
        background-size: 400% 400%;
        animation: rainbow 15s ease infinite;
    }
    
    @keyframes rainbow {
        0% {
            background-position: 0% 50%;
        }
        50% {
            background-position: 100% 50%;
        }
        100% {
            background-position: 0% 50%;
        }
    }
    
    /* Make content more readable with semi-transparent background */
    .content-container {
        background-color: rgba(0, 0, 0, 0.6);
        border-radius: 15px;
        padding: 20px;
        margin: 10px;
        backdrop-filter: blur(5px);
    }
    
    .welcome-text {
        font-size: 40px;
        font-weight: bold;
        text-align: center;
        color: white;
        text-shadow: 2px 2px 4px #000000;
        padding: 20px;
        position: absolute;
        width: 100%;
        top: 160px;
    }
    .time-text {
        font-size: 30px;
        text-align: center;
        color: white;
        font-weight: bold;
        text-shadow: 2px 2px 4px #000000;
        padding: 10px;
    }
    .robot-container {
        text-align: center;
        margin: 20px;
        position: relative;
    }
    .robot {
        font-size: 120px;
        animation: hover 3s infinite;
        text-shadow: 0 0 20px #ff00ff,
                     0 0 30px #ff00ff,
                     0 0 40px #ff00ff;
        position: relative;
    }
    .robot::after {
        content: '⚡';
        font-size: 30px;
        position: absolute;
        top: 20px;
        right: -20px;
        animation: spark 1s infinite;
    }
    @keyframes hover {
        0% { transform: translateY(0) rotate(0deg); }
        25% { transform: translateY(-10px) rotate(3deg); }
        50% { transform: translateY(0) rotate(0deg); }
        75% { transform: translateY(-10px) rotate(-3deg); }
        100% { transform: translateY(0) rotate(0deg); }
    }
    @keyframes spark {
        0%, 100% { opacity: 0; }
        50% { opacity: 1; }
    }
    .robot-text {
        font-family: 'Courier New', monospace;
        font-size: 24px;
        color: #ff00ff;
        text-shadow: 0 0 10px #ff00ff;
        animation: glitch 2s infinite;
    }
    @keyframes glitch {
        0% { transform: translate(0) }
        20% { transform: translate(-2px, 2px) }
        40% { transform: translate(-2px, -2px) }
        60% { transform: translate(2px, 2px) }
        80% { transform: translate(2px, -2px) }
        100% { transform: translate(0) }
    }
    .metric-container {
        background-color: rgba(0, 0, 0, 0.5);
        padding: 20px;
        border-radius: 10px;
        margin: 10px;
    }
    @keyframes bounce {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-20px); }
    }
    /* Override Streamlit's default text colors */
    .stMetric {
        color: white !important;
    }
    .stMetric > div {
        color: white !important;
    }
    .stMetric label {
        color: white !important;
    }
    .weather-container {
        text-align: center;
        margin: 20px;
        position: relative;
        height: 200px;
        padding-top: 20px;
    }
    .sun {
        font-size: 80px;
        position: absolute;
        left: 50%;
        top: 20px;
        transform: translateX(-50%);
        animation: sunRotate 10s linear infinite;
        text-shadow: 0 0 20px #FFD700,
                     0 0 30px #FFA500,
                     0 0 40px #FF8C00;
    }
    .rain {
        font-size: 40px;
        position: absolute;
        top: 80px;
        left: 50%;
        transform: translateX(-50%);
        display: flex;
        gap: 10px;
    }
    .raindrop {
        animation: rainFall 1.5s linear infinite;
        opacity: 0.8;
        text-shadow: 0 0 10px #00BFFF,
                     0 0 15px #1E90FF;
    }
    .raindrop:nth-child(2) { animation-delay: 0.5s; }
    .raindrop:nth-child(3) { animation-delay: 1s; }
    
    @keyframes sunRotate {
        0% { transform: translateX(-50%) rotate(0deg); }
        100% { transform: translateX(-50%) rotate(360deg); }
    }
    @keyframes rainFall {
        0% {
            transform: translateY(0) rotate(0deg);
            opacity: 0.8;
        }
        80% {
            transform: translateY(40px) rotate(15deg);
            opacity: 0.5;
        }
        100% {
            transform: translateY(60px) rotate(20deg);
            opacity: 0;
        }
    }
    .weather-text {
        font-family: 'Courier New', monospace;
        font-size: 24px;
        color: #00BFFF;
        text-shadow: 0 0 10px #00BFFF;
        animation: glitch 2s infinite;
        position: absolute;
        width: 100%;
        top: 140px;
    }
    </style>
""", unsafe_allow_html=True)

# Update the API configuration
WAQI_API_KEY = "8371396831b407f604fae5379c764aa6788c2718"  # Get free token from https://aqicn.org/data-platform/token/
AQI_LEVELS = {
    'Good': {
        "range": (0, 50), 
        "color": "green", 
        "delta_color": "normal",
        "description": "Air quality is satisfactory"
    },
    'Moderate': {
        "range": (51, 100), 
        "color": "yellow", 
        "delta_color": "normal",
        "description": "Moderate air quality"
    },
    'Unhealthy for Sensitive': {
        "range": (101, 150), 
        "color": "orange", 
        "delta_color": "inverse",
        "description": "Unhealthy for sensitive groups"
    },
    'Unhealthy': {
        "range": (151, 200), 
        "color": "red", 
        "delta_color": "inverse",
        "description": "Health effects can be felt by all"
    },
    'Very Unhealthy': {
        "range": (201, 300), 
        "color": "purple", 
        "delta_color": "inverse",
        "description": "Health warnings of emergency conditions"
    },
    'Hazardous': {
        "range": (301, 500), 
        "color": "maroon", 
        "delta_color": "inverse",
        "description": "Health alert: everyone may experience effects"
    }
}

def get_aqi_level(aqi_value):
    """Determine AQI level based on value"""
    for level, info in AQI_LEVELS.items():
        if info['range'][0] <= aqi_value <= info['range'][1]:
            return {
                'level': level,
                'color': info['color'],
                'delta_color': info['delta_color'],
                'description': info['description']
            }
    return {
        'level': 'Unknown',
        'color': 'gray',
        'delta_color': 'normal',
        'description': 'Unable to determine AQI level'
    }

def get_weather_data(lat, lon):
    """Fetch weather and AQI data"""
    try:
        logger.info(f"Fetching weather data for coordinates: {lat}, {lon}")
        
        # Get AQI data from WAQI
        aqi_url = f"https://api.waqi.info/feed/geo:{lat};{lon}/?token={WAQI_API_KEY}"
        logger.debug(f"Making API request to: {aqi_url}")
        
        aqi_response = requests.get(aqi_url)
        logger.debug(f"API Response Status Code: {aqi_response.status_code}")
        logger.debug(f"API Response Content: {aqi_response.text}")
        
        aqi_response.raise_for_status()
        aqi_data = aqi_response.json()
        
        if aqi_data['status'] == 'ok':
            data = aqi_data['data']
            logger.info(f"Received AQI data: {data}")
            
            # Check if AQI value exists
            if 'aqi' not in data:
                logger.error("No AQI value in response data")
                return None
                
            aqi_value = data['aqi']
            aqi_info = get_aqi_level(aqi_value)
            
            # Get components with more robust error handling
            iaqi = data.get('iaqi', {})
            components = {
                'pm25': iaqi.get('pm25', {}).get('v', 'N/A'),
                'pm10': iaqi.get('pm10', {}).get('v', 'N/A'),
                'o3': iaqi.get('o3', {}).get('v', 'N/A'),
                'no2': iaqi.get('no2', {}).get('v', 'N/A'),
                'so2': iaqi.get('so2', {}).get('v', 'N/A')
            }
            
            # Get station name with fallback
            station = data.get('city', {})
            station_name = station.get('name') if isinstance(station, dict) else str(station)
            
            return {
                'aqi': aqi_value,
                'aqi_level': aqi_info['level'],
                'aqi_color': aqi_info['color'],
                'delta_color': aqi_info['delta_color'],
                'aqi_description': aqi_info['description'],
                'components': components,
                'station': station_name or 'Unknown Station'
            }
        else:
            logger.warning(f"API returned non-OK status: {aqi_data.get('status')}")
            logger.warning(f"API message: {aqi_data.get('data')}")
            return None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching AQI data: {str(e)}")
        return None
    except KeyError as e:
        logger.error(f"Missing key in API response: {str(e)}")
        logger.error(f"Full response: {aqi_data}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        logger.error(f"Full response: {aqi_data if 'aqi_data' in locals() else 'No response data'}")
        return None

def get_city_aqi(city_name):
    """Alternative method to fetch AQI using city name directly"""
    try:
        logger.info(f"Fetching AQI data for city: {city_name}")
        aqi_url = f"https://api.waqi.info/feed/{city_name}/?token={WAQI_API_KEY}"
        
        response = requests.get(aqi_url)
        response.raise_for_status()
        data = response.json()
        
        if data['status'] == 'ok':
            return data['data']
        return None
    except Exception as e:
        logger.error(f"Error fetching city AQI: {str(e)}")
        return None

def get_location_info(location_name):
    try:
        logger.info(f"Attempting to geocode location: {location_name}")
        geolocator = Nominatim(user_agent="weather_app")
        location = geolocator.geocode(location_name, timeout=10)
        
        if location:
            logger.info(f"Location found: {location.address}")
            logger.info(f"Coordinates: {location.latitude}, {location.longitude}")
            return {
                'latitude': location.latitude,
                'longitude': location.longitude,
                'address': location.address
            }
        logger.warning(f"Location not found: {location_name}")
        return None
    except GeocoderTimedOut:
        logger.error(f"Geocoding timed out for location: {location_name}")
        return None
    except Exception as e:
        logger.error(f"Error geocoding location {location_name}: {str(e)}")
        return None

def display_weather_metrics(location_data):
    """Display weather metrics including AQI"""
    try:
        with st.spinner("Fetching air quality data..."):
            weather_data = get_weather_data(location_data['latitude'], location_data['longitude'])
        
        if weather_data:
            # Create columns for metrics
            col_a, col_b = st.columns(2)
            
            with col_a:
                st.metric(
                    label="Air Quality Index",
                    value=f"{weather_data['aqi']}",
                    delta=weather_data['aqi_level'],
                    delta_color=weather_data['delta_color']
                )
            
            with col_b:
                st.markdown(f"""
                <div style="padding: 10px; border-radius: 5px; background-color: rgba(255,255,255,0.1);">
                    <p style="color: white; margin: 0;">
                        📍 {weather_data['station']}
                    </p>
                    <p style="color: white; margin: 5px 0 0 0;">
                        Status: {weather_data['aqi_description']}
                    </p>
                </div>
                """, unsafe_allow_html=True)
            
            # Display detailed air quality components
            st.markdown("""
                <h4 style='color: white; text-align: center; margin-top: 20px;'>
                    Air Quality Components
                </h4>
            """, unsafe_allow_html=True)
            
            components = weather_data['components']
            comp_cols = st.columns(5)
            
            metrics = [
                ("PM2.5", components['pm25'], "μg/m³"),
                ("PM10", components['pm10'], "μg/m³"),
                ("Ozone", components['o3'], "μg/m³"),
                ("NO₂", components['no2'], "μg/m³"),
                ("SO₂", components['so2'], "μg/m³")
            ]
            
            for col, (label, value, unit) in zip(comp_cols, metrics):
                with col:
                    if value != 'N/A':
                        st.metric(label, f"{value:.1f} {unit}")
                    else:
                        st.metric(label, "N/A")
            
        else:
            st.error("""
                Unable to fetch air quality data. This might be because:
                1. No monitoring station near this location
                2. API rate limit reached
                3. Temporary service disruption
                
                Please try another location or try again later.
            """)
            
    except Exception as e:
        logger.error(f"Error displaying weather metrics: {str(e)}")
        st.error("Unable to display weather metrics. Please check the logs for details.")

def main():
    logger.info("Application started")
    try:
        # Create two columns for layout
        logger.debug("Creating layout columns")
        col1, col2, col3 = st.columns([1,2,1])
        
        with col2:
            logger.debug("Rendering main content container")
            # st.markdown('<div class="content-container">', unsafe_allow_html=True)
            
            # Weather animation
            logger.debug("Rendering weather animation")
            st.markdown("""
                <div class="weather-container">
                    <div class="sun">☀️</div>
                    <div class="rain">
                        <div class="raindrop">💧</div>
                        <div class="raindrop">💧</div>
                        <div class="raindrop">💧</div>
                    </div>
                    <div class="weather-text">WEATHER SYSTEM ACTIVE</div>
                    <div class="welcome-text">Welcome to the Weather Show!</div>
                </div>
            """, unsafe_allow_html=True)
            
            # Modified Location search section
            logger.debug("Setting up location search")
            # Add a form to handle Enter key press
            with st.form(key='location_form'):
                location_query = st.text_input(
                    "Enter a location and press Enter:",
                    placeholder="e.g., New York, London, Tokyo"
                )
                # Hidden submit button that will be triggered by Enter
                submit_button = st.form_submit_button(label='Search', type='primary')
                
                if submit_button:
                    if location_query:
                        logger.info(f"Location search initiated for: {location_query}")
                        with st.spinner("Fetching location details..."):
                            location_data = get_location_info(location_query)
                            if location_data:
                                logger.info("Successfully retrieved location data")
                                st.success("Location found!")
                                
                                # Display location details
                                logger.debug("Rendering location details")
                                st.markdown(f"""
                                <div style="background-color: rgba(255,255,255,0.1); 
                                            padding: 15px; 
                                            border-radius: 10px; 
                                            margin: 10px 0;">
                                    <h3 style="color: white;">📍 Location Details</h3>
                                    <p style="color: white;">Address: {location_data['address']}</p>
                                    <p style="color: white;">Latitude: {location_data['latitude']:.4f}</p>
                                    <p style="color: white;">Longitude: {location_data['longitude']:.4f}</p>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                # Display map
                                logger.debug("Rendering map")
                                map_data = {
                                    'lat': [location_data['latitude']],
                                    'lon': [location_data['longitude']]
                                }
                                st.map(map_data)
                                
                                # Update metrics section
                                logger.debug("Rendering weather metrics")

                                display_weather_metrics(location_data)
                                st.markdown('</div>', unsafe_allow_html=True)
                            else:
                                logger.warning("Location search failed")
                                st.error("Location not found. Please try again.")
                    else:
                        logger.warning("Empty location search attempted")
                        st.warning("Please enter a location to search")
            
            # Time display
            logger.debug("Setting up time display")
            time_placeholder = st.empty()
            
           

        def update_time():
            logger.debug("Starting time update loop")
            while True:
                try:
                    current_time = datetime.now(pytz.timezone('UTC'))
                    formatted_time = current_time.strftime("%B %d, %Y %H:%M:%S")
                    time_placeholder.markdown(
                        f'<p class="time-text">🕒 Current Time:<br>{formatted_time}</p>',
                        unsafe_allow_html=True
                    )
                    time.sleep(1)
                except Exception as e:
                    logger.error(f"Error updating time: {str(e)}")

        update_time()

    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        st.error("An error occurred in the application. Please check the logs.")

if __name__ == "__main__":
    logger.info("Starting weather application")
    main()

# Add required pip packages
requirements = """
geopy==2.3.0
requests==2.31.0  # For API calls
"""

# Save as requirements.txt
with open("requirements.txt", "w") as f:
    f.write(requirements) 