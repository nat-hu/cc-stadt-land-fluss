import json
import boto3
import set_room_data_handler

region = set_room_data_handler.region
api = set_room_data_handler.api
dynamo = set_room_data_handler.dynamo



def broadcast_to_room(event, context):
  
  """  This method broadcasts a given message to all players in a room
Args:
:param event: message from websocket
:return statuscode
 """
      

  print("Event", event)


  # Get the roomId from the Event to look up, which players are connected to the game room by Id

  room_id = str(event['roomId']) if 'roomId' in event else None
  print("RoomID: ", room_id)

  if room_id is None:
    print(f'Error while broadcasting message: no room id')
    return {'statusCode': 400, 'body': 'Failed to broadcast message: no room id'}

  request_body_without_room_id = dict(event)
  for entry in request_body_without_room_id.keys():
    print(request_body_without_room_id[entry])

  del request_body_without_room_id['roomId']
  print("Request body without roomId keys:", request_body_without_room_id.keys())

  print("event", event)
  # get all data from game room with given room id
  room_data = dynamo.get_item(TableName='game_data', Key={'roomId': {'S': room_id}}).get('Item')
  game_players = room_data.get('game_players').get('L')

  # loop through players data to get each connection id
  for entry in game_players:
    try:
      m = entry.get('M')
      user_name = list(m.keys())[0]
      user = m.get(user_name).get('M')
      connection_id_user = user.get('connectionId').get('S')
      print(f'Connection id to broadcast to: {connection_id_user}')
      api.post_to_connection(ConnectionId=connection_id_user, Data=json.dumps(dict(event)).encode('utf-8'))
    except Exception as e:
      print(f'Broadcasting message failed: {e}')
      if event['requestContext']['connectionId']:
        api.post_to_connection(ConnectionId=event['requestContext']['connectionId'],
                               Data=json.dumps({'statusCode': 400, 'method': 'broadcast_to_room',
                                                'body': 'Broadcasting message failed'}).encode('utf-8'))
      return {'statusCode': 400, 'body': 'Error while broadcasting message: ' + json.dumps(e)}

  return {'statusCode': 200, 'body': 'Broadcast successful'}


def stop_round(event, context):
  
  """  This method stops a game round, when someone has pressed the stop button. 
  A message is sent to all players in a game room and causes the timer of the game round is set to 10 seconds.

  Args:
  :param event: message from websocket
  :return statuscode
  """

  lambda_client = boto3.client('lambda')
  request_body = json.loads(event['body'])
  room_id = str(request_body['roomId']) if 'roomId' in request_body else None
  msg = {'method': 'stop_round', "roomId": room_id, "stop_round": "Stop"}
  print("stop_round with roomId: ", room_id)
  broadcast_response = lambda_client.invoke(FunctionName="aws-serverless-websockets-dev-broadcast_to_room",
                                            InvocationType='RequestResponse',
                                            Payload=json.dumps(msg))

  if broadcast_response['statusCode'] != 200:
    return {'statusCode': 400, 'body': 'Stopping round failed'}

  return {'statusCode': 200}



def navigatePlayersToNextRoom(event, context):
    
  """  This method navigates all players in one room to game room and is called when main player presses 'start game' button

  Args:
  :param event: message from websocket
  :return statuscode
  """

  request_body = json.loads(event['body'])
  room_id = str(request_body['roomId']) if 'roomId' in request_body else None
  msg = {'method': 'navigatePlayersToNextRoom', "roomId": room_id, "navigateToGameRoom": "Start"}
  lambda_client = boto3.client('lambda')
  broadcast_response = lambda_client.invoke(FunctionName="aws-serverless-websockets-dev-broadcast_to_room",
                                            InvocationType='RequestResponse',
                                            Payload=json.dumps(msg))

  if broadcast_response['statusCode'] != 200:
    return {'statusCode': 400, 'body': 'Navigating players to next room failed'}

  return {'statusCode': 200, 'body': 'Navigate successful'}
