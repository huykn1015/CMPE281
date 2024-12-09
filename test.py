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
    url = 'http://cmpe281-2007092816.us-east-2.elb.amazonaws.com/api/locations/register'

    # Prepare the data to send in the request
    data = {
        'location_id': location_id,
        'xyz_point': xyz_point,
        'token': '4d8d4c9f-4a01-4702-acb5-debf5b7c63b4'
    }

    try:
        # Make the POST request to the Flask endpoint
        response = requests.post(url, json=data)

        # Check if the request was successful
        if response.status_code == 200:
            print(f"Location {location_id} created successfully!")
            print("Response:", response.json())
        else:
            print(f"Failed to create location. Status Code: {response.status_code}")
            print("Error:", response.json())
            print(response, data)
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
for i, c in enumerate(coordinates):
    create_location(str(i), c)
    print(c)
    if i > 22:
        break
# Print the resulting list
print(coordinates)