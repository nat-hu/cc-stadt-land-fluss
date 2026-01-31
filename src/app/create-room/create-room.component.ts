import { Component } from '@angular/core';
import {Router} from "@angular/router";
import {v4 as uuidv4} from 'uuid';
import {websocket} from "../_services/websocket-global";

@Component({
  selector: 'app-create-room',
  templateUrl: './create-room.component.html',
  styleUrls: ['./create-room.component.scss']
})
export class CreateRoomComponent {

   /**
   * creates the page that allows a user to customize a game room according to his wishes.
   **/

  username: string = '';
  numberPlayers: number = 2;
  timerOptions: number[] = [60, 120, 180, 240, 300];
  selectedTimerOption: number = 180;
  rounds: number = 3;
  categories: string[] = ['Stadt', 'Land', 'Fluss', 'Name', 'Essen', 'Stars', 'Film', 'Farbe'];
  selectedCategoriesIndices: number[] = [];
  selectedCategories : string[] = [];

  constructor(private router: Router) {
    const routerNavState = this.router.getCurrentNavigation() ?
    this.router.getCurrentNavigation()!.extras.state : null;
    this.username = sessionStorage.getItem('username') || "";
  }

  toggleCategory(index: number): void {
   /**  
   * This method checks that at least three categories have been selected by a user before a game room can be created.
   */
    let categories = document.getElementsByClassName('category');
    categories[index].classList.toggle('category-active');
    if (this.selectedCategoriesIndices.includes(index)) {
      const selectedIndex = this.selectedCategoriesIndices.indexOf(index);
      this.selectedCategoriesIndices.splice(selectedIndex, 1);
      this.selectedCategories.splice(selectedIndex,1);
    } else {
      this.selectedCategoriesIndices.push(index);
      this.selectedCategories.push(this.categories[index]);
    }
  }

  createRoom(): void {

  /**  
   * This method is triggered by the "create room" button click. By storing the most important data of a game room in the session storage, so that they are not lost when the page is reloaded. 
   * In addition, the "create_room" action is triggered via the websocket, so that the most important game room data is also stored in the database. 
   * The user is further navigated to the waiting room.  
   * @example  
   *  <button id="create-room" (click)="createRoom()">
   */

    const roomId = uuidv4();
    sessionStorage.setItem('roomId', roomId);
    sessionStorage.setItem('timer', String(this.selectedTimerOption));
    sessionStorage.setItem('rounds', String(this.rounds));
    sessionStorage.setItem('categories', JSON.stringify(this.selectedCategories));
    sessionStorage.setItem('username', this.username);
    sessionStorage.setItem('newRoom', 'true');
    sessionStorage.setItem('numberOfPlayers', String(this.numberPlayers));
    sessionStorage.setItem('startGameEnabled', String(true));

    websocket.send(JSON.stringify({
      action: 'create_room',
      roomId: roomId,
      timer: this.selectedTimerOption,
      rounds: this.rounds,
      usedLetters: [],
      categories: this.selectedCategories,
      userName: this.username,
      numberOfPlayers: this.numberPlayers
    }));
    this.router.navigate(['waiting-room']);


  }

}
