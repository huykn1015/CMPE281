from flask import Flask, request, jsonify
from CalraManager.CarlaManager import CarlaManager

app = Flask(__name__)

# Instantiate the CarlaManager
carla_manager = CarlaManager()


@app.route('/create_vehicle', methods=['POST'])
def create_vehicle():
    """
    Create a vehicle with a specified ID and path.
    """
    data = request.get_json()
    vehicle_id = data.get('vehicle_id')
    path = data.get('path')

    if not vehicle_id or not path:
        return jsonify({"error": "Both 'vehicle_id' and 'path' are required"}), 400

    try:
        carla_manager.create_vehicle(vehicle_id, path)
        return jsonify({"message": f"Vehicle '{vehicle_id}' created successfully!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/get_vehicle_location/<vehicle_id>', methods=['GET'])
def get_vehicle_location(vehicle_id):
    """
    Retrieve the current location of a vehicle.
    """
    try:
        location = carla_manager.get_vehicle_location(vehicle_id)
        if location is None:
            return jsonify({"error": f"Vehicle '{vehicle_id}' not found"}), 404

        return jsonify({
            "vehicle_id": vehicle_id,
            "location": {
                "x": location[0],
                "y": location[1],
                "z": location[2]
            }
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/get_all_spawn_points', methods=['GET'])
def get_all_spawn_points():
    """
    Retrieve all spawn points in the simulator.
    """
    try:
        spawn_points = carla_manager.get_all_locations()
        return jsonify({"spawn_points": spawn_points}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/destroy_all_vehicles', methods=['POST'])
def destroy_all_vehicles():
    """
    Destroy all vehicles in the simulator.
    """
    try:
        carla_manager.destroy_all_vehicles()
        return jsonify({"message": "All vehicles destroyed successfully!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)