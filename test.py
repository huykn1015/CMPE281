import ast

# Your input string
# Specify the file path
file_path = "stops.txt"

# Read the content from the file
with open(file_path, "r") as file:
    input_string = file.read()
coordinates = ast.literal_eval(input_string)

import requests
import json

def create_location(location_id, xyz_point):
    # Define the Flask API URL (assuming it's running locally)
    url = 'http://18.116.118.74/locations'

    # Prepare the data to send in the request
    data = {
        'location_id': location_id,
        'xyz_point': xyz_point
    }

    try:
        # Make the POST request to the Flask endpoint
        response = requests.post(url, json=data)

        # Check if the request was successful
        if response.status_code == 201:
            print(f"Location {location_id} created successfully!")
            print("Response:", response.json())
        else:
            print(f"Failed to create location. Status Code: {response.status_code}")
            print("Error:", response.json())
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
for i, c in enumerate(coordinates):
    create_location(str(i), c)
# Print the resulting list
print(coordinates)