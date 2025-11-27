import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DeteccionComponent } from './deteccion.component';

describe('DeteccionComponent', () => {
  let component: DeteccionComponent;
  let fixture: ComponentFixture<DeteccionComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DeteccionComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(DeteccionComponent);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
