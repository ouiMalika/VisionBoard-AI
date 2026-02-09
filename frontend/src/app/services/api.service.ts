import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, timer, switchMap, takeWhile, map, last } from 'rxjs';
import { ClusterResult } from '../models/image.model';

interface UploadResponse {
  image_urls: string[];
}

interface ClusterResponse {
  job_id: string;
}

interface JobStatusResponse {
  job_id: string;
  status: string;
  result: ClusterResult | null;
}

@Injectable({
  providedIn: 'root',
})
export class ApiService {
  private baseUrl = 'http://localhost:8000/api';

  constructor(private http: HttpClient) {}

  uploadImages(files: File[]): Observable<UploadResponse> {
    const formData = new FormData();
    for (const file of files) {
      formData.append('files', file);
    }
    return this.http.post<UploadResponse>(`${this.baseUrl}/upload/`, formData);
  }

  startClustering(imageUrls: string[], nClusters: number): Observable<ClusterResponse> {
    return this.http.post<ClusterResponse>(`${this.baseUrl}/cluster/`, {
      image_urls: imageUrls,
      n_clusters: nClusters,
    });
  }

  pollJobStatus(jobId: string): Observable<JobStatusResponse> {
    return timer(0, 2000).pipe(
      switchMap(() => this.http.get<JobStatusResponse>(`${this.baseUrl}/jobs/${jobId}/`)),
      takeWhile((res) => res.status === 'PENDING' || res.status === 'STARTED', true),
      last(),
    );
  }
}
