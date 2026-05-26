import { Component, inject, OnInit, signal, AfterViewInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { PersonalService } from '../../../core/services/personal/personal.service';
import { MediaService } from '../../../core/services/media.service';
import { EmergenciaWsService, EmergenciaNotificacion } from '../../../core/services/emergencia/emergencia-ws.service';
import { PersonalTaller } from '../../../core/models/personal.model';
import { environment } from 'src/environments/environment';
import * as L from 'leaflet';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './dashboard.component.html',
  styleUrls: ['../home.component.css']
})
export class DashboardComponent implements OnInit {
  private personalService = inject(PersonalService);
  private fb = inject(FormBuilder);
  private mediaService = inject(MediaService);
  private emergenciaWs = inject(EmergenciaWsService);
  private http = inject(HttpClient);

  userRole = signal<string>('');
  listaPersonal = signal<PersonalTaller[]>([]);
  listaTalleres = signal<any[]>([]);
  emergenciasPendientes = signal<EmergenciaNotificacion['data'][]>([]);
  
  mostrarModalDetalle = signal<boolean>(false);
  emergenciaSeleccionada = signal<any | null>(null);
  personalSeleccionadoId = signal<number | null>(null);
  distanciaCalculada = signal<string | null>(null);
  diagnosticoAnimado = signal<string>('');
  typingInProgress = signal<boolean>(false);

  // --- NUEVOS SEÑALES PARA TALLERES ---
  mostrarModalTaller = signal<boolean>(false);
  tallerSeleccionado = signal<any | null>(null);
  private mapTaller: L.Map | null = null;
  
  tallerLat: number = 0;
  tallerLon: number = 0;
  serviciosPendientes: number = 0;
  promedioCalificacion = signal<number>(0);
  totalVotos = signal<number>(0);
  listaReviews = signal<any[]>([]);
  mostrarModal = signal<boolean>(false);

  personalForm: FormGroup;
  fotoPreview = signal<string | null>(null);
  subiendoFoto = signal<boolean>(false);
  private typingInterval: any;

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
    this.cargarDatosPerfil();
    
    if (this.userRole() === 'admin_sistema') {
      this.cargarTalleres();
    } else {
      this.cargarPersonal();
      this.cargarEmergenciasPendientes();
      this.cargarStats();
      this.cargarReviews();

      this.emergenciaWs.emergencias$.subscribe((msg) => {
        if (msg.type === 'NEW_EMERGENCY') {
          this.emergenciasPendientes.update((emergencias) => [msg.data, ...emergencias]);
          this.serviciosPendientes = this.emergenciasPendientes().length;
        }
      });
    }
  }

  cargarTalleres() {
    this.http.get<any[]>(`${environment.apiUrl}/usuarios/lista-talleres`).subscribe({
      next: (data) => this.listaTalleres.set(data),
      error: (err) => console.error('Error al cargar talleres:', err)
    });
  }

  abrirDetalleTaller(taller: any) {
    this.tallerSeleccionado.set(taller);
    this.mostrarModalTaller.set(true);
    
    // Esperar a que el modal se renderice para inicializar el mapa
    setTimeout(() => {
      this.initMapaTaller(taller.latitud, taller.longitud, taller.nombre_taller);
    }, 100);
  }

  cerrarModalTaller() {
    this.mostrarModalTaller.set(false);
    this.tallerSeleccionado.set(null);
    if (this.mapTaller) {
      this.mapTaller.remove();
      this.mapTaller = null;
    }
  }

  private initMapaTaller(lat: number, lng: number, nombre: string) {
    if (this.mapTaller) {
      this.mapTaller.remove();
    }

    const defaultLat = lat || -17.7833;
    const defaultLng = lng || -63.1821;

    // Configuración de iconos de Leaflet (para que no salgan rotos)
    const customIcon = L.icon({
      iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
      iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
      shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
      iconSize: [25, 41],
      iconAnchor: [12, 41],
      popupAnchor: [1, -34],
      shadowSize: [41, 41]
    });

    this.mapTaller = L.map('mapa-taller').setView([defaultLat, defaultLng], 15);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors'
    }).addTo(this.mapTaller);

    L.marker([defaultLat, defaultLng], { icon: customIcon })
      .addTo(this.mapTaller)
      .bindPopup(`<b>${nombre}</b>`)
      .openPopup();
  }

  cargarReviews() {
    const token = localStorage.getItem('access_token');
    const headers = new HttpHeaders({ Authorization: `Bearer ${token}` });
    this.http.get<any[]>(`${environment.apiUrl}/usuarios/taller/reviews`, { headers }).subscribe({
      next: (data) => this.listaReviews.set(data),
      error: (err) => console.error('Error al cargar reseñas:', err)
    });
  }

  cargarStats() {
    const token = localStorage.getItem('access_token');
    const headers = new HttpHeaders({ Authorization: `Bearer ${token}` });
    this.http.get<any>(`${environment.apiUrl}/usuarios/taller/stats`, { headers }).subscribe({
      next: (data) => {
        this.promedioCalificacion.set(data.promedio);
        this.totalVotos.set(data.total);
      },
      error: (err) => console.error('Error al cargar stats:', err)
    });
  }

  cargarEmergenciasPendientes() {
    this.http.get<any[]>(`${environment.apiUrl}/emergencias/espera`).subscribe({
      next: (data) => {
        // Mapear los datos del backend al formato que espera el frontend (data del WS)
        const mapeadas = data.map(e => ({
          nro: e.nro,
          ubicacion_real: e.ubicacion_real,
          descripcion: e.descripcion,
          fotos: e.fotos,
          vehiculo: e.vehiculo ? `${e.vehiculo.marca} ${e.vehiculo.modelo} (${e.vehiculo.placa})` : 'Vehículo desconocido',
          diagnostico_ia: e.diagnostico_ia,
          prioridad: e.prioridad
        }));
        this.emergenciasPendientes.set(mapeadas);
        this.serviciosPendientes = mapeadas.length;
      },
      error: (err) => console.error('Error al cargar emergencias en espera:', err)
    });
  }

  private cargarDatosPerfil() {
    const userDataJson = localStorage.getItem('user_data');
    if (userDataJson) {
      try {
        const userData = JSON.parse(userDataJson);
        this.userRole.set(userData.rol || '');
        this.tallerLat = userData.latitud || -17.7833;
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
      const reader = new FileReader();
      reader.onload = () => this.fotoPreview.set(reader.result as string);
      reader.readAsDataURL(file);

      this.mediaService.uploadImage(file).subscribe({
        next: (response) => {
          this.personalForm.patchValue({ foto_perfil: response.url });
          this.subiendoFoto.set(false);
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
      next: (data) => this.listaPersonal.set(data),
      error: (err) => console.error('Error al obtener el personal:', err),
    });
  }

  guardarPersonal() {
    if (this.personalForm.valid) {
      this.personalService.registrarPersonal(this.personalForm.value).subscribe({
        next: () => {
          this.cargarPersonal();
          this.cerrarModal();
        },
        error: (err) => alert(err.error.detail || 'Error al registrar al empleado'),
      });
    }
  }

  abrirModal() { this.mostrarModal.set(true); }
  cerrarModal() {
    this.mostrarModal.set(false);
    this.personalForm.reset({ cargo: 'Mecánico' });
    this.fotoPreview.set(null);
  }

  abrirDetalleEmergencia(emergencia: any) {
    this.emergenciaSeleccionada.set(emergencia);
    this.personalSeleccionadoId.set(null);

    // Iniciar efecto typewriter si hay diagnóstico
    if (emergencia.diagnostico_ia) {
      this.iniciarTypewriter(emergencia.diagnostico_ia);
    } else {
      this.diagnosticoAnimado.set('');
      this.typingInProgress.set(false);
    }

    if (emergencia.ubicacion_real && emergencia.ubicacion_real.includes(',')) {
      const coordenadas = emergencia.ubicacion_real.split(',');
      const lat = parseFloat(coordenadas[0].trim());
      const lon = parseFloat(coordenadas[1].trim());
      emergencia.latMap = lat;
      emergencia.lonMap = lon;
      const dist = this.calcularDistancia(this.tallerLat, this.tallerLon, lat, lon);
      this.distanciaCalculada.set(dist.toFixed(2) + ' km');
    } else {
      this.distanciaCalculada.set('Ubicación no disponible');
    }
    this.mostrarModalDetalle.set(true);
  }

  cerrarDetalleEmergencia() {
    if (this.typingInterval) clearInterval(this.typingInterval);
    this.diagnosticoAnimado.set('');
    this.typingInProgress.set(false);
    this.mostrarModalDetalle.set(false);
    this.emergenciaSeleccionada.set(null);
    this.personalSeleccionadoId.set(null);
  }

  iniciarTypewriter(text: string) {
    if (this.typingInterval) clearInterval(this.typingInterval);
    this.diagnosticoAnimado.set('');
    this.typingInProgress.set(true);
    let index = 0;
    this.typingInterval = setInterval(() => {
      if (index < text.length) {
        this.diagnosticoAnimado.update(current => current + text[index]);
        index++;
      } else {
        clearInterval(this.typingInterval);
        this.typingInProgress.set(false);
      }
    }, 15); // Velocidad de escritura
  }

  seleccionarPersonal(event: any) {
    this.personalSeleccionadoId.set(Number(event.target.value));
  }

  aceptarEmergencia() {
    const emergencia = this.emergenciaSeleccionada();
    const idPersonal = this.personalSeleccionadoId();
    if (!emergencia || !idPersonal) return;

    const token = localStorage.getItem('access_token');
    const headers = new HttpHeaders({ Authorization: `Bearer ${token}` });

    this.http.post(`${environment.apiUrl}/emergencias/${emergencia.nro}/aceptar`, 
      { id_personal: idPersonal }, { headers }).subscribe({
        next: () => {
          alert('¡Emergencia Aceptada y Asignada!');
          this.emergenciasPendientes.update((emergencias) =>
            emergencias.filter((e) => e.nro !== emergencia.nro));
          this.serviciosPendientes = this.emergenciasPendientes().length;
          this.cerrarDetalleEmergencia();
        },
        error: () => alert('Error al aceptar la emergencia'),
      });
  }

  private calcularDistancia(lat1: number, lon1: number, lat2: number, lon2: number): number {
    const R = 6371;
    const dLat = this.deg2rad(lat2 - lat1);
    const dLon = this.deg2rad(lon2 - lon1);
    const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos(this.deg2rad(lat1)) * Math.cos(this.deg2rad(lat2)) *
      Math.sin(dLon / 2) * Math.sin(dLon / 2);
    return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  }

  private deg2rad(deg: number): number { return deg * (Math.PI / 180); }
  verFotoGrande(url: string) { if (url) window.open(url, '_blank'); }
}
