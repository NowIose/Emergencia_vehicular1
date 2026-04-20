import { HttpClient, HttpHeaders } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { PersonalTaller } from '../../models/personal.model';

@Injectable({ providedIn: 'root' })
export class PersonalService {
  private http = inject(HttpClient);
  private apiUrl = 'http://localhost:8000/usuarios/personal';

  // Función para obtener el token del localStorage
  private getHeaders() {
    const token = localStorage.getItem('access_token');
    return new HttpHeaders().set('Authorization', `Bearer ${token}`);
  }

  getPersonal() {
    return this.http.get<PersonalTaller[]>(this.apiUrl, { headers: this.getHeaders() });
  }

  registrarPersonal(datos: PersonalTaller) {
    return this.http.post<PersonalTaller>(this.apiUrl, datos, { headers: this.getHeaders() });
  }

  eliminarPersonal(id: number) {
    return this.http.delete(`${this.apiUrl}/${id}`, { headers: this.getHeaders() });
  }
}