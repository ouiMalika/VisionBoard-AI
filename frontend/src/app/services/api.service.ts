import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface ImageData {
  id: number;
  url: string;
}

export interface BoardData {
  id: number;
  name: string;
  created_at: string;
  images: ImageData[];
  tags: string[];
}

export interface JobStatus {
  job_id: string;
  status: string;
  result: any;
}

@Injectable({ providedIn: 'root' })
export class ApiService {
  private base = 'http://localhost:8000/api';

  constructor(private http: HttpClient) {}

  upload(files: File[]): Observable<{ image_urls: string[] }> {
    const fd = new FormData();
    files.forEach((f) => fd.append('files', f));
    return this.http.post<{ image_urls: string[] }>(`${this.base}/upload/`, fd);
  }

  cluster(imageUrls: string[], nClusters: number, boardName: string): Observable<{ job_id: string }> {
    return this.http.post<{ job_id: string }>(`${this.base}/cluster/`, {
      image_urls: imageUrls,
      n_clusters: nClusters,
      board_name: boardName,
    });
  }

  jobStatus(jobId: string): Observable<JobStatus> {
    return this.http.get<JobStatus>(`${this.base}/jobs/${jobId}/`);
  }

  getBoards(): Observable<BoardData[]> {
    return this.http.get<BoardData[]>(`${this.base}/boards/`);
  }

  getBoard(id: number): Observable<BoardData> {
    return this.http.get<BoardData>(`${this.base}/boards/${id}/`);
  }

  updateBoard(id: number, data: { name?: string; tags?: string[] }): Observable<any> {
    return this.http.patch(`${this.base}/boards/${id}/`, data);
  }

  deleteBoard(id: number): Observable<any> {
    return this.http.delete(`${this.base}/boards/${id}/`);
  }
}
