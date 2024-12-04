from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.exceptions import BadRequest, NotFound
import uuid
from botocore.exceptions import BotoCoreError, ClientError

from ScheduleManager.ScheduleManager import ScheduleManager
from PathManager.PathManager import PathManager
from AlertManager.AlertManager import AlertManager
from Verifier.Verifier import Verifier


app = Flask(__name__)
CORS(app)
key_id = ''
key = ''
schedule_manager = ScheduleManager(key_id, key)
path_manager = PathManager(key_id, key)
alert_manager = AlertManager(key_id, key)
verifier = Verifier()

VERIFIER_ACTIVE = False


@app.route('/api/path-manager/<schedule_id>', methods=['GET'])
def get_path(schedule_id):

    if VERIFIER_ACTIVE:
        data = request.json
        session_token = data.get('token')
        token_is_valid = verifier.validate_session_token(session_token)
        if not token_is_valid:
            raise BadRequest("Invalid session token")

    path = path_manager.get_path(schedule_id)
    if path is not None:
        return jsonify(path)
    stops = schedule_manager.get_schedule(schedule_id)
    if stops is None:
        raise BadRequest(f"Schedule {{{schedule_id}}} does not exist")

    path = path_manager.find_efficient_path(stops)
    path_manager.save_path(schedule_id, path)

    return jsonify({"schedule_id": schedule_id, "path": path}, 200)


@app.route('/api/schedule-manager/', methods=['GET'])
@app.route('/api/schedule-manager/<schedule_id>', methods=['GET'])
def get_schedules(schedule_id=None):

    if VERIFIER_ACTIVE:
        data = request.get_json()
        session_token = data.get('token')
        token_is_valid = verifier.validate_session_token(session_token)
        if not token_is_valid:
            raise BadRequest("Invalid session token")

    if schedule_id:
        # If schedule_id is provided, return the corresponding schedule
        schedule = schedule_manager.get_schedule(schedule_id)
        if not schedule:
            raise NotFound(f"Schedule ID {schedule_id} not found.")
        return jsonify(schedule)
    else:
        # If no schedule_id is provided, return all schedules
        return jsonify(list(schedule_manager.get_all_schedules()))


@app.route('/api/schedule-manager', methods=['POST'])
def create_schedule():
    # Parse JSON data from request
    data = request.get_json()
    if VERIFIER_ACTIVE:
        session_token = data.get('token')
        token_is_valid = verifier.validate_session_token(session_token)
        if not token_is_valid:
            raise BadRequest("Invalid session token")

    # Validate input
    if not data or 'stops' not in data or not isinstance(data['stops'], list):
        print(data["stops"])
        print(type(data["stops"]))
        raise BadRequest("Invalid input: 'Stops' is required and must be a list of strings.")

    # Check if all items in 'Stops' are strings
    if not all(isinstance(stop, str) for stop in data['stops']):
        print(data["stops"])
        raise BadRequest("Invalid input: 'Stops' list must contain only strings.")

    # Create a unique schedule ID
    schedule_id = str(uuid.uuid4())  # or "123" as per your example

    schedule_manager.create_schedule(schedule_id, data['stops'])

    # Construct response
    response = {
        "schedule_id": schedule_id,
        "stops": data['stops']
    }

    return jsonify(response), 201  # 201 Created status


@app.route('/api/schedule-manager/<schedule_id>/', methods=['POST'])
def modify_schedule(schedule_id):
    # Parse JSON data from request
    data = request.get_json()

    if VERIFIER_ACTIVE:
        session_token = data.get('token')
        token_is_valid = verifier.validate_session_token(session_token)
        if not token_is_valid:
            raise BadRequest("Invalid session token")

    warning_message = None
    new_stops = None
    # Validate input parameters
    if 'mod_type' not in data or 'stops' not in data:
        raise BadRequest("Invalid input: 'Modification_type' and 'Stops' are required.")

    modification_type = data['mod_type']
    modified_stops = data['stops']

    schedule = schedule_manager.get_schedule(schedule_id)
    stops = schedule
    print(modified_stops)
    if modification_type == "add":
        new_stops = list(set(stops + modified_stops))
        if len(new_stops) != len(stops) + len(modified_stops):
            shared_stops = list(set(stops) & set(modified_stops))
            warning_message = f"{shared_stops} already in existing schedule"
    elif modification_type == "remove":
        new_stops = [stop for stop in stops if stop not in modified_stops]

    schedule_manager.update_schedule(schedule_id, new_stops)
    # Build the response
    response = {
        "Schedule_id": schedule_id,
        "Stops": new_stops
    }

    if warning_message:
        response["Warning"] = warning_message

    return jsonify(response), 200  # 200 OK status


@app.route('/api/alerts/active', methods=['GET'])
def get_active_alerts():
    if VERIFIER_ACTIVE:
        data = request.get_json()
        session_token = data.get('token')
        token_is_valid = verifier.validate_session_token(session_token)
        if not token_is_valid:
            raise BadRequest("Invalid session token")

    try:
        alerts = alert_manager.get_all_active_alerts()
        return jsonify(alerts), 200
    except Exception as e:
        return jsonify({"error": "Alert service is down"}), 400


@app.route('/api/alerts/resolved', methods=['GET'])
def get_resolved_alerts():
    if VERIFIER_ACTIVE:
        data = request.get_json()
        session_token = data.get('token')
        token_is_valid = verifier.validate_session_token(session_token)
        if not token_is_valid:
            raise BadRequest("Invalid session token")

    try:
        alerts = alert_manager.get_all_resolved_alerts()
        return jsonify(alerts), 200
    except Exception as e:
        return jsonify({"error": "Alert service is down"}), 400


@app.route('/api/alerts', methods=['POST'])
def create_alert():
    try:
        data = request.get_json()
        if VERIFIER_ACTIVE:
            session_token = data.get('token')
            token_is_valid = verifier.validate_session_token(session_token)
            if not token_is_valid:
                raise BadRequest("Invalid session token")
        description = data.get('Description')

        if not description:
            return jsonify({"error": "Description is required"}), 400

        new_alert = alert_manager.create_alert(description)
        return jsonify(new_alert), 200
    except Exception as e:
        print(e)
        return jsonify({"error": "Failed to create alert"}), 400


@app.route('/api/alerts/<alert_id>', methods=['DELETE'])
def resolve_alert(alert_id):
    if VERIFIER_ACTIVE:
        data = request.get_json()
        session_token = data.get('token')
        token_is_valid = verifier.validate_session_token(session_token)
        if not token_is_valid:
            raise BadRequest("Invalid session token")
    try:
        alert = alert_manager.resolve_alert(alert_id)
        if not alert:
            return jsonify({"error": "Alert ID not found"}), 400

        return jsonify({
            "alert_id": alert_id,
            "status": "deleted"
        }), 200
    except Exception as e:
        print(e)
        return jsonify({"error": "Failed to resolve alert"}), 400


@app.route('/locations', methods=['POST'])
def register_location():
    try:
        # Parse incoming JSON data
        data = request.get_json()
        if VERIFIER_ACTIVE:
            session_token = data.get('token')
            token_is_valid = verifier.validate_session_token(session_token)
            if not token_is_valid:
                raise BadRequest("Invalid session token")

        # Check if the data contains 'location_id' and 'xyz_point'
        if 'location_id' not in data or 'xyz_point' not in data:
            return jsonify({'error': 'Both location_id and xyz_point are required'}), 400

        location_id = data['location_id']
        coord = tuple(data['xyz_point'])  # Ensure xyz_point is a tuple

        # Check if the location already exists

        # If the location doesn't exist, create a new entry with xyz_points as a list of tuples

        path_manager.register_location(location_id, coord)
        return jsonify({'Success': 'Location Registered'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/locations', methods=['GET'])
def get_all_locations_endpoint():
    if VERIFIER_ACTIVE:
        data = request.get_json()
        session_token = data.get('token')
        token_is_valid = verifier.validate_session_token(session_token)
        if not token_is_valid:
            raise BadRequest("Invalid session token")
    try:
        # Call the get_all_locations function
        locations = path_manager.get_all_locations()
        return jsonify(locations), 200

    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/verify/create_user', methods=['POST'])
def create_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    result = verifier.create_user(username, password)
    if result:
        return jsonify({'message': 'User created successfully', 'user': result}), 201
    else:
        return jsonify({'error': 'User creation failed'}), 400


@app.route('/api/verify/get_token', methods=['POST'])
def get_session_token():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    try:
        session_token = verifier.get_session_token(username, password)
        if session_token:
            return jsonify({'token': session_token}), 200
        else:
            return jsonify({'error': 'Invalid username or password'}), 401
    except (BotoCoreError, ClientError) as e:
        return jsonify({'error': f'Failed to get token: {str(e)}'}), 500


@app.route('/api/verify/validate_token', methods=['POST'])
def validate_session_token():
    data = request.json
    session_token = data.get('token')

    if not session_token:
        return jsonify({'error': 'Token is required'}), 400

    permissions = verifier.validate_session_token(session_token)
    if permissions:
        return jsonify({'permission': permissions}), 200
    else:
        return jsonify({'error': 'Invalid or expired token'}), 401


@app.route('/api/verify/invalidate_token', methods=['DELETE'])
def invalidate_session_token():
    data = request.json
    session_token = data.get('token')

    if not session_token:
        return jsonify({'error': 'Token is required'}), 400

    try:
        success = verifier.invalidate_session_token(session_token)
        if success:
            return jsonify({'message': 'Token invalidated successfully'}), 200
        else:
            return jsonify({'error': 'Failed to invalidate token'}), 500
    except Exception as e:
        return jsonify({'error': f'Failed to invalidate token: {str(e)}'}), 500


@app.route('/api/verify/add_permissions', methods=['POST'])
def add_permissions():
    data = request.json
    session_token = data.get('session_token')
    username = data.get('username')
    new_permissions = data.get('permissions')

    # Check for missing fields
    if not session_token or not username or not new_permissions:
        return jsonify({'error': 'session_token, username, and permissions are required'}), 400

    # Validate the permissions input
    valid_permissions = {'R', 'W', 'A'}
    if not set(new_permissions).issubset(valid_permissions):
        return jsonify({'error': 'Invalid permissions. Only R, W, and A are allowed.'}), 400

    # Attempt to add permissions
    try:
        result = verifier.add_user_permissions(session_token, username, new_permissions)
        print(result)
        if result:
            return jsonify({'message': 'Permissions updated successfully', 'updated_permissions': result}), 200
        else:
            return jsonify({'error': 'Failed to update permissions. Ensure session token is valid and has the required permissions.'}), 403
    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
