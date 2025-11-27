import { Component } from '@angular/core';
import { IndividuosComponent } from './individuos/individuos/individuos.component';

@Component({
  selector: 'app-root',
  template: `<app-individuos></app-individuos>`,
  imports: [IndividuosComponent]
})
export class AppComponent {}
