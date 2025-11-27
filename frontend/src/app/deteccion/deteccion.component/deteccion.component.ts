import { Component, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { IndividuosService } from '../../individuos/service/individuos-service';
import { Individuo } from '../../individuos/models/individuo.model';

interface FrameVideo {
  frame_path: string;
  individuo: Individuo;
}

interface IndividuoConFrames extends Individuo {
  frames?: FrameVideo[];
  carasUrls?: string[];
}

@Component({
  selector: 'app-deteccion',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './deteccion.component.html',
  styleUrls: ['./deteccion.component.css'],
})
export class DeteccionComponent {
  // ------------------ DETECCIÓN IMAGEN ------------------
  selectedFileDetect: File | null = null;
  detectedIndividuos: Individuo[] = [];
  detectedImageUrl: string | null = null;

  // ------------------ DETECCIÓN VIDEO ------------------
  selectedFileVideo: File | null = null;
  individuosVideo: IndividuoConFrames[] = [];
  framesVideo: FrameVideo[] = [];

  constructor(
    private individuosService: IndividuosService,
    private cdr: ChangeDetectorRef
  ) {}

  // ================= IMAGEN =================
  onFileSelectedDetect(event: any) {
    if (event.target.files && event.target.files.length > 0) {
      this.selectedFileDetect = event.target.files[0];
    }
  }

  detectarImagen() {
  if (!this.selectedFileDetect) return;
  const formData = new FormData();
  formData.append('file', this.selectedFileDetect);

  this.individuosService.detectarImagen(formData).subscribe((res: any) => {
    // Guardar la lista de individuos detectados
    this.detectedIndividuos = res.individuos_detectados || [];

    // Tomar la primera imagen anotada
    if (res.imagen_deteccion) {
      this.detectedImageUrl = `http://localhost:5000/${res.imagen_deteccion}`;
    } else {
      this.detectedImageUrl = null;
    }

    // Forzar actualización del template
    this.cdr.detectChanges();
  });
}


  // ================= VIDEO =================
  onFileSelectedVideo(event: any) {
    if (event.target.files && event.target.files.length > 0) {
      this.selectedFileVideo = event.target.files[0];
    }
  }

  detectarVideo() {
    if (!this.selectedFileVideo) return;
    const formData = new FormData();
    formData.append('file', this.selectedFileVideo);

    this.individuosService.detectarVideo(formData).subscribe((res: any) => {
      // Guardar los frames de detección
      this.framesVideo = (res.frames_deteccion || []).map((f: any) => ({
        frame_path: `http://localhost:5000/${f.frame_path}`,
        individuo: f.individuo,
      }));

      // Mapear individuos y asignar solo sus frames
      this.individuosVideo = (res.individuos_detectados || []).map((ind: any) => {
        const indConFrames: IndividuoConFrames = { ...ind };
        indConFrames.frames = this.framesVideo.filter(fv => fv.individuo._id === ind._id);
        indConFrames.carasUrls = []; // No mostrar caras
        return indConFrames;
      });

      this.cdr.detectChanges();
    });
  }

  getImageUrl(path: string) {
    return path ? path : '';
  }
}
