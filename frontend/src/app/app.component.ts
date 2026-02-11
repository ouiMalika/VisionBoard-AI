import { Component, OnInit, OnDestroy, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { UploadComponent } from './components/upload/upload.component';
import { ClusterBoardComponent } from './components/cluster-board/cluster-board.component';
import { ApiService } from './services/api.service';
import { firstValueFrom } from 'rxjs';
import { UploadedImage, ClusterResult } from './models/image.model';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, UploadComponent, ClusterBoardComponent],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css',
})
export class AppComponent implements OnInit, OnDestroy {
  images: UploadedImage[] = [];
  clusterCount = 3;
  showBoard = false;
  uploading = false;
  error = '';
  clusterResult: ClusterResult = {};

  private pollTimer: ReturnType<typeof setInterval> | null = null;

  constructor(private api: ApiService, private cdr: ChangeDetectorRef) {}

  async ngOnInit(): Promise<void> {
    try {
      await this.api.ensureAnonymousToken();
    } catch {
      this.error = 'Could not connect to backend.';
    }
  }

  ngOnDestroy(): void {
    this.clearPoll();
  }

  onFilesAdded(files: File[]): void {
    const newImages: UploadedImage[] = files
      .filter(f => f.type.startsWith('image/'))
      .map(f => ({
        id: Math.random().toString(36).substr(2, 9),
        file: f,
        url: URL.createObjectURL(f),
      }));

    this.images = [...this.images, ...newImages];
  }

  onClusterCountChange(n: number): void {
    this.clusterCount = n;
  }

  async onCreateBoard(): Promise<void> {
    if (this.images.length === 0) {
      this.error = 'Please upload some images first!';
      return;
    }

    if (this.clusterCount < 1 || this.clusterCount > this.images.length) {
      this.error = `Please enter a valid number of clusters (1-${this.images.length})`;
      return;
    }

    this.error = '';
    this.uploading = true;

    try {
      // 1. Upload files to backend
      const files = this.images.map(img => img.file);
      const uploadRes = await firstValueFrom(this.api.upload(files));

      // 2. Trigger clustering
      const clusterRes = await firstValueFrom(
        this.api.cluster(uploadRes.image_urls, 'My Board', this.clusterCount)
      );

      // 3. Poll for results
      this.pollJob(clusterRes.job_id);
    } catch (err) {
      this.error = 'Upload failed. Is the backend running?';
      this.uploading = false;
    }
  }

  onBackToUpload(): void {
    this.showBoard = false;
    this.clusterResult = {};
    this.images = [];
    this.error = '';
  }

  private pollJob(jobId: string): void {
    this.clearPoll();

    this.pollTimer = setInterval(async () => {
      try {
        const job = await firstValueFrom(this.api.jobStatus(jobId));
        console.log('Poll:', job.status, job.result ? 'has result' : 'no result');

        if (job.status === 'SUCCESS' && job.result) {
          this.clearPoll();
          this.uploading = false;

          const result: ClusterResult = {};
          for (const [id, data] of Object.entries<any>(job.result)) {
            result[id] = data.images || data;
          }

          this.clusterResult = result;
          this.showBoard = true;
          console.log('showBoard set to true, detecting changes');
          this.cdr.detectChanges();
        } else if (job.status === 'FAILURE') {
          this.clearPoll();
          this.uploading = false;
          this.error = 'Clustering failed. Please try again.';
          this.cdr.detectChanges();
        }
      } catch {
        this.clearPoll();
        this.uploading = false;
        this.error = 'Lost connection while waiting for results.';
        this.cdr.detectChanges();
      }
    }, 2000);
  }

  private clearPoll(): void {
    if (this.pollTimer) {
      clearInterval(this.pollTimer);
      this.pollTimer = null;
    }
  }
}
