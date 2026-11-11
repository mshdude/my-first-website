import os
import json
from datetime import datetime, timedelta
import pytz
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory

app = Flask(__name__)
app.secret_key = "sgc_parham_secret_key_change_me"  # Required for secure admin login sessions

# CHANGE THIS PASSWORD for instructor access
ADMIN_PASSWORD = "jox@parham26!"
DATA_FILE = "status_data.json"
UK_TZ = pytz.timezone("Europe/London")

# Your 7 custom status modes and logical colours
STATUS_MODES = {
    "open": ("Open", "#16a34a"),                                     # Green
    "open_winch": ("Open - winch only", "#15803d"),                  # Forest Green
    "open_xc": ("Open for cross country", "#0284c7"),                # Sky Blue
    "delayed": ("Delayed start", "#d97706"),                         # Amber
    "finished_early": ("Finished early", "#7c3aed"),                 # Purple
    "closed_notice": ("Closed until further notice", "#ea580c"),     # Deep Orange
    "closed": ("Closed", "#dc2626")                                  # Red
}

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "current": {
            "status": "Open",
            "color": "#16a34a",
            "message": "Normal airfield operations. Check in at the launch point.",
            "updated_at": datetime.now(UK_TZ).strftime("%d %b %Y, %H:%M")
        },
        "history": []
    }

def save_data(data):
    # Filter history to strictly keep only the last 14 days (2 weeks)
    cutoff = datetime.now(UK_TZ) - timedelta(days=14)
    filtered_history = []
    for entry in data.get("history", []):
        try:
            entry_dt = datetime.fromisoformat(entry["iso_time"])
            if entry_dt >= cutoff:
                filtered_history.append(entry)
        except Exception:
            continue
    data["history"] = filtered_history

    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

# Serve background image directly from your root folder
@app.route('/background.jpg')
def background_image():
    return send_from_directory('.', 'background.jpg')

# Main Public Status Page (plus password gate)
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

    return render_template('index.html', page="public", state=data["current"], error=login_error)

# Dedicated Admin Page (Protected behind password)
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
            "updated_at": formatted_time
        }

        # Update current status and prepend to top of 2-week history log
        data["current"] = new_status
        data["history"].insert(0, {
            "status": title,
            "color": color,
            "message": custom_msg,
            "timestamp": formatted_time,
            "iso_time": now_uk.isoformat()
        })

        save_data(data)
        return redirect(url_for('admin'))

    return render_template(
        'index.html',
        page="admin",
        state=data["current"],
        history=data["history"],
        modes=STATUS_MODES
    )

@app.route('/logout')
def logout():
    session.pop('is_admin', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
