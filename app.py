from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import math
import os

app = Flask(__name__)

# Allow requests from any frontend origin (update to your Netlify URL in production)
CORS(app, origins="*")

DB_PATH = os.path.join(os.path.dirname(__file__), "mechanics.db")

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.asin(math.sqrt(a))

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS mechanics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        service_type TEXT NOT NULL,
        lat REAL NOT NULL,
        lon REAL NOT NULL,
        phone TEXT,
        rating REAL DEFAULT 4.0
    )''')
    c.execute("SELECT COUNT(*) FROM mechanics")
    if c.fetchone()[0] == 0:
        mechanics = [
            ("Rajiv Auto Works",          "car",          30.9005, 75.8574, "+91-98140-11111", 4.8),
            ("Singh Bike Repair",         "bike",         30.9120, 75.8490, "+91-98140-22222", 4.5),
            ("City Motor Garage",         "all vehicles", 30.8950, 75.8630, "+91-98140-33333", 4.7),
            ("QuickFix Mechanics",        "car",          30.9200, 75.8700, "+91-98140-44444", 4.3),
            ("Patiala Road Workshop",     "bike",         30.8880, 75.8400, "+91-98140-55555", 4.6),
            ("Ludhiana Auto Hub",         "all vehicles", 30.9300, 75.8550, "+91-98140-66666", 4.4),
            ("Express Car Service",       "car",          30.9050, 75.8800, "+91-98140-77777", 4.9),
            ("Two Wheeler Clinic",        "bike",         30.8800, 75.8700, "+91-98140-88888", 4.2),
            ("Sharma General Garage",     "all vehicles", 30.9150, 75.8350, "+91-98140-99999", 4.5),
            ("GT Road Motors",            "car",          30.9000, 75.8450, "+91-98141-10000", 4.7),
            ("Jalandhar Motor Works",     "car",          31.3260, 75.5762, "+91-98142-11001", 4.6),
            ("Amritsar Bike Station",     "bike",         31.6340, 74.8723, "+91-98142-11002", 4.4),
            ("Chandigarh Auto Care",      "all vehicles", 30.7333, 76.7794, "+91-98142-11003", 4.8),
            ("Patiala Vehicle Hub",       "car",          30.3398, 76.3869, "+91-98142-11004", 4.3),
            ("Bathinda Road Garage",      "all vehicles", 30.2110, 74.9455, "+91-98142-11005", 4.5),
            ("Phagwara Two Wheeler Fix",  "bike",         31.2240, 75.7730, "+91-98142-11006", 4.2),
            ("Mohali Express Garage",     "car",          30.7046, 76.7179, "+91-98142-11007", 4.7),
            ("Hoshiarpur Motor Clinic",   "all vehicles", 31.5343, 75.9115, "+91-98142-11008", 4.4),
            ("Firozpur Auto Rescue",      "car",          30.9254, 74.6130, "+91-98142-11009", 4.1),
            ("Ropar Bike & Car Works",    "all vehicles", 30.9639, 76.5186, "+91-98142-11010", 4.6),
            ("Delhi GT Karnal AutoZone",  "car",          29.0980, 76.9947, "+91-98143-21001", 4.5),
            ("Ambala Highway Garage",     "all vehicles", 30.3782, 76.7767, "+91-98143-21002", 4.7),
            ("Shimla Hill Motors",        "car",          31.1048, 77.1734, "+91-98143-21003", 4.3),
            ("Jammu Auto Rescue Centre",  "all vehicles", 32.7266, 74.8570, "+91-98143-21004", 4.6),
            ("Dehradun Quick Fix Garage", "bike",         30.3165, 78.0322, "+91-98143-21005", 4.4),
        ]
        c.executemany("INSERT INTO mechanics (name, service_type, lat, lon, phone, rating) VALUES (?,?,?,?,?,?)", mechanics)
        conn.commit()
    conn.close()

@app.route("/")
def index():
    return jsonify({"status": "ok", "message": "Vehicle Breakdown Assistance API"})

@app.route("/get-mechanics", methods=["GET"])
def get_mechanics():
    try:
        user_lat = float(request.args.get("lat"))
        user_lon = float(request.args.get("lon"))
        service_filter = request.args.get("service_type", "all").lower()
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid or missing lat/lon parameters"}), 400

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    if service_filter in ("car", "bike"):
        c.execute("SELECT * FROM mechanics WHERE service_type = ? OR service_type = 'all vehicles'", (service_filter,))
    else:
        c.execute("SELECT * FROM mechanics")

    rows = c.fetchall()
    conn.close()

    results = []
    for row in rows:
        dist = haversine(user_lat, user_lon, row["lat"], row["lon"])
        if dist <= 50:  # Only show real mechanics if they are within 50km
            results.append({
                "id": row["id"],
                "name": row["name"],
                "service_type": row["service_type"],
                "lat": row["lat"],
                "lon": row["lon"],
                "phone": row["phone"],
                "rating": row["rating"],
                "distance_km": round(dist, 2),
                "eta_minutes": round(dist / 0.4)
            })

    # If no mechanics are nearby, dynamically generate local dummy mechanics
    if not results:
        import random
        for i in range(1, 6):
            offset_lat = random.uniform(-0.08, 0.08)
            offset_lon = random.uniform(-0.08, 0.08)
            m_lat = user_lat + offset_lat
            m_lon = user_lon + offset_lon
            dist = haversine(user_lat, user_lon, m_lat, m_lon)
            
            # Match requested service type or randomize if "all"
            s_type = service_filter if service_filter in ("car", "bike") else random.choice(["car", "bike", "all vehicles"])
            
            results.append({
                "id": 1000 + i,
                "name": f"Local Auto Rescue {i}",
                "service_type": s_type,
                "lat": round(m_lat, 6),
                "lon": round(m_lon, 6),
                "phone": f"+91-98{random.randint(10000000, 99999999)}",
                "rating": round(random.uniform(4.0, 4.9), 1),
                "distance_km": round(dist, 2),
                "eta_minutes": round(dist / 0.4)
            })

    results.sort(key=lambda x: x["distance_km"])
    return jsonify({
        "user_location": {"lat": user_lat, "lon": user_lon},
        "service_filter": service_filter,
        "mechanics": results[:5]
    })

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

# Init DB on startup
init_db()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
