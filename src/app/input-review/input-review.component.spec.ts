import { ComponentFixture, TestBed } from '@angular/core/testing';

import { InputReviewComponent } from './input-review.component';
import {RouterTestingModule} from "@angular/router/testing";

describe('InputReviewComponent', () => {
  let component: InputReviewComponent;
  let fixture: ComponentFixture<InputReviewComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [RouterTestingModule],
      declarations: [ InputReviewComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(InputReviewComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
