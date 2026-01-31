import { Component, OnInit } from '@angular/core';
import {websocket} from "../_services/websocket-global";
import {Router} from "@angular/router";
import {MessageService} from "../_services/toast.service";

@Component({
  selector: 'app-input-review',
  templateUrl: './input-review.component.html',
  styleUrls: ['./input-review.component.scss']
})
export class InputReviewComponent implements OnInit {

   /**
   * Represents the view of the game, in which the user is shown what his own input and that of the other players were. 
   **/

  roomId : string = '';
  username: string = '';
  generatedLetter : string = '';
  startGameEnabled : boolean = false;
  numberOfRounds: number = 0;
  categories: string[] = [];
  timer : string = '';
  currentRound: number = 0;

  jsonData: any = [];
  _object = Object;
  userInputsLoaded: boolean = false;
  nextRoundButtonDisabled: boolean = false;

  constructor(private router: Router, private messageService: MessageService) {
    const routerNavState = this.router.getCurrentNavigation() ?
      this.router.getCurrentNavigation()!.extras.state : null;
      this.roomId = sessionStorage.getItem('roomId') || "";
      this.generatedLetter = sessionStorage.getItem('generatedLetter') || "";
      console.log("room id in input review: ", this.roomId)
      console.log("generated letter in input review: ", this.generatedLetter)

      var currentRound = sessionStorage.getItem('currentRound') || "";
      this.currentRound = Number(currentRound);
      var rounds = sessionStorage.getItem('rounds') || "";
      this.numberOfRounds = Number(rounds);
      var startGameEnabled = sessionStorage.getItem('startGameEnabled');
      console.log('startgameEnabled in input review ', startGameEnabled)
      if(startGameEnabled && startGameEnabled == 'true'){
        this.startGameEnabled = true;
      }
 /*    if (routerNavState) {
      this.roomId = routerNavState['roomId'];
      this.username = routerNavState['username'];
      this.startGameEnabled = routerNavState['startGameEnabled'];
      this.generatedLetter = routerNavState['generatedLetter'];
      this.categories = routerNavState['categories'];
      this.timer = routerNavState['timer'];
      this.numberOfRounds = routerNavState['rounds'];
      this.currentRound = routerNavState['currentRound'];
    } */
    websocket.addEventListener('message', this.setUserInputs);
    websocket.addEventListener('message', this.goToGenerateLetter);
  }

  ngOnInit(): void {
    if (this.startGameEnabled) {
      setTimeout(() => {
        // getting user inputs after timeout to make sure all data was saved first
        // TODO: only navigate to input review if all data was saved instead
        websocket.send(JSON.stringify({action: 'load_user_inputs',roomId: this.roomId}));
      }, 3000);
    }
  }

  ngOnDestroy(): void {
    websocket.removeEventListener('message', this.setUserInputs);
    websocket.removeEventListener('message', this.goToGenerateLetter);
  }

  startNextRound(): void {
    /**  
   This method triggers the websocket route check_round. 
   */

    this.nextRoundButtonDisabled = true;
    this.messageService.add('Die nächste Runde wird gestartet, wenn alle Spieler bereit sind');
    websocket.send(JSON.stringify({
      action: 'check_round',
      roomId: this.roomId
    }));
  }

  navigateToHallOfFame(): void {
    this.router.navigate(['hall-of-fame']);
  }

  private setUserInputs = (e: any) => {
   /**  
   This method waits for a message from the server, which contains the information 'load_user_inputs'. From this, the user_inputs are taken and displayed.
   */
   

    const serverMessage = JSON.parse(e.data);
    if (serverMessage.method && serverMessage.method === 'load_user_inputs'
      && serverMessage.body && serverMessage.body.user_inputs) {
      this.jsonData = serverMessage.body.user_inputs;
      console.log("jsondata", this.jsonData)
      this.userInputsLoaded = true;
    }
  }

  private goToGenerateLetter = (e: any) => {
  /**  
   This method saves the number of the current round in the session Storage and navigates to the letter-generator.
   It waits for a message from the server, which contains the information 'next_round'.
   */

    const serverMessage = JSON.parse(e.data);
    if (serverMessage.method && serverMessage.method === 'next_round') {
      this.messageService.clear();
      this.currentRound += 1;
      sessionStorage.setItem('currentRound', String(this.currentRound));
      
      this.router.navigate(['letter-generator']);
    }
  }

}
