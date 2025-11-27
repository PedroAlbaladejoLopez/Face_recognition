import { Routes } from '@angular/router';
import { HomeComponent } from './home/home.component/home.component';
import { IndividuosComponent } from './individuos/individuos/individuos.component';
import { DeteccionComponent } from './deteccion/deteccion.component/deteccion.component';

export const routes: Routes = [
  {
    path: '',
    component: HomeComponent   // <-- ruta raíz
  },
  {
    path: 'individuos',
    component: IndividuosComponent
  },
  {
    path: 'deteccion',
    component: DeteccionComponent
  },
  {
    path: '**',
    redirectTo: ''
  }
];
