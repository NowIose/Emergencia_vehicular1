import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { AuthService } from '../../core/services/auth/auth.service';
import { PersonalService } from '../../core/services/personal/personal.service';
import { PersonalTaller } from '../../core/models/personal.model';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { MediaService } from '../../core/services/media.service';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [CommonModule,ReactiveFormsModule],
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.css']
})
export class HomeComponent implements OnInit {
  // Inyección de servicios necesarios
  private authService = inject(AuthService);
  private personalService = inject(PersonalService);
  private router = inject(Router);  
  private fb = inject(FormBuilder);
  private mediaService = inject(MediaService);
  // Signals para reactividad en la UI
  // Se usan con () en el HTML: listaPersonal()
  listaPersonal = signal<PersonalTaller[]>([]);
  
  // Variables de estado simples
  // Se usan directo en el HTML: {{ tallerNombre }}
  tallerNombre: string = 'Taller';
  serviciosPendientes: number = 0;
  mostrarModal = signal<boolean>(false);

  // Formulario
  personalForm: FormGroup;
 //para la vista previa de la foto de perfil en el formulario de registro de personal
  fotoPreview = signal<string | null>(null);
  subiendoFoto = signal<boolean>(false);
  constructor() {
    this.personalForm = this.fb.group({
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.required, Validators.minLength(6)]],
      nombre_completo: ['', Validators.required],
      cargo: ['Mecánico', Validators.required],
      especialidad: [''],
      foto_perfil: ['']
    });
  }
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
  onFileSelected(event: any) {
    const file: File = event.target.files[0];
    if (file) {
      this.subiendoFoto.set(true);
      
      // 1. Mostramos previsualización local inmediata
      const reader = new FileReader();
      reader.onload = () => this.fotoPreview.set(reader.result as string);
      reader.readAsDataURL(file);

      // 2. Subimos a Cloudinary a través de tu MediaService
      this.mediaService.uploadImage(file).subscribe({
        next: (response) => {
          // Guardamos la URL final en el formulario
          this.personalForm.patchValue({ foto_perfil: response.url });
          this.subiendoFoto.set(false);
          console.log('Foto subida a Cloudinary:', response.url);
        },
        error: (err) => {
          console.error('Error al subir imagen:', err);
          this.subiendoFoto.set(false);
          alert('No se pudo subir la imagen, intenta de nuevo.');
        }
      });
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
  guardarPersonal() {
    if (this.personalForm.valid) {
      this.personalService.registrarPersonal(this.personalForm.value).subscribe({
        next: () => {
          this.cargarPersonal(); // Refresca la lista de las tarjetas
          this.cerrarModal();    // Cierra el modal y limpia el form
        },
        error: (err) => {
          alert(err.error.detail || 'Error al registrar al empleado');
        }
      });
    }
  }

  abrirModal() { this.mostrarModal.set(true); }
  cerrarModal() { 
    this.mostrarModal.set(false); 
    this.personalForm.reset({ cargo: 'Mecánico' }); 
    this.fotoPreview.set(null);
  }

  logout() {
    // Limpieza de seguridad
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_data');
    
    // Redirección al login
    this.router.navigate(['/login']);
  }
}