import { Component } from '@angular/core';
import { IndividuosComponent } from './individuos/individuos/individuos.component';

@Component({
  selector: 'app-root',
  template: `<app-individuos></app-individuos>`,
  standalone: true,
  imports: [IndividuosComponent]
})
export class App {}
