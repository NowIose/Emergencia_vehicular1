import { Routes } from '@angular/router';
import { LoginComponent } from './features/auth/login/login.component';
import { RegisterComponent } from './features/auth/register/register.component';
import { HomeComponent } from './features/home/home.component';
import { EmergenciasTallerComponent } from './features/emergencia/emergencia.component';
<<<<<<< ours
=======
import { DashboardComponent } from './features/home/dashboard/dashboard.component';
import { ReportesComponent } from './features/reportes/reportes.component';
import { ReportesAdminComponent }from './features/reportes-admin/reportes-admin.component'
>>>>>>> theirs

export const routes: Routes = [
  // Cambiamos el redireccionamiento para que apunte a 'login'
  { path: '', redirectTo: 'login', pathMatch: 'full' },
  { path: 'login', component: LoginComponent },
  { path: 'register', component: RegisterComponent },
<<<<<<< ours
  { path: 'home', component: HomeComponent },
  { path: 'emergencia', component: EmergenciasTallerComponent }, // Asegúrate de tener un HomeComponent creado
=======
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
>>>>>>> theirs
];
