import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';
import { Observable, Subject } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ChatService {
  private http = inject(HttpClient);
  private apiUrl = environment.apiUrl;
  private socket?: WebSocket;
  
  // Subject para notificar nuevos mensajes a los componentes
  private messageSubject = new Subject<any>();
  public messages$ = this.messageSubject.asObservable();

  constructor() {}

  private getHeaders() {
    const token = localStorage.getItem('access_token');
    return {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    };
  }

  // --- MÉTODOS HTTP ---

  getChatsActivos(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/emergencias/chats/activos`, this.getHeaders());
  }

  getHistorial(nroEmergencia: number): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/emergencias/${nroEmergencia}/mensajes`, this.getHeaders());
  }

  enviarMensaje(nroEmergencia: number, mensaje: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/emergencias/${nroEmergencia}/mensajes`, { mensaje }, this.getHeaders());
  }

  marcarComoLeidos(nroEmergencia: number): Observable<any> {
    return this.http.put(`${this.apiUrl}/emergencias/${nroEmergencia}/mensajes/leer`, {}, this.getHeaders());
  }

  // --- MÉTODOS WEBSOCKET ---

  conectarTaller() {
    // Aseguramos que la URL no tenga doble slash y sea correcta
    const wsUrl = this.apiUrl.replace('http', 'ws').replace(/\/$/, '') + '/emergencias/ws/taller';
    console.log('🔌 Intentando conectar WebSocket a:', wsUrl);
    
    this.socket = new WebSocket(wsUrl);

    this.socket.onopen = () => {
      console.log('✅ WebSocket Chat Taller conectado con éxito');
    };

    this.socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.messageSubject.next(data);
      } catch (e) {
        console.error('❌ Error parseando mensaje WS:', e);
      }
    };

    this.socket.onclose = (event) => {
      console.log(`⚠️ WebSocket Chat Taller cerrado (Código: ${event.code}). Reintentando en 3s...`);
      setTimeout(() => this.conectarTaller(), 3000);
    };

    this.socket.onerror = (error) => {
      console.error('❌ Error en el WebSocket del Chat:', error);
    };
  }

  desconectar() {
    this.socket?.close();
  }
}
