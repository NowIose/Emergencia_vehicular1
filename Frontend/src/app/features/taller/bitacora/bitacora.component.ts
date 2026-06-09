import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { BitacoraService, BitacoraEntry } from '../../../core/services/bitacora.service';

@Component({
  selector: 'app-bitacora',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="min-h-screen bg-slate-50 p-4 md:p-8 font-manrope">
      <div class="max-w-5xl mx-auto">
        <!-- Header -->
        <div class="mb-10 flex justify-between items-end">
          <div>
            <h1 class="text-4xl font-black text-slate-900 tracking-tight">Bitácora del Sistema</h1>
            <p class="text-slate-500 font-medium mt-1">Control de auditoría y eventos globales.</p>
          </div>
          <button (click)="cargarBitacora()" class="p-3 bg-white border border-slate-200 rounded-2xl hover:bg-slate-50 transition-all shadow-sm flex items-center gap-2 text-slate-600 font-bold text-sm">
            <span class="material-symbols-outlined text-lg" [class.animate-spin]="loading">refresh</span>
            Actualizar
          </button>
        </div>

        <!-- Panel de Filtros -->
        <div class="mb-8 flex flex-wrap gap-4 bg-white p-6 rounded-[2.5rem] shadow-sm border border-slate-100 items-end">
          <div class="flex-grow min-w-[280px]">
            <p class="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2 ml-4">Buscar (Usuario, Taller, Acción, Correo...)</p>
            <div class="relative">
              <span class="material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-slate-400">search</span>
              <input 
                type="text" 
                [(ngModel)]="searchTerm"
                placeholder="Ej: admin, taller_norte, inicio..." 
                class="w-full pl-12 pr-4 py-3 bg-slate-50 border-none rounded-2xl focus:ring-2 focus:ring-primary/20 transition-all font-bold text-slate-700 placeholder:text-slate-300"
              >
            </div>
          </div>
          <div class="w-full md:w-56">
            <p class="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2 ml-4">Filtrar por Fecha</p>
            <input 
              type="date" 
              [(ngModel)]="filterDate"
              class="w-full px-4 py-3 bg-slate-50 border-none rounded-2xl focus:ring-2 focus:ring-primary/20 transition-all font-bold text-slate-700"
            >
          </div>
          <button 
            *ngIf="searchTerm || filterDate" 
            (click)="limpiarFiltros()" 
            class="p-3 bg-red-50 text-red-500 rounded-2xl hover:bg-red-100 transition-all flex items-center justify-center shadow-sm"
            title="Limpiar filtros"
          >
            <span class="material-symbols-outlined">filter_alt_off</span>
          </button>
        </div>

        @if (loading && entries.length === 0) {
          <div class="flex flex-col items-center justify-center py-32">
            <div class="w-16 h-16 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
            <p class="mt-6 text-slate-400 font-bold animate-pulse">Sincronizando registros...</p>
          </div>
        } @else if (error) {
          <div class="bg-red-50 border-2 border-dashed border-red-200 rounded-[2rem] p-12 text-center">
            <span class="material-symbols-outlined text-red-400 text-6xl mb-4">report</span>
            <h2 class="text-xl font-black text-red-900">{{ error }}</h2>
            <button (click)="cargarBitacora()" class="mt-6 px-8 py-3 bg-red-600 text-white rounded-2xl font-black hover:bg-red-700 transition-all shadow-lg shadow-red-200">
              Reintentar Conexión
            </button>
          </div>
        } @else {
          <div class="relative">
            <div class="absolute left-4 md:left-1/2 top-0 bottom-0 w-1 bg-slate-200 -translate-x-1/2 rounded-full opacity-50 hidden md:block"></div>

            <div class="space-y-8">
              @for (entry of filteredEntries; track entry.id; let i = $index) {
                <div class="relative flex flex-col md:flex-row items-center group">
                  <div class="absolute left-4 md:left-1/2 w-5 h-5 bg-white border-4 border-primary rounded-full -translate-x-1/2 z-20 shadow-sm hidden md:block"></div>

                  <div [class]="'w-full md:w-[45%] ' + (i % 2 === 0 ? 'md:mr-auto md:text-right' : 'md:ml-auto md:pl-12')">
                    <div (click)="seleccionarEntrada(entry)" class="bg-white p-6 rounded-[2rem] shadow-sm border border-slate-100 hover:shadow-xl hover:border-primary/40 cursor-pointer transition-all duration-300 relative overflow-hidden">
                      <div class="flex items-center gap-2 mb-4" [class.justify-end]="i % 2 === 0 && !isMobile()">
                        <span [class]="obtenerClaseAccion(entry.accion) + ' text-[10px] font-black px-3 py-1 rounded-full uppercase tracking-tighter'">
                          {{ entry.accion }}
                        </span>
                        <span class="text-[11px] font-bold text-slate-400 bg-slate-50 px-3 py-1 rounded-full">
                          {{ entry.fecha }} | {{ formatHora(entry.hora) }}
                        </span>
                      </div>

                      <p class="text-slate-800 font-bold text-lg leading-tight mb-4">
                        {{ entry.detalle }}
                      </p>

                      <div class="flex flex-col gap-3 pt-4 border-t border-slate-50" [class.items-end]="i % 2 === 0 && !isMobile()">
                        <div class="flex flex-wrap gap-2" [class.justify-end]="i % 2 === 0 && !isMobile()">
                          <div class="flex items-center gap-1 bg-slate-100 px-3 py-1 rounded-xl text-[10px] font-black text-slate-500">
                            UID: {{ entry.id_usuario || 'SISTEMA' }}
                          </div>
                          @if (entry.id_taller) {
                            <div class="flex items-center gap-1 bg-amber-50 px-3 py-1 rounded-xl text-[10px] font-black text-amber-600">
                              TALLER: {{ entry.id_taller }}
                            </div>
                          }
                          <div class="flex items-center gap-1 bg-blue-50 px-3 py-1 rounded-xl text-[10px] font-black text-blue-600">
                            IP: {{ entry.ip }}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              } @empty {
                <div class="bg-white border-2 border-dashed border-slate-200 rounded-[3rem] p-20 text-center">
                  <div class="w-20 h-20 bg-slate-50 rounded-full flex items-center justify-center mx-auto mb-6">
                    <span class="material-symbols-outlined text-slate-300 text-4xl">search_off</span>
                  </div>
                  <h3 class="text-xl font-black text-slate-800">Sin resultados</h3>
                  <p class="text-slate-400 font-medium">No hay registros que coincidan con los filtros aplicados.</p>
                  <button (click)="limpiarFiltros()" class="mt-4 text-primary font-bold hover:underline">
                    Ver todos los registros
                  </button>
                </div>
              }
            </div>
          </div>
        }
      </div>

      <!-- Modal de Detalles -->
      @if (selectedEntry) {
        <div class="fixed inset-0 z-[100] flex items-start justify-center p-4 overflow-y-auto pt-10 sm:pt-20 bg-slate-900/40 backdrop-blur-sm animate-in fade-in duration-200">
          <div class="bg-white w-full max-w-2xl rounded-[2.5rem] shadow-2xl overflow-hidden animate-in zoom-in-95 duration-200">
            <div class="p-8 border-b border-slate-100 flex justify-between items-center bg-slate-50/50">
              <div>
                <span [class]="obtenerClaseAccion(selectedEntry.accion) + ' text-[10px] font-black px-4 py-1.5 rounded-full uppercase tracking-widest'">
                  {{ selectedEntry.accion }}
                </span>
                <h2 class="text-2xl font-black text-slate-900 mt-2">Detalles del Evento</h2>
              </div>
              <button (click)="selectedEntry = null" class="w-12 h-12 flex items-center justify-center rounded-2xl bg-white border border-slate-200 text-slate-400 hover:text-slate-900 hover:border-slate-900 transition-all">
                <span class="material-symbols-outlined">close</span>
              </button>
            </div>

            <div class="p-8 space-y-6">
              <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div class="space-y-1">
                  <p class="text-[10px] font-black text-slate-400 uppercase tracking-widest">Fecha y Hora</p>
                  <p class="text-slate-900 font-bold flex items-center gap-2">
                    <span class="material-symbols-outlined text-primary">calendar_today</span>
                    {{ selectedEntry.fecha }} a las {{ selectedEntry.hora }}
                  </p>
                </div>
                <div class="space-y-1">
                  <p class="text-[10px] font-black text-slate-400 uppercase tracking-widest">Dirección IP</p>
                  <p class="text-slate-900 font-bold flex items-center gap-2">
                    <span class="material-symbols-outlined text-primary">lan</span>
                    {{ selectedEntry.ip }}
                  </p>
                </div>
              </div>

              <div class="space-y-1">
                <p class="text-[10px] font-black text-slate-400 uppercase tracking-widest">Descripción Completa</p>
                <div class="bg-slate-50 p-4 rounded-2xl border border-slate-100 text-slate-800 font-medium leading-relaxed">
                  {{ selectedEntry.detalle }}
                </div>
              </div>

              <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div class="space-y-1">
                  <p class="text-[10px] font-black text-slate-400 uppercase tracking-widest">Usuario Responsable</p>
                  <p class="text-slate-900 font-bold flex items-center gap-2">
                    <span class="material-symbols-outlined text-primary">person</span>
                    ID Usuario: {{ selectedEntry.id_usuario || 'Sistema / Automático' }}
                  </p>
                </div>
                @if (selectedEntry.id_taller) {
                  <div class="space-y-1">
                    <p class="text-[10px] font-black text-slate-400 uppercase tracking-widest">Taller Relacionado</p>
                    <p class="text-slate-900 font-bold flex items-center gap-2">
                      <span class="material-symbols-outlined text-amber-500">store</span>
                      ID Taller: {{ selectedEntry.id_taller }}
                    </p>
                  </div>
                }
              </div>

              <div class="space-y-1">
                <p class="text-[10px] font-black text-slate-400 uppercase tracking-widest">Agente del Navegador (User Agent)</p>
                <div class="bg-slate-50 p-4 rounded-2xl border border-slate-100 text-slate-500 font-mono text-[11px] break-all leading-normal">
                  {{ selectedEntry.agente }}
                </div>
              </div>
            </div>

            <div class="p-8 bg-slate-50/50 border-t border-slate-100 flex justify-end">
              <button (click)="selectedEntry = null" class="px-8 py-3 bg-slate-900 text-white rounded-2xl font-black hover:bg-slate-800 transition-all">
                Cerrar Detalle
              </button>
            </div>
          </div>
        </div>
      }
    </div>
  `,
  styles: [`
    :host { display: block; }
  `]
})
export class BitacoraComponent implements OnInit {
  private bitacoraService = inject(BitacoraService);
  entries: BitacoraEntry[] = [];
  loading: boolean = true;
  error: string | null = null;
  selectedEntry: BitacoraEntry | null = null;

  // Filtros
  searchTerm: string = '';
  filterDate: string = '';

  ngOnInit(): void {
    this.cargarBitacora();
  }

  get filteredEntries() {
    return this.entries.filter(entry => {
      const term = this.searchTerm.toLowerCase();
      const matchSearch = !this.searchTerm || 
        entry.detalle.toLowerCase().includes(term) ||
        entry.accion.toLowerCase().includes(term) ||
        (entry.id_usuario && entry.id_usuario.toString().includes(term)) ||
        (entry.id_taller && entry.id_taller.toString().includes(term));
      
      const matchDate = !this.filterDate || entry.fecha.toString() === this.filterDate;
      
      return matchSearch && matchDate;
    });
  }

  limpiarFiltros(): void {
    this.searchTerm = '';
    this.filterDate = '';
  }

  cargarBitacora(): void {
    this.loading = true;
    this.bitacoraService.getBitacora().subscribe({
      next: (data) => {
        this.entries = data;
        this.loading = false;
        this.error = null;
      },
      error: (err) => {
        this.loading = false;
        this.error = err.status === 403 
          ? 'Acceso Denegado: Se requieren permisos de administrador.' 
          : 'Error de conexión con el servidor.';
      }
    });
  }

  seleccionarEntrada(entry: BitacoraEntry): void {
    this.selectedEntry = entry;
  }

  formatHora(hora: string): string {
    if (!hora) return '00:00';
    return hora.split('.')[0].substring(0, 5);
  }

  obtenerClaseAccion(accion: string): string {
    const a = accion.toLowerCase();
    if (a.includes('inicio')) return 'bg-green-100 text-green-700';
    if (a.includes('fallido') || a.includes('error')) return 'bg-red-100 text-red-700';
    if (a.includes('actualiz') || a.includes('modific')) return 'bg-blue-100 text-blue-700';
    if (a.includes('elimin')) return 'bg-rose-100 text-rose-700';
    return 'bg-slate-100 text-slate-700';
  }

  isMobile(): boolean {
    return window.innerWidth < 768;
  }
}
