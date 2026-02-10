import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable, firstValueFrom } from 'rxjs';

export interface ImageData {
  id: number;
  url: string;
}

export interface BoardData {
  id: number;
  name: string;
  created_at: string;
  images: { id: number; url: string }[];
  tags: string[];
}

@Injectable({ providedIn: 'root' })
export class ApiService {
  private base = 'http://localhost:8000/api';
  private authBase = 'http://localhost:8000/api/auth';
  private tokenKey = 'auth_token';

  constructor(private http: HttpClient) {}

  // ---------- AUTH (anonymous) ----------

  private get token(): string | null {
    return localStorage.getItem(this.tokenKey);
  }

  async ensureAnonymousToken(): Promise<void> {
    if (this.token) return;

    const res = await firstValueFrom(
      this.http.post<{ token: string }>(`${this.authBase}/anonymous/`, {})
    );

    localStorage.setItem(this.tokenKey, res.token);
  }

  private authHeaders() {
    if (!this.token) {
      throw new Error('No auth token');
    }

    return {
      headers: new HttpHeaders({
        Authorization: `Token ${this.token}`,
      }),
    };
  }

  // ---------- API ----------

  upload(files: File[]): Observable<{ image_urls: string[] }> {
    const fd = new FormData();
    files.forEach(f => fd.append('files', f));

    return this.http.post<{ image_urls: string[] }>(
      `${this.base}/upload/`,
      fd,
      this.authHeaders()
    );
  }

  cluster(imageUrls: string[], boardName: string): Observable<{ job_id: string }> {
    return this.http.post<{ job_id: string }>(
      `${this.base}/cluster/`,
      {
        image_urls: imageUrls,
        n_clusters: 3,
        board_name: boardName,
      },
      this.authHeaders()
    );
  }

  jobStatus(jobId: string): Observable<{ status: string }> {
    return this.http.get<{ status: string }>(
      `${this.base}/jobs/${jobId}/`,
      this.authHeaders()
    );
  }

  getBoards(): Observable<BoardData[]> {
    return this.http.get<BoardData[]>(
      `${this.base}/boards/`,
      this.authHeaders()
    );
  }
}
