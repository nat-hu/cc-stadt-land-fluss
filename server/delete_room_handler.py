import json
import boto3

import set_room_data_handler

region = set_room_data_handler.region
api = set_room_data_handler.api
dynamo = set_room_data_handler.dynamo


def remove_player_from_room(event, context):
  """ This method sets player status to inactive and deletes room, if all players of this room are inactive
  Args:
  :param event: message from websocket
  :return statuscode
  """

  print(f'event: {event}')

  connection_id = event['requestContext']['connectionId']
  request_body = json.loads(event['body'])
  room_id = str(request_body['roomId']) if 'roomId' in request_body else None

  if room_id is None:
    room_id = find_room_id_by_player_connection_id(connection_id)
    print(f'found room id for client id: {room_id}')
    if room_id is None:
      print(f'Error while removing player from room: failed to find connection id {connection_id} in any room')
      api.post_to_connection(ConnectionId=connection_id, Data=json.dumps({
        'statusCode': 400, 'method': 'remove_player_from_room',
        'body': 'Failed to remove player from room: no room id'}).encode('utf-8'))
      return {'statusCode': 400, 'body': 'Failed to remove player from room: no room id'}

  delete_room = True
  try:
    room_data = dynamo.get_item(TableName='game_data', Key={'roomId': {'S': room_id}}).get('Item')
    players_data = room_data.get('game_players').get('L')
    index = 0
    for player in players_data:
      m = player.get('M')
      user_name = list(m.keys())[0]
      user = m.get(user_name).get('M')
      connection_id_user = user.get('connectionId')
      if connection_id_user.get('S') == connection_id:
        game_data_table = boto3.resource('dynamodb', region_name=region).Table('game_data')
        print(f'setting status of player <{user_name}> to inactive player')

        game_data_table.update_item(
          Key={'roomId': room_id},
          ConditionExpression='attribute_exists(roomId)',
          UpdateExpression=f"SET #g[{index}].#username.#next = :r",
          ExpressionAttributeNames={
            '#g': 'game_players',
            '#username': user_name,
            '#next': 'status'
          },
          ExpressionAttributeValues={':r': 'inactive'},
          ReturnValues="UPDATED_NEW")
      else:
        user_status = user.get('status').get('S')
        print(f'checking status of other player {user_name}: {user_status}')
        if user_status != 'inactive':
          delete_room = False
      index += 1

    if delete_room:
      delete_room_by_id(room_id)

    return {'statusCode': 200, 'body': 'Successfully removed player from room'}

  except Exception as e:
    print(f'Failed to set player status to inactive and delete room: {e}')
    api.post_to_connection(ConnectionId=connection_id, Data=json.dumps(
      {'statusCode': 400, 'method': 'remove_player_from_room',
       'body': 'Failed to set player status to inactive and delete room'}).encode('utf-8'))
    return {'statusCode': 400, 'body': 'Error while setting player status to inactive and delete room'}


def delete_room_by_id(room_id):
  """ This method deletes the entry of the corresponding room id in the dynamo db.
  Args:
  :param event: message from websocket
  :return statuscode
  """

  print(f'Deleting room with id {room_id} from DB')
  game_data_table = boto3.resource('dynamodb', region_name=region).Table('game_data')
  game_data_table.delete_item(
    Key={'roomId': room_id},
    ConditionExpression='attribute_exists(roomId)',
    ReturnValues="NONE")


def find_room_id_by_player_connection_id(connection_id):
  """ This method requests the room id from the database based on the given player connection id.
  Args:
  :param event: message from websocket
  :return statuscode
  """

  print(f'getting room id of player with connection id {connection_id}')
  game_data_table = boto3.resource('dynamodb', region_name=region).Table('game_data')
  rooms = game_data_table.scan()['Items']
  for room in rooms:
    for player in room.get('game_players'):
      user_name = list(player.keys())[0]
      if connection_id == player.get(user_name).get('connectionId'):
        return room.get('roomId')
  return None
