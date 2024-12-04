import uuid
import hashlib
import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import BotoCoreError, ClientError


class Verifier:
    user_table_name = 'Users'
    user_key_name = 'user_name'
    user_field_name = 'password_hash'

    tokens_table_name = 'SessionTokens'
    token_key_name = 'active_tokens'
    token_field_name = 'perm'

    def __init__(self,
                 region_name='us-east-2'):
        self.dynamodb = boto3.resource('dynamodb', region_name=region_name)
        self.users_table = self.dynamodb.Table(self.user_table_name)
        self.sessions_table = self.dynamodb.Table(self.tokens_table_name)

    def create_user(self, username, password):
        password_bytes = password.encode('utf-8')
        hashed_password = hashlib.sha256(password_bytes).hexdigest()
        response = self.users_table.get_item(Key={self.user_key_name: username})

        if 'Item' in response:
            print(f'User {username} already exists')
            return None
        try:
            self.users_table.put_item(
                Item={
                    self.user_key_name: username,
                    self.user_field_name: hashed_password,
                    self.token_field_name: 'R'
                }
            )
            print(f"User {username} created successfully.")
            return {"User": username}
        except (BotoCoreError, ClientError) as error:
            print(f"Failed to create {username}: {error}")
            return None

    def add_user_permissions(self, session_token, username, new_permissions):
        permissions = self.validate_session_token(session_token)
        if 'A' in permissions:
            try:
                response = self.users_table.update_item(
                    Key={self.user_key_name: username },
                    UpdateExpression='SET permissions = :new_permissions',
                    ExpressionAttributeValues={
                        ':new_permissions': new_permissions
                    },
                    ReturnValues="UPDATED_NEW"
                )
                return response
            except (BotoCoreError, ClientError) as error:
                print(f"Failed to create {username}: {error}")
                return None
        return None

    def get_session_token(self, username, password):
        response = self.users_table.get_item(Key={self.user_key_name: username})
        if 'Item' not in response:
            print(f'User {username} does not exists')
            return None

        password_bytes = password.encode('utf-8')
        hashed_password = hashlib.sha256(password_bytes).hexdigest()
        expected_hash = response['Item'][self.user_field_name]
        if hashed_password != expected_hash:
            print("Invalid Password")
            print(hashed_password, expected_hash)
            return None

        session_token = str(uuid.uuid4())
        permissions = response['Item'][self.token_field_name]
        self.sessions_table.put_item(
            Item={
                self.token_key_name: session_token,
                self.token_field_name: permissions
            }
        )
        return session_token

    def validate_session_token(self, session_token):
        response = self.sessions_table.get_item(Key={self.token_key_name: session_token})
        if 'Item' not in response:
            print(f'Session {session_token} does not exist')
            return None

        return response['Item'][self.token_field_name]

    def invalidate_session_token(self, session_token):
        try:
            self.sessions_table.delete_item(Key={self.token_key_name: session_token})
            return True
        except Exception as e:
            print(f"Failed to delete session token: {e}")
            return False
