from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',
    'database': 'medical'
}

def create_database_and_tables():
    setup_conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root"
    )
    setup_cursor = setup_conn.cursor()
    setup_cursor.execute("CREATE DATABASE IF NOT EXISTS medical")
    setup_cursor.close()
    setup_conn.close()

    global db, cursor
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="medical"
    )
    cursor = db.cursor()

    table_queries = {
        "ldr_data1": """
            CREATE TABLE IF NOT EXISTS ldr_data1 (
                id INT AUTO_INCREMENT PRIMARY KEY,
                intensity FLOAT,
                timestamp DATETIME
            )
        """,
        "ldr_data2": """
            CREATE TABLE IF NOT EXISTS ldr_data2 (
                id INT AUTO_INCREMENT PRIMARY KEY,
                intensity FLOAT,
                timestamp DATETIME
            )
        """,
        "pir_data": """
            CREATE TABLE IF NOT EXISTS pir_data (
                id INT AUTO_INCREMENT PRIMARY KEY,
                motion INT,
                timestamp DATETIME
            )
        """,
        "humidity_data": """
            CREATE TABLE IF NOT EXISTS humidity_data (
                id INT AUTO_INCREMENT PRIMARY KEY,
                humidity FLOAT,
                timestamp DATETIME
            )
        """,
        "temperature_data": """
            CREATE TABLE IF NOT EXISTS temperature_data (
                id INT AUTO_INCREMENT PRIMARY KEY,
                temperature FLOAT,
                timestamp DATETIME
            )
        """
    }

    for query in table_queries.values():
        cursor.execute(query)
    db.commit()
    
@app.route("/")
def home():
    return render_template("index.html")

create_database_and_tables()

# User credentials with roles
users = {
    "admin": {"password": "admin123", "role": "admin"},
    "ldr1": {"password": "ldr1pass", "role": "ldr1"},
    "ldr2": {"password": "ldr2pass", "role": "ldr2"},
    "pir": {"password": "pirpass", "role": "pir"},
    "humidity": {"password": "humidpass", "role": "humidity"},
    "temp": {"password": "temppass", "role": "temp"},
}

# Login route
@app.route('/log', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = users.get(username)
        if user and user['password'] == password:
            session['username'] = username
            session['role'] = user['role']
            print(f"Logged in as {username} with role {user['role']}")  # Debugging statement
            if username == 'admin':
                return redirect(url_for('admin'))
            return redirect(url_for(f"view_{user['role']}"))
        else:
            error = 'Invalid credentials'
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/admin')
def admin():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM ldr_data1")
    ldr1 = cursor.fetchall()

    cursor.execute("SELECT * FROM ldr_data2")
    ldr2 = cursor.fetchall()

    cursor.execute("SELECT * FROM pir_data")
    pir = cursor.fetchall()

    cursor.execute("SELECT * FROM humidity_data") 
    humidity = cursor.fetchall()

    cursor.execute("SELECT * FROM temperature_data") 
    temp = cursor.fetchall()

    conn.close()

    return render_template("admin.html", ldr1=ldr1, ldr2=ldr2, pir=pir, humidity=humidity, temp=temp, title='Admin Dashboard')


# Helper function to fetch data and plot graph
def fetch_data_and_plot(table_name, ylabel, img_name):
    cursor.execute(f"SELECT * FROM {table_name}")
    records = cursor.fetchall()
    if records:
        times = [r[2].strftime('%H:%M:%S') for r in records]
        values = [r[1] for r in records]

        plt.figure(figsize=(6, 4))
        plt.plot(times, values, marker='o')
        plt.title(f"{ylabel} Data")
        plt.xlabel("Time")
        plt.ylabel(ylabel)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(f"static/{img_name}")
        plt.close()
    return records

# Sensor data views (for ldr1, ldr2, pir, humidity, temp)
@app.route('/ldr1')
def view_ldr1():
    if session.get('role') not in ['ldr1', 'admin']:
        return redirect(url_for('login'))
    records = fetch_data_and_plot('ldr_data1', 'LDR 1', 'ldr1_graph.png')
    return render_template('ldr1.html', data=records, title='LDR 1 Data')

@app.route('/ldr2')
def view_ldr2():
    if session.get('role') not in ['ldr2', 'admin']:
        return redirect(url_for('login'))
    records = fetch_data_and_plot('ldr_data2', 'LDR 2', 'ldr2_graph.png')
    return render_template('ldr2.html', data=records, title='LDR 2 Data')

@app.route('/pir')
def view_pir():
    if session.get('role') not in ['pir', 'admin']:
        return redirect(url_for('login'))
    records = fetch_data_and_plot('pir_data', 'Motion', 'pir_graph.png')
    return render_template('pir.html', data=records, title='PIR Data')

@app.route('/humidity')
def view_humidity():
    if session.get('role') not in ['humidity', 'admin']:
        return redirect(url_for('login'))
    records = fetch_data_and_plot('humidity_data', 'Humidity', 'humidity_graph.png')
    return render_template('humidity.html', data=records, title='Humidity Data')

@app.route('/temp')
def view_temp():
    if session.get('role') not in ['temp', 'admin']:
        return redirect(url_for('login'))
    records = fetch_data_and_plot('temperature_data', 'Temperature', 'temp_graph.png')
    return render_template('temp.html', data=records, title='Temperature Data')

# Route to receive data from ESP32 or other sensors
@app.route('/data', methods=['POST'])
def receive_data():
    data = request.json
    now = datetime.now()

    if 'ldr1' in data:
        cursor.execute("INSERT INTO ldr_data1 (intensity, timestamp) VALUES (%s, %s)", (data['ldr1'], now))
    if 'ldr2' in data:
        cursor.execute("INSERT INTO ldr_data2 (intensity, timestamp) VALUES (%s, %s)", (data['ldr2'], now))
    if 'pir' in data:
        cursor.execute("INSERT INTO pir_data (motion, timestamp) VALUES (%s, %s)", (data['pir'], now))
    if 'humidity' in data:
        cursor.execute("INSERT INTO humidity_data (humidity, timestamp) VALUES (%s, %s)", (data['humidity'], now))
    if 'temperature' in data:
        cursor.execute("INSERT INTO temperature_data (temperature, timestamp) VALUES (%s, %s)", (data['temperature'], now))

    db.commit()
    return {'status': 'success'}

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
