import { Component, OnInit, OnDestroy, ViewChild, ElementRef, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ChatService } from '../../core/services/chat.service';

@Component({
  selector: 'app-chat',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './chat.component.html'
})
export class ChatComponent implements OnInit, OnDestroy {
  private chatService = inject(ChatService);
  
  // Usamos signals para asegurar que Angular detecte los cambios al instante
  chatsActivos = signal<any[]>([]);
  mensajes = signal<any[]>([]);
  chatSeleccionado = signal<any | null>(null);
  
  nuevoMensaje: string = '';
  myId: number | null = null;
  
  @ViewChild('scrollContainer') private scrollContainer!: ElementRef;

  ngOnInit() {
    this.obtenerMiId();
    this.cargarChats();
    this.chatService.conectarTaller();
    
    // Suscribirse a mensajes nuevos vía WebSocket
    this.chatService.messages$.subscribe(payload => {
      this.procesarMensajeWS(payload);
    });
  }

  ngOnDestroy() {
    this.chatService.desconectar();
  }

  obtenerMiId() {
    const token = localStorage.getItem('access_token'); 
    if (token) {
      try {
        const base64Url = token.split('.')[1];
        const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
        const jsonPayload = decodeURIComponent(atob(base64).split('').map(c => {
          return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
        }).join(''));
        const decoded = JSON.parse(jsonPayload);
        this.myId = decoded.sub ? parseInt(decoded.sub) : null;
        console.log("✅ Mi ID decodificado del token:", this.myId);
      } catch (e) {
        console.error("❌ Error decodificando token", e);
      }
    }
  }

  cargarChats() {
    console.log("⏳ Cargando chats activos...");
    this.chatService.getChatsActivos().subscribe({
      next: (chats) => {
        this.chatsActivos.set(chats);
        console.log("📥 Chats activos cargados en el signal:", this.chatsActivos());
      },
      error: (err) => console.error("❌ Error al cargar chats activos:", err)
    });
  }

  seleccionarChat(chat: any) {
    console.log("👉 Chat seleccionado:", chat);
    this.chatSeleccionado.set(chat);
    this.cargarHistorial(chat.nro_emergencia);
    this.marcarComoLeido(chat.nro_emergencia);
    
    // Resetear contador local en el objeto del signal
    this.chatsActivos.update(list => 
      list.map(c => c.nro_emergencia === chat.nro_emergencia ? { ...c, mensajes_pendientes: 0 } : c)
    );
  }

  cargarHistorial(nro: number) {
    console.log(`⏳ Cargando historial para emergencia #${nro}...`);
    this.chatService.getHistorial(nro).subscribe(msgs => {
      this.mensajes.set(msgs);
      console.log("📥 Mensajes cargados en el signal:", this.mensajes());
      this.scrollToBottom();
    });
  }

  marcarComoLeido(nro: number) {
    this.chatService.marcarComoLeidos(nro).subscribe();
  }

  enviar() {
    if (!this.nuevoMensaje.trim() || !this.chatSeleccionado()) return;

    const texto = this.nuevoMensaje;
    const nro = this.chatSeleccionado().nro_emergencia;
    
    // Optimistic Update: Añadir mensaje al signal inmediatamente
    this.mensajes.update(prev => [...prev, {
      id_remitente: this.myId,
      mensaje: texto,
      fecha_hora: new Date().toISOString(),
      leido: false
    }]);
    
    const msgAEnviar = this.nuevoMensaje;
    this.nuevoMensaje = '';
    this.scrollToBottom();

    this.chatService.enviarMensaje(nro, msgAEnviar).subscribe({
      error: (err) => console.error("❌ Error enviando mensaje", err)
    });
  }

  procesarMensajeWS(payload: any) {
    console.log("🔌 Mensaje recibido por WS:", payload);
    if (payload.type === 'NEW_MESSAGE') {
      const msg = payload.data;

      // Filtrado: ¿Este mensaje es para mi taller? (comparación flexible ==)
      const esParaMi = msg.id_taller == this.myId || msg.id_remitente == this.myId;
      if (!esParaMi) return;

      const chatActual = this.chatSeleccionado();
      
      if (chatActual && msg.nro_emergencia === chatActual.nro_emergencia) {
        if (msg.id_remitente !== this.myId) {
          this.mensajes.update(prev => [...prev, {
            id_remitente: msg.id_remitente,
            mensaje: msg.mensaje,
            fecha_hora: new Date().toISOString(),
            leido: false
          }]);
          this.scrollToBottom();
          this.marcarComoLeido(msg.nro_emergencia);
        }
      } else {
        // Actualizar contador en la lista
        this.chatsActivos.update(list => {
          const index = list.findIndex(c => c.nro_emergencia === msg.nro_emergencia);
          if (index !== -1) {
            const newList = [...list];
            newList[index] = {
              ...newList[index],
              mensajes_pendientes: (newList[index].mensajes_pendientes || 0) + 1,
              ultimo_mensaje: msg.mensaje,
              fecha_ultimo_mensaje: new Date().toISOString()
            };
            return newList;
          } else {
            this.cargarChats(); // Chat nuevo, recargar
            return list;
          }
        });
      }
    } else if (payload.type === 'MESSAGES_READ') {
      const data = payload.data;
      if (this.chatSeleccionado() && data.nro_emergencia === this.chatSeleccionado().nro_emergencia) {
        this.mensajes.update(msgs => msgs.map(m => m.id_remitente === this.myId ? { ...m, leido: true } : m));
      }
    }
  }

  esMio(msg: any): boolean {
    return msg.id_remitente === this.myId;
  }

  private scrollToBottom() {
    setTimeout(() => {
      if (this.scrollContainer) {
        this.scrollContainer.nativeElement.scrollTop = this.scrollContainer.nativeElement.scrollHeight;
      }
    }, 100);
  }
}
