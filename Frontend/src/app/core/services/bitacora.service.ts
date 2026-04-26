import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from 'src/environments/environment';

export interface BitacoraEntry {
  id: number;
  ip: string;
  agente: string;
  hora: string;
  fecha: string;
  accion: string;
  detalle: string;
  id_usuario: number;
  id_taller: number;
}

@Injectable({
  providedIn: 'root'
})
export class BitacoraService {
  private http = inject(HttpClient);
  private apiUrl = `${environment.apiUrl}/bitacora`;

  getBitacora(): Observable<BitacoraEntry[]> {
    const token = localStorage.getItem('access_token');
    const headers = new HttpHeaders().set('Authorization', `Bearer ${token}`);
    return this.http.get<BitacoraEntry[]>(`${this.apiUrl}/`, { headers });
  }
}
