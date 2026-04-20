import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { AuthService } from '../../core/services/auth/auth.service';
import { PersonalService } from '../../core/services/personal/personal.service';
import { PersonalTaller } from '../../core/models/personal.model';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.css']
})
export class HomeComponent implements OnInit {
  // Inyección de servicios necesarios
  private authService = inject(AuthService);
  private personalService = inject(PersonalService);
  private router = inject(Router);

  // Signals para reactividad en la UI
  // Se usan con () en el HTML: listaPersonal()
  listaPersonal = signal<PersonalTaller[]>([]);
  
  // Variables de estado simples
  // Se usan directo en el HTML: {{ tallerNombre }}
  tallerNombre: string = 'Taller';
  serviciosPendientes: number = 0;

  ngOnInit() {
    // 1. Cargar datos del perfil desde localStorage
    this.cargarDatosPerfil();
    
    // 2. Cargar lista de mecánicos desde el backend
    this.cargarPersonal();
  }

  private cargarDatosPerfil() {
    const userDataJson = localStorage.getItem('user_data');
    if (userDataJson) {
      try {
        const userData = JSON.parse(userDataJson);
        // Extraemos el nombre que guardamos en el login
        this.tallerNombre = userData.nombre || 'Taller';
      } catch (error) {
        console.error('Error al parsear user_data:', error);
      }
    }
  }

  cargarPersonal() {
    this.personalService.getPersonal().subscribe({
      next: (data) => {
        // Actualizamos el signal con la data que viene de Python
        this.listaPersonal.set(data);
      },
      error: (err) => {
        console.error('Error al obtener el personal:', err);
        // Si el token expiró o es inválido (401), cerramos sesión
        if (err.status === 401) {
          this.logout();
        }
      }
    });
  }

  logout() {
    // Limpieza de seguridad
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_data');
    
    // Redirección al login
    this.router.navigate(['/login']);
  }
}