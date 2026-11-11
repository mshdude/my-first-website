from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# CHANGE THIS PASSWORD for updating the status on the website
ADMIN_PASSWORD = "jox@parham2!"

# Default status when the server boots up
airfield_state = {
    "status": "OPEN - NORMAL OPERATIONS",
    "color": "#16a34a",  # Green
    "message": "Winch and aerotow launches active. Check in at the launch point."
}

# Preset status levels and colours
STATUS_PRESETS = {
    "open": ("OPEN - NORMAL OPERATIONS", "#16a34a"),             # Green
    "delayed": ("STANDBY - MAY OPEN LATER", "#d97706"),          # Amber
    "restricted": ("OPEN - RESTRICTED / SOLO ONLY", "#2563eb"),  # Blue
    "closed": ("CLOSED - NO FLYING", "#dc2626")                  # Red
}

@app.route('/', methods=['GET', 'POST'])
def home():
    error = None
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
            preset_key = request.form.get('status_choice')
            custom_msg = request.form.get('message')
            
            title, color = STATUS_PRESETS.get(preset_key, ("OPEN", "#16a34a"))
            airfield_state["status"] = title
            airfield_state["color"] = color
            airfield_state["message"] = custom_msg
            return redirect(url_for('home'))
        else:
            error = "Incorrect password. Status was not updated."

    return render_template('index.html', state=airfield_state, error=error)

if __name__ == '__main__':
    app.run(debug=True)
