import boto3
from boto3.dynamodb.conditions import Key


class ScheduleManager:

    key_name = "schedule_id"
    field_name = "stops"

    def __init__(self,
                 key_id,
                 key,
                 dynamodb_endpoint='http://localhost:8000',
                 region_name='us-east-2',
                 table_name='Schedules'):
        # Initialize the DynamoDB resource with region_name specified
        self.dynamodb = boto3.resource('dynamodb', region_name=region_name)
        self.table = self.dynamodb.Table(table_name)

    def create_schedule(self, key: str, data: list, ser_ids: list=None):
        """
        Creates a new schedule entry for a truck with a list of stops.

        :param key: The ID .
        :param data: A list of stop names (strings).
        :return: Response from DynamoDB put_item operation.
        """
        # Check if the truck_id already exists
        response = self.table.get_item(Key={self.key_name: key})

        if 'Item' in response:
            print(f"Truck ID {key} already has a schedule.")
            return response  # Optionally return the current schedule or handle as needed
        print(data)
        # Create the schedule entry
        ser_ids = [] if ser_ids is None else ser_ids
        response = self.table.put_item(
            Item={
                self.key_name: key,
                self.field_name: data,
                'service_id': ser_ids,
            }
        )

        print(f"Schedule created for  {self.key_name}: {key} with stops: {data}")
        return response

    def get_schedule(self, key: str):
        """
        Retrieves the schedule for a given truck.

        :param key: The ID
        :return: The schedule (list of stops) for the truck.
        """
        response = self.table.get_item(Key={self.key_name: key})

        if 'Item' in response:
            return response['Item'][self.field_name]
        else:
            return None  # Return None if the truck_id does not exist

    def get_schedule_(self, key: str):
        """
        Retrieves the schedule for a given truck.

        :param key: The ID
        :return: The schedule (list of stops) for the truck.
        """
        response = self.table.get_item(Key={self.key_name: key})

        if 'Item' in response:
            return response['Item']['service_id']
        else:
            return None  # Return None if the truck_id does not exist

    def update_schedule(self, key: str, new_stops: list):
        """
        Updates the schedule (stops) for a given truck.

        :param key: The ID of the truck.
        :param new_stops: The new list of stops for the truck.
        :return: Response from DynamoDB update_item operation.
        """
        response = self.table.update_item(
            Key={self.key_name: key},
            UpdateExpression='SET stops = :new_stops',
            ExpressionAttributeValues={
                ':new_stops': new_stops
            },
            ReturnValues="UPDATED_NEW"
        )
        print(f"Updated schedule for Truck ID: {key} with stops: {new_stops}")
        return response

    def get_all_schedules(self):
        """
        Retrieves all truck schedules (truck_id and corresponding stops) from the table.

        :return: A list of dictionaries containing truck_id and stops.
        """
        # Scan the entire table to retrieve all items
        response = self.table.scan()

        # If the scan is successful, return a list of truck_id and stops
        if 'Items' in response:
            return [{self.key_name: item[self.key_name],
                     self.field_name: item[self.field_name]} for item in response['Items']]
        else:
            return []  # Return an empty list if no items are found
