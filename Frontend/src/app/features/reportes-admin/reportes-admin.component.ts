import { Component, inject, OnInit } from '@angular/core';
import { AdminReportesService } from './../../core/services/reportes/admin-reportes.service';
import { CommonModule } from '@angular/common'; // Para *ngFor y [ngClass]
import { FormsModule } from '@angular/forms';
import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';
import * as XLSX from 'xlsx';

@Component({
  selector: 'app-reportes-admin',
  standalone: true,           // <--- IMPORTANTE: Asegúrate que diga true
  imports: [CommonModule, FormsModule],
  templateUrl: './reportes-admin.component.html',
  styleUrls: ['./reportes-admin.component.css']
})
export class ReportesAdminComponent implements OnInit {
  private reportesService = inject(AdminReportesService);
  usuarios: any[] = [];
  filtroRol: string = '';
  filtroOrden: string = '';

  ngOnInit() {
    this.cargarDatos();
  }

  cargarDatos() {
    // Es buena práctica limpiar el orden si cambian de rol
    if (this.filtroRol !== 'ADMIN_TALLER') {
      this.filtroOrden = '';
    }

    // Asegúrate de pasar ambos argumentos al servicio
    this.reportesService.getUsuariosReporte(this.filtroRol, this.filtroOrden).subscribe(data => {
      this.usuarios = data;
    });
  }

  descargarPDF() {
    const DATA = document.getElementById('tablaAdmin'); // El ID de tu tabla
    const doc = new jsPDF('p', 'pt', 'a4');
    const options = {
      background: 'white',
      scale: 3
    };

    if (DATA) {
      html2canvas(DATA, options).then((canvas) => {
        const img = canvas.toDataURL('image/PNG');

        // Cálculos para que la imagen quepa en el A4
        const bufferX = 15;
        const bufferY = 15;
        const imgProps = (doc as any).getImageProperties(img);
        const pdfWidth = doc.internal.pageSize.getWidth() - 2 * bufferX;
        const pdfHeight = (imgProps.height * pdfWidth) / imgProps.width;

        doc.addImage(img, 'PNG', bufferX, bufferY, pdfWidth, pdfHeight, undefined, 'FAST');
        return doc;
      }).then((docResult) => {
        docResult.save(`${new Date().toISOString()}_reporte_maestro.pdf`);
      });
    }
  }
  descargarExcel() {
    // 1. Mapeamos los datos para que tengan nombres de columnas bonitos
    const datosLimpios = this.usuarios.map(u => {
      return {
        'ID': u.id,
        'NOMBRE / TALLER': u.nombre,
        'CORREO ELECTRÓNICO': u.email,
        'ROL': u.rol.toUpperCase(),
        'DETALLE (Calificación/Contacto)': u.extra
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
}