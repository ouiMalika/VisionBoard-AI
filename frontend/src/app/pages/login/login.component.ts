import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './login.component.html',
  styleUrl: './login.component.scss',
})
export class LoginComponent {
  isRegister = false;
  username = '';
  password = '';
  email = '';
  error = '';

  constructor(private auth: AuthService, private router: Router) {}

  submit() {
    this.error = '';

    if (this.isRegister) {
      this.auth.register(this.username, this.password, this.email).subscribe({
        next: () => this.router.navigate(['/']),
        error: (err) => (this.error = err.error?.error || 'Registration failed'),
      });
    } else {
      this.auth.login(this.username, this.password).subscribe({
        next: () => this.router.navigate(['/']),
        error: (err) => (this.error = err.error?.error || 'Login failed'),
      });
    }
  }

  toggleMode() {
    this.isRegister = !this.isRegister;
    this.error = '';
  }
}
