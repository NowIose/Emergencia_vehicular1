import { Component, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { AuthService } from '../../../core/services/auth/auth.service';
import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [ReactiveFormsModule, CommonModule], // Asegúrate de importar esto
  templateUrl: './register.component.html',
})
export class RegisterComponent {
  private fb = inject(FormBuilder);
  private authService = inject(AuthService);
  private router = inject(Router);

  // Definimos el formulario con los nombres que pusimos en el HTML
  registerForm = this.fb.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(8)]],
    telefono: ['', Validators.required],
    nombre_taller: ['', Validators.required],
    nit: ['', Validators.required],
    ciudad: ['', Validators.required],
    direccion: ['', Validators.required],
    // AGREGAMOS ESTOS PARA EVITAR ERRORES DE VALIDACIÓN EN EL BACK
    latitud: [0], 
    longitud: [0],
    foto_perfil: [''] 
  });

  onSubmit() {
    if (this.registerForm.valid) {
      // 1. Preparamos los datos (incluyendo los campos ocultos que el backend pide)
      const datosRegistro = {
        ...this.registerForm.value,
        latitud: 0,        // Valores por defecto para que no falle el backend
        longitud: 0,
        foto_perfil: 'default.png'
      };

      console.log('Enviando datos al servidor...', datosRegistro);

      // 2. Llamamos al servicio de registro
      this.authService.registrarTaller(datosRegistro).subscribe({
        next: (res) => {
          // 3. Si todo sale bien, notificamos y redirigimos
          alert('¡Registro exitoso! Ahora ingresa con tus credenciales.');
          this.router.navigate(['/login']); // <--- Redirección manual al login
        },
        error: (err) => {
          console.error('Error en el registro:', err);
          // Mostramos el error que viene de FastAPI (ej: "El email ya existe")
          const mensajeError = err.error?.detail || 'No se pudo completar el registro';
          alert('Error: ' + mensajeError);
        }
      });
    } else {
      alert('Por favor, completa todos los campos obligatorios.');
    }
  }
}
