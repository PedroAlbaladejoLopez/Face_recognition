import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { IndividuosComponent } from './individuos/individuos.component';
import { IndividuoComponent } from './individuos/individuo/individuo.component';

@NgModule({
  declarations: [
    // No declares componentes standalone
  ],
  imports: [
    CommonModule,
    FormsModule,
    IndividuosComponent, // Importas el standalone component
    IndividuoComponent
  ],
  exports: [
    IndividuosComponent // Lo exportas para usarlo en otros módulos
  ]
})
export class IndividuosModule {}
