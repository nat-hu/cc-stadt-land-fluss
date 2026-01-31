import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { FormsModule } from '@angular/forms';

import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { HomeComponent } from './home/home.component';
import { CreateRoomComponent } from './create-room/create-room.component';
import { WaitingRoomComponent } from './waiting-room/waiting-room.component';
import { GameRoomComponent } from './game-room/game-room.component';
import { LetterGeneratorComponent } from './letter-generator/letter-generator.component';
import { InputReviewComponent } from './input-review/input-review.component';
import { MessagesComponent } from './messages/messages.component';
import { HallOfFameComponent } from './hall-of-fame/hall-of-fame.component';

@NgModule({
  declarations: [
    AppComponent,
    HomeComponent,
    CreateRoomComponent,
    WaitingRoomComponent,
    GameRoomComponent,
    LetterGeneratorComponent,
    InputReviewComponent,
    MessagesComponent,
    HallOfFameComponent
  ],
  imports: [
    BrowserModule,
    AppRoutingModule,
    FormsModule
  ],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule { }
