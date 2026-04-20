// src/app/core/services/media.service.ts
import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class MediaService {
  private http = inject(HttpClient);
  private apiUrl = `${environment.apiUrl}`; // Ajusta a tu URL de FastAPI

  uploadImage(file: File): Observable<{ url: string, public_id: string }> {
    const formData = new FormData();
    formData.append('file', file);
    // folder es opcional ya que el backend tiene un default, pero puedes enviarlo
    formData.append('folder', 'emergencia_vehicular/perfiles');

    return this.http.post<{ url: string, public_id: string }>(
      `${this.apiUrl}/usuarios/upload-image`, 
      formData
    );
  }
  deleteImage(publicId: string): Observable<any> {
  // En FastAPI, el delete suele ser un DELETE o un POST
    return this.http.post(`${this.apiUrl}/usuarios/delete-image`, { public_id: publicId });
  }
}