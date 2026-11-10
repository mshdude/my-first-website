import requests
from flask import Flask, render_template
from datetime import datetime

app = Flask(__name__)

# PARHAM AIRFIELD COORDINATES
LATITUDE = 50.923
LONGITUDE = -0.474

@app.route('/')
def home():
    # A completely clean, direct request line to the weather servers
    url = f"https://open-meteo.com{LATITUDE}&longitude={LONGITUDE}&hourly=temperature_2m,temperature_850hPa,boundary_layer_height,wind_speed_10m,wind_speed_850hPa,wind_direction_10m,wind_direction_850hPa,dew_point_2m&timezone=Europe%2FLondon"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        # Pull the current hour index from the clock
        current_hour = datetime.now().hour
        if current_hour < len(data['hourly']['temperature_2m']):
            h = current_hour
        else:
            h = 12
            
        # 1. Convective Soaring Values
        temp_surface = data['hourly']['temperature_2m'][h]
        temp_850hPa = data['hourly']['temperature_850hPa'][h] 
        top_of_lift = data['hourly']['boundary_layer_height'][h]
        dew_point = data['hourly']['dew_point_2m'][h]
        
        thermal_index = round(temp_850hPa - (temp_surface - 15), 1) 
        cumulus_cloudbase = round((temp_surface - dew_point) * 400)
        
        # 2. Wind Profiles
        wind_surface = round(data['hourly']['wind_speed_10m'][h] * 0.539957) 
        wind_aloft = round(data['hourly']['wind_speed_850hPa'][h] * 0.539957)   
        dir_surface = data['hourly']['wind_direction_10m'][h]
        dir_aloft = data['hourly']['wind_direction_850hPa'][h]
        
        # 3. South Downs Custom Ridge Vector Matrix
        if wind_surface < 8:
            ridge_status = "INACTIVE"
            ridge_advice = "Surface winds are too low (<8 KT) to generate reliable orographic slope lift. Prepare for winch launches or check thermal cycles."
        elif (290 <= dir_surface <= 360) or (0 <= dir_surface <= 40):
            ridge_status = "NORTH FACE ACTIVE (EXCELLENT)"
            ridge_advice = f"Winds are from {dir_surface}°. The main South Downs scarp faces (Parham bowl, Amberley, and Chanctonbury Ring) will yield clean, strong slope lift."
        elif (160 <= dir_surface <= 220):
            ridge_status = "SOUTH FACE ACTIVE (MODERATE)"
            ridge_advice = f"Southerly component ({dir_surface}°). Orographic lift active on southern shallow ridges. Watch out for heavy sink fields north of the ridges."
        elif (240 <= dir_surface <= 280) or (70 <= dir_surface <= 110):
            ridge_status = "PARALLEL AIRFLOW // ZERO LIFT"
            ridge_advice = f"Winds ({dir_surface}°) run parallel to the ridge lines. Expect no slope lift along with strong crosswind mechanical turbulence inside the circuit."
        else:
            ridge_status = "MARGINAL / OBLIQUE"
            ridge_advice = "Wind angle is heavily offset. Ridge lift will be erratic, weak, and highly isolated to specific bowls."

        # 4. Lee-Wave Calculations
        wind_increase = wind_aloft > wind_surface
        dir_stable = abs(dir_surface - dir_aloft) < 30
        wave_potential = "HIGH POTENTIAL" if (wind_increase and dir_stable and wind_aloft > 25) else "LOW / UNLIKELY"
        
        soaring_data = {
            "thermal_idx": thermal_index,
            "top_lift": round(top_of_lift * 3.28084), 
            "cloudbase": f"{cumulus_cloudbase} FT" if cumulus_cloudbase > 0 else "Blue Thermal Day",
            "wind_surface": wind_surface,
            "dir_surface": dir_surface,
            "wind_aloft": wind_aloft,
            "dir_aloft": dir_aloft,
            "wave_potential": wave_potential,
            "ridge_status": ridge_status,
            "ridge_advice": ridge_advice,
            "time_updated": f"{h:02d}:00"
        }
        
    except Exception as e:
        soaring_data = {
            "thermal_idx": "--", "top_lift": "--", "cloudbase": "--", 
            "wind_surface": "--", "dir_surface": "--", "wind_aloft": "--", "dir_aloft": "--", 
            "wave_potential": "ERROR", "ridge_status": "OFFLINE", 
            "ridge_advice": f"Data stream interrupted. Details: {str(e)}", "time_updated": "--:--"
        }

    return render_template('index.html', telemetry=soaring_data)

if __name__ == '__main__':
    app.run(debug=True)


if __name__ == '__main__':
    app.run(debug=True)
