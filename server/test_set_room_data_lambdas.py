import json
import boto3
from moto import mock_dynamodb2
import uuid
import unittest
from unittest.mock import patch

import set_room_data_handler as handler


@mock_dynamodb2
class LambdaFunctionsTest(unittest.TestCase):

  def setUp(self):
    self.api = handler.api

    # create test db
    self.table_name = 'game_data'
    self.dynamodb = boto3.resource('dynamodb', region_name=handler.region)
    self.table = self.dynamodb.create_table(
      TableName=self.table_name,
      KeySchema=[{'AttributeName': 'roomId', 'KeyType': 'HASH'}],
      AttributeDefinitions=[{'AttributeName': 'roomId', 'AttributeType': 'S'}],
      ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
    )

    # insert test data (test room)
    self.test_room_id = str(uuid.uuid4())
    test_users = [
      {'testUser': {'status': 'active', 'points': [], 'connectionId': 'TODOTODO', 'next_round': False, 'values': []}},
      {'testUser2': {'status': 'active', 'points': [], 'connectionId': 'testtest', 'next_round': False, 'values': []}}
    ]
    data = {'roomId': self.test_room_id, 'timer': str('60'), 'rounds': 1, 'used_letters': [],
            'categories': ['Fluss', 'Land', 'Tier'], 'game_players': test_users}
    self.table.put_item(Item=data)

  def test_create_room(self):
    test_connection_id = 'TestConnectionId'
    test_user_name = 'testUserName'
    with patch.object(self.api, 'post_to_connection') as mock:
      test_event = {
        'requestContext': {
          'connectionId': test_connection_id
        },
        'body': '{"action": "create_room", "userName": "' + test_user_name + '"}'
      }
      result = handler.create_room(event=test_event, context={})

    # check return value
    expected_result = {'statusCode': 200, 'body': 'Successfully created new room'}
    self.assertEqual(expected_result, result)

    # check if correct values are send to clients
    expected = [
      ({'ConnectionId': test_connection_id, 'Data':
        json.dumps({'statusCode': 200, 'method': 'create_room', 'body': 'success'}).encode('utf-8')},)
    ]
    self.assertTrue(mock.call_args_list == expected)

    # check if data for new room is inserted in db
    table_elements = self.dynamodb.Table(self.table_name).scan()
    self.assertEqual(2, len(table_elements['Items']))
    for room in table_elements['Items']:
      if room['roomId'] != self.test_room_id:
        self.assertEqual('180', room['timer'])
        self.assertEqual(3, room['rounds'])
        self.assertEqual(2, room['number_of_players'])
        self.assertEqual([], room['used_letters'])
        self.assertEqual(['Stadt', 'Land', 'Fluss'], room['categories'])
        self.assertEqual(1, len(room['game_players']))
        self.assertTrue(test_user_name in room['game_players'][0])
        self.assertEqual(test_connection_id, room['game_players'][0][test_user_name]['connectionId'])

  def tearDown(self):
    self.table.delete()
    self.dynamodb = None


if __name__ == '__main__':
  unittest.main()
