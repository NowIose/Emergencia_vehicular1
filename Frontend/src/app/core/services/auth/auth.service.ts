import { HttpClient } from '@angular/common/http';
import { inject, Injectable, signal } from '@angular/core';
import { tap } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private http = inject(HttpClient);
  private apiUrl = 'http://localhost:8000/usuarios';

  // Usamos un 'signal' para saber en todo momento si hay alguien logueado
  currentUser = signal<any>(null);

  registrarTaller(datos: any) {
    return this.http.post(`${this.apiUrl}/register-taller`, datos);
  }

  // NUEVA FUNCIÓN PARA TU LOGIN
  login(credentials: { email: string; password: string }) {
    return this.http.post<any>(`${this.apiUrl}/login`, credentials).pipe(
      tap((response) => {
        // Guardamos el token en el navegador para que no se borre al refrescar
        localStorage.setItem('access_token', response.access_token);
        this.currentUser.set(response.user); // Guardamos info del usuario
      })
    );
  }

  // Función para cerrar sesión
  logout() {
    localStorage.removeItem('access_token');
    this.currentUser.set(null);
  }

  // Verifica si el usuario tiene sesión activa
  isAuthenticated(): boolean {
    return !!localStorage.getItem('access_token');
  }
}