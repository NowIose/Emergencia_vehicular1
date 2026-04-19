import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink, Router } from '@angular/router';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { AuthService } from '../../../core/services/auth/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, RouterLink, ReactiveFormsModule], // Importamos ReactiveFormsModule
  templateUrl: './login.component.html',
  styleUrl: './login.component.css'
})
export class LoginComponent {
  private fb = inject(FormBuilder);
  private authService = inject(AuthService);
  private router = inject(Router);

  // Definimos el formulario con validaciones básicas
  loginForm = this.fb.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(6)]],
  });

  onSubmit() {
    if (this.loginForm.valid) {
      // Usamos 'any' o una interfaz para no pelear con tipos estrictos aquí
      const credentials = this.loginForm.value as any; 
      
      this.authService.login(credentials).subscribe({
        next: (response) => {
          // response ahora trae { access_token, token_type, user }
          console.log('Datos del usuario logueado:', response.user);
          this.router.navigate(['/home']);
        },
        error: (err) => {
          console.error('Error en login', err);
          // Mostramos el mensaje exacto que viene del backend
          const msg = err.error?.detail || 'Credenciales incorrectas';
          alert(msg);
        }
      });
    }
}
}