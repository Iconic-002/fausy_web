import os
import json
import psycopg2
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
from twilio.rest import Client
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# --- CONFIGURATION ---
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_TOKEN')
TWILIO_WHATSAPP_FROM = 'whatsapp:+14155238886'
MY_WHATSAPP_NUMBER = 'whatsapp:+254103119007'
PAYMENT_PHONE = "0726694019"

# Use the Environment Variable for Database
DATABASE_URL = os.environ.get('DATABASE_URL')

# Initialize Twilio
try:
    twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
except Exception as e:
    print(f"Twilio Client Error: {e}")

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, sslmode='require')

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id SERIAL PRIMARY KEY,
            customer_name TEXT,
            phone TEXT,
            style_name TEXT,
            booking_date TEXT,
            start_time TEXT,
            duration INTEGER,
            mpesa_code TEXT UNIQUE,
            status TEXT DEFAULT 'Pending'
        );
    ''')
    conn.commit()
    cur.close()
    conn.close()

# Initialize tables on startup
with app.app_context():
    init_db()

@app.route('/')
def home():
    return f"""
    <body style="font-family: sans-serif; text-align: center; padding-top: 50px; background: #fdfaf6; color: #8b5e3c;">
        <h1>🌿 Fausy Stylist API (PostgreSQL) is Live</h1>
        <p>Backend is connected to Render Database.</p>
    </body>
    """

@app.route('/api/styles/', methods=['GET'])
def get_styles():
    try:
        with open('styles_data.json', 'r') as f:
            styles = json.load(f)
        return jsonify(styles)
    except Exception as e:
        return jsonify([])

@app.route('/api/admin/bookings', methods=['GET'])
def get_all_bookings():
    password = request.args.get('password')
    if password != "fausy2026":
        return jsonify({"error": "Unauthorized"}), 401
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM bookings ORDER BY booking_date DESC, start_time DESC")
        bookings = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(bookings)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/bookings/', methods=['POST'])
def create_booking():
    data = request.json
    customer_name = data.get('customer_name')
    client_phone = data.get('phone')
    style_id = data.get('style_id')
    custom_name = data.get('custom_style_name', '')
    booking_date = data.get('booking_date')
    start_time = data.get('start_time')
    mpesa_code = data.get('mpesa_code', '').strip().upper()
    duration = int(data.get('duration', 120))

    style_display = custom_name if style_id == "custom" else f"Style: {style_id}"

    try:
        new_start = datetime.strptime(f"{booking_date} {start_time}", '%Y-%m-%d %H:%M')
        new_end = new_start + timedelta(minutes=duration)
    except Exception:
        return jsonify({"error": "Invalid date or time format"}), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Overlap Check
        cursor.execute("SELECT booking_date, start_time, duration FROM bookings WHERE booking_date = %s", (booking_date,))
        existing_bookings = cursor.fetchall()
        for b in existing_bookings:
            b_start = datetime.strptime(f"{b[0]} {b[1]}", '%Y-%m-%d %H:%M')
            b_end = b_start + timedelta(minutes=int(b[2]))
            if new_start < b_end and new_end > b_start:
                cursor.close()
                conn.close()
                return jsonify({"error": "Time slot occupied"}), 409

        # Duplicate M-Pesa Code Check
        cursor.execute("SELECT id FROM bookings WHERE mpesa_code = %s", (mpesa_code,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({"error": "This M-Pesa code has already been used."}), 400

        cursor.execute('''
            INSERT INTO bookings (customer_name, phone, style_name, booking_date, start_time, duration, mpesa_code)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (customer_name, client_phone, style_display, booking_date, start_time, duration, mpesa_code))
        
        conn.commit()
        cursor.close()
        conn.close()

        # Twilio Alert
        try:
            message_body = f"🔥 *New Booking!*\n👤 {customer_name}\n📞 {client_phone}\n💇‍♀️ {style_display}\n📅 {booking_date} at {start_time}\n💰 {mpesa_code}"
            twilio_client.messages.create(body=message_body, from_=TWILIO_WHATSAPP_FROM, to=MY_WHATSAPP_NUMBER)
        except: pass

        return jsonify({"message": "Booking successful!"}), 201

    except Exception as e:
        return jsonify({"error": f"Database Error: {str(e)}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)