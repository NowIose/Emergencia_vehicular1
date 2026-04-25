import { Component, signal, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { EmergenciaService } from '../../core/services/emergencia/emergencia.service';

// 1. Actualiza la interfaz para usar 'nro' como número
export interface Emergencia {
  nro: number; // <-- Cambiado de id: string a nro: number
  vehiculo: string;
  cliente: string;
  descripcion: string;
  ubicacion_real: string;
  estado: 'espera' | 'atendiendo' | 'terminado' | 'cancelado';
  mecanico_asignado?: string;
  fecha_creacion: Date; // <-- Ajustado para que coincida con el backend
}

@Component({
  selector: 'app-emergencias',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './emergencia.component.html',
})
export class EmergenciasTallerComponent implements OnInit {
  private emergenciaService = inject(EmergenciaService);
  // Usando signals (puedes adaptarlo a variables normales si usas versiones anteriores)
  // 3. Puedes dejarlo vacío al inicio o con los datos de prueba
  emergencias = signal<Emergencia[]>([]);
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
    this.cargarEmergencias(); // 4. Llama a la carga al iniciar
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
