import { Component, OnInit, inject, ChangeDetectorRef } from '@angular/core'; // 1. Agregamos ChangeDetectorRef
import { CommonModule } from '@angular/common';
import { BackupsService, Backup } from '../../../core/services/backups.service';
import { Router } from '@angular/router';

@Component({
  selector: 'app-backups',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './Backups.component.html',
  styleUrls: ['./Backups.component.css'],
})
export class BackupsComponent implements OnInit {
  private backupsService = inject(BackupsService);
  private router = inject(Router);
  private cdr = inject(ChangeDetectorRef); // 2. Inyectamos el detector de cambios

  backups: Backup[] = [];
  cargando: boolean = false;
  mensaje: string = '';

  ngOnInit() {
    this.cargarBackups();
  }

  cargarBackups() {
    this.cargando = true;

    (this.backupsService.listarBackups() as any).subscribe({
      next: (res: any) => {
        this.backups = res.backups || [];
        this.cargando = false;

        // 3. LA MAGIA: Obligamos a Angular a redibujar la vista inmediatamente
        this.cdr.detectChanges();
      },
      error: (err: any) => {
        console.error('Error al cargar backups', err);
        this.mensaje = 'Error al cargar el historial de respaldos.';
        this.cargando = false;
        this.cdr.detectChanges(); // También actualizamos la vista si hay error
      },
    });
  }

  generarNuevoBackup() {
    this.cargando = true;
    this.mensaje =
      'Generando backup y subiendo a Cloudflare R2... Esto puede tardar unos segundos.';

    (this.backupsService.crearBackup() as any).subscribe({
      next: (res: any) => {
        this.mensaje = res.mensaje;
        this.cargarBackups(); // Al llamar esto, el ChangeDetectorRef volverá a actualizar la vista
      },
      error: (err: any) => {
        console.error('Error al crear backup', err);
        this.mensaje = 'Hubo un error al generar el respaldo en la nube.';
        this.cargando = false;
        this.cdr.detectChanges();
      },
    });
  }

  restaurar(filename: string) {
    const confirmacion = confirm(
      `⚠️ CUIDADO ⚠️\n\n¿Estás seguro de que deseas restaurar la base de datos a la versión: ${filename}?\n\nEsto sobrescribirá todos los datos actuales del sistema de Emergencia Vehicular.`,
    );

    if (confirmacion) {
      this.cargando = true;
      this.mensaje = `Descargando desde la nube y restaurando ${filename}...`;

      (this.backupsService.restaurarBackup(filename) as any).subscribe({
        next: (res: any) => {
          this.mensaje = res.mensaje;
          this.cargando = false;
          alert(
            '✅ Base de datos restaurada con éxito. Por seguridad, debes iniciar sesión nuevamente.',
          );

          localStorage.removeItem('access_token');
          localStorage.removeItem('user_data');
          this.router.navigate(['/login']);
        },
        error: (err: any) => {
          console.error('Error al restaurar', err);
          this.mensaje =
            'Error crítico al restaurar la base de datos. Revisa los logs del servidor.';
          this.cargando = false;
          this.cdr.detectChanges();
        },
      });
    }
  }
}
