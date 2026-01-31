import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import {HomeComponent} from "./home/home.component";
import {WaitingRoomComponent} from "./waiting-room/waiting-room.component";
import {CreateRoomComponent} from "./create-room/create-room.component";
import {LetterGeneratorComponent} from "./letter-generator/letter-generator.component";
import {GameRoomComponent} from "./game-room/game-room.component";
import { InputReviewComponent } from "./input-review/input-review.component";
import {HallOfFameComponent} from "./hall-of-fame/hall-of-fame.component";

const routes: Routes = [
  { path: '', component: HomeComponent },
  { path: 'create-room', component: CreateRoomComponent },
  { path: 'waiting-room', component: WaitingRoomComponent },
  { path: 'letter-generator', component: LetterGeneratorComponent },
  { path: 'game-room', component: GameRoomComponent },
  { path: 'input-review', component: InputReviewComponent },
  { path: 'hall-of-fame', component: HallOfFameComponent },
  { path: '**', component: HomeComponent },
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
