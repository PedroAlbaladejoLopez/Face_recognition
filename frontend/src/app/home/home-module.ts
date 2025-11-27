import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    loadChildren: () => import('../home/home.component/home.component').then(m => m.HomeComponent)
  },
  {
    path: 'individuos',
    loadComponent: () =>
      import('../individuos/individuos/individuos.component').then(c => c.IndividuosComponent)
  },
  {
    path: 'deteccion',
    loadComponent: () =>
      import('../deteccion/deteccion.component/deteccion.component').then(c => c.DeteccionComponent)
  }
];
