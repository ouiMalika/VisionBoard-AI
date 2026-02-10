import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private base = 'http://localhost:8000/api/auth';
  private tokenKey = 'auth_token';

  constructor(private http: HttpClient) {}

  getToken(): string | null {
    return localStorage.getItem(this.tokenKey);
  }

  login(username: string, password: string): Observable<{ token: string }> {
    return this.http
      .post<{ token: string }>(`${this.base}/login/`, { username, password })
      .pipe(
        tap(res => localStorage.setItem(this.tokenKey, res.token))
      );
  }

  register(username: string, password: string, email: string): Observable<any> {
    return this.http.post(`${this.base}/register/`, {
      username,
      password,
      email,
    });
  }

  logout(): void {
    localStorage.removeItem(this.tokenKey);
  }
}
