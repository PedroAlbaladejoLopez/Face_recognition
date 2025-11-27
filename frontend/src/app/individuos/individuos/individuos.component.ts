import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { IndividuoComponent } from './individuo/individuo.component';
import { IndividuosService } from '../service/individuos-service';
import { Individuo } from '../models/individuo.model';

declare var bootstrap: any;

@Component({
  selector: 'app-individuos',
  templateUrl: './individuos.component.html',
  standalone: true,
  imports: [CommonModule, FormsModule, IndividuoComponent]
})
export class IndividuosComponent implements OnInit {
  // Lista de individuos
  individuos: Individuo[] = [];

  // Para agregar un nuevo individuo
  individuoNuevo: Individuo = new Individuo();
  selectedFile: File | null = null;

  // Para editar un individuo
  individuoEditando: Individuo = new Individuo();
  modal: any;
  selectedFileEdit: File | null = null;

  // Para detectar individuos en imagen
  selectedFileDetect: File | null = null;
  detectedIndividuos: Individuo[] = [];
  detectedImageUrl: string | null = null;

  constructor(
    private individuosService: IndividuosService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.cargarIndividuos();
  }

  // --------------------------
  // CRUD de individuos
  // --------------------------
  cargarIndividuos() {
    this.individuosService.getIndividuos().subscribe(data => {
      this.individuos = data;
      this.cdr.detectChanges();
    });
  }

  onFileSelected(event: any) {
    if (event.target.files && event.target.files.length > 0) {
      this.selectedFile = event.target.files[0];
    }
  }

  agregarIndividuo() {
    const formData = new FormData();
    formData.append('nombre', this.individuoNuevo.nombre);
    formData.append('apellido1', this.individuoNuevo.apellido1 || '');
    formData.append('apellido2', this.individuoNuevo.apellido2 || '');
    if (this.selectedFile) formData.append('file', this.selectedFile);

    this.individuosService.postIndividuoConCara(formData).subscribe(() => {
      this.individuoNuevo = new Individuo();
      this.selectedFile = null;
      this.cargarIndividuos();
    });
  }

  eliminarIndividuo(id: string) {
    this.individuosService.deleteIndividuo(id).subscribe(() => this.cargarIndividuos());
  }

  abrirModal(individuo: Individuo) {
    this.individuoEditando = { ...individuo };
    if (!this.modal) {
      this.modal = new bootstrap.Modal(document.getElementById('modalEditar'));
    }
    this.modal.show();
  }

  onFileSelectedEdit(event: any) {
    if (event.target.files && event.target.files.length > 0) {
      this.selectedFileEdit = event.target.files[0];
    }
  }

  guardarEdicion() {
    const formData = new FormData();
    formData.append('id', this.individuoEditando._id);
    formData.append('nombre', this.individuoEditando.nombre);
    formData.append('apellido1', this.individuoEditando.apellido1 || '');
    formData.append('apellido2', this.individuoEditando.apellido2 || '');
    if (this.selectedFileEdit) formData.append('file', this.selectedFileEdit);

    this.individuosService.updateIndividuoConCara(formData).subscribe(() => {
      this.cargarIndividuos();
      this.modal.hide();
      this.selectedFileEdit = null;
    });
  }

  gestionarCaras(id: string) {
    console.log('Gestionar caras:', id);
  }

}
