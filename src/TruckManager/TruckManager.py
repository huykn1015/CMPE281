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


@app.route('/api/user', methods=['POST'])
def get_current_user():
    data = request.json
    username = data.get('username')
    if not username:
        return jsonify({"error": "Missing 'username' parameter"}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM \"autonomous-truck\".users WHERE username = %s", (username,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    if len(rows) == 0:
        return jsonify({"error": f"Could not find user ({username})."})
    elif len(rows) > 1:
        return jsonify({"error": f"FATAL: {username} matches multiple results."})

    user = {
        "id": rows[0][0],
        "name": rows[0][1],
        "username": username
    }
    
    return jsonify(user), 200


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
    owner_id = data.get('owner_id', None)

    if owner_id is None:
        return jsonify({"error": "Owner ID not found but is a required field."})
    
    status = data.get('status', 'Idle')
    maintenance_status = data.get('maintenance_status', 'OK')
    system_health = data.get('system_health', 'Normal')

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT MAX(id) FROM "autonomous-truck".autonomous_truck')
    max_id = cursor.fetchone()[0]
    next_truck_id = (int(max_id) + 1) if max_id else 1  # Increment max_id or start at 1

    cursor.execute("""
        INSERT INTO "autonomous-truck".autonomous_truck (id, owner_id, status, maintenance_status, system_health)
        VALUES (%s, %s, %s, %s, %s)
    """, (next_truck_id, owner_id, status, maintenance_status, system_health))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": f"Truck {next_truck_id} added successfully", "vehicle_id": next_truck_id}), 201

@app.route('/api/trucks/<int:truck_id>', methods=['DELETE'])
def delete_truck_from_db(truck_id):
    """Delete a truck from the database."""

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

@app.route('/api/truck/<int:truck_id>', methods=['PUT'])
def update_truck(truck_id):
    try:
        # Parse the JSON body
        data = request.json
        status = data.get('status')
        maintenance_status = data.get('maintenance_status')
        system_health = data.get('system_health')

        if not (status or maintenance_status or system_health):
            return jsonify({"error": "No fields to update provided"}), 400

        # Connect to the database
        conn = get_db_connection()
        cursor = conn.cursor()

        # Build the SQL query dynamically based on provided fields
        update_fields = []
        query_params = []
        if status:
            update_fields.append("status = %s")
            query_params.append(status)
        if maintenance_status:
            update_fields.append("maintenance_status = %s")
            query_params.append(maintenance_status)
        if system_health:
            update_fields.append("system_health = %s")
            query_params.append(system_health)

        query_params.append(truck_id)
        update_query = f"UPDATE autonomous_truck SET {', '.join(update_fields)} WHERE id = %s"

        # Execute the query
        cursor.execute(update_query, query_params)
        conn.commit()

        # Close connection
        cursor.close()
        conn.close()

        return jsonify({"message": "Truck details updated successfully"}), 200

    except psycopg2.Error as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500
