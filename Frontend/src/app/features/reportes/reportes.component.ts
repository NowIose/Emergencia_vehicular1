import { Component, OnInit } from '@angular/core';
import { ReportesService, EstadisticaEmergencia } from './../../core/services/reportes/reportes.service';
import { ChartConfiguration, ChartOptions } from 'chart.js';
import { BaseChartDirective } from 'ng2-charts';
import { CommonModule } from '@angular/common'; 
import { FormsModule } from '@angular/forms';
import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';

@Component({
  selector: 'app-reportes',
  standalone: true, // Verifica que esto esté así
  imports: [CommonModule, FormsModule, BaseChartDirective], // <--- AGREGA ESTO AQUÍ
  templateUrl: './reportes.component.html',
  styleUrls: ['./reportes.component.css']
})
export class ReportesComponent implements OnInit {
  // Filtros por defecto (Último mes)
  fechaInicio: string = '';
  fechaFin: string = '';
  agrupacion: string = 'dia';

  // Configuración del Gráfico
  public lineChartData: ChartConfiguration<'line'>['data'] = {
    labels: [],
    datasets: [
      {
        data: [],
        label: 'Emergencias Atendidas',
        fill: true,
        tension: 0.5,
        borderColor: '#0056b3',
        backgroundColor: 'rgba(0, 86, 179, 0.3)'
      }
    ]
  };
  public lineChartOptions: ChartOptions<'line'> = { responsive: true };

  constructor(private reportesService: ReportesService) {}

  ngOnInit() {
    this.establecerFechasPorDefecto();
    this.cargarGrafico();
  }

  establecerFechasPorDefecto() {
    const hoy = new Date();
    this.fechaFin = hoy.toISOString().split('T')[0]; // YYYY-MM-DD
    
    const mesPasado = new Date();
    mesPasado.setMonth(mesPasado.getMonth() - 1);
    this.fechaInicio = mesPasado.toISOString().split('T')[0];
  }

  cargarGrafico() {
    this.reportesService.obtenerEstadisticas(this.fechaInicio, this.fechaFin, this.agrupacion)
    .subscribe({
      next: (data) => {
        console.log('Datos recibidos:', data); // Mira esto en la consola del navegador (F12)

        if (data && data.length > 0) {
          const etiquetas = data.map(item => item.etiqueta);
          const totales = data.map(item => item.total);

          // ¡ESTO ES LO MÁS IMPORTANTE! 
          // Creamos un objeto nuevo para que Angular detecte el cambio
          this.lineChartData = {
            labels: etiquetas,
            datasets: [
              {
                data: totales,
                label: 'Cantidad de Emergencias',
                borderColor: '#0056b3',
                backgroundColor: 'rgba(0, 86, 179, 0.1)',
                fill: 'origin',
                tension: 0.4 // Hace la línea curva y profesional
              }
            ]
          };
        } else {
          console.warn('El backend devolvió una lista vacía. Revisa el rango de fechas.');
          // Limpiamos la gráfica si no hay datos
          this.lineChartData.datasets[0].data = [];
        }
      },
      error: (err) => console.error('Error al cargar gráfica:', err)
    });
    }
    async descargarPDF() {
    const DATA = document.getElementById('reporteContenedor');
  
  if (!DATA) return;

  // Mostramos un mensaje de "Procesando..." si fuera necesario
  const doc = new jsPDF('p', 'pt', 'a4');
  const options = {
    background: 'white',
    scale: 3 // Mayor escala = mejor calidad de imagen
  };

  html2canvas(DATA, options).then((canvas) => {
    const img = canvas.toDataURL('image/PNG');

    // Cálculos para ajustar la imagen al tamaño A4
    const bufferX = 15;
    const bufferY = 15;
    const imgProps = (doc as any).getImageProperties(img);
    const pdfWidth = doc.internal.pageSize.getWidth() - 2 * bufferX;
    const pdfHeight = (imgProps.height * pdfWidth) / imgProps.width;

    // Añadir encabezado personalizado
    doc.setFontSize(18);
    doc.text('Análisis de Emergencias Vehiculares', bufferX, 40);
    doc.setFontSize(11);
    doc.text(`Fecha de generación: ${new Date().toLocaleString()}`, bufferX, 60);

    // Añadir la imagen del gráfico
    doc.addImage(img, 'PNG', bufferX, 80, pdfWidth, pdfHeight, undefined, 'FAST');
    
    // Guardar el archivo con las fechas elegidas
    doc.save(`Reporte_Emergencias_${this.fechaInicio}_to_${this.fechaFin}.pdf`);
  });
}
}