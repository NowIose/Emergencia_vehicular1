import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { AuthService } from '../../core/services/auth/auth.service';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.css']
})
export class HomeComponent implements OnInit {
  private authService = inject(AuthService);
  private router = inject(Router);

  // Datos de prueba (luego vendrán de tu API de Python)
  tallerNombre = 'Taller Central'; 
  serviciosPendientes = 5;

  ngOnInit() {
    console.log('Panel de control cargado');
  }

  logout() {
    this.authService.logout();
    this.router.navigate(['/login']);
  }
}