import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { BitacoraService, BitacoraEntry } from '../../../core/services/bitacora.service';

@Component({
  selector: 'app-bitacora',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="min-h-screen bg-gray-50 p-4 md:p-8">
      <div class="max-w-4xl mx-auto">
        <!-- Header -->
        <div class="mb-8">
          <h1 class="text-3xl font-bold text-gray-800">Bitácora de Actividades</h1>
          <p class="text-gray-600">Historial de movimientos y acciones realizadas en el taller.</p>
        </div>

        <!-- Timeline Container -->
        <div class="relative">
          <!-- Vertical Line -->
          <div class="absolute left-4 md:left-1/2 top-0 bottom-0 w-0.5 bg-gray-200 -translate-x-1/2 hidden md:block"></div>

          <div class="space-y-12">
            @for (entry of entries; track entry.id; let first = $first; let last = $last) {
              <div class="relative flex flex-col md:flex-row items-center">
                <!-- Dot -->
                <div class="absolute left-4 md:left-1/2 w-4 h-4 bg-blue-500 rounded-full border-4 border-white shadow -translate-x-1/2 z-10"></div>

                <!-- Content Wrapper (Alternate Left/Right) -->
                <div [class]="'w-full md:w-1/2 ' + (entry.id % 2 === 0 ? 'md:pr-12 md:text-right md:order-1' : 'md:pl-12 md:order-2 ml-8 md:ml-0')">
                  <div class="bg-white p-6 rounded-xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
                    <div class="flex items-center justify-between mb-2" [class.md:flex-row-reverse]="entry.id % 2 === 0">
                      <span class="text-xs font-semibold px-2 py-1 bg-blue-50 text-blue-600 rounded-full uppercase tracking-wider">
                        {{ entry.accion }}
                      </span>
                      <span class="text-xs text-gray-400 font-medium">
                        {{ entry.fecha }} | {{ entry.hora }}
                      </span>
                    </div>
                    
                    <h3 class="text-lg font-bold text-gray-800 mb-2">{{ entry.detalle }}</h3>
                    
                    <div class="flex flex-col space-y-1 text-sm text-gray-500" [class.md:items-end]="entry.id % 2 === 0">
                      <div class="flex items-center gap-2">
                        <span class="font-medium text-gray-700">IP:</span> {{ entry.ip }}
                      </div>
                      <div class="flex items-center gap-2 truncate max-w-xs">
                        <span class="font-medium text-gray-700">Agente:</span> 
                        <span class="truncate" [title]="entry.agente">{{ entry.agente }}</span>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Empty Spacer for the other side -->
                <div class="hidden md:block md:w-1/2" [class.order-2]="entry.id % 2 === 0" [class.order-1]="entry.id % 2 !== 0"></div>
              </div>
            } @empty {
              <div class="text-center py-20 bg-white rounded-2xl border-2 border-dashed border-gray-200">
                <div class="text-gray-400 mb-2">
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <p class="text-gray-500 font-medium">No se han registrado movimientos aún.</p>
              </div>
            }
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    :host { display: block; }
    .timeline-container::before {
      content: '';
      position: absolute;
      top: 0;
      bottom: 0;
      width: 2px;
      background: #e5e7eb;
      left: 1rem;
    }
    @media (min-width: 768px) {
      .timeline-container::before {
        left: 50%;
        margin-left: -1px;
      }
    }
  `]
})
export class BitacoraComponent implements OnInit {
  private bitacoraService = inject(BitacoraService);
  entries: BitacoraEntry[] = [];

  ngOnInit(): void {
    this.bitacoraService.getBitacora().subscribe({
      next: (data) => {
        this.entries = data;
      },
      error: (err) => {
        console.error('Error al cargar la bitácora:', err);
      }
    });
  }
}
