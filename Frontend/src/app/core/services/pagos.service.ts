import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { environment } from 'src/environments/environment';

@Injectable({ providedIn: 'root' })
export class PagosService {
  private http = inject(HttpClient);
  private apiUrl = `${environment.apiUrl}/pagos`;

  private getHeaders() {
    const token = localStorage.getItem('access_token');
    return new HttpHeaders({ Authorization: `Bearer ${token}` });
  }

  crearCheckoutSession(planCodigo: string) {
    return this.http.post<{ checkout_url: string }>(
      `${this.apiUrl}/checkout-session`,
      { plan_codigo: planCodigo },
      { headers: this.getHeaders() }
    );
  }

  obtenerMiSuscripcion() {
    return this.http.get<any>(`${this.apiUrl}/mi-suscripcion`, { headers: this.getHeaders() });
  }

  abrirPortalFacturacion() {
    return this.http.post<{ portal_url: string }>(
      `${this.apiUrl}/portal-session`,
      {},
      { headers: this.getHeaders() }
    );
  }

  obtenerStatsAdmin() {
    return this.http.get<any[]>(`${this.apiUrl}/admin/stats`, { headers: this.getHeaders() });
  }
  
  fijarPrecioEmergencia(nro_emergencia: number, monto: number, moneda: string = 'usd') {
    return this.http.post<any>(
      `${this.apiUrl}/emergencia/set-precio`,
      { nro_emergencia, monto, moneda },
      { headers: this.getHeaders() }
    );
  }

  obtenerHistorialServicios() {
    return this.http.get<any[]>(
      `${this.apiUrl}/emergencia/taller/historial`,
      { headers: this.getHeaders() }
    );
  }
}
