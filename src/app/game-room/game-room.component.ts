import { Component, OnInit } from '@angular/core';
import {websocket} from "../_services/websocket-global";
import {Router} from "@angular/router";
import { MessageService } from '../_services/toast.service';
import { FormsModule } from '@angular/forms';


@Component({
  selector: 'app-game-room',
  templateUrl: './game-room.component.html',
  styleUrls: ['./game-room.component.scss']
})
export class GameRoomComponent implements OnInit {

   /**
   * creates the page that allows a user to enter his text input in the fields of the given category
   **/

  currentRound: number = 1;
  numberOfRounds: number = 0;
  generatedLetter: string = '';
  categories: string[] = [];
  room_id : string = '';
  timer : string = '';
  expirationCounter : string = '';
  username:string = '';
  timer2: any;
  

  startGameEnabled : boolean = false;
  buttonClicked : boolean = false;
  stopButtonDisabled: boolean = true;
  inputsFieldsDisabled: boolean = false;

  constructor(private router: Router, private messageService: MessageService) {
    const routerNavState = this.router.getCurrentNavigation() ?
      this.router.getCurrentNavigation()!.extras.state : null;
      this.room_id = sessionStorage.getItem('roomId') || "";
      this.username = sessionStorage.getItem('username') || "" ;
      this.generatedLetter = sessionStorage.getItem('generatedLetter') || "" ;
      var startGameEnabled = sessionStorage.getItem('startGameEnabled');
      console.log('session storage in game room')
      console.log('username', this.username);
      console.log('generatedletter', this.generatedLetter);

      if(startGameEnabled && startGameEnabled == 'true'){
        this.startGameEnabled = true;
      }
      var categories = sessionStorage.getItem('categories') || "";
      categories = categories.replace('[', "");
      categories =  categories.replace(new RegExp('"', 'g'), "");
      categories = categories.replace(']', "");

      console.log('categories in game room ', categories)
      if(categories){
        this.categories = categories.split(","); 
      }
      console.log('categories', this.categories);

      this.timer = sessionStorage.getItem('timer') || '180';  
      this.numberOfRounds = Number(sessionStorage.getItem('rounds'));
      var currentRound = sessionStorage.getItem('currentRound');
      this.currentRound = Number(currentRound);
 
    websocket.addEventListener('message', this.roundStopped);
    websocket.addEventListener('message', this.navigateToInputReview);
  }

  ngOnInit(): void {
    this.startTimer(this.timer);
  }

  ngOnDestroy(): void {
    websocket.removeEventListener('message', this.roundStopped);
    websocket.removeEventListener('message', this.navigateToInputReview);
  }

  checkStopButtonEnabled(): void {
    let allInputFieldsContainText = true;
    for (const category of this.categories) {
      const inputText = (<HTMLInputElement>document.getElementById('cat-' + category)).value;
      if (!inputText || '' === inputText.trim()) {
        allInputFieldsContainText = false;
        break;
      }
    }
    this.stopButtonDisabled = !allInputFieldsContainText;
  }

  stopRound(buttonClicked: boolean): void {
   /**  
   * This method triggers that the game timer of a round is set to 10 seconds and the method sendStopBroadcast() is called.
   * It comes to the method call as soon as a player presses the Stop button.
   */

    if (buttonClicked) {
      this.buttonClicked = true;
      this.sendStopBroadcast();
      this.startTimer('10');
    } else {
      this.saveRound();
    }
  }

  saveRound() : void {
  /**  
   This method triggers the route save_round on the websocket. 
   After a game round, the user entries of the individual categories with the corresponding user name are sent to the websocket so that they can be saved in the Dynamo DB. 
   */

    let  categoriesValues: string [] = [];
    // get user input from category fields
    for (const category of this.categories) {
      const inputText = (<HTMLInputElement>document.getElementById('cat-' + category)).value;
      if (inputText) {
        categoriesValues.push(inputText);
      } else {
        categoriesValues.push('');
      }
    }

    websocket.send(JSON.stringify({
      action: 'save_round',
      roomId: this.room_id,
      categories_values: categoriesValues,
      username: this.username}));
  }

  sendStopBroadcast(): void {
  /**  
   This method triggers the route stop_round on the websocket. 
   */

    websocket.send(JSON.stringify({
      action: 'stop_round',
      roomId: this.room_id,
    }));
  }

  startTimer(secsToStart: string): void {
  /**  
   This method sets the timer of the game round and counts it down every second. 
   When it expires, the round is stopped and the user's input is sent to the websocket for saving.
   */

    clearInterval(this.timer2);
    let start: number = Number(secsToStart);
    let s: number;
    this.timer2 = setInterval(() => {
      s = start;
      const second = s < 10 ? '0' + s : s;
      this.expirationCounter = second.toString();
      if (Number(start) <= 0) {
          clearInterval(this.timer2);
          this.expirationCounter = 'Zeit abgelaufen';
          this.stopRound(false);
      }
      start--;
    }, 1000);
  }

  private roundStopped = (e: any) => {

  /**  
   This methode waits for the message from the websocket 
   which contains the information that the round has been stopped. 
   When the message is received, messages are sent to all players in the room that there are only 10 seconds left and the timer is set to 10 seconds.
   */

    const serverMessage = JSON.parse(e.data);
    if (serverMessage.method && serverMessage.method === 'stop_round') {
      if (serverMessage.stop_round) {
        if (this.buttonClicked) {
          this.messageService.add('Runde gestoppt - Die anderen Spieler haben noch 10 Sekunden Zeit');
          this.inputsFieldsDisabled = true;
        } else {
          this.messageService.add('Jemand hat den Stopp-Button gedrückt! Du hast noch 10 Sekunden!');
        }
        // If someone clicks the stop button, the timer for every other player is set to 10
        this.startTimer('10');
        this.buttonClicked = true;
      }
    }
  }

  private navigateToInputReview = (e:any) => {
   /**  
   This method navigates the user to the view input-review
   */

    const serverMessage = JSON.parse(e.data);
    if (serverMessage.method && serverMessage.method === 'save_round' && serverMessage.statusCode === 200) {
      this.router.navigate(['input-review']
      );
    }
  }

 
}



