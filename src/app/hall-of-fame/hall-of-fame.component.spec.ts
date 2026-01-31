import { ComponentFixture, TestBed } from '@angular/core/testing';

import { HallOfFameComponent } from './hall-of-fame.component';
import {RouterTestingModule} from "@angular/router/testing";

describe('HallOfFameComponent', () => {
  let component: HallOfFameComponent;
  let fixture: ComponentFixture<HallOfFameComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [RouterTestingModule],
      declarations: [ HallOfFameComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(HallOfFameComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
