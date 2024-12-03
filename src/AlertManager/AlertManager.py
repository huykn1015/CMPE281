import uuid

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import BotoCoreError, ClientError


class AlertManager:
    alert_key_name = 'alert_id'
    active_table_name = 'ActiveAlerts'
    alert_field_name = 'Description'
    resolved_table_name = 'ResolvedAlerts'

    def __init__(self,
                 key_id,
                 key,
                 dynamodb_endpoint='http://localhost:8000',
                 region_name='us-west-2'):
        # Initialize the DynamoDB resource with region_name specified
        self.dynamodb = boto3.resource('dynamodb',
                                       endpoint_url=dynamodb_endpoint,
                                       region_name=region_name,  # or any other region
                                       aws_access_key_id=key_id,
                                       aws_secret_access_key=key)
        # self.stops_table = self.dynamodb.Table(self.stops_table_name)
        self.active_alerts_table = self.dynamodb.Table(self.active_table_name)
        self.past_alerts_table = self.dynamodb.Table(self.resolved_table_name)

    def create_alert(self, description):
        """
        Creates a new alert in the active alerts table, automatically assigning a unique alert ID.
        """
        alert_id = str(uuid.uuid4())  # Generate a unique alert ID
        try:
            self.active_alerts_table.put_item(
                Item={
                    self.alert_key_name: alert_id,
                    self.alert_field_name: description
                }
            )
            print(f"Alert {alert_id} created successfully.")
            return {"alert_id": alert_id, "description": description}
        except (BotoCoreError, ClientError) as error:
            print(f"Failed to create alert {alert_id}: {error}")
            return None

    def get_all_active_alerts(self):
        """
        Retrieves all alerts from the active alerts table.
        """
        try:
            response = self.active_alerts_table.scan()
            return response.get('Items', [])
        except (BotoCoreError, ClientError) as error:
            print(f"Failed to retrieve active alerts: {error}")
            return []

    def get_all_resolved_alerts(self):
        """
        Retrieves all alerts from the active alerts table.
        """
        try:
            response = self.past_alerts_table.scan()
            return response.get('Items', [])
        except (BotoCoreError, ClientError) as error:
            print(f"Failed to retrieve active alerts: {error}")
            return []

    def resolve_alert(self, alert_id):
        """
        Resolves an alert by moving it from the active alerts table to the past alerts table.
        """
        try:
            # Retrieve the alert from the active alerts table
            response = self.active_alerts_table.get_item(Key={self.alert_key_name: alert_id})
            alert = response.get('Item')

            if not alert:
                print(f"Alert {alert_id} not found.")
                return

            # Insert the alert into the past alerts table
            self.past_alerts_table.put_item(Item=alert)

            # Delete the alert from the active alerts table
            self.active_alerts_table.delete_item(Key={self.alert_key_name: alert_id})
            print(f"Alert {alert_id} resolved successfully.")
            return True
        except (BotoCoreError, ClientError) as error:
            print(f"Failed to resolve alert {alert_id}: {error}")

    def get_all_alerts(self):
        """
        Retrieves all alerts from both active and past alerts tables.
        """
        try:
            # Retrieve active alerts
            active_alerts_response = self.active_alerts_table.scan()
            active_alerts = active_alerts_response.get('Items', [])

            # Retrieve past alerts
            past_alerts_response = self.past_alerts_table.scan()
            past_alerts = past_alerts_response.get('Items', [])

            return {
                'active_alerts': active_alerts,
                'past_alerts': past_alerts
            }
        except (BotoCoreError, ClientError) as error:
            print(f"Failed to retrieve all alerts: {error}")
            return {'active_alerts': [], 'past_alerts': []}