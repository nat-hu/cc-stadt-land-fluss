import json
import boto3
import uuid
import random
import re

region = 'eu-central-1'
api = boto3.client('apigatewaymanagementapi',
                   endpoint_url='https://tjmy88rryf.execute-api.eu-central-1.amazonaws.com/dev/',
                   region_name=region)
dynamo = boto3.client('dynamodb', region_name=region)
pattern_letters = re.compile(r"[a-zA-Z\- ]*")
pattern_alphanumeric = re.compile(r"[a-zA-Z0-9\- ]*")



def create_room(event, context):
  """  This method creates a new room with the given values or default values, if no values are given
  Args:
  :param event: message from websocket
  :return statuscode
  """
  print(event)

  connection_id = event['requestContext']['connectionId']
  request_body = json.loads(event['body'])

  # validate room_id pattern
  room_id = str(request_body['roomId']) if 'roomId' in request_body else str(uuid.uuid4())


  timer = request_body['timer'] if 'timer' in request_body else "180"
  rounds = request_body['rounds'] if 'rounds' in request_body else 3
  number_of_players = request_body['numberOfPlayers'] if 'numberOfPlayers' in request_body else 2
  categories = request_body['categories'] if 'categories' in request_body else ['Stadt', 'Land', 'Fluss']
  used_letters = request_body['usedLetters'] if 'usedLetters' in request_body else []

  #validate username pattern
  user_name = request_body['userName'] if 'userName' in request_body else None
  user_name = user_name if re.fullmatch(pattern_letters,user_name) else "Username"

  users = [
    {user_name: {'status': 'active', 'points': [], 'connectionId': connection_id, 'next_round': False, 'values': []}}]

  if user_name is None:
    print('Error while creating new room: no user name')
    api.post_to_connection(ConnectionId=connection_id, Data=json.dumps(
      {'statusCode': 400, 'method': 'create_room',
       'body': 'Failed to create new room: user name is required'}).encode('utf-8'))
    return {'statusCode': 400, 'body': 'Failed to create new room: user name is required'}

  try:
    print(f'Saving new room with room id {room_id}')




    json_obj_room = {'roomId': room_id, 'timer': str(timer), 'rounds': rounds, 'number_of_players': number_of_players,
                     'used_letters': used_letters, 'categories': categories, 'game_players': users}
    game_data_table = boto3.resource('dynamodb', region_name=region).Table('game_data')
    game_data_table.put_item(Item=json_obj_room)

    api.post_to_connection(ConnectionId=connection_id, Data=json.dumps(
      {'statusCode': 200, 'method': 'create_room', 'body': 'success'}).encode('utf-8'))
    return {'statusCode': 200, 'body': 'Successfully created new room'}

  except Exception as e:
    print(f'Error while saving new room in DB: {e}')
    api.post_to_connection(ConnectionId=connection_id, Data=json.dumps(
      {'statusCode': 400, 'method': 'create_room',
       'body': 'Some error occurred while saving new room in DB: ' + json.dumps(e)}).encode('utf-8'))
    return {'statusCode': 400, 'body': 'Error while saving new room in DB'}



def start_round(event, context):

  """  This method starts next round by generating new letter and checking if that letter was already chosen
  and saves generated letter to database.
  Args:
  :param event: message from websocket
  :return statuscode
  """

  connection_id = event['requestContext']['connectionId']
  request_body = json.loads(event['body'])
  room_id = str(request_body['roomId']) if 'roomId' in request_body else None

  if room_id is None:
    print(f'Error while starting round: no room id')
    api.post_to_connection(ConnectionId=connection_id, Data=json.dumps(
      {'statusCode': 400, 'method': 'start_round',
       'body': 'Failed to start round: no room id'}).encode('utf-8'))
    return {'statusCode': 400, 'body': 'Failed to start round: no room id'}

  room_data = dynamo.get_item(TableName='game_data', Key={'roomId': {'S': room_id}}).get('Item')
  used_letters = list(map(lambda letter: letter.get('S'), room_data.get('used_letters').get('L')))
  alphabet = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U",
              "V", "W", "X", "Y", "Z"]
  print(f'used letters: {used_letters}')
  s = set(used_letters)
  not_used_letters = [x for x in alphabet if x not in s]
  generated_letter = random.choice(not_used_letters)
  msg = {'method': 'start_round', "roomId": room_id, "generated_letter": generated_letter}
  try:
    game_data_table = boto3.resource('dynamodb', region_name=region).Table('game_data')
    response = game_data_table.update_item(
      Key={'roomId': room_id},
      ConditionExpression='attribute_exists(roomId)',
      UpdateExpression="SET #p = list_append(#p, :generated_letter)",
      ExpressionAttributeNames={"#p": "used_letters", },
      ExpressionAttributeValues={':generated_letter': [generated_letter]},
      ReturnValues="UPDATED_NEW")

    lambda_client = boto3.client('lambda', region_name=region)
    print("Broadcast message", msg)
    broadcast_response = lambda_client.invoke(FunctionName="aws-serverless-websockets-dev-broadcast_to_room",
                                              InvocationType='RequestResponse',
                                              Payload=json.dumps(msg))
    if broadcast_response['statusCode'] != 200:
      return {'statusCode': 400, 'body': 'Broadcasting new letter failed'}

    return {'statusCode': 200, 'method': 'start_round', 'body': json.dumps(response)}

  except Exception as e:
    print(f'Error while starting round: {e}')
    api.post_to_connection(ConnectionId=connection_id, Data=json.dumps(
      {'statusCode': 400, 'method': 'start_round', 'body': 'Failed to start new round'}).encode('utf-8'))
    return {'statusCode': 400, 'body': 'Error while adding new letter'}


# sets next round status of given user
# sends next round message to players in room, if all users clicked next round
def check_round(event, context):
  connection_id = event['requestContext']['connectionId']
  request_body = json.loads(event['body'])
  room_id = str(request_body['roomId']) if 'roomId' in request_body else None

  if room_id is None:
    print(f'Error while checking round: no room id')
    api.post_to_connection(ConnectionId=connection_id, Data=json.dumps(
      {'statusCode': 400, 'method': 'check_round', 'body': 'Failed to check round: no room id'}).encode('utf-8'))
    return {'statusCode': 400, 'body': 'Failed to check round: no room id'}

  start_next_round = True
  try:
    room_data = dynamo.get_item(TableName='game_data', Key={'roomId': {'S': room_id}}).get('Item')
    game_data_table = boto3.resource('dynamodb', region_name=region).Table('game_data')
    players_data = room_data.get('game_players').get('L')
    index = 0
    for entry in players_data:
      m = entry.get('M')
      user_name = list(m.keys())[0]
      user = m.get(user_name).get('M')
      if user.get('connectionId').get('S') == connection_id:
        print("set next round to true for player", user_name)
        # set next_round of current connection_id to true to indicate that this user is ready to start
        # the next round
        game_data_table.update_item(
          Key={'roomId': room_id},
          ConditionExpression='attribute_exists(roomId)',
          UpdateExpression=f"SET #g[{index}].#username.#next = :r",
          ExpressionAttributeNames={
            '#g': 'game_players',
            '#username': user_name,
            '#next': 'next_round'
          },
          ExpressionAttributeValues={':r': True},
          ReturnValues="UPDATED_NEW")
      elif start_next_round:
        print("checking next round status for other player ", user_name)
        next_round = user.get('next_round')
        next_round_value = next_round.get('BOOL')
        print("next_round_value for player ", next_round_value)
        if not next_round_value:
          start_next_round = False
      index += 1

    # if all users of one room are ready to start the next round, next_round is set back to False
    # start next round by calling next_round
    if start_next_round:
      print("next round for all players is true")
      index = 0
      for entry in players_data:
        m = entry.get('M')
        user_name = list(m.keys())[0]
        user = m.get(user_name).get('M')
        connection_id = user.get('connectionId')
        connection_id_value = connection_id.get('S')
        game_data_table.update_item(
          Key={'roomId': room_id},  # , 'userName' : user_name
          ConditionExpression='attribute_exists(roomId)',
          UpdateExpression=f"SET #g[{index}].#username.#next = :r",
          ExpressionAttributeNames={
            '#g': 'game_players',
            '#username': user_name,
            '#next': 'next_round'
          },
          ExpressionAttributeValues={':r': False},
          ReturnValues="UPDATED_NEW")
        index += 1
        print("sending start next round message to connectionId", connection_id_value)
        api.post_to_connection(ConnectionId=connection_id_value, Data=json.dumps({
          'statusCode': 200, 'method': 'next_round', 'body': 'start next round'}).encode('utf-8'))
      return {'statusCode': 200, 'body': 'Successfully started new round'}

  except Exception as e:
    print(f'Error while resetting next round data: {e}')
    api.post_to_connection(ConnectionId=connection_id, Data=json.dumps(
      {'statusCode': 400, 'method': 'check_round', 'body': 'Error while resetting next round data: ' + json.dumps(e)})
                           .encode('utf-8'))
    return {'statusCode': 400, 'body': 'Error while resetting next round data'}


def enter_room(event, context):
  
  """  This method adds a user to a room.
  Args:
  :param event: message from websocket
  :return statuscode
  """

  print("Event", event)

  connection_id = event['requestContext']['connectionId']
  request_body = json.loads(event['body'])

  #validate room_id
  room_id = str(request_body['roomId']) if 'roomId' in request_body else None
  print("validation", re.fullmatch(pattern_alphanumeric,room_id))
  room_id = room_id if re.fullmatch(pattern_alphanumeric,room_id) else None

  #validate user_name input
  user_name = request_body['userName'] if 'userName' in request_body else None
  print("validation", re.fullmatch(pattern_letters,user_name))
  user_name = user_name if re.fullmatch(pattern_letters,user_name) else "Username"

  if room_id is None:
    print('error: no room_id')
    api.post_to_connection(ConnectionId=connection_id, Data=json.dumps(
      {'statusCode': 400, 'method': 'enter_room', 'body': 'room_id is required to enter an existing room.'})
                           .encode('utf-8'))
    return {'statusCode': 400, 'body': 'room_id is required to enter an existing room'}

  if user_name is None:
    print('error: no user name')
    api.post_to_connection(ConnectionId=connection_id, Data=json.dumps(
      {'statusCode': 400, 'method': 'enter_room', 'body': 'user name is required.'}).encode('utf-8'))
    return {'statusCode': 400, 'body': 'user name is are required.'}

  try:
    print(f'Adding user ({user_name}) to room {room_id}')
    json_obj_new_user = {
      user_name: {'status': 'active', 'points': [], 'connectionId': connection_id, 'next_round': False, 'values': []}}
    game_data_table = boto3.resource('dynamodb', region_name=region).Table('game_data')
    game_data_table.update_item(
      Key={'roomId': room_id},
      ConditionExpression='attribute_exists(roomId)',
      UpdateExpression="SET #p = list_append(#p, :json_obj_new_user)",
      ExpressionAttributeNames={"#p": "game_players", },
      ExpressionAttributeValues={':json_obj_new_user': [json_obj_new_user]},
      ReturnValues="UPDATED_NEW")

    lambda_client = boto3.client('lambda')
    msg = {'method': 'enter_room', 'roomId': room_id, 'newUser': user_name}
    broadcast_response = lambda_client.invoke(FunctionName="aws-serverless-websockets-dev-broadcast_to_room",
                                              InvocationType='RequestResponse',
                                              Payload=json.dumps(msg))

    if broadcast_response['statusCode'] != 200:
      return {'statusCode': 400, 'body': 'Error while sending new user to players of room with id ' + room_id}

    return {'statusCode': 200, 'body': 'Successfully added new user to room with id ' + room_id}

  except Exception as e:
    print(f'Error while adding user to room: {e}')
    api.post_to_connection(ConnectionId=connection_id, Data=json.dumps(
      {'statusCode': 400, 'method': 'enter_room', 'body': 'Error while adding user to room: ' + json.dumps(2)}).encode(
      'utf-8'))
    return {'statusCode': 400, 'body': 'Error while adding new user to room in DB'}


def save_round(event, context):

  """  This method saves user inputs from category fields in database
  Args:
  :param event: message from websocket
  :return statuscode
  """

  print(f' event: {event}')
  connection_id = event['requestContext']['connectionId']

  request_body = json.loads(event['body'])
  room_id = str(request_body['roomId']) if 'roomId' in request_body else None
  user_name = request_body['username'] if 'username' in request_body else None
  categories_values = request_body['categories_values'] if 'categories_values' in request_body else None
  categories_list = []
  categories_list_validated = []

  #validate category values

  if categories_values:

    for cat in categories_values:
      cat = cat if re.fullmatch(pattern_letters,cat) else ""
      categories_list_validated.append(cat)
    categories_list.append(categories_list_validated)
  else:
    categories_list = []

  if room_id is None:
    print('error: no room_id')
    api.post_to_connection(ConnectionId=connection_id, Data=json.dumps(
      {'statusCode': 400, 'method': 'save_round', 'body': 'room_id is required'}).encode('utf-8'))
    return {'statusCode': 400, 'body': 'room_id is required'}

  if user_name is None:
    print('error: no user name')
    api.post_to_connection(ConnectionId=connection_id, Data=json.dumps(
      {'statusCode': 400, 'method': 'save_round', 'body': 'user name is required.'}).encode('utf-8'))
    return {'statusCode': 400, 'body': 'user name is are required.'}

  try:
    room_data = dynamo.get_item(TableName='game_data', Key={'roomId': {'S': room_id}}).get('Item')
    players_data = room_data.get('game_players').get('L')

    index = 0
    response = None
    for entry in players_data:
      m = entry.get('M')
      user_name_db = list(m.keys())[0]
      if user_name_db == user_name:
        game_data_table = boto3.resource('dynamodb', region_name=region).Table('game_data')
        response = game_data_table.update_item(
          Key={'roomId': room_id},
          ConditionExpression='attribute_exists(roomId)',
          UpdateExpression=f"SET #g[{index}].#username.#val = list_append(#g[{index}].#username.#val, :input)",
          ExpressionAttributeNames={
            '#g': 'game_players',
            '#username': user_name,
            '#val': 'values'
          },
          ExpressionAttributeValues={':input': categories_list},
          ReturnValues="UPDATED_NEW")
      index += 1

    api.post_to_connection(ConnectionId=connection_id, Data=json.dumps(
      {'statusCode': 200, 'method': 'save_round', 'body': 'successfully saved user inputs'}).encode('utf-8'))
    return response['Attributes']

  except Exception as e:
    print(f'Failed to save round: {e}')
    api.post_to_connection(ConnectionId=connection_id, Data=json.dumps(
      {'statusCode': 400, 'method': 'save_round', 'body': 'Failed to save round'}).encode('utf-8'))
    return {'statusCode': 400, 'body': 'Error while adding categories to room in DB'}


def save_points_of_last_round(room_id, user_inputs):
  """ This method saves the points won by the players of a game room under the respective user name in the Dynamo DB at the end of a game round.
  Args:
  :param event: message from websocket
  :return statuscode
  """

  print(f'saving points of last round for room with id {room_id} and user inputs: {user_inputs}')
  try:
    room_data = dynamo.get_item(TableName='game_data', Key={'roomId': {'S': room_id}}).get('Item')
    players_data = room_data.get('game_players').get('L')
    letter = room_data.get('used_letters').get('L')[-1].get('S')
    game_data_table = boto3.resource('dynamodb', region_name=region).Table('game_data')

    calculated_points = calculate_points(user_inputs, letter)
    print(f'calculated points: {calculated_points}')

    index = 0
    saved_points = {}
    for player in players_data:
      user_name = list(player.get('M').keys())[0]
      print(f'saving points for user {user_name} at index {index}: {calculated_points[index]}')
      game_data_table.update_item(
        Key={'roomId': room_id},
        ConditionExpression='attribute_exists(roomId)',
        UpdateExpression=f"SET #g[{index}].#username.#val = list_append(#g[{index}].#username.#val, :input)",
        ExpressionAttributeNames={
          '#g': 'game_players',
          '#username': user_name,
          '#val': 'points'
        },
        ExpressionAttributeValues={':input': [calculated_points[index]]},
        ReturnValues="UPDATED_NEW")
      saved_points.update({user_name: calculated_points[index]})
      index += 1
    return {'statusCode': 200, 'body': saved_points}

  except Exception as e:
    print(f'Failed to save calculated points: {e}')
    return {'statusCode': 400, 'body': 'Error while saving calculated points'}


def calculate_points(user_inputs, letter):
  """ This method calculates the scores of each player in a game room. 
  The calculation follows based on the inputs. The text inputs of the respective players are compared with each other. 
  The point scale is built in such a way that :
  -  a player gets 20 points if no one else has written anything in the column. 
  - 10 points are given if the entry is unique in a column. 
  - 5 points are awarded if another player has entered the same entry in the same column. 
  - Zero points are awarded if there is no entry and if only the corresponding letter was entered or the entry started with a wrong letter. 

  Args:
  :param event: message from websocket
  :return statuscode
  """

  reformatted_user_inputs = user_inputs
  for index in range(len(user_inputs)):
    print(f'reformatting {user_inputs[index]}')
    reformatted_user_inputs[index] = list(map(lambda input_value: check_input_value(input_value, letter),
                                              user_inputs[index]))
    print(f'reformatted user inputs: {reformatted_user_inputs}')
  calculated_points = [0] * len(user_inputs)
  for value_index in range(max([len(value_list) for value_list in reformatted_user_inputs])):
    values_at_index = [value_list[value_index] for value_list in reformatted_user_inputs]
    print(f'values at index {value_index}: {values_at_index}')
    for player_index in range(len(reformatted_user_inputs)):
      player_value = reformatted_user_inputs[player_index][value_index]
      if player_value == '' or len(player_value) == 1:
        # invalid value
        print(f'invalid value')
        calculated_points[player_index] += 0
      elif values_at_index.count(player_value) > 1:
        # other players entered same value
        print(f'adding 5 points')
        calculated_points[player_index] += 5
      elif sum(map(lambda value: len(value) > 0, values_at_index)) == 1:
        # no other player entered a valid value
        print(f'adding 20 points')
        calculated_points[player_index] += 20
      else:
        # no other player entered the same value
        print(f'adding 10 points')
        calculated_points[player_index] += 10
  return calculated_points


def check_input_value(input_value, letter):
  print(f'checking input value {input_value}, letter {letter}')
  input_value = input_value.strip()
  if input_value is not None and len(input_value) > 0 and input_value[0].lower() == letter.lower():
    return input_value.lower()
  else:
    # invalid value (0 points)
    return ''
