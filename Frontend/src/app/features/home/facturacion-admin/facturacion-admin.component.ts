import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { PagosService } from '../../../core/services/pagos.service';

@Component({
  selector: 'app-facturacion-admin',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './facturacion-admin.component.html',
})
export class FacturacionAdminComponent implements OnInit {
  private pagosService = inject(PagosService);

  talleresStats = signal<any[]>([]);
  resumen = signal({
    activos: 0,
    pendientes: 0,
    porVencer: 0,
    totalFacturado: 0
  });
  cargando = signal<boolean>(true);

  ngOnInit() {
    this.cargarStats();
  }

  cargarStats() {
    this.cargando.set(true);
    this.pagosService.obtenerStatsAdmin().subscribe({
      next: (data) => {
        this.talleresStats.set(data);
        this.calcularResumen(data);
        this.cargando.set(false);
      },
      error: (err) => {
        console.error('Error al cargar stats de admin:', err);
        this.cargando.set(false);
      }
    });
  }

  private calcularResumen(data: any[]) {
    let activos = 0;
    let pendientes = 0;
    let porVencer = 0;
    let total = 0;

    const hoy = new Date();
    const proximaSemana = new Date();
    proximaSemana.setDate(hoy.getDate() + 7);

    data.forEach(t => {
      if (t.estado_pago === 'active' || t.estado_pago === 'trialing') activos++;
      else if (t.estado_pago === 'pending' || t.estado_pago === 'past_due') pendientes++;

      if (t.periodo_fin) {
        const fechaFin = new Date(t.periodo_fin);
        if (fechaFin > hoy && fechaFin < proximaSemana) porVencer++;
      }

      total += (t.monto_centavos / 100);
    });

    this.resumen.set({ activos, pendientes, porVencer, totalFacturado: total });
  }

  abrirFactura(url: string) {
    if (url) window.open(url, '_blank');
  }
}
