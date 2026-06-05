import { Component, signal, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { EmergenciaService } from '../../core/services/emergencia/emergencia.service';

// 1. Actualiza la interfaz para usar 'nro' como número
export interface Emergencia {
  nro: number;
  vehiculo: any; // <-- Cambiado de string a any para soportar objeto o texto
  cliente: string;
  descripcion: string;
  ubicacion_real: string;
  estado: 'espera' | 'atendiendo' | 'terminado' | 'cancelado';
  mecanico_asignado?: string;
  fecha_creacion: Date;
  diagnostico_ia?: string;
  fotos?: string[];
}

@Component({
  selector: 'app-emergencias',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './emergencia.component.html',
})
export class EmergenciasTallerComponent implements OnInit {
  private emergenciaService = inject(EmergenciaService);
  private http = inject(HttpClient); // Necesario para stats o distancias

  userRole = signal<string>('');
  emergencias = signal<Emergencia[]>([]);

  // --- Lógica de Detalles (Igual que en Dashboard) ---
  mostrarModalDetalle = signal<boolean>(false);
  emergenciaSeleccionada = signal<any | null>(null);
  diagnosticoAnimado = signal<string>('');
  typingInProgress = signal<boolean>(false);
  distanciaCalculada = signal<string>('');
  private typingInterval: any;

  tallerLat: number = 0;
  tallerLon: number = 0;

  abrirDetalle(eme: any) {
    // Asegurar que el objeto tenga el formato que el modal espera (vehiculo como string)
    const vehiculoStr = eme.vehiculo?.marca 
      ? `${eme.vehiculo.marca} ${eme.vehiculo.modelo} (${eme.vehiculo.placa})` 
      : (typeof eme.vehiculo === 'string' ? eme.vehiculo : 'Vehículo desconocido');

    const data = {
      ...eme,
      vehiculo: vehiculoStr,
    };
    
    this.emergenciaSeleccionada.set(data);

    if (data.diagnostico_ia) {
      this.iniciarTypewriter(data.diagnostico_ia);
    }

    if (data.ubicacion_real && data.ubicacion_real.includes(',')) {
      const coordenadas = data.ubicacion_real.split(',');
      const lat = parseFloat(coordenadas[0].trim());
      const lon = parseFloat(coordenadas[1].trim());
      const dist = this.calcularDistancia(this.tallerLat, this.tallerLon, lat, lon);
      this.distanciaCalculada.set(dist.toFixed(2) + ' km');
    }

    this.mostrarModalDetalle.set(true);
  }

  cerrarDetalle() {
    if (this.typingInterval) clearInterval(this.typingInterval);
    this.mostrarModalDetalle.set(false);
    this.emergenciaSeleccionada.set(null);
  }

  iniciarTypewriter(text: string) {
    if (this.typingInterval) clearInterval(this.typingInterval);
    this.diagnosticoAnimado.set('');
    this.typingInProgress.set(true);
    let index = 0;
    this.typingInterval = setInterval(() => {
      if (index < text.length) {
        this.diagnosticoAnimado.update((current) => current + text[index]);
        index++;
      } else {
        clearInterval(this.typingInterval);
        this.typingInProgress.set(false);
      }
    }, 15);
  }

  private calcularDistancia(lat1: number, lon1: number, lat2: number, lon2: number): number {
    const R = 6371;
    const dLat = (lat2 - lat1) * (Math.PI / 180);
    const dLon = (lon2 - lon1) * (Math.PI / 180);
    const a =
      Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos(lat1 * (Math.PI / 180)) *
        Math.cos(lat2 * (Math.PI / 180)) *
        Math.sin(dLon / 2) *
        Math.sin(dLon / 2);
    return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  }

  // ... (rest of the component)
  // Definimos las reglas de oro: ¿A qué estados puedo saltar desde el actual?
  estadosDisponibles = [
    { valor: 'espera', texto: 'En Espera' },
    { valor: 'atendiendo', texto: 'Atendiendo' },
    { valor: 'terminado', texto: 'Terminado' },
    { valor: 'cancelado', texto: 'Cancelado' },
  ];

  private readonly REGLAS_ESTADO: Record<string, string[]> = {
    espera: ['atendiendo', 'cancelado'],
    atendiendo: ['terminado'],
    terminado: [], // No se mueve más
    cancelado: [], // No se mueve más
  };
  ngOnInit() {
    this.cargarDatosPerfil();
    if (this.userRole() !== 'admin_sistema') {
      this.cargarEmergencias();
    }
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

  cambiarEstado(nro: number, nuevoEstado: any) {
    const emergenciaActual = this.emergencias().find((e) => e.nro === nro);
    if (!emergenciaActual) return;

    const estadoAnterior = emergenciaActual.estado;
    const transicionesValidas = this.REGLAS_ESTADO[estadoAnterior];

    if (!transicionesValidas.includes(nuevoEstado)) {
      alert(`Movimiento no permitido de ${estadoAnterior} a ${nuevoEstado}.`);
      return;
    }

    // Asegúrate de convertir nro a string en la llamada al servicio si tu servicio lo pide como string,
    // o cambia el servicio para que acepte number. FastAPI lo leerá bien de ambas formas en la URL.
    this.emergenciaService.actualizarEstado(nro.toString(), nuevoEstado).subscribe({
      next: (res) => {
        this.emergencias.update((emps) =>
          emps.map((emp) => (emp.nro === nro ? { ...emp, estado: nuevoEstado } : emp)),
        );
        console.log('Estado actualizado en la BD');
      },
      error: (err) => {
        alert('Error al guardar: ' + (err.error?.detail || err.message));
      },
    });
  }
  // --- Helpers para el HTML ---

  // Para bloquear el select si el estado es final (terminado/cancelado)
  estaBloqueado(estado: string): boolean {
    return estado === 'terminado' || estado === 'cancelado';
  }

  cargarEmergencias() {
    this.emergenciaService.getMisEmergencias().subscribe({
      next: (data) => {
        // Mapeamos los datos por si el backend trae 'id' en lugar de 'nro'
        // o para asegurar el formato de fecha
        const formateadas = data.map((e) => ({
          ...e,
          nro: e.nro || e.id, // Ajuste por si el backend manda 'id'
          fecha_creacion: new Date(e.fecha_creacion),
        }));

        this.emergencias.set(formateadas); // 5. Actualiza el signal con datos reales
      },
      error: (err) => {
        console.error('Error cargando emergencias:', err);
      },
    });
  }

  // Para ocultar opciones inválidas en el dropdown y no confundir al usuario
  esOpcionValida(estadoActual: string, opcionDestino: string): boolean {
    if (estadoActual === opcionDestino) return true; // Siempre mostrar el actual
    return this.REGLAS_ESTADO[estadoActual]?.includes(opcionDestino) || false;
  }

  // (Tus funciones de clases e iconos se mantienen igual...
  obtenerClasesEstado(estado: string): string {
    switch (estado) {
      case 'espera':
        return 'bg-amber-100 text-amber-700 border-amber-200';
      case 'atendiendo':
        return 'bg-blue-100 text-blue-700 border-blue-200';
      case 'terminado':
        return 'bg-green-100 text-green-700 border-green-200';
      case 'cancelado':
        return 'bg-red-100 text-red-700 border-red-200';
      default:
        return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  }

  obtenerIconoEstado(estado: string): string {
    switch (estado) {
      case 'espera':
        return 'schedule';
      case 'atendiendo':
        return 'build';
      case 'terminado':
        return 'check_circle';
      case 'cancelado':
        return 'cancel';
      default:
        return 'info';
    }
  }
}
