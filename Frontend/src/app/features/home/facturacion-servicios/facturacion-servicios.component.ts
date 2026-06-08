import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { PagosService } from '../../../core/services/pagos.service';

@Component({
  selector: 'app-facturacion-servicios',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="p-4 md:p-8 max-w-7xl mx-auto font-manrope">
      <div class="mb-8">
        <h2 class="text-2xl font-black text-slate-800 flex items-center gap-3">
          <span class="material-symbols-outlined text-green-500 text-3xl">receipt_long</span>
          Facturación de Servicios
        </h2>
        <p class="text-slate-500 font-medium">Historial de pagos de emergencias realizadas a clientes.</p>
      </div>

      <div class="bg-white rounded-[2rem] border border-slate-100 shadow-sm overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full text-left border-collapse">
            <thead>
              <tr class="bg-slate-50/50 text-[10px] uppercase tracking-widest text-slate-400 font-black">
                <th class="p-4 pl-6">Nro Auxilio</th>
                <th class="p-4">Cliente / Vehículo</th>
                <th class="p-4">Monto</th>
                <th class="p-4">Estado Pago</th>
                <th class="p-4">Fecha Pago</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100 text-sm">
              <tr *ngFor="let p of historial()" class="hover:bg-slate-50/50 transition-colors group">
                <td class="p-4 pl-6 font-bold text-slate-800">#{{ p.nro_emergencia }}</td>
                <td class="p-4">
                  <p class="font-bold text-slate-700">{{ p.cliente }}</p>
                  <p class="text-xs text-slate-400">{{ p.vehiculo }}</p>
                </td>
                <td class="p-4 font-black text-slate-800">
                  {{ p.moneda | uppercase }} $ {{ p.monto_centavos / 100 | number:'1.2-2' }}
                </td>
                <td class="p-4">
                  <span class="px-3 py-1 rounded-xl text-[10px] font-black uppercase tracking-wider border flex items-center inline-flex gap-1"
                        [ngClass]="p.pagado ? 'bg-green-50 text-green-600 border-green-200' : 'bg-amber-50 text-amber-600 border-amber-200'">
                    <span class="material-symbols-outlined text-[14px]">{{ p.pagado ? 'check_circle' : 'pending' }}</span>
                    {{ p.pagado ? 'Pagado' : 'Pendiente' }}
                  </span>
                </td>
                <td class="p-4 text-slate-500 font-medium">
                  {{ p.fecha_pago ? (p.fecha_pago | date:'short') : '--/--/----' }}
                </td>
              </tr>
              <tr *ngIf="historial().length === 0">
                <td colspan="5" class="p-10 text-center text-slate-400">No hay servicios registrados aún.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  `
})
export class FacturacionServiciosComponent implements OnInit {
  private pagosService = inject(PagosService);
  historial = signal<any[]>([]);

  ngOnInit() {
    this.pagosService.obtenerHistorialServicios().subscribe({
      next: (data) => this.historial.set(data),
      error: (err) => console.error('Error cargando historial', err)
    });
  }
}