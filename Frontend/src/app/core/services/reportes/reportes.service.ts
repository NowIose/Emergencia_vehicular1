import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from 'src/environments/environment';
export interface EstadisticaEmergencia {
  etiqueta: string;
  total: number;
}

@Injectable({
  providedIn: 'root'
})
export class ReportesService {
  private http = inject(HttpClient);
  private apiUrl = `${environment.apiUrl}/reportes/estadisticas`;

  constructor() {}

  // Seguimos tu patrón de ChatService para las cabeceras
  private getHeaders() {
    const token = localStorage.getItem('access_token');
    return {
      headers: new HttpHeaders({
        'Authorization': `Bearer ${token}`
      })
    };
  }

  obtenerEstadisticas(fechaInicio: string, fechaFin: string, agrupacion: string): Observable<EstadisticaEmergencia[]> {
    let params = new HttpParams()
      .set('fecha_inicio', fechaInicio)
      .set('fecha_fin', fechaFin)
      .set('agrupacion', agrupacion);
    // Combinamos los parámetros con las cabeceras de autorización
    const options = {
      ...this.getHeaders(),
      params: params
    };
    // Recuerda que el Token JWT lo debe estar inyectando tu Interceptor
    return this.http.get<EstadisticaEmergencia[]>(this.apiUrl, options);
  }
}