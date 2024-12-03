from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.exceptions import BadRequest, NotFound
import uuid
from botocore.exceptions import BotoCoreError, ClientError

from ScheduleManager.ScheduleManager import ScheduleManager
from PathManager.PathManager import PathManager
from AlertManager.AlertManager import AlertManager


app = Flask(__name__)
CORS(app)
key_id = 'jve9vw'
key = 'fx211'
schedule_manager = ScheduleManager(key_id, key)
path_manager = PathManager(key_id, key)
alert_manager = AlertManager(key_id, key)

@app.route('/api/path-manager/<schedule_id>', methods=['GET'])
def get_path(schedule_id):
    path = path_manager.get_path(schedule_id)
    if path is not None:
        return jsonify({"schedule_id": schedule_id, "path": path}, 200)
    stops = schedule_manager.get_schedule(schedule_id)
    if stops is None:
        raise BadRequest(f"Schedule {{{schedule_id}}} does not exist")

    path = path_manager.find_efficient_path(stops)
    path_manager.save_path(schedule_id, path)

    return jsonify({"schedule_id": schedule_id, "path": path}, 200)


@app.route('/api/schedule-manager/', methods=['GET'])
@app.route('/api/schedule-manager/<schedule_id>', methods=['GET'])
def get_schedules(schedule_id=None):
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
    print(data)
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
    try:
        alerts = alert_manager.get_all_active_alerts()
        return jsonify(alerts), 200
    except Exception as e:
        return jsonify({"error": "Alert service is down"}), 400

@app.route('/api/alerts/resolved', methods=['GET'])
def get_resolved_alerts():
    try:
        alerts = alert_manager.get_all_resolved_alerts()
        return jsonify(alerts), 200
    except Exception as e:
        return jsonify({"error": "Alert service is down"}), 400

@app.route('/api/alerts', methods=['POST'])
def create_alert():
    try:
        data = request.get_json()
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



if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
