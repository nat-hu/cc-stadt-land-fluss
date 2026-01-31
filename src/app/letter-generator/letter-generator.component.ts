import { Component, OnInit } from '@angular/core';
import {Router} from "@angular/router";
import {websocket} from "../_services/websocket-global";

@Component({
  selector: 'app-letter-generator',
  templateUrl: './letter-generator.component.html',
  styleUrls: ['./letter-generator.component.scss']
})
export class LetterGeneratorComponent implements OnInit {

   /**
   * Generates a random letter and checks if it has not been selected yet within the other game rounds.
   **/

  generatedLetter: string = '';
  generatedLetter2: string = ''
  room_id : string = '';
  username: string = '';
  startGameEnabled: boolean = false;
  timer: string = '';
  rounds: number = 0;
  categories: string[] = [];
  currentRound: number = 0;

  constructor(private router: Router) {
    const routerNavState = this.router.getCurrentNavigation() ?
    this.router.getCurrentNavigation()!.extras.state : null;
    this.room_id = sessionStorage.getItem('roomId') || "";
    var startGameEnabled = sessionStorage.getItem('startGameEnabled') || "";
    if(startGameEnabled && startGameEnabled == 'true'){
      this.startGameEnabled = true;
    }
    var currentRound = sessionStorage.getItem('currentRound') || "";
    this.currentRound = Number(currentRound);

    websocket.addEventListener('message', this.getGeneratedLetter)
  }

  ngOnInit(): void {
    //console.log("this is startGameEnabled", this.startGameEnabled)
    if (this.startGameEnabled) {
      websocket.send(JSON.stringify({
        action: 'start_round',
        roomId: this.room_id
      }));
    }

    setTimeout(() => {
      this.router.navigate(['game-room']);
     }, 5000);
  }

  ngOnDestroy(): void {
    websocket.removeEventListener('message', this.getGeneratedLetter);
  }

  private getGeneratedLetter = (e: any) => {
  /**  
   This method waits for a message from the server, which contains the information 'start_round'. From this, the generated letter is taken, 
   with which the entries of the categories should begin in the following game round.
   */

    const serverMessage = JSON.parse(e.data);
    if (serverMessage.method && serverMessage.method === 'start_round' && serverMessage.generated_letter) {
      this.generatedLetter = serverMessage.generated_letter;
      this.generatedLetter2 = this.generatedLetter;
      sessionStorage.setItem('generatedLetter', this.generatedLetter)
    }
  }

}
