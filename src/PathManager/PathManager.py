from decimal import Decimal

import boto3
import math


class PathManager:
    stops_table_name = 'Locations'
    stops_table_key = 'stop_name'
    location_field_name = 'location_id'

    location_table_name = "Coordinates"
    location_table_key = location_field_name
    coordinate_field_name = 'coordinates'

    path_table_name = 'Paths'
    path_table_key = 'schedule_id'
    path_field_name = 'paths'

    def __init__(self,
                 key_id,
                 key,
                 dynamodb_endpoint='http://localhost:8000',
                 region_name='us-east-2'):
        # Initialize the DynamoDB resource with region_name specified
        self.dynamodb = boto3.resource('dynamodb', region_name=region_name)
        # self.stops_table = self.dynamodb.Table(self.stops_table_name)
        self.stops_table = self.dynamodb.Table(self.stops_table_name)
        self.location_table = self.dynamodb.Table(self.location_table_name)
        self.path_table = self.dynamodb.Table(self.path_table_name)

    def get_location_id(self, stop_name):
        # Retrieve location_id from schedule_id
        response = self.stops_table.get_item(Key={self.stops_table_key: stop_name})
        return response['Item'][self.location_field_name] if 'Item' in response else None

    def register_stops(self, stop_name, location_id):
        try:
            # Check if the location already exists
            response = self.location_table.get_item(Key={self.stops_table_key: stop_name})

            if 'Item' in response:
                # If the location already exists, raise an exception
                raise ValueError(f"Stop {stop_name} already exists. Cannot register new points.")

            # If the location doesn't exist, create a new entry with xyz_points as a list of tuples
            self.location_table.put_item(
                Item={
                    self.stops_table_key: stop_name,
                    self.location_field_name: location_id  # Store the tuple as part of a list directly
                }
            )
            print(f"Stop {stop_name} created with id {location_id}")

        except Exception as e:
            print(f"Error registering location: {e}")

    def register_location(self, location_id, coords):
        x, y, z = coords
        try:
            # Check if the location already exists
            response = self.location_table.get_item(Key={self.location_table_key: location_id})

            if 'Item' in response:
                # If the location already exists, raise an exception
                raise ValueError(f"Location ID {location_id} already exists. Cannot register new points.")

            # If the location doesn't exist, create a new entry with xyz_points as a list of tuples
            self.location_table.put_item(
                Item={
                    self.location_table_key: location_id,
                    self.coordinate_field_name: [Decimal(x), Decimal(y), Decimal(z)]  # Store the tuple as part of a list directly
                }
            )
            print(f"Location {location_id} created with point: {coords}")

        except Exception as e:
            print(f"Error registering location: {e}")

    def get_all_locations(self):
        try:
            # Scan the DynamoDB table to get all items
            response = self.location_table.scan()

            # Retrieve and return the list of locations with their xyz points
            locations = []
            for item in response['Items']:
                location_id = item[self.location_table_key]
                xyz_points = item[self.location_field_name]  # Directly access the list of tuples stored in DynamoDB
                locations.append((location_id, xyz_points))

            return locations

        except Exception as e:
            print(f"Error retrieving all locations: {e}")
            return []

    def get_coordinates(self, location_id):
        # Retrieve coordinates from location_id
        response = self.location_table.get_item(Key={self.location_table_key: location_id})
        return response['Item'][self.coordinate_field_name] if 'Item' in response else None

    @staticmethod
    def calculate_distance(coord1, coord2):
        # Calculate Euclidean distance between two points in 3D space
        return math.sqrt(sum((c2 - c1) ** 2 for c1, c2 in zip(coord1, coord2)))

    def find_efficient_path(self, stops_list):
        # Retrieve all coordinates and pair them with stops
        coords = []
        for stop in stops_list:
            location_id = self.get_location_id(stop)
            if location_id:
                coord = self.get_coordinates(location_id)
                if coord:
                    coords.append((stop, coord))

        # Start the path with the first coordinate
        if not coords:
            return []

        visited = [coords.pop(0)]  # List to store the ordered path
        while coords:
            last_stop, last_coord = visited[-1]
            # Find the nearest unvisited point
            nearest = min(coords, key=lambda item: self.calculate_distance(last_coord, item[1]))
            coords.remove(nearest)
            visited.append(nearest)

        # Return the ordered list of stops
        return [coord for stop, coord in visited]

    def save_path(self, schedule_id, path_list):
        # Save the calculated path to the paths table
        self.path_table.put_item(Item={self.path_table_key: schedule_id, self.path_field_name: path_list})
        print(f"Path saved with path_id: {schedule_id}")

    def get_path(self, schedule_id):
        # Retrieve a path from the paths table
        response = self.path_table.get_item(Key={self.path_table_key: schedule_id})
        return response['Item'][self.path_field_name] if 'Item' in response else None

    def get_all_paths(self):
        # Scan the entire table to retrieve all items
        response = self.path_table.scan()
        # If the scan is successful, return a list of truck_id and stops
        if 'Items' in response:
            return [{self.path_table_key: item[self.path_table_key],
                     self.path_field_name: item[self.path_field_name]} for item in response['Items']]
        else:
            return []  # Return an empty list if no items are found


# Example usage
if __name__ == "__main__":
    # Replace 'ScheduleTableName' and 'LocationTableName' with your table names
    path_finder = PathManager('ScheduleTableName', 'LocationTableName')

    stops = ['stop1', 'stop2', 'stop3']
    path = path_finder.find_efficient_path(stops)
    print("Efficient Path:", path)
