import { Cara } from './cara.model';

export class Individuo {
  _id!: string;
  nombre!: string;
  apellido1!: string;
  apellido2!: string;
  caras: Cara[] = [];
}
