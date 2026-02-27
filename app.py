"""
CrowdGuardian Sentinel - Flask API Backend
Serves the YOLOv8 crowd analysis model via REST endpoints.
"""

import csv
from datetime import datetime, timedelta
import random
from io import StringIO
import urllib.request
from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
from model import analyze_image, analyze_video_frame
import os

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

# Serve frontend
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('.', path)

def trigger_ntfy_alert(people_count):
    """Sends a free push notification to mobile via ntfy.sh"""
    topic = "crowdguardian_cit_hack"
    url = f"https://ntfy.sh/{topic}"
    message = f"🚨 HIGH RISK ALERT! Crowd density is critical. Detected {people_count} people in the area. Please redirect flow."
    
    headers = {
        "Title": "CrowdGuardian Alert",
        "Priority": "high",
        "Tags": "rotating_light,warning"
    }
    
    try:
        req = urllib.request.Request(url, data=message.encode('utf-8'), headers=headers, method='POST')
        urllib.request.urlopen(req, timeout=3)
        print(">> Mobile Push Alert Sent Successfully!")
    except Exception as e:
        print(f">> Failed to send mobile alert: {e}")

# API endpoint for crowd analysis
@app.route('/api/analyze', methods=['POST'])
def analyze():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    file_bytes = file.read()
    filename = file.filename.lower()
    
    try:
        if filename.endswith(('.mp4', '.avi', '.mov', '.mkv', '.webm')):
            result = analyze_video_frame(file_bytes)
        else:
            result = analyze_image(file_bytes)
            
        # Check if risk is high and send mobile notification
        if result.get('density_level') == 'HIGH':
            trigger_ntfy_alert(result.get('people_count'))
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# API endpoint for Analytics
@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    # Mocking historical analytics data for a bar/line chart
    days = []
    total_people = []
    avg_density = []
    
    now = datetime.now()
    for i in range(7):
        date = now - timedelta(days=6-i)
        days.append(date.strftime('%A'))
        total_people.append(random.randint(8000, 15000))
        avg_density.append(round(random.uniform(0.1, 0.4), 2))
        
    return jsonify({
        "labels": days,
        "datasets": {
            "total_people": total_people,
            "avg_density": avg_density
        },
        "zones": [
            {"name": "Main Entrance", "current_count": random.randint(50, 200), "status": "Stable"},
            {"name": "Food Court", "current_count": random.randint(150, 400), "status": "Crowded"},
            {"name": "Concert Hall", "current_count": random.randint(100, 300), "status": "Normal"},
            {"name": "VIP Lounge", "current_count": random.randint(10, 50), "status": "Quiet"}
        ]
    })

# API endpoint for Reports Download
@app.route('/api/reports/download', methods=['GET'])
def download_report():
    # Generate a mock CSV report
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(["Date", "Time", "Zone", "People Count", "Density Level", "Alerts Generated"])
    
    now = datetime.now()
    zones = ["Main Entrance", "Food Court", "Concert Hall", "VIP Lounge"]
    
    # Generate random data for the past 24 hours
    for i in range(24):
        record_time = now - timedelta(hours=24-i)
        for zone in zones:
            count = random.randint(10, 500)
            density = "LOW" if count < 100 else ("MODERATE" if count < 300 else "HIGH")
            alerts = random.randint(0, 2) if density == "HIGH" else 0
            cw.writerow([
                record_time.strftime("%Y-%m-%d"),
                record_time.strftime("%H:00"),
                zone,
                count,
                density,
                alerts
            ])
            
    output = si.getvalue()
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=crowd_report_{now.strftime('%Y%m%d')}.csv"}
    )

if __name__ == '__main__':

    print("=" * 50)
    print("  CrowdGuardian Sentinel - AI Backend")
    print("  Server running at http://localhost:5000")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5000, debug=True)
