import { ComponentFixture, TestBed } from '@angular/core/testing';

import { IndividuosComponent } from './individuos.component';

describe('Individuos', () => {
  let component: IndividuosComponent;
  let fixture: ComponentFixture<IndividuosComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [IndividuosComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(IndividuosComponent);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
