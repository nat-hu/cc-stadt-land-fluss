export const websocket: WebSocket = new WebSocket("wss://tjmy88rryf.execute-api.eu-central-1.amazonaws.com/dev")

websocket.addEventListener('open', e => {
  console.log('New WebSocket is connected')
});

websocket.addEventListener('close', e => {
  console.log('WebSocket is closed - removing player from room');
  websocket.send(JSON.stringify({ action: 'remove_player_from_room'}));
});

websocket.addEventListener('error', e => console.error('Error in Websocket: ', e));

websocket.addEventListener('message', e => {
  //console.log('Received message: ', JSON.parse(e.data).message)
});

window.onbeforeunload = function() {
  websocket.send(JSON.stringify({ action: 'remove_player_from_room'}));
  websocket.onclose = function () {};
  websocket.close();
};
