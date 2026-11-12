import os
import json
import glob
import base64
from datetime import datetime, timedelta
import pytz
import requests
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory

app = Flask(__name__)
app.secret_key = "sgc_parham_secret_key_change_me"

ADMIN_PASSWORD = "masonh"
DATA_FILE = "status_data.json"
UK_TZ = pytz.timezone("Europe/London")

# Optional GitHub persistence settings (set in Render Environment Variables)
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "").strip()
GITHUB_REPO = os.environ.get("GITHUB_REPO", "").strip()

STATUS_MODES = {
    "open": ("Open", "#16a34a"),                                             # Green
    "open_winch": ("Open - winch only", "#16a34a"),                          # Green
    "open_xc": ("Open for cross country", "#16a34a"),                        # Green
    "weather_hold": ("Weather Hold - Awaiting Clearance", "#eab308"),        # Yellow
    "delayed": ("Delayed start", "#d97706"),                                 # Amber
    "finished_early": ("Finished early", "#dc2626"),                         # Red
    "closed_notice": ("Closed until further notice", "#dc2626"),             # Red
    "closed": ("Closed", "#dc2626")                                          # Red
}

def github_load():
    if not (GITHUB_TOKEN and GITHUB_REPO):
        return None
    url = f"https://github.com{GITHUB_REPO}/contents/{DATA_FILE}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        r = requests.get(url, headers=headers, timeout=5)
        if r.status_code == 200:
            content = base64.b64decode(r.json()["content"]).decode("utf-8")
            return json.loads(content)
    except Exception:
        pass
    return None

def github_save(data):
    if not (GITHUB_TOKEN and GITHUB_REPO):
        return
    url = f"https://github.com{GITHUB_REPO}/contents/{DATA_FILE}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        sha = None
        r_get = requests.get(url, headers=headers, timeout=5)
        if r_get.status_code == 200:
            sha = r_get.json().get("sha")
        encoded = base64.b64encode(json.dumps(data, indent=2).encode("utf-8")).decode("utf-8")
        payload = {
            "message": "Update airfield status via web panel",
            "content": encoded
        }
        if sha:
            payload["sha"] = sha
        requests.put(url, headers=headers, json=payload, timeout=5)
    except Exception:
        pass

def load_data():
    data = github_load()
    if not data and os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
        except Exception:
            data = None

    if not data:
        now_uk = datetime.now(UK_TZ)
        data = {
            "current": {
                "status": "Closed",
                "color": "#dc2626",
                "message": "Airfield closed outside flying hours.",
                "updated_at": now_uk.strftime("%a %d %b %Y at %H:%M"),
                "iso_time": now_uk.isoformat()
            },
            "history": []
        }

    # AUTOMATIC 5:00 PM (17:00) DAILY CLOSURE CHECK
    now_uk = datetime.now(UK_TZ)
    today_5pm = now_uk.replace(hour=17, minute=0, second=0, microsecond=0)
    last_iso = data.get("current", {}).get("iso_time", "")

    try:
        last_dt = datetime.fromisoformat(last_iso)
    except Exception:
        last_dt = now_uk - timedelta(days=1)

    # If it is currently 17:00 or later today, and the last update happened BEFORE 17:00 today:
    if now_uk >= today_5pm and last_dt < today_5pm:
        if data["current"].get("status") != "Closed":
            formatted_5pm = today_5pm.strftime("%a %d %b %Y at 17:00")
            closed_state = {
                "status": "Closed",
                "color": "#dc2626",
                "message": "Flying operations concluded for the day (Automatic 5:00 PM closure).",
                "updated_at": formatted_5pm,
                "iso_time": today_5pm.isoformat()
            }
            data["current"] = closed_state
            data["history"].insert(0, {
                "status": "Closed",
                "color": "#dc2626",
                "message": "Automatic 5:00 PM daily closure.",
                "timestamp": formatted_5pm,
                "iso_time": today_5pm.isoformat()
            })
            save_data(data)

    return data

def save_data(data):
    cutoff = datetime.now(UK_TZ) - timedelta(days=14)
    filtered_history = []
    for entry in data.get("history", []):
        try:
            if datetime.fromisoformat(entry["iso_time"]) >= cutoff:
                filtered_history.append(entry)
        except Exception:
            continue
    data["history"] = filtered_history

    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)
    github_save(data)

def get_weather_summary():
    try:
        url = "https://open-meteo.com"
        r = requests.get(url, timeout=3)
        c = r.json().get("current", {})
        wind_kt = round(c.get("wind_speed_10m", 0))
        wind_dir = round(c.get("wind_direction_10m", 0))
        temp = round(c.get("temperature_2m", 0))
        clouds = round(c.get("cloud_cover", 0))
        rain = c.get("precipitation", 0)

        # Gliding ridge & conditions analysis for Parham / South Downs
        if rain > 0.2:
            outlook = "Precipitation detected at Parham; visibility and launch operations likely affected."
        elif wind_kt > 22:
            outlook = f"Strong winds ({wind_kt} kt); challenging ground handling and winch/aerotow limits."
        elif (290 <= wind_dir <= 360 or 0 <= wind_dir <= 40) and wind_kt >= 10:
            outlook = f"Northerly airflow ({wind_dir}° at {wind_kt} kt) — favourable for South Downs ridge lift."
        elif wind_kt < 8:
            outlook = f"Light winds ({wind_kt} kt); calm circuit conditions, thermal-dependent soaring."
        else:
            outlook = f"Moderate {wind_dir}° breeze at {wind_kt} kt with {clouds}% cloud cover; flyable conditions."

        return f"{temp}°C • Wind {wind_kt} kt from {wind_dir}° • {outlook}"
    except Exception:
        return None

@app.route('/background.jpg')
def background_image():
    for pattern in [
        'background.jpg',
        'background.JPG',
        'background.jpeg',
        'background.JPEG',
        'background.png',
        'background.PNG'
    ]:
        matches = glob.glob(pattern)

        if matches:
            return send_from_directory('.', matches[0])

    return "Image not found", 404

@app.route('/', methods=['GET', 'POST'])
def home():
    data = load_data()
    login_error = None

    if request.method == 'POST':
        entered_pw = request.form.get('password')
        if entered_pw == ADMIN_PASSWORD:
            session['is_admin'] = True
            return redirect(url_for('admin'))
        else:
            login_error = "Incorrect password."

    weather_brief = get_weather_summary()
    return render_template('index.html', page="public", state=data["current"], weather=weather_brief, error=login_error)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not session.get('is_admin'):
        return redirect(url_for('home'))

    data = load_data()

    if request.method == 'POST':
        mode_key = request.form.get('status_choice')
        custom_msg = request.form.get('message', '').strip()
        title, color = STATUS_MODES.get(mode_key, ("Open", "#16a34a"))

        now_uk = datetime.now(UK_TZ)
        formatted_time = now_uk.strftime("%a %d %b %Y at %H:%M")

        new_status = {
            "status": title,
            "color": color,
            "message": custom_msg,
            "updated_at": formatted_time,
            "iso_time": now_uk.isoformat()
        }

        data["current"] = new_status
        data["history"].insert(0, {
            "status": title,
            "color": color,
            "message": custom_msg,
            "timestamp": formatted_time,
            "iso_time": now_uk.isoformat()
        })

        save_data(data)
        # Lock session and return straight to the live public page
        session.pop('is_admin', None)
        return redirect(url_for('home'))

    return render_template(
        'index.html',
        page="admin",
        state=data["current"],
        history=data["history"],
        modes=STATUS_MODES
    )

if __name__ == '__main__':
    app.run(debug=True)
