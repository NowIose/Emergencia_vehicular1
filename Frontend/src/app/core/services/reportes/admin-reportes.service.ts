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
  // <--- NUEVA FUNCIÓN PARA EL AUDIO --->
  enviarAudioFiltro(formData: FormData) {
    // Cambia 'access_token' por el nombre correcto si es diferente
    const token = localStorage.getItem('access_token') || '';
    const headers = new HttpHeaders().set('Authorization', `Bearer ${token}`);

    return this.http.post<any>(`${this.apiUrl}/filtro-voz`, formData, { headers });
  }
  getKPIsDashboard(tenantId?: number) {
    // Extraemos el token correcto de tu localStorage
    const token = localStorage.getItem('access_token');
    const headers = new HttpHeaders().set('Authorization', `Bearer ${token}`);

    let params = new HttpParams();
    // Si viene el id del taller (tenant), lo seteamos limpiamente en los parámetros
    if (tenantId) {
      params = params.set('tenant_id', tenantId.toString());
    }

    // Enviamos la petición GET con la llave de acceso (headers) y los parámetros correspondientes
    return this.http.get<any>(`${this.apiUrl}/kpis-dashboard`, { headers, params });
  }
}
