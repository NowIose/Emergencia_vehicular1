import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from 'src/environments/environment';

@Injectable({
  providedIn: 'root',
})
export class EmergenciaService {
  private http = inject(HttpClient);
  private url = `${environment.apiUrl}/emergencias`;

  actualizarEstado(id: string, nuevoEstado: string): Observable<any> {
    // CORRECCIÓN AQUÍ: Usar 'access_token' igual que en tu AuthService
    const token = localStorage.getItem('access_token');

    const headers = new HttpHeaders().set('Authorization', `Bearer ${token}`);

    return this.http.patch(`${this.url}/${id}/estado`, { estado: nuevoEstado }, { headers });
  }

  getMisEmergencias(): Observable<any[]> {
    // CORRECCIÓN AQUÍ TAMBIÉN
    const token = localStorage.getItem('access_token');
    const headers = new HttpHeaders().set('Authorization', `Bearer ${token}`);

    return this.http.get<any[]>(`${this.url}/taller`, { headers });
  }
}
