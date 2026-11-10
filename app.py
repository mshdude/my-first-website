import requests
from flask import Flask, render_template
from datetime import datetime

app = Flask(__name__)

# THE EXACT GEOGRAPHIC DATA FOR SOUTHDOWN GLIDING CLUB (PARHAM)
LATITUDE = 50.923
LONGITUDE = -0.474

@app.route('/')
def home():
    url = f"https://open-meteo.com{LATITUDE}&longitude={LONGITUDE}&hourly=temperature_2m,temperature_850hPa,boundary_layer_height,wind_speed_10m,wind_speed_850hPa,wind_direction_10m,wind_direction_850hPa,deadpoint_2m&timezone=Europe%2FLondon"
    
    # Try fetching with dew_point_2m instead if api standard changes
    url = url.replace("deadpoint_2m", "dew_point_2m")

    try:
        response = requests.get(url)
        data = response.json()
        
        # HOUR SYNC WITH FALLBACK: Use current hour, but fallback to 12 if data array is tricky at night
        current_hour = datetime.now().hour
        if current_hour < len(data['hourly']['temperature_2m']):
            h = current_hour
        else:
            h = 12
            
        # 1. Thermal Calculations
        temp_surface = data['hourly']['temperature_2m'][h]
        temp_850hPa = data['hourly']['temperature_850hPa'][h] 
        top_of_lift = data['hourly']['boundary_layer_height'][h]
        dew_point = data['hourly']['dew_point_2m'][h]
        
        thermal_index = round(temp_850hPa - (temp_surface - 15), 1) 
        cumulus_cloudbase = round((temp_surface - dew_point) * 400)
        
        # 2. Wind Vectors
        wind_surface = round(data['hourly']['wind_speed_10m'][h] * 0.539957) 
        wind_aloft = round(data['hourly']['wind_speed_850hPa'][h] * 0.539957)   
        dir_surface = data['hourly']['wind_direction_10m'][h]
        dir_aloft = data['hourly']['wind_direction_850hPa'][h]
        
        # 3. SOUTH DOWNS RIDGE VECTOR ALGORITHM
        if wind_surface < 8:
            ridge_status = "INACTIVE"
            ridge_advice = "Surface wind velocity is too low (<8 KT) to generate sustainable orographic lift. Stick to the winch or look for thermal triggers."
        elif (290 <= dir_surface <= 360) or (0 <= dir_surface <= 40):
            ridge_status = "NORTH FACE ACTIVE (EXCELLENT)"
            ridge_advice = f"Clean Northerly flow ({dir_surface}°). The main South Downs ridge lines (the Parham bowl, Amberley, and Chanctonbury Ring) will yield excellent, reliable slope lift."
        elif (160 <= dir_surface <= 220):
            ridge_status = "SOUTH FACE ACTIVE (MODERATE)"
            ridge_advice = f"Southerly flow ({dir_surface}°). Working orographic lift on the shallower southern slopes. Expect heavy sink on the northern drop-offs."
        elif (240 <= dir_surface <= 280) or (70 <= dir_surface <= 110):
            ridge_status = "PARALLEL FLOW // DANGER ZONE"
            ridge_advice = f"Wind ({dir_surface}°) is blowing parallel to the East-West ridge lines. Yields zero slope lift. Anticipate severe mechanical turbulence and wind-shear on crosswind/final legs."
        else:
            ridge_status = "MARGINAL / PATCHY LIFT"
            ridge_advice = "The wind angle is highly oblique to the slopes. Orographic lift will be local, erratic, and tightly confined to isolated bowls."

        # 4. LEE-WAVE PROPAGATION ANALYSIS
        wind_increase = wind_aloft > wind_surface
        dir_stable = abs(dir_surface - dir_aloft) < 30
        wave_potential = "HIGH POTENTIAL" if (wind_increase and dir_stable and wind_aloft > 25) else "LOW / UNLIKELY"
        
        soaring_data = {
            "thermal_idx": thermal_index,
            "top_lift": round(top_of_lift * 3.28084), 
            "cloudbase": cumulus_cloudbase if cumulus_cloudbase > 0 else "No Cloud / Blue Thermal Day",
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
            "ridge_advice": f"Unable to verify meteorological streams. Details: {str(e)}", "time_updated": "--:--"
        }

    return render_template('index.html', telemetry=soaring_data)

if __name__ == '__main__':
    app.run(debug=True)


if __name__ == '__main__':
    app.run(debug=True)
