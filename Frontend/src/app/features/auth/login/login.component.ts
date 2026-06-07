import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink, Router } from '@angular/router';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { AuthService } from '../../../core/services/auth/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, RouterLink, ReactiveFormsModule],
  templateUrl: './login.component.html',
  styleUrl: './login.component.css'
})
export class LoginComponent {
  private fb = inject(FormBuilder);
  private authService = inject(AuthService);
  private router = inject(Router);

  loginForm = this.fb.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(6)]],
  });

  onSubmit() {
    if (this.loginForm.valid) {
      const credentials = this.loginForm.value as any; 
      
      this.authService.login(credentials).subscribe({
        next: (res) => {
          console.log('Login exitoso:', res);
          
          // Guardamos token y datos del usuario
          localStorage.setItem('access_token', res.access_token);
          localStorage.setItem('user_data', JSON.stringify(res.user));

          // Verificamos si es un taller que aún no ha pagado
          if (res.requiere_pago) {
            alert('Cuenta registrada. Redirigiendo a facturación para activar tu suscripción...');
            this.router.navigate(['/home/facturacion']);
            return;
          }

          // Redirigimos según rol
          if (res.user.rol === 'admin_sistema') {
            this.router.navigate(['/home/reportes-admin']);
          } else {
            this.router.navigate(['/home']);
          }
        },
        error: (err) => {
          console.error('Error en login', err);
          const msg = err.error?.detail || 'Email o contraseña incorrectos';
          alert(msg);
        }
      });
    }
  }
}
