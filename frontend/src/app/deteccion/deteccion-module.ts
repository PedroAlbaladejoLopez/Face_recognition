import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

import { DeteccionRoutingModule } from './deteccion-routing-module';
import { DeteccionComponent } from './deteccion.component/deteccion.component';
import { FormsModule } from '@angular/forms';


@NgModule({
  declarations: [],
  imports: [
    CommonModule,
    DeteccionRoutingModule,
    FormsModule
  ]
})
export class DeteccionModule { }
