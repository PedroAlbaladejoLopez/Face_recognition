import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Individuo } from './individuo.component';

describe('Individuo', () => {
  let component: Individuo;
  let fixture: ComponentFixture<Individuo>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Individuo]
    })
    .compileComponents();

    fixture = TestBed.createComponent(Individuo);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
