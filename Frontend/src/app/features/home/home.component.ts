import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { AuthService } from '../../core/services/auth/auth.service';
import { PersonalService } from '../../core/services/personal/personal.service';
import { PersonalTaller } from '../../core/models/personal.model';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { MediaService } from '../../core/services/media.service';
import {
  EmergenciaWsService,
  EmergenciaNotificacion,
} from '../../core/services/emergencia-ws.service';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { environment } from 'src/environments/environment';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.css'],
})
export class HomeComponent implements OnInit {
  // Inyección de servicios necesarios
  private authService = inject(AuthService);
  private personalService = inject(PersonalService);
  private router = inject(Router);
  private fb = inject(FormBuilder);
  private mediaService = inject(MediaService);
  private emergenciaWs = inject(EmergenciaWsService);
  private http = inject(HttpClient);
  // Signals para reactividad en la UI
  // Se usan con () en el HTML: listaPersonal()
  listaPersonal = signal<PersonalTaller[]>([]);
  emergenciasPendientes = signal<EmergenciaNotificacion['data'][]>([]);
  // --- NUEVOS SIGNALS PARA EL DETALLE DE EMERGENCIA ---
  mostrarModalDetalle = signal<boolean>(false);
  emergenciaSeleccionada = signal<any | null>(null); // Reemplaza 'any' por tu interfaz si la tienes
  personalSeleccionadoId = signal<number | null>(null);
  distanciaCalculada = signal<string | null>(null);
  // Variables de estado simples
  // Se usan directo en el HTML: {{ tallerNombre }}
  tallerNombre: string = 'Taller';
  tallerLat: number = 0; // Coordenadas de tu taller
  tallerLon: number = 0;
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
      foto_perfil: [''],
    });
  }
  ngOnInit() {
    // 1. Cargar datos del perfil desde localStorage
    this.cargarDatosPerfil();

    // 2. Cargar lista de mecánicos desde el backend
    this.cargarPersonal();

    // 3. Conectar a WebSockets de emergencias
    this.emergenciaWs.conectar();
    this.emergenciaWs.emergencias$.subscribe((msg) => {
      if (msg.type === 'NEW_EMERGENCY') {
        this.emergenciasPendientes.update((emergencias) => [msg.data, ...emergencias]);
        this.serviciosPendientes = this.emergenciasPendientes().length;
      }
    });
  }

  private cargarDatosPerfil() {
    const userDataJson = localStorage.getItem('user_data');
    if (userDataJson) {
      try {
        const userData = JSON.parse(userDataJson);
        this.tallerNombre = userData.nombre || 'Taller';
        // Asignamos las coordenadas del taller si existen en tu JSON
        this.tallerLat = userData.latitud || -17.7833; // Ejemplo: Santa Cruz
        this.tallerLon = userData.longitud || -63.1821;
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
        },
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
      },
    });
  }
  guardarPersonal() {
    if (this.personalForm.valid) {
      this.personalService.registrarPersonal(this.personalForm.value).subscribe({
        next: () => {
          this.cargarPersonal(); // Refresca la lista de las tarjetas
          this.cerrarModal(); // Cierra el modal y limpia el form
        },
        error: (err) => {
          alert(err.error.detail || 'Error al registrar al empleado');
        },
      });
    }
  }

  abrirModal() {
    this.mostrarModal.set(true);
  }
  cerrarModal() {
    this.mostrarModal.set(false);
    this.personalForm.reset({ cargo: 'Mecánico' });
    this.fotoPreview.set(null);
  }

  logout() {
    // Limpieza de seguridad
    this.emergenciaWs.desconectar();
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_data');

    // Redirección al login
    this.router.navigate(['/login']);
  }
  abrirDetalleEmergencia(emergencia: any) {
    this.emergenciaSeleccionada.set(emergencia);
    this.personalSeleccionadoId.set(null); // Reiniciamos la selección del mecánico

    // Calculamos la distancia si la emergencia tiene lat y lon
    if (emergencia.latitud && emergencia.longitud) {
      const dist = this.calcularDistancia(
        this.tallerLat,
        this.tallerLon,
        emergencia.latitud,
        emergencia.longitud,
      );
      this.distanciaCalculada.set(dist.toFixed(2) + ' km');
    } else {
      this.distanciaCalculada.set('Ubicación no disponible');
    }

    this.mostrarModalDetalle.set(true);
  }

  cerrarDetalleEmergencia() {
    this.mostrarModalDetalle.set(false);
    this.emergenciaSeleccionada.set(null);
    this.personalSeleccionadoId.set(null);
  }

  seleccionarPersonal(event: any) {
    // Captura el ID del mecánico seleccionado en el <select> del HTML
    const id = Number(event.target.value);
    this.personalSeleccionadoId.set(id);
  }

  aceptarEmergencia() {
    const emergencia = this.emergenciaSeleccionada();
    const idPersonal = this.personalSeleccionadoId();

    if (!emergencia) return;

    if (!idPersonal) {
      alert('Por favor, selecciona un mecánico de la lista antes de aceptar.');
      return;
    }

    const token = localStorage.getItem('access_token');
    if (!token) {
      alert('Sesión expirada. Por favor, vuelve a iniciar sesión.');
      return;
    }

    const headers = new HttpHeaders({
      Authorization: `Bearer ${token}`,
    });

    this.http
      .post(
        `${environment.apiUrl}/emergencias/${emergencia.nro}/aceptar`, // <-- Ambas deben ser comillas invertidas
        { id_personal: idPersonal },
        { headers: headers },
      )
      .subscribe({
        next: () => {
          alert('¡Emergencia Aceptada y Asignada!');
          // Quitamos la emergencia de la lista de pendientes
          this.emergenciasPendientes.update((emergencias) =>
            emergencias.filter((e) => e.nro !== emergencia.nro),
          );
          this.serviciosPendientes = this.emergenciasPendientes().length;
          this.cerrarDetalleEmergencia(); // Cerramos el modal
        },
        error: (err) => {
          if (err.status === 401) {
            alert('Error 401: No tienes permiso o tu sesión expiró.');
          } else {
            alert('Error al aceptar la emergencia');
          }
          console.error(err);
        },
      });
  }

  // Función matemática para calcular distancia entre dos coordenadas (Fórmula de Haversine)
  private calcularDistancia(lat1: number, lon1: number, lat2: number, lon2: number): number {
    const R = 6371; // Radio de la Tierra en km
    const dLat = this.deg2rad(lat2 - lat1);
    const dLon = this.deg2rad(lon2 - lon1);
    const a =
      Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos(this.deg2rad(lat1)) *
        Math.cos(this.deg2rad(lat2)) *
        Math.sin(dLon / 2) *
        Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c; // Distancia en km
  }

  private deg2rad(deg: number): number {
    return deg * (Math.PI / 180);
  }
}
