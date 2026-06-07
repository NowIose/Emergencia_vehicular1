import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { PagosService } from '../../../core/services/pagos.service';
import { ActivatedRoute } from '@angular/router';

@Component({
  selector: 'app-facturacion',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './facturacion.component.html',
})
export class FacturacionComponent implements OnInit {
  private pagosService = inject(PagosService);
  private route = inject(ActivatedRoute);

  suscripcion = signal<any>(null);
  cargando = signal<boolean>(true);
  mensajeSuccess = signal<boolean>(false);

  ngOnInit() {
    this.route.queryParams.subscribe(params => {
      if (params['checkout'] === 'success') {
        this.mensajeSuccess.set(true);
      }
    });
    this.cargarSuscripcion();
  }

  cargarSuscripcion() {
    this.cargando.set(true);
    this.pagosService.obtenerMiSuscripcion().subscribe({
      next: (data) => {
        // Aseguramos que las fechas sean objetos Date si vienen como string
        if (data.periodo_inicio) data.periodo_inicio = new Date(data.periodo_inicio);
        if (data.periodo_fin) data.periodo_fin = new Date(data.periodo_fin);
        
        this.suscripcion.set(data);
        this.cargando.set(false);
      },
      error: (err) => {
        console.error('Error al cargar suscripción:', err);
        this.cargando.set(false);
      }
    });
  }

  gestionarFacturacion() {
    this.pagosService.abrirPortalFacturacion().subscribe({
      next: (res) => {
        window.location.href = res.portal_url;
      },
      error: (err) => alert('No se pudo abrir el portal de facturación: ' + (err.error?.detail || 'Error desconocido'))
    });
  }

  contratarPlan(plan: string) {
    this.pagosService.crearCheckoutSession(plan).subscribe({
      next: (res) => {
        window.location.href = res.checkout_url;
      },
      error: (err) => alert('Error al iniciar pago: ' + (err.error?.detail || 'Error desconocido'))
    });
  }
}
