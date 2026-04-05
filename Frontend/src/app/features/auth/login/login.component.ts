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
      const credentials = this.loginForm.value as { email: string; password: string };
      
      this.authService.login(credentials).subscribe({
        next: (response) => {
          console.log('Login exitoso', response);
          this.router.navigate(['/home']); // ¡Aquí es donde ocurre la redirección!
        },
        error: (err) => {
          console.error('Error en login', err);
          alert('Credenciales incorrectas o error en el servidor');
        }
      });
    } else {
      alert('Por favor, rellena los campos correctamente');
    }
  }
}