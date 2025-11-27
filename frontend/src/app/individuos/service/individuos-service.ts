import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Individuo } from '../models/individuo.model';

@Injectable({
  providedIn: 'root'
})
export class IndividuosService {

  private baseUrl = 'http://localhost:5000/api';

  constructor(private http: HttpClient) {}

  getIndividuos(): Observable<Individuo[]> {
    return this.http.get<Individuo[]>(`${this.baseUrl}/consultar_individuos`);
  }

  postIndividuo(individuo: Individuo): Observable<any> {
    return this.http.post(`${this.baseUrl}/crear_individuo`, individuo);
  }

  deleteIndividuo(id: string): Observable<any> {
    return this.http.delete(`${this.baseUrl}/borrar_individuo/${id}`);
  }

  updateIndividuo(individuo: Individuo): Observable<any> {
    return this.http.put(`${this.baseUrl}/modificar_individuo`, individuo);
  }
  getImagenCara(idCara: string): Observable<any> {
    return this.http.get(`${this.baseUrl}'/cara/'${idCara}'/imagen'`)
  }
  postIndividuoConCara(formData: FormData) {
  return this.http.post(`${this.baseUrl}/crear_individuo_con_cara`, formData);
}
  updateIndividuoConCara(formData: FormData): Observable<any> {
  return this.http.put(`${this.baseUrl}/modificar_individuo_con_cara`, formData);
}
// Nuevo método para detectar imagen
  detectarImagen(formData: FormData): Observable<any> {
    return this.http.post(`${this.baseUrl}/detectar_imagen`, formData);
  }
  detectarVideo(formData: FormData) {
    return this.http.post(`${this.baseUrl}/detectar_video`, formData);
  }

}
