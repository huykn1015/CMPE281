from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
import psycopg2
import os

app = Flask(__name__)
CORS(app)
load_dotenv()

DB_CONFIG = {
    'host': os.getenv("DB_HOST"),
    'database': os.getenv("DB_NAME"),
    'user': os.getenv("DB_USER"),
    'password': os.getenv("DB_PASSWORD"),
    'port': 5432
}

def get_db_connection():
    return psycopg2.connect(
        host=DB_CONFIG['host'],
        database=DB_CONFIG['database'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        port=DB_CONFIG['port'],
        sslmode='require'
    )


@app.route('/api/trucks', methods=['GET'])
def get_trucks():
    """Fetch all trucks from the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, owner_id, status, maintenance_status, system_health FROM \"autonomous-truck\".autonomous_truck")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    trucks = [
        {
            "id": row[0],
            "owner_id": row[1],
            "status": row[2],
            "maintenance_status": row[3],
            "system_health": row[4]
        }
        for row in rows
    ]
    return jsonify(trucks), 200

@app.route('/api/trucks', methods=['POST'])
def add_truck_to_db():
    """Add a new truck to the database."""
    data = request.json
    truck_id = data['truck_id']
    owner_id = data.get('owner_id', None)
    status = data.get('status', 'Idle')
    maintenance_status = data.get('maintenance_status', 'OK')
    system_health = data.get('system_health', 'Normal')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO autonomous_truck (id, owner_id, status, maintenance_status, system_health)
        VALUES (%s, %s, %s, %s, %s)
    """, (truck_id, owner_id, status, maintenance_status, system_health))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Truck added successfully"}), 201

@app.route('/api/trucks/<int:truck_id>', methods=['DELETE'])
def delete_truck_from_db():
    """Delete a truck from the database."""
    truck_id = request.view_args['truck_id']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM \"autonomous-truck\".autonomous_truck WHERE id = %s", (truck_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": f"Truck {truck_id} deleted successfully"}), 200

@app.route('/api/trucks/<int:truck_id>', methods=['GET'])
def get_truck_by_id(truck_id):
    """Fetch a specific truck from the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, owner_id, status, maintenance_status, system_health
        FROM \"autonomous-truck\".autonomous_truck
        WHERE id = %s
    """, (truck_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if not row:
        return jsonify({"error": "Truck not found"}), 404

    truck = {
        "id": row[0],
        "owner_id": row[1],
        "status": row[2],
        "maintenance_status": row[3],
        "system_health": row[4]
    }
    return jsonify(truck), 200
