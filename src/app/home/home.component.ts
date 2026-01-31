import { Component } from '@angular/core';
import {Router} from "@angular/router";
import {websocket} from "../_services/websocket-global";
import { MessageService } from '../_services/toast.service';





@Component({
  selector: 'app-home',
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.scss']
})
export class HomeComponent {
   /**
   * Represents the home page of the game.
   **/

  username: string = '';
  link: string = '';

  constructor(private router: Router, private messageService: MessageService) {
    websocket.addEventListener('message', this.getPlayersOfRoom);
  }

  ngOnDestroy(): void {
    websocket.removeEventListener('message', this.getPlayersOfRoom);
  }

  createRoom() {
    this.router.navigate(['create-room'], { state: {username: this.username.trim()} });
    sessionStorage.setItem('username', this.username.trim());
  }

  enterRoom() {
    websocket.send(JSON.stringify({action: 'get_current_room_ids', roomId: String(this.link)}));
    websocket.send(JSON.stringify({action: 'get_current_players', roomId: String(this.link)}));
  }

  private getPlayersOfRoom = (e: any) => {
    /**  
   This method waits for a message from the server, which contains the information 'get_current_players'. 
   It triggers the websocket route enter_room. The attributes username, roomId, newRoom and players are also stored in the session storage. 
   The user is navigated to the waiting room.
   */

    const serverMessage = JSON.parse(e.data);

    if (serverMessage.method && serverMessage.method === 'get_current_players' && serverMessage.body) {
      if (serverMessage.statusCode === 400 && 'Too many players' === serverMessage.body) {
        this.messageService.add('Raum kann nicht betreten werden - die angegebene Spieleranzahl wurde bereits erreicht');
      } else if (serverMessage.statusCode === 400 && 'Room id does not exist' === serverMessage.body) {
        this.messageService.add('Es konnte kein Raum mit der angegebenen ID gefunden werden. Stelle sicher, dass die Raum-ID stimmt!');
      } else if (serverMessage.statusCode === 200 && serverMessage.body.current_players) {
        let currentPlayers: string[] = serverMessage.body.current_players;
        console.log("current players in home", currentPlayers)
        if (currentPlayers.indexOf(this.username) >= 0) {

          this.messageService.add('Username existiert bereits! Wähle einen anderen Usernamen und fahre fort.');
        } else {
          websocket.send(JSON.stringify({action: 'enter_room', roomId: this.link, userName: this.username.trim()}));

          sessionStorage.setItem('username', this.username);
          sessionStorage.setItem('roomId', this.link);
          sessionStorage.setItem('newRoom', 'false');
          sessionStorage.setItem('players', JSON.stringify(currentPlayers));
          console.log("Set local storage in get_players_of_room: ", sessionStorage.getItem('players'))
          this.router.navigate(['waiting-room']);
        }
      }
    }
  }
}
