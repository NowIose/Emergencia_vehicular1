import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams, HttpHeaders } from '@angular/common/http';
import { environment } from 'src/environments/environment';

@Injectable({ providedIn: 'root' })
export class AdminReportesService {
  private http = inject(HttpClient);
  private apiUrl = `${environment.apiUrl}/admin/reportes`;

  // 1. Agregamos el parámetro 'orden' como opcional
  getUsuariosReporte(rol?: string, orden?: string) {
    const token = localStorage.getItem('access_token');
    const headers = new HttpHeaders().set('Authorization', `Bearer ${token}`);
    
    let params = new HttpParams();
    
    // 2. Si existe el rol, lo añadimos a los params
    if (rol) params = params.set('rol', rol);
    
    // 3. Si existe el orden, lo añadimos a los params
    if (orden) params = params.set('orden', orden);

    return this.http.get<any[]>(`${this.apiUrl}/usuarios-lista`, { headers, params });
  }
}