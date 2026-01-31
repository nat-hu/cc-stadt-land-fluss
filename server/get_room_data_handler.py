import json
import set_room_data_handler
import boto3

region = set_room_data_handler.region
api = set_room_data_handler.api
dynamo = set_room_data_handler.dynamo



def play_round(event, context):

  """ This method gets timer, categories and rounds settings to set game room
  Args:
  :param event: message from websocket
  :return statuscode
  """

  print("Event", event)

  request_body = json.loads(event['body'])
  connection_id = event['requestContext']['connectionId']
  room_id = str(request_body['roomId']) if 'roomId' in request_body else None

  if room_id is None:
    print(f'Error while getting room data: no room id')
    api.post_to_connection(ConnectionId=connection_id, Data=json.dumps(
      {'statusCode': 400, 'method': 'play_round', 'body': 'Failed to get room data to play round: no room id'})
                           .encode('utf-8'))
    return {'statusCode': 400, 'body': 'Failed to get room data: no room id'}

  try:
    # get all data from game room with given room id
    room_data = dynamo.get_item(TableName='game_data', Key={'roomId': {'S': room_id}}).get('Item')
    timer = room_data.get('timer').get('S')
    categories = room_data.get('categories').get('L')
    rounds = room_data.get('rounds').get('N')
    number_of_players = room_data.get('number_of_players').get('N')
    print(f"Timer : {timer}, Categories {categories}, Rounds : {rounds} ")

    msg = {'method': 'play_round', "roomId": room_id, "timer": timer, "categories": categories,
           "rounds": rounds, 'numberOfPlayers': number_of_players}
    api.post_to_connection(ConnectionId=connection_id,
                           Data=json.dumps({'statusCode': 200, 'method': 'play_round', 'body': msg}).encode('utf-8'))

  except Exception as e:
    print(f'Failed to get timer, categories and rounds of room with id {room_id}: {e}')
    api.post_to_connection(ConnectionId=connection_id,
                           Data=json.dumps({'statusCode': 400, 'method': 'play_round',
                                            'body': 'Error while broadcasting room data'}).encode('utf-8'))



def get_current_players(event, context):

  """ This method checks if the player can enter the room and sends all player names of the room to the new player
  Args:
  :param event: message from websocket
  :return statuscode
  """

  print("Event", event)

  connection_id = event['requestContext']['connectionId']
  request_body = json.loads(event['body'])
  room_id = str(request_body['roomId']) if 'roomId' in request_body else None

  if room_id is None:
    print(f'Error while getting room data: no room id')
    api.post_to_connection(ConnectionId=connection_id, Data=json.dumps(
      {'statusCode': 400, 'method': 'get_current_players', 'body': 'Failed to get room data: no room id'})
                           .encode('utf-8'))
    return {'statusCode': 400, 'body': 'Failed to get room data: no room id'}

  try:
    room_data = dynamo.get_item(TableName='game_data', Key={'roomId': {'S': room_id}}).get('Item')
    print("Room data", room_data)

    if room_data is None:
      # room id doesn't exist
      print(f"Cannot add new user to room with id {room_id}: room id doesn't exist")
      api.post_to_connection(ConnectionId=connection_id, Data=json.dumps(
        {'statusCode': 400, 'method': 'get_current_players', 'body': 'Room id does not exist'}).encode('utf-8'))
      return {'statusCode': 400, 'body': "Cannot add new user to room: room id doesn't exist"}

    players_data = room_data.get('game_players').get('L')
    print("game_players", players_data)

    # check if maximum number of players is already reached
    allowed_number_of_payers = int(room_data.get('number_of_players').get('N'))
    print(f'allowed number of players: {allowed_number_of_payers}, number of players in room: {len(players_data)}')
    if len(players_data) >= allowed_number_of_payers:
      print(f'Cannot add new user to room with id {room_id}: maximum number of players reached')
      api.post_to_connection(ConnectionId=connection_id, Data=json.dumps(
        {'statusCode': 400, 'method': 'get_current_players', 'body': 'Too many players'}).encode('utf-8'))
      return {'statusCode': 400, 'body': 'Cannot add new user to room: maximum number of players reached'}

    # loop through players data to get each username
    current_players = []
    for entry in players_data:
      m = entry.get('M')
      user_name = list(m.keys())[0]
      print(f"user_name : {user_name}")
      current_players.append(user_name)

    msg = {'method': 'get_current_players', "roomId": room_id, "current_players": current_players}
    api.post_to_connection(ConnectionId=connection_id,
                           Data=json.dumps({'statusCode': 200, 'method': 'get_current_players',
                                            'body': msg}).encode('utf-8'))

  except Exception as e:
    print(f'Failed to get players of current room: {e}')
    api.post_to_connection(ConnectionId=connection_id,
                           Data=json.dumps({'statusCode': 400, 'method': 'get_current_players',
                                            'body': 'Failed to get players of current room'}).encode('utf-8'))


def get_results_for_room(event, context):

  """ This method sends room data and players data to all players of the room eith the given id.
  Args:
  :param event: message from websocket
  :return statuscode
  """


  print(f'event: {event}')

  connection_id = event['requestContext']['connectionId']
  request_body = json.loads(event['body'])
  room_id = str(request_body['roomId']) if 'roomId' in request_body else None

  if room_id is None:
    print(f'Error while getting results for room: no room id')
    api.post_to_connection(ConnectionId=connection_id,
                           Data=json.dumps({'statusCode': 400, 'method': 'get_results_for_room',
                                            'body': 'Failed to get room results: no room id'}).encode('utf-8'))
    return {'statusCode': 400, 'body': 'Failed to get room results: no room id'}

  try:
    print(f'Getting categories, used letters and users of room with id {room_id}')
    room = dynamo.get_item(TableName='game_data', Key={'roomId': {'S': room_id}}).get('Item')
    categories = list(map(lambda category: category.get('S'), room.get('categories').get('L')))
    used_letters = list(map(lambda letter: letter.get('S'), room.get('used_letters').get('L')))
    print(f'room data: {room}')

    # get points of each player
    game_players = room.get('game_players').get('L')
    current_players_data = []
    for player in game_players:
      m = player.get('M')
      user_name = list(m.keys())[0]
      print(f'Getting data of user with user_name {user_name}: {player}')
      points = m.get(user_name).get('M').get('points').get('L')
      points = list(map(lambda point: int(point.get('N')), points))
      points_sum = sum(points)
      values = m.get(user_name).get('M').get('values').get('L')
      values = list(map(lambda value_list:
                        list(map(lambda value: value.get('S'), value_list.get('L'))),
                        values))
      current_players_data.append({'username': user_name, 'points': points, 'points_sum': points_sum, 'values': values})

    api.post_to_connection(ConnectionId=connection_id,
                           Data=json.dumps({'statusCode': 200, 'method': 'get_results_for_room', 'body': {
                             'playersData': current_players_data,
                             'categories': categories,
                             'usedLetters': used_letters
                           }}).encode('utf-8'))
    return {'statusCode': 200, 'body': {
      'playersData': current_players_data,
      'categories': categories,
      'usedLetters': used_letters
      }
    }

  except Exception as e:
    print(f'Exception while getting room data of room with id {room_id}: {e}')
    api.post_to_connection(ConnectionId=connection_id,
                           Data=json.dumps({'statusCode': 400, 'method': 'get_results_for_room',
                                            'body': 'Failed to get room data: ' + json.dumps(e)}).encode('utf-8'))
    return {'statusCode': 400, 'body': 'Failed to get room data: ' + json.dumps(e)}



def load_user_inputs(event, context):
  """ This method loads all user inputs from database and sends all_values 
  (e.g. [["Stuttgart","Rhein", "Deutschland"]]) to players of the room with the given id.
  Args:
  :param event: message from websocket
  :return statuscode
  """

  print(f'event: {event}')

  connection_id = event['requestContext']['connectionId']
  request_body = json.loads(event['body'])
  room_id = str(request_body['roomId']) if 'roomId' in request_body else None

  if room_id is None:
    print(f'Error while getting user inputs for room: no room id')
    api.post_to_connection(ConnectionId=connection_id,
                           Data=json.dumps({'statusCode': 400, 'method': 'load_user_inputs',
                                            'body': 'Failed to get user inputs: no room id'}).encode('utf-8'))
    return {'statusCode': 400, 'body': 'Failed to get user inputs: no room id'}

  data_list = []
  all_categories = []
  try:
    room_data = dynamo.get_item(TableName='game_data', Key={'roomId': {'S': room_id}}).get('Item')
    categories = room_data.get('categories').get('L')
    for category in categories:
      all_categories.append(category.get('S'))
    print("all categories ", categories)
    players_data = room_data.get('game_players').get('L')
    index = 0
    user_inputs = []
    for player in players_data:
      player_values = {}
      m = player.get('M')
      user_name = list(m.keys())[0]
      user = m.get(user_name)
      player_values["username"] = user_name
      print("created dict with username as key and inputs as values", player_values)
      values_list = user.get('M').get('values').get('L')
      print(f'values list for user {user_name}: {values_list}')

      if values_list:
        # get last user inputs of player (current round)
        values = values_list[-1].get('L')
        print('values ', values)
        if values:
          index2 = 0
          for x in range(len(values)):
            player_values[all_categories[index2]] = values[x].get('S')
            index2 += 1
        else:
          player_values[user_name] = {}
        data_list.append(player_values.copy())
      print(f'added user inputs of player {user_name}: {player_values}')
      user_inputs.append(list(map(lambda input_value: input_value.get('S'), values_list[-1].get('L'))))
      index += 1
    print("dict: ", data_list)
    saved_points = set_room_data_handler.save_points_of_last_round(room_id, user_inputs)['body']
    print(f'calculated points: {saved_points}')
    for player in data_list:
      player['points'] = saved_points[player['username']] if player['username'] in saved_points else 0

    lambda_client = boto3.client('lambda', region_name=region)
    msg = {'roomId': room_id, 'statusCode': 200, 'method': 'load_user_inputs', 'body': {"user_inputs": data_list}}
    print(f'Broadcasting user inputs to all users of room with id {room_id}')
    broadcast_response = lambda_client.invoke(FunctionName="aws-serverless-websockets-dev-broadcast_to_room",
                                              InvocationType='RequestResponse',
                                              Payload=json.dumps(msg))
    if broadcast_response['statusCode'] != 200:
      return {'statusCode': 400, 'body': 'Broadcasting user inputs failed'}

    return {"statusCode": 200}
  except Exception as e:
    print(f'Error while loading user inputs: {e}')
    api.post_to_connection(ConnectionId=connection_id, Data=json.dumps(
      {'statusCode': 400, 'method': 'load_user_inputs', 'body': 'Error while loading user inputs: ' + json.dumps(e)})
                           .encode('utf-8'))
    return {'statusCode': 400, 'body': 'Error while loading user input'}
