import { Component, inject ,ChangeDetectorRef ,OnDestroy, HostListener } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { AuthService } from '../../../core/services/auth/auth.service';
import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { MediaService } from '../../../core/services/media.service';


@Component({
  selector: 'app-register',
  standalone: true,
  imports: [ReactiveFormsModule, CommonModule], // Asegúrate de importar esto
  templateUrl: './register.component.html',
})
export class RegisterComponent implements OnDestroy {
  private fb = inject(FormBuilder);
  private authService = inject(AuthService);
  private router = inject(Router);
  private cdr = inject(ChangeDetectorRef);
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
  registroCompletado: boolean = false; // Para verificar si el registro se completó 
  onSubmit() {
  if (this.registerForm.valid) {
    // 1. Obtenemos los valores actuales del formulario
    const formValues = this.registerForm.value;

    // 2. Preparamos el objeto para el backend
    const datosRegistro = {
      ...formValues,
      // Si foto_perfil está vacío (no subió nada), usamos el default
      foto_perfil: formValues.foto_perfil || 'default.png',
      latitud: formValues.latitud || 0,
      longitud: formValues.longitud || 0
    };

    console.log('Enviando datos al servidor...', datosRegistro);

    this.authService.registrarTaller(datosRegistro).subscribe({
      next: (res) => {
        this.registroCompletado = true; // <--- Marcamos como completado
        alert('¡Registro exitoso! Ahora ingresa con tus credenciales.');
        this.router.navigate(['/login']);
      },
      error: (err) => {
        const mensajeError = err.error?.detail || 'No se pudo completar el registro';
        alert('Error: ' + mensajeError);
        console.error('ERROR DETALLADO:', err);
        // Esto te mostrará en el alert qué campo está fallando
        const detail = err.error?.detail;
        const msg = typeof detail === 'string' ? detail : JSON.stringify(detail);
        alert('Error 400: ' + msg);
      }
    });
    } else {
      alert('Por favor, completa todos los campos obligatorios.');
    }
  }

  fotoPrevisualizacion: string = ''; // Para mostrar la imagen subida en el formulario
  currentPublicId: string = ''; // Guardamos el public_id para poder eliminar la imagen si el usuario sube otra o cancela el registro

  //para manejar cloudinary
  private mediaService = inject(MediaService);
  // Función para manejar la subida
  onFileSelected(event: any) {
    const file: File = event.target.files[0];
    if (!file) return;

    // 1. Limpieza: Si ya había subido una foto antes y la está cambiando, 
    // borramos la vieja de Cloudinary para no dejar basura.
    if (this.currentPublicId) {
      this.mediaService.deleteImage(this.currentPublicId).subscribe({
        next: () => console.log('Imagen anterior borrada de la nube'),
        error: (e) => console.error('No se pudo borrar la imagen anterior', e)
      });
    }

    console.log('Subiendo nueva imagen...');
    this.mediaService.uploadImage(file).subscribe({
      next: (res) => {
        console.log('Imagen subida con éxito:', res.url);
        
        this.fotoPrevisualizacion = res.url;
        this.currentPublicId = res.public_id; // Guardamos el nuevo ID
        
        this.registerForm.patchValue({
          foto_perfil: res.url
        });

        // 2. Solución al error NG0100: Forzamos a Angular a detectar el cambio
        this.cdr.detectChanges();
      },
      error: (err) => {
        console.error('Error al subir imagen', err);
        alert('No se pudo subir la imagen.');
      }
    });
  }
  ngOnDestroy() {
    this.ejecutarLimpiezaHuerfana();
  }

  // Caso B: Si el usuario cierra la pestaña o recarga
  @HostListener('window:beforeunload', ['$event'])
  unloadHandler(event: Event) {
    this.ejecutarLimpiezaHuerfana();
  }

  // Función auxiliar para no repetir código
  private ejecutarLimpiezaHuerfana() {
    // Solo borramos si hay una imagen en la nube Y el registro NO se completó con éxito
    if (this.currentPublicId && !this.registroCompletado) {
      console.log('Limpiando imagen no utilizada en Cloudinary...');
      this.mediaService.deleteImage(this.currentPublicId).subscribe();
    }
  }
}
