from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# CHANGE THIS PASSWORD so only club staff can update the airfield status
ADMIN_PASSWORD = "parham2026"

# Default status when the server boots up
airfield_state = {
    "status": "OPEN - NORMAL OPERATIONS",
    "color": "#16a34a",  # Green
    "message": "Winch and aerotow launches active. Check in at the launch point.",
    "updated_by": "Duty Instructor"
}

# Preset status levels for quick updating
STATUS_PRESETS = {
    "open": ("OPEN - NORMAL OPERATIONS", "#16a34a"),       # Green
    "delayed": ("STANDBY - MAY OPEN LATER", "#d97706"),    # Amber/Orange
    "restricted": ("OPEN - RESTRICTED / SOLO ONLY", "#2563eb"), # Blue
    "closed": ("CLOSED - NO FLYING", "#dc2626")            # Red
}

@app.route('/')
def home():
    return render_template('index.html', state=airfield_state)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
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
            error = "Incorrect password."
            
    return render_template('admin.html', state=airfield_state, error=error)

if __name__ == '__main__':
    app.run(debug=True)
