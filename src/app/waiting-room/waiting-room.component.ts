import { Component } from '@angular/core';
import {Router} from "@angular/router";
import {websocket} from "../_services/websocket-global";

@Component({
  selector: 'app-waiting-room',
  templateUrl: './waiting-room.component.html',
  styleUrls: ['./waiting-room.component.scss']
})
export class WaitingRoomComponent {

  /**
   * the page to which a user comes after creating a game room or joining a room. 
   * Here it waits for all players to join as determined by the number of players selected. 
   **/

  username: string = '';
  rounds: number | null = 0;
  roomId: string  | null= '';
  timer: string | null = '';
  players: string[] = [];
  startGameEnabled: boolean = false;
  usedLetters: string[] | null = [];
  categories: string[] = [];
  roomDataLoaded: boolean = false;
  numberOfPlayers: number = 0;

  constructor(private router: Router) {
    const routerNavState = this.router.getCurrentNavigation() ?
      this.router.getCurrentNavigation()!.extras.state : null;
      this.username = sessionStorage.getItem('username') || "";
      this.roomId = sessionStorage.getItem('roomId');
      var newRoom = sessionStorage.getItem('newRoom');

      console.log("session storage in waiting room:")
      console.log('username', this.username);
      console.log('roomId', this.roomId);
      console.log('newRoom ', newRoom);

      if(newRoom && newRoom == "true"){
        console.log("new room is true");
        this.timer = sessionStorage.getItem('timer');
        this.players = [this.username];
        this.roomDataLoaded = true;
        var categories = sessionStorage.getItem('categories') || "";
        console.log("categories in waiting room ", categories)
        this.categories = JSON.parse(categories);
        var numberOfPlayers = sessionStorage.getItem('numberOfPlayers') || "";
        this.numberOfPlayers = Number(numberOfPlayers);
        console.log("number of players", this.numberOfPlayers)
        this.rounds = Number(sessionStorage.getItem('rounds'));
        console.log('rounds in waiting room', this.rounds)
        console.log("Session storage in waiting room categories: ", this.categories);
        console.log("Number of players ", this.numberOfPlayers);
        var players = sessionStorage.getItem('players') || "";
        console.log("players", players);
        if(players != ""){

        this.players = JSON.parse(players);
        }

        var startGameEnabled = sessionStorage.getItem('startGameEnabled') || "";
        console.log("startGameEnbaled", startGameEnabled)
        if(startGameEnabled && startGameEnabled == 'true'){
          this.startGameEnabled = true;
        }
        //if (this.categories.length != null && this.categories.length > 0) {
         // this.startGameEnabled = true;
         // sessionStorage.setItem('startGameEnabled', 'true');
        //}

      } else {
        var players = sessionStorage.getItem('players') || "";
        console.log("players in else", players);

        this.players = JSON.parse(players);
        console.log("players in else", this.players);

      }

    websocket.addEventListener('message', this.getRoundData);
    websocket.addEventListener('message', this.addPlayer);
    websocket.addEventListener('message', this.navigateToGameRoom);
  }


  ngOnInit(): void {
    try {
      websocket.send(JSON.stringify({action: 'play_round', roomId: this.roomId}))
    } catch (err) {
      setTimeout(() => {
        // retry sending request in case websocket wasn't set up yet
        websocket.send(JSON.stringify({action: 'play_round', roomId: this.roomId}))
      }, 500);
    }
  }

  ngOnDestroy(): void {
    websocket.removeEventListener('message', this.getRoundData);
    websocket.removeEventListener('message', this.addPlayer);
    websocket.removeEventListener('message', this.navigateToGameRoom);
  }

  startGame(): void {
    /**  
   This method triggers the websocket route navigatePlayersToNextRoom
   */

    console.log("navigate Players To NextRoom")
    console.log("roomId", this.roomId)
    websocket.send(JSON.stringify({
      action: 'navigatePlayersToNextRoom',
      roomId: this.roomId,
    }));

  }

  private getRoundData = (e: any) => {
   /**  
   this method waits for a message from the server, which contains the information about a game round, so that it can be displayed.
   The information is stored in the session storage..
   */

    const serverMessage = JSON.parse(e.data);
    if (serverMessage.method && serverMessage.method === 'play_round'
      && serverMessage.statusCode === 200 && serverMessage.body) {
      if (serverMessage.body.timer) {
        this.timer = serverMessage.body.timer;
        sessionStorage.setItem('timer', String(this.timer))
        //console.log("Timer:" + this.timer)
      }

      if (serverMessage.body.categories) {
        let categories = serverMessage.body.categories;
        let categories_parsed = [];
        for (let category of categories) {
          //console.log("Category to add " + category.S)
          console.log('category', category)
          var parsed = JSON.parse(JSON.stringify(category));
          console.log("value", parsed["S"])
          categories_parsed.push(parsed["S"]);

          console.log('categories_parsed', categories_parsed)

        }
        this.categories = categories_parsed;
        sessionStorage.setItem('categories', String(this.categories))

      }


      if (serverMessage.body.rounds) {
        this.rounds = serverMessage.body.rounds;
        sessionStorage.setItem('rounds', String(this.rounds))

      }

      if (serverMessage.body.numberOfPlayers) {
        this.numberOfPlayers = serverMessage.body.numberOfPlayers;
      }

      this.roomDataLoaded = true;
    }
  }

  private addPlayer = (e: any) => {
   
   /**  
   This method waits for a message from the server, which contains the information if an user entered the game room. If so the new user is displayed by its username. 
   */

    const serverMessage = JSON.parse(e.data);
    console.log("this is addplayer")
    console.log("servermessage", serverMessage)
    if (serverMessage.method && serverMessage.method === 'enter_room' && serverMessage.newUser) {
      this.players.push(serverMessage.newUser);
      sessionStorage.setItem('players', JSON.stringify(this.players));
      console.log("players", this.players)

    }
    /*if (this.numberOfPlayers === this.players.length) { //TODO: check number of players
      this.startGameEnabled = true;
      sessionStorage.setItem('startGameEnabled', 'true');
      console.log("startGameEnabled", this.startGameEnabled)
    }*/
  }

  private navigateToGameRoom = (e: any) => {
    /**  
   This method waits for a message from the server, which contains the information 'navigatePlayersToNextRoom'. It navigates the user to the letter-generator and sets the currentRound Attribute to 1. 
   */
    const serverMessage = JSON.parse(e.data);
    if (serverMessage.method && serverMessage.method === 'navigatePlayersToNextRoom') {
      if (serverMessage.navigateToGameRoom) {
        sessionStorage.setItem('currentRound', '1');
        this.router.navigate(['letter-generator']);
      }
    }
  }

}
