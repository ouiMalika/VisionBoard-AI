import { Routes } from '@angular/router';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from './services/auth.service';
import { UploadComponent } from './pages/upload/upload.component';
import { BoardsComponent } from './pages/boards/boards.component';
import { BoardDetailComponent } from './pages/board-detail/board-detail.component';
import { LoginComponent } from './pages/login/login.component';

const authGuard = () => {
  const auth = inject(AuthService);
  const router = inject(Router);
  if (auth.getToken()) return true;
  return router.createUrlTree(['/login']);
};

export const routes: Routes = [
  { path: 'login', component: LoginComponent },
  { path: '', component: UploadComponent, canActivate: [authGuard] },
  { path: 'boards', component: BoardsComponent, canActivate: [authGuard] },
  { path: 'boards/:id', component: BoardDetailComponent, canActivate: [authGuard] },
];
