import { Routes } from '@angular/router';
import { LoginComponent } from './features/auth/login/login.component';
import { RegisterComponent } from './features/auth/register/register.component';
import { HomeComponent } from './features/home/home.component';
import { LandingComponent } from './features/home-page/landing.component';
import { ChatComponent } from './features/chat/chat.component';
import { EmergenciasTallerComponent } from './features/emergencia/emergencia.component';

export const routes: Routes = [
  // Cambiamos el redireccionamiento para que apunte a 'login'
  { path: '', redirectTo: 'landing', pathMatch: 'full' },
  { path: 'landing', component: LandingComponent },
  { path: 'login', component: LoginComponent },
  { path: 'register', component: RegisterComponent },
  { path: 'home', component: HomeComponent },
  { path: 'emergencia', component: EmergenciasTallerComponent },
  { path: 'chat', component: ChatComponent },
];
