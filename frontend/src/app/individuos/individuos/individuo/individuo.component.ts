import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Individuo } from '../../models/individuo.model';

@Component({
  selector: 'app-individuo',
  templateUrl: './individuo.component.html',
  styleUrls: ['./individuo.component.css'],
  standalone: true,
  imports: [CommonModule]
})
export class IndividuoComponent {

  @Input() individuo!: Individuo;

  @Output() eliminar = new EventEmitter<string>();
  @Output() editar = new EventEmitter<Individuo>();
  @Output() gestionarCaras = new EventEmitter<string>();

  onEliminar() {
    this.eliminar.emit(this.individuo._id);
  }

  onEditar() {
    this.editar.emit(this.individuo);
  }

  onGestionarCaras() {
    this.gestionarCaras.emit(this.individuo._id);
  }
  getImageUrl(path: string): string {
  // Si el backend devuelve rutas relativas
  if (!path.startsWith('http')) {
    return 'http://localhost:5000' + path;
  }
  return path;
}

}
