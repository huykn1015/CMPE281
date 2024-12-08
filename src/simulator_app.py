from flask import Flask, request, jsonify
from flask_cors import CORS
from CalraManager.CarlaManager import CarlaManager


app = Flask(__name__)
CORS(app)
carla_manager = CarlaManager()  # Instantiate CarlaManager


@app.route('/api/sim/create_vehicle', methods=['POST'])
def create_vehicle():
    data = request.json
    vehicle_id = data.get('vehicle_id')

    if not vehicle_id:
        return jsonify({"error": "vehicle_id is required"}), 400

    try:
        vehicle = carla_manager.create_vehicle(vehicle_id)
        return jsonify({"vehicle_id": vehicle_id, "message": "Vehicle created successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/sim/set_path', methods=['POST'])
def set_path():
    data = request.json
    vehicle_id = data.get('vehicle_id')
    path = data.get('path')

    if not vehicle_id or not path:
        return jsonify({"error": "vehicle_id and path are required"}), 400

    try:
        carla_manager.set_path2(vehicle_id, path)
        return jsonify({"vehicle_id": vehicle_id, "message": "Path set successfully"}), 200
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/sim/check_request_status', methods=['POST'])
def get_request_status():
    data = request.json
    vehicle_id = data.get('vehicle_id')

    if not vehicle_id:
        return jsonify({"error": "vehicle_id is required"}), 400

    try:
        status = carla_manager.get_vehicle_status(vehicle_id)
        return jsonify({"status": status}), 200
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/sim/get_vehicle_location/<vehicle_id>', methods=['GET'])
def get_vehicle_location(vehicle_id):
    try:
        location = carla_manager.get_vehicle_location(vehicle_id)
        if location is None:
            return jsonify({"error": "Vehicle not found"}), 404
        return jsonify({"vehicle_id": vehicle_id, "location": location}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    
@app.route('/api/sim/get_vehicle_telemetry/<vehicle_id>', methods=['GET'])
def get_vehicle_telemetry(vehicle_id):
    try:
        data = carla_manager.get_vehicle_telemetry(vehicle_id)
        if data is None:
            return jsonify({"error": "Vehicle not found"}), 404
        return jsonify({"vehicle_id": vehicle_id, "data": data}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/sim/get_all_locations', methods=['GET'])
def get_all_locations():
    try:
        locations = carla_manager.get_all_locations()
        return jsonify({"locations": locations}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/sim/destroy_vehicle', methods=['POST'])
def destroy_vehicle():
    data = request.json
    vehicle_id = data.get('vehicle_id')

    if not vehicle_id:
        return jsonify({"error": "vehicle_id is required"}), 400

    try:
        carla_manager.destroy_truck(vehicle_id)
        return jsonify({"vehicle_id": vehicle_id, "message": "Vehicle destroyed successfully"}), 200
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/sim/destroy_all_vehicles', methods=['POST'])
def destroy_all_vehicles():
    try:
        carla_manager.destroy_all_vehicles()
        return jsonify({"message": "All vehicles destroyed successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
