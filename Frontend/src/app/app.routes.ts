import { Routes } from '@angular/router';
import { LoginComponent } from './features/auth/login/login.component';
import { RegisterComponent } from './features/auth/register/register.component';
import { HomeComponent } from './features/home/home.component';
import { LandingComponent } from './features/home-page/landing.component';
import { ChatComponent } from './features/chat/chat.component';
import { EmergenciasTallerComponent } from './features/emergencia/emergencia.component';
import { DashboardComponent } from './features/home/dashboard/dashboard.component';
import { ReportesComponent } from './features/reportes/reportes.component';
import { ReportesAdminComponent }from './features/reportes-admin/reportes-admin.component'

export const routes: Routes = [
  { path: '', redirectTo: 'landing', pathMatch: 'full' },
  { path: 'landing', component: LandingComponent },
  { path: 'login', component: LoginComponent },
  { path: 'register', component: RegisterComponent },
  { 
    path: 'home', 
    component: HomeComponent,
    children: [
      { path: '', component: DashboardComponent },
      { path: 'emergencia', component: EmergenciasTallerComponent },
      { path: 'chat', component: ChatComponent },
      { path: 'reportes', component:ReportesComponent},
      { path: 'reportes-admin', component:ReportesAdminComponent},
    ]
  },
];
