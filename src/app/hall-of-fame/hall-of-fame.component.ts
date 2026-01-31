import { Component, OnInit } from '@angular/core';
import {Router} from "@angular/router";
import {websocket} from "../_services/websocket-global";

interface Player {
  username: string;
  points: number[];
  pointsSum: number;
  values: string[][];
}

interface Room {
  categories: string[];
  usedLetters: string[];
}

@Component({
  selector: 'app-hall-of-fame',
  templateUrl: './hall-of-fame.component.html',
  styleUrls: ['./hall-of-fame.component.scss']
})
export class HallOfFameComponent implements OnInit {
   /**
   * creates the page which allows the user to get an overview of the results of the played rounds.
   **/

  roomId: string | undefined;
  playersData: Player[] = [];
  roomData: Room | undefined;
  displayResults: boolean = false;
  displayRoomIdInput: boolean = false;
  resultsLoaded: boolean = false;
  resultsLoadingError: boolean = false;

  constructor(private router: Router) {
    const routerNavState = this.router.getCurrentNavigation() ?
       this.router.getCurrentNavigation()!.extras.state : null;
       this.roomId = sessionStorage.getItem('roomId') || "";

     if (routerNavState) {
       this.displayRoomIdInput = false;
     } else {
       this.resultsLoaded = true;
       this.resultsLoadingError = true;
       this.displayRoomIdInput = true;
     }
    websocket.addEventListener('message', this.getRoomData);
  }

  ngOnInit(): void {
    try {
      websocket.send(JSON.stringify({ action: 'get_results_for_room', roomId: this.roomId }));
    } catch (err) {
      setTimeout(() => {
        // retry sending request in case websocket wasn't set up yet
        websocket.send(JSON.stringify({ action: 'get_results_for_room', roomId: this.roomId }));
      }, 500);
    }
  }

  ngOnDestroy(): void {
    websocket.removeEventListener('message', this.getRoomData);
  }

  setPlayersData(playersData: any): void {
  /**  
   This method is used to display the player results sorted by the achieved points.
   */

    for (let player of playersData) {
      const values: string[][] = [];
      player['values'].forEach((value: string) => values.push(JSON.parse(JSON.stringify(value))));
      this.playersData.push({
        username: player['username'],
        points: player['points'],
        pointsSum: player['points_sum'],
        values: values
      });
    }
    this.playersData.sort((user1, user2) => user1.pointsSum > user2.pointsSum ? -1 : 1);
    this.resultsLoaded = true;
  }

  setNewRoomId() {
   /**  
   This method is used to reload the data of the final results of a room from the DB by triggering the websocket route 'get_results_for_room'.
   */

    this.resultsLoaded = false;
    this.resultsLoadingError = false;
    this.displayRoomIdInput = false;
    websocket.send(JSON.stringify({ action: 'get_results_for_room', roomId: this.roomId }));
  }

  showResults(): void {

    this.displayResults = true;
  }

  closeResults(): void {
    this.displayResults = false;
  }

  exitRoom(): void {
  /**  
   This method triggers the websocket route remove_player_from_room. 
   It waits for a message from the server, which contains the information 'get_results_for_room'. From this, the categories and used letters and the player data are taken and displayed.
   */

    websocket.send(JSON.stringify({ action: 'remove_player_from_room', roomId: this.roomId }));
    sessionStorage.clear();
    this.router.navigate(['']);
  }

  private getRoomData = (e: any) => {
    const serverMessage = JSON.parse(e.data);
    if (serverMessage.method && serverMessage.method === 'get_results_for_room') {
      this.resultsLoaded = true;
      if (serverMessage.statusCode && serverMessage.statusCode === 200
        && serverMessage.body && serverMessage.body.playersData) {
        this.setPlayersData(serverMessage.body.playersData);
        if (serverMessage.body.categories && serverMessage.body.usedLetters) {
          this.roomData = {
            categories: serverMessage.body.categories,
            usedLetters: serverMessage.body.usedLetters
          };
          this.resultsLoadingError = false;
        }
      } else {
        this.resultsLoadingError = true;
      }
    }
  }

}
