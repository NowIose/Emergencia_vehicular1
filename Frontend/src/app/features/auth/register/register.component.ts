import { Component, inject ,ChangeDetectorRef ,OnDestroy, HostListener } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { AuthService } from '../../../core/services/auth/auth.service';
import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { MediaService } from '../../../core/services/media.service';
import { environment } from '../../../../environments/environment';

declare var mapboxgl: any;

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [ReactiveFormsModule, CommonModule],
  templateUrl: './register.component.html',
})
export class RegisterComponent implements OnDestroy {
  private fb = inject(FormBuilder);
  private authService = inject(AuthService);
  private router = inject(Router);
  private cdr = inject(ChangeDetectorRef);
  private map: any;
  private marker: any;
  // Definimos el formulario con los nombres que pusimos en el HTML
  registerForm = this.fb.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(8)]],
    telefono: ['', Validators.required],
    nombre_taller: ['', Validators.required],
    nit: ['', Validators.required],
    ciudad: ['', Validators.required],
    direccion: ['', Validators.required],
    latitud: [0, [Validators.required, Validators.min(-90), Validators.max(90)]], 
    longitud: [0, [Validators.required, Validators.min(-180), Validators.max(180)]],
    foto_perfil: [''] 
  });
  registroCompletado: boolean = false; 

  onSubmit() {
    if (this.registerForm.valid) {
      const formValues = this.registerForm.value;
      const datosRegistro = {
        ...formValues,
        foto_perfil: formValues.foto_perfil || 'default.png',
        latitud: formValues.latitud || 0,
        longitud: formValues.longitud || 0
      };

      console.log('Enviando datos al servidor...', datosRegistro);

      this.authService.registrarTaller(datosRegistro).subscribe({
        next: (res) => {
          this.registroCompletado = true;
          alert('¡Registro exitoso! Ahora ingresa con tus credenciales.');
          this.router.navigate(['/login']);
        },
        error: (err) => {
          const mensajeError = err.error?.detail || 'No se pudo completar el registro';
          alert('Error: ' + mensajeError);
        }
      });
    } else {
      alert('Por favor, completa todos los campos obligatorios incluyendo la ubicación en el mapa.');
    }
  }

  fotoPrevisualizacion: string = ''; 
  currentPublicId: string = ''; 

  private mediaService = inject(MediaService);

  onFileSelected(event: any) {
    const file: File = event.target.files[0];
    if (!file) return;

    if (this.currentPublicId) {
      this.mediaService.deleteImage(this.currentPublicId).subscribe({
        next: () => console.log('Imagen anterior borrada'),
        error: (e) => console.error('No se pudo borrar', e)
      });
    }

    this.mediaService.uploadImage(file).subscribe({
      next: (res) => {
        this.fotoPrevisualizacion = res.url;
        this.currentPublicId = res.public_id;
        this.registerForm.patchValue({ foto_perfil: res.url });
        this.cdr.detectChanges();
      },
      error: (err) => {
        console.error('Error al subir imagen', err);
        alert('No se pudo subir la imagen.');
      }
    });
  }

  ngOnDestroy() {
    this.ejecutarLimpiezaHuerfana();
  }

  obtenerUbicacion() {
    if ('geolocation' in navigator) {
      console.log('Solicitando geolocalización...');
      navigator.geolocation.getCurrentPosition((position) => {
        const lat = position.coords.latitude;
        const lng = position.coords.longitude;

        this.registerForm.patchValue({ latitud: lat, longitud: lng });
        this.mostrarMapa(lat, lng);
        this.cdr.detectChanges();
      }, (error) => {
        console.error('Error de geolocalización:', error);
        alert('Error al obtener ubicación: ' + error.message);
        // Fallback: mostrar mapa en una ubicación por defecto (Santa Cruz)
        this.mostrarMapa(-17.7833, -63.1821);
      }, { 
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0
      });
    } else {
      alert('Tu navegador no soporta geolocalización.');
      this.mostrarMapa(-17.7833, -63.1821);
    }
  }

  private mostrarMapa(lat: number, lng: number) {
    setTimeout(() => {
      const container = document.getElementById('mapa-registro');
      if (!container) return;

      if (!this.map) {
        mapboxgl.accessToken = environment.mapboxToken;
        
        this.map = new mapboxgl.Map({
          container: 'mapa-registro',
          style: 'mapbox://styles/mapbox/streets-v12',
          center: [lng, lat],
          zoom: 15
        });

        this.marker = new mapboxgl.Marker({
          draggable: true,
          color: "#af101a"
        })
        .setLngLat([lng, lat])
        .addTo(this.map);

        this.marker.on('dragend', () => {
          const lngLat = this.marker.getLngLat();
          this.registerForm.patchValue({
            latitud: lngLat.lat,
            longitud: lngLat.lng
          });
          this.cdr.detectChanges();
        });

        // Al hacer click en el mapa, mover el marcador
        this.map.on('click', (e: any) => {
          this.marker.setLngLat(e.lngLat);
          this.registerForm.patchValue({
            latitud: e.lngLat.lat,
            longitud: e.lngLat.lng
          });
          this.cdr.detectChanges();
        });

      } else {
        this.map.flyTo({ center: [lng, lat], zoom: 15 });
        this.marker.setLngLat([lng, lat]);
      }

      setTimeout(() => {
        this.map.resize();
      }, 200);
    }, 100);
  }

  @HostListener('window:beforeunload', ['$event'])
  unloadHandler(event: Event) {
    this.ejecutarLimpiezaHuerfana();
  }

  private ejecutarLimpiezaHuerfana() {
    if (this.currentPublicId && !this.registroCompletado) {
      console.log('Limpiando imagen no utilizada en Cloudinary...');
      this.mediaService.deleteImage(this.currentPublicId).subscribe();
    }
  }
}
