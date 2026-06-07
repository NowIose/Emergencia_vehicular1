import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
// Ajusta esta ruta a donde tengas tu environment configurado
import { environment } from '../../../environments/environment';

export interface Backup {
  id: number;
  nombre: string;
  url: string;
  key_r2: string;
  tamano: number;
  fecha_creacion: string;
  filename: string;
}

@Injectable({
  providedIn: 'root',
})
export class BackupsService {
  private http = inject(HttpClient);
  private apiUrl = `${environment.apiUrl}/backups`; // Reemplaza por tu URL base si no usas environment

  listarBackups(): Observable<{ backups: Backup[] }> {
    return this.http.get<{ backups: Backup[] }>(`${this.apiUrl}/`);
  }

  crearBackup(): Observable<{ mensaje: string; archivo: string }> {
    return this.http.post<{ mensaje: string; archivo: string }>(`${this.apiUrl}/crear`, {});
  }

  restaurarBackup(filename: string): Observable<{ mensaje: string }> {
    return this.http.post<{ mensaje: string }>(`${this.apiUrl}/restaurar/${filename}`, {});
  }
}
