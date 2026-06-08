import { Component, inject, OnInit, ChangeDetectorRef } from '@angular/core';
import { AdminReportesService } from './../../core/services/reportes/admin-reportes.service';
import { CommonModule } from '@angular/common'; // Para *ngFor y [ngClass]
import { FormsModule } from '@angular/forms';
import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';
import * as XLSX from 'xlsx';
import { color } from 'chart.js/helpers';
@Component({
  selector: 'app-reportes-admin',
  standalone: true, // <--- IMPORTANTE: Asegúrate que diga true
  imports: [CommonModule, FormsModule],
  templateUrl: './reportes-admin.component.html',
  styleUrls: ['./reportes-admin.component.css'],
})
export class ReportesAdminComponent implements OnInit {
  private reportesService = inject(AdminReportesService);
  private cdr = inject(ChangeDetectorRef); // <--- 1. Inyectamos ChangeDetectorRef
  usuarios: any[] = [];
  filtroRol: string = '';
  filtroOrden: string = '';
  // Añade estas variables dentro de tu clase:
  isRecording: boolean = false;
  mediaRecorder: any;
  audioChunks: any[] = [];
  isProcessingVoice: boolean = false; // Para mostrar un loader mientras la IA piensa
  kpis: any = {
    tiempo_promedio_llegada: '0 min',
    casos_cancelados: 0,
    nivel_sla: '0%',
    incidentes_por_tipo: {},
    talleres_eficientes: [],
  };
  ngOnInit() {
    this.cargarDatos();
    this.cargarKPIs();
  }

  cargarDatos() {
    // Es buena práctica limpiar el orden si cambian de rol
    if (this.filtroRol !== 'ADMIN_TALLER') {
      this.filtroOrden = '';
    }

    // Asegúrate de pasar ambos argumentos al servicio
    this.reportesService.getUsuariosReporte(this.filtroRol, this.filtroOrden).subscribe((data) => {
      this.usuarios = data;
    });
  }
  // 3. El método para obtener los KPIs
  cargarKPIs() {
    this.reportesService.getKPIsDashboard().subscribe({
      next: (data: any) => {
        this.kpis = data;
        this.cdr.detectChanges(); // Forzamos a Angular a repintar el HTML
      },
      error: (err) => {
        console.error('Error cargando los KPIs del Dashboard', err);
      },
    });
  }
  descargarPDF() {
    const DATA = document.getElementById('tablaAdmin'); // El ID de tu tabla
    const doc = new jsPDF('p', 'pt', 'a4');
    const options = {
      background: 'white',
      scale: 3,
    };

    if (DATA) {
      html2canvas(DATA, options)
        .then((canvas) => {
          const img = canvas.toDataURL('image/PNG');

          // Cálculos para que la imagen quepa en el A4
          const bufferX = 15;
          const bufferY = 15;
          const imgProps = (doc as any).getImageProperties(img);
          const pdfWidth = doc.internal.pageSize.getWidth() - 2 * bufferX;
          const pdfHeight = (imgProps.height * pdfWidth) / imgProps.width;

          doc.addImage(img, 'PNG', bufferX, bufferY, pdfWidth, pdfHeight, undefined, 'FAST');
          return doc;
        })
        .then((docResult) => {
          docResult.save(`${new Date().toISOString()}_reporte_maestro.pdf`);
        });
    }
  }
  descargarExcel() {
    // 1. Mapeamos los datos para que tengan nombres de columnas bonitos
    const datosLimpios = this.usuarios.map((u) => {
      return {
        ID: u.id,
        'NOMBRE / TALLER': u.nombre,
        'CORREO ELECTRÓNICO': u.email,
        ROL: u.rol.toUpperCase(),
        'DETALLE (Calificación/Contacto)': u.extra,
      };
    });

    // 2. Creamos la hoja de trabajo (Worksheet)
    const ws: XLSX.WorkSheet = XLSX.utils.json_to_sheet(datosLimpios);

    // 3. (El detalle extra) Ajustamos el ancho de las columnas automáticamente
    const columnWidths = [
      { wch: 10 }, // ID
      { wch: 35 }, // Nombre
      { wch: 30 }, // Email
      { wch: 15 }, // Rol
      { wch: 30 }, // Detalle
    ];
    ws['!cols'] = columnWidths;

    // 4. Creamos el libro (Workbook) y añadimos la hoja
    const wb: XLSX.WorkBook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, 'Usuarios');

    // 5. Guardamos el archivo
    const fecha = new Date().toISOString().split('T')[0];
    XLSX.writeFile(wb, `Reporte_Usuarios_${fecha}.xlsx`);
  }
  // Añade estos métodos:
  iniciarGrabacion() {
    navigator.mediaDevices
      .getUserMedia({ audio: true })
      .then((stream) => {
        this.isRecording = true;
        this.mediaRecorder = new (window as any).MediaRecorder(stream);
        this.audioChunks = [];

        this.mediaRecorder.ondataavailable = (event: any) => {
          this.audioChunks.push(event.data);
        };

        this.mediaRecorder.onstop = () => {
          const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
          this.enviarAudioAIA(audioBlob);
          stream.getTracks().forEach((track) => track.stop()); // Apagar el mic
        };

        this.mediaRecorder.start();
      })
      .catch((err) => console.error('Error accediendo al micrófono', err));
  }

  detenerGrabacion() {
    if (this.mediaRecorder) {
      this.isRecording = false;
      this.mediaRecorder.stop();
    }
  }

  toggleGrabacion() {
    this.isRecording ? this.detenerGrabacion() : this.iniciarGrabacion();
  }

  enviarAudioAIA(audioBlob: Blob) {
    this.isProcessingVoice = true;
    const formData = new FormData();
    formData.append('file', audioBlob, 'audio_filtro.webm');

    this.reportesService.enviarAudioFiltro(formData).subscribe({
      next: (respuestaRAW: any) => {
        // 2. Limpieza extrema: por si la IA devuelve markdown (```json ... ```)
        let jsonStr =
          typeof respuestaRAW === 'string' ? respuestaRAW : JSON.stringify(respuestaRAW);
        jsonStr = jsonStr
          .replace(/```json/g, '')
          .replace(/```/g, '')
          .trim();
        const respuestaIA = JSON.parse(jsonStr);

        console.log('✅ IA (Limpio):', respuestaIA);

        // 3. Normalizamos a mayúsculas/minúsculas para que coincida exacto con los <select>
        this.filtroRol = respuestaIA.rol ? respuestaIA.rol.trim().toUpperCase() : '';
        this.filtroOrden = respuestaIA.orden ? respuestaIA.orden.trim().toLowerCase() : '';

        // Si el rol no es ADMIN_TALLER, vaciamos el orden para evitar inconsistencias
        if (this.filtroRol !== 'ADMIN_TALLER') {
          this.filtroOrden = '';
        }

        // 4. Hacemos la petición con los filtros limpios
        this.reportesService
          .getUsuariosReporte(this.filtroRol, this.filtroOrden)
          .subscribe((data) => {
            this.usuarios = data;
            this.isProcessingVoice = false;

            // 5. ¡EL TRUCO MÁGICO! Obligamos a Angular a redibujar la tabla HTML AHORA MISMO
            this.cdr.detectChanges();

            // 6. Ejecutamos la acción con la garantía de que el front ya está actualizado
            setTimeout(() => {
              const accion = respuestaIA.accion ? respuestaIA.accion.trim().toLowerCase() : '';
              if (accion === 'pdf') {
                this.descargarPDF();
              } else if (accion === 'excel') {
                this.descargarExcel();
              }
            }, 100); // Como forzamos los cambios arriba, 100ms es más que suficiente
          });
      },
      error: (err: any) => {
        console.error('Error procesando audio con IA', err);
        this.isProcessingVoice = false;
      },
    });
  }
}
